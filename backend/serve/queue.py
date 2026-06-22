"""异步任务队列 - 单 worker 串行处理 CPU 推理"""
import asyncio
import logging
import uuid
import time
from dataclasses import dataclass, field
from typing import Any, Optional, List, Callable
from PIL import Image

logger = logging.getLogger(__name__)

DEFAULT_TIME_PER_STEP_S = 1.5
MAX_QUEUE_SIZE = 20
RESULT_TTL_SECONDS = 1800  # 30 分钟


@dataclass
class TaskState:
    task_id: str
    params: dict
    status: str = "queued"   # queued / running / done / failed
    queue_position: int = 0
    progress: float = 0.0
    current_step: int = 0
    total_steps: int = 0
    images: Optional[List[Image.Image]] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None


class TaskQueue:
    def __init__(self, pipeline_provider):
        self.pipeline_provider = pipeline_provider
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=MAX_QUEUE_SIZE)
        self.tasks: dict[str, TaskState] = {}
        self._worker_task = None
        self._shutdown = False

    def start(self):
        if self._worker_task is None:
            self._worker_task = asyncio.create_task(self._worker())

    async def shutdown(self):
        self._shutdown = True
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

    async def submit(self, params: dict) -> str:
        if self.queue.full():
            raise RuntimeError("队列已满,稍后再试")
        task_id = uuid.uuid4().hex[:12]
        state = TaskState(
            task_id=task_id,
            params=params,
            queue_position=self.queue.qsize() + 1,
            total_steps=params.get("steps", 6),
        )
        self.tasks[task_id] = state
        await self.queue.put(task_id)
        if self._worker_task is None:
            self.start()
        self._cleanup_old()
        return task_id

    def get_state(self, task_id: str) -> Optional[TaskState]:
        return self.tasks.get(task_id)

    def estimated_seconds(self, state: TaskState) -> int:
        return int(state.total_steps * DEFAULT_TIME_PER_STEP_S * state.queue_position)

    async def _worker(self):
        while not self._shutdown:
            try:
                task_id = await self.queue.get()
            except asyncio.CancelledError:
                return
            state = self.tasks.get(task_id)
            if state is None:
                continue
            state.status = "running"
            state.queue_position = 0
            try:
                params = state.params

                def _progress(step, total):
                    state.current_step = step
                    state.total_steps = total
                    state.progress = step / total if total else 0

                # 真实推理(在线程池里跑,避免阻塞事件循环)
                loop = asyncio.get_event_loop()
                images = await loop.run_in_executor(
                    None,
                    lambda: self.pipeline_provider.generate_for_params(params, _progress),
                )
                state.images = images
                state.status = "done"
                state.completed_at = time.time()
            except Exception as e:
                logger.exception("任务失败")
                state.status = "failed"
                state.error = str(e)
                state.completed_at = time.time()

    def _cleanup_old(self):
        now = time.time()
        to_drop = [
            tid for tid, s in self.tasks.items()
            if s.completed_at and now - s.completed_at > RESULT_TTL_SECONDS
        ]
        for tid in to_drop:
            del self.tasks[tid]
