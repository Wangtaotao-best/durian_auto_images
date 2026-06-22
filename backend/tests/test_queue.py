"""测试任务队列状态机"""
import asyncio
import pytest
from backend.serve.queue import TaskQueue, TaskState


class FakePipeline:
    def __init__(self, delay=0.01):
        self.delay = delay

    def generate_for_params(self, params, progress_cb=None):
        import time
        time.sleep(self.delay)
        if progress_cb:
            progress_cb(params.get("steps", 1), params.get("steps", 1))
        from PIL import Image
        return [Image.new("RGB", (8, 8))]


@pytest.mark.asyncio
async def test_submit_returns_task_id():
    q = TaskQueue(FakePipeline())
    task_id = await q.submit({"variety": "x", "steps": 1})
    assert isinstance(task_id, str)
    assert len(task_id) >= 6
    await q.shutdown()


@pytest.mark.asyncio
async def test_task_completes():
    q = TaskQueue(FakePipeline())
    task_id = await q.submit({"variety": "x", "steps": 1})
    # 等任务完成
    for _ in range(50):
        await asyncio.sleep(0.05)
        s = q.get_state(task_id)
        if s.status == "done":
            break
    assert s.status == "done"
    assert s.images is not None and len(s.images) == 1
    await q.shutdown()
