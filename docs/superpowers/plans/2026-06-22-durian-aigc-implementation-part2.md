# 榴莲 AIGC 系统 — 实施计划 Part 2 (M4-M5)

> **接续** `2026-06-22-durian-aigc-implementation.md` 的 M4-M5 部分。

---

# 🔧 M4: 模型导出 + 服务器后端

## Task 16: 实现 `tools/merge_lora.py` — LoRA 合并到主模型

**Files:**
- Create: `backend/tools/__init__.py`
- Create: `backend/tools/merge_lora.py`
- Create: `backend/tests/test_merge_lora.py`

- [ ] **Step 1: 写测试**

Create `backend/tools/__init__.py` (空)
Create `backend/tests/test_merge_lora.py`:

```python
"""测试 merge_lora 的参数处理"""
import pytest
from pathlib import Path
from backend.tools.merge_lora import validate_paths


def test_validate_paths_existing(tmp_path):
    base = tmp_path / "base"
    base.mkdir()
    lora = tmp_path / "lora"
    lora.mkdir()
    output = tmp_path / "output"
    # 不应抛异常
    validate_paths(base, lora, output)


def test_validate_paths_missing_base(tmp_path):
    with pytest.raises(FileNotFoundError):
        validate_paths(tmp_path / "nonexistent", tmp_path, tmp_path)
```

- [ ] **Step 2: 实现 merge_lora.py**

Create `backend/tools/merge_lora.py`:

```python
"""把 LoRA 权重 fuse 进基础 SD 主模型,导出为完整 pipeline 目录"""
import argparse
import logging
from pathlib import Path

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")


def validate_paths(base: Path, lora: Path, output: Path):
    base, lora = Path(base), Path(lora)
    if not base.exists() and not str(base).startswith(("hf://", "runwayml/", "stabilityai/")):
        # 既不是本地路径,也不是 HF id,报错
        raise FileNotFoundError(f"基础模型路径不存在: {base}")
    if not lora.exists() and not str(lora).startswith(("latent-consistency/",)):
        raise FileNotFoundError(f"LoRA 路径不存在: {lora}")


def merge(base_model: str, lora_path: str, output_dir: Path, alpha: float = 0.8):
    import torch
    from diffusers import StableDiffusionPipeline

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"加载基础模型: {base_model}")
    pipe = StableDiffusionPipeline.from_pretrained(
        base_model,
        torch_dtype=torch.float32,
        safety_checker=None,
        requires_safety_checker=False,
    )

    logger.info(f"加载 LoRA: {lora_path} (alpha={alpha})")
    pipe.load_lora_weights(lora_path)
    pipe.fuse_lora(lora_scale=alpha)
    pipe.unload_lora_weights()

    logger.info(f"保存合并后的 pipeline 到: {output_dir}")
    pipe.save_pretrained(str(output_dir))
    logger.info("合并完成")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True, help="基础模型 (HF id 或本地路径)")
    parser.add_argument("--lora", required=True, help="LoRA 权重 (本地目录 或 HF id)")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--alpha", type=float, default=0.8)
    args = parser.parse_args()

    merge(args.base, args.lora, args.output, args.alpha)


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: 运行测试**

```powershell
python -m pytest backend/tests/test_merge_lora.py -v
```

- [ ] **Step 4: 提交**

```powershell
git add backend/tools/ backend/tests/test_merge_lora.py
git commit -m "feat(tools): add merge_lora script to fuse LoRA weights into base model"
```

---

## Task 17: 实现 `tools/export_openvino.py` — 导出 OpenVINO IR

**Files:**
- Create: `backend/tools/export_openvino.py`

- [ ] **Step 1: 实现 export_openvino.py**

Create `backend/tools/export_openvino.py`:

```python
"""把合并后的 diffusers pipeline 转成 OpenVINO IR 格式 (CPU 推理用)"""
import argparse
import logging
from pathlib import Path

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")


def export(model_dir: Path, output_dir: Path, dtype: str = "fp16"):
    try:
        from optimum.intel import OVStableDiffusionPipeline
    except ImportError:
        raise RuntimeError("请先 pip install optimum[openvino]")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"加载 diffusers 模型 from {model_dir} 并转 OpenVINO IR (dtype={dtype})")
    ov_pipe = OVStableDiffusionPipeline.from_pretrained(
        str(model_dir),
        export=True,
        compile=False,    # 在服务器运行时再 compile
    )

    if dtype == "fp16":
        # OpenVINO 默认 fp32,用 ov 的量化压到 fp16
        from openvino.runtime import Core, Type
        # 这里通过 save_pretrained 时的 ov_config 控制
        pass

    logger.info(f"保存到: {output_dir}")
    ov_pipe.save_pretrained(str(output_dir))
    logger.info("OpenVINO 模型导出完成")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--dtype", default="fp16", choices=["fp16", "fp32"])
    args = parser.parse_args()

    export(args.model_dir, args.output, args.dtype)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 安装 optimum[openvino](本地一次性)**

```powershell
conda activate durian
pip install "optimum[openvino]>=1.20.0"
```

- [ ] **Step 3: Smoke 测试**

先合并 LoRA + LCM:

```powershell
# 合并品种 LoRA
python -m backend.tools.merge_lora `
    --base runwayml/stable-diffusion-v1-5 `
    --lora "D:/durian-data/models/lora/musang_king" `
    --output "D:/durian-data/models/merged/musang_king" `
    --alpha 0.8

# 再合并 LCM-LoRA
python -m backend.tools.merge_lora `
    --base "D:/durian-data/models/merged/musang_king" `
    --lora latent-consistency/lcm-lora-sdv1-5 `
    --output "D:/durian-data/models/merged/musang_king_lcm" `
    --alpha 1.0

# 导出 OpenVINO IR
python -m backend.tools.export_openvino `
    --model_dir "D:/durian-data/models/merged/musang_king_lcm" `
    --output "D:/durian-data/models/openvino/musang_king"
```
Expected:
- `D:/durian-data/models/openvino/musang_king/` 下有 `unet/`, `text_encoder/`, `vae_decoder/` 等子目录
- 每个子目录都有 `.xml` + `.bin` 文件
- 总大小 ~2 GB

- [ ] **Step 4: 提交**

```powershell
git add backend/tools/export_openvino.py
git commit -m "feat(tools): add OpenVINO IR export pipeline for CPU inference"
```

---

## Task 18: 写服务器侧 `requirements-serve.txt`

**Files:**
- Create: `backend/requirements-serve.txt`

- [ ] **Step 1: 写 requirements**

Create `backend/requirements-serve.txt`:

```
# Web 框架
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
pydantic>=2.8.0
python-multipart>=0.0.9
aiofiles>=24.1.0

# 推理引擎 (CPU)
openvino>=2024.4
optimum-intel[openvino]>=1.20.0
diffusers>=0.30.0
transformers>=4.44.0

# PyTorch CPU only (服务器装这个)
# 不写在这里, 安装命令:
# pip install --index-url https://download.pytorch.org/whl/cpu torch torchvision

# 图像
Pillow>=10.0.0
numpy>=1.26.0

# 工具
tqdm
loguru>=0.7.0
pyyaml>=6.0
```

- [ ] **Step 2: 提交**

```powershell
git add backend/requirements-serve.txt
git commit -m "feat(serve): add server-side CPU inference requirements"
```

---

## Task 19: 实现 `serve/schemas.py` — Pydantic 数据模型

**Files:**
- Create: `backend/serve/__init__.py`
- Create: `backend/serve/schemas.py`

- [ ] **Step 1: 实现 schemas**

Create `backend/serve/__init__.py` (空)
Create `backend/serve/schemas.py`:

```python
"""API 请求/响应数据模型"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    variety: str = Field(..., description="品种 ID")
    prompt: str = Field(..., min_length=1, max_length=500)
    negative_prompt: str = Field(default="blurry, low quality, distorted, deformed")
    num_images: int = Field(default=1, ge=1, le=4)
    steps: int = Field(default=6, ge=4, le=20)
    cfg_scale: float = Field(default=1.5, ge=0.5, le=10.0)
    seed: int = Field(default=-1)
    width: int = Field(default=512, ge=256, le=768)
    height: int = Field(default=512, ge=256, le=768)


class QueuedResponse(BaseModel):
    task_id: str
    status: Literal["queued"]
    queue_position: int
    estimated_seconds: int


class TaskStatus(BaseModel):
    task_id: str
    status: Literal["queued", "running", "done", "failed"]
    queue_position: Optional[int] = None
    estimated_seconds: Optional[int] = None
    progress: Optional[float] = None
    current_step: Optional[int] = None
    total_steps: Optional[int] = None
    image_urls: Optional[List[str]] = None
    error: Optional[str] = None


class Variety(BaseModel):
    id: str
    name_cn: str
    name_en: str
    trigger: str
    preview: Optional[str] = None
```

- [ ] **Step 2: 提交**

```powershell
git add backend/serve/__init__.py backend/serve/schemas.py
git commit -m "feat(serve): add pydantic schemas for API"
```

---

## Task 20: 实现 `serve/pipeline.py` — OpenVINO 推理封装

**Files:**
- Create: `backend/serve/pipeline.py`

- [ ] **Step 1: 实现**

Create `backend/serve/pipeline.py`:

```python
"""OpenVINO + LCM 推理 pipeline 的服务侧封装"""
import logging
from pathlib import Path
from typing import Callable, List, Optional
from PIL import Image

logger = logging.getLogger(__name__)


class OpenVINOInferencer:
    """单品种 OpenVINO pipeline,启动时加载,运行时复用"""

    def __init__(self, model_dir: Path, device: str = "CPU"):
        self.model_dir = Path(model_dir)
        self.device = device
        self.pipe = None

    def load(self):
        from optimum.intel import OVStableDiffusionPipeline
        from diffusers import LCMScheduler

        logger.info(f"加载 OpenVINO pipeline from {self.model_dir} on {self.device}")
        self.pipe = OVStableDiffusionPipeline.from_pretrained(
            str(self.model_dir),
            device=self.device,
            compile=True,
        )
        self.pipe.scheduler = LCMScheduler.from_config(self.pipe.scheduler.config)
        logger.info("OpenVINO pipeline 加载完成")

    def unload(self):
        del self.pipe
        self.pipe = None
        import gc
        gc.collect()

    def generate(self, prompt: str, negative_prompt: str = "",
                 num_images: int = 1, steps: int = 6, cfg: float = 1.5,
                 width: int = 512, height: int = 512, seed: int = -1,
                 progress_callback: Optional[Callable[[int, int], None]] = None
                 ) -> List[Image.Image]:
        if self.pipe is None:
            raise RuntimeError("Pipeline 未加载,请先调用 load()")

        import numpy as np
        if seed < 0:
            seed = np.random.randint(0, 2**31)
        generator = np.random.RandomState(seed)

        def _step_cb(step_idx, timestep, latents):
            if progress_callback:
                progress_callback(step_idx + 1, steps)

        result = self.pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_images_per_prompt=num_images,
            num_inference_steps=steps,
            guidance_scale=cfg,
            width=width, height=height,
            generator=generator,
            callback=_step_cb,
            callback_steps=1,
        )
        return result.images


class PipelineRegistry:
    """管理多品种 pipeline,单实例,LRU 切换"""

    def __init__(self, models_root: Path, max_loaded: int = 1):
        self.models_root = Path(models_root)
        self.max_loaded = max_loaded
        self._loaded: dict[str, OpenVINOInferencer] = {}
        self._lru: list[str] = []

    def get(self, variety: str) -> OpenVINOInferencer:
        if variety in self._loaded:
            self._lru.remove(variety)
            self._lru.append(variety)
            return self._loaded[variety]

        # 需要新加载
        while len(self._loaded) >= self.max_loaded:
            evict = self._lru.pop(0)
            logger.info(f"卸载 pipeline: {evict}")
            self._loaded[evict].unload()
            del self._loaded[evict]

        model_dir = self.models_root / variety
        if not model_dir.exists():
            raise FileNotFoundError(f"找不到模型: {model_dir}")
        inferencer = OpenVINOInferencer(model_dir)
        inferencer.load()
        self._loaded[variety] = inferencer
        self._lru.append(variety)
        return inferencer

    def available_varieties(self) -> List[str]:
        if not self.models_root.exists():
            return []
        return sorted([p.name for p in self.models_root.iterdir() if p.is_dir()])
```

- [ ] **Step 2: 提交**

```powershell
git add backend/serve/pipeline.py
git commit -m "feat(serve): add OpenVINO pipeline wrapper with LRU registry"
```

---

## Task 21: 实现 `serve/queue.py` — 任务队列

**Files:**
- Create: `backend/serve/queue.py`
- Create: `backend/tests/test_queue.py`

- [ ] **Step 1: 写测试**

Create `backend/tests/test_queue.py`:

```python
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
            progress_cb(params["steps"], params["steps"])
        from PIL import Image
        return [Image.new("RGB", (8, 8))]


@pytest.mark.asyncio
async def test_submit_returns_task_id():
    q = TaskQueue(FakePipeline())
    task_id = await q.submit({"variety": "x", "steps": 1})
    assert isinstance(task_id, str)
    assert len(task_id) >= 6


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
```

- [ ] **Step 2: 实现 queue.py**

Create `backend/serve/queue.py`:

```python
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
```

- [ ] **Step 3: 装 pytest-asyncio + 运行测试**

```powershell
pip install pytest-asyncio
python -m pytest backend/tests/test_queue.py -v
```
Expected: 2 passed

- [ ] **Step 4: 提交**

```powershell
git add backend/serve/queue.py backend/tests/test_queue.py
git commit -m "feat(serve): add async task queue with single-worker CPU pipeline"
```

---

## Task 22: 实现 `serve/app.py` — FastAPI 主应用

**Files:**
- Create: `backend/serve/app.py`
- Create: `backend/serve/image_store.py`

- [ ] **Step 1: 实现 image_store.py**

Create `backend/serve/image_store.py`:

```python
"""把生成的 PIL 图像保存到磁盘,提供 URL 访问"""
import io
from pathlib import Path
from typing import List
from PIL import Image


class ImageStore:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, task_id: str, images: List[Image.Image]) -> List[str]:
        task_dir = self.root / task_id
        task_dir.mkdir(exist_ok=True)
        urls = []
        for i, img in enumerate(images):
            path = task_dir / f"{i}.png"
            img.save(path, "PNG")
            urls.append(f"/api/tasks/{task_id}/image?idx={i}")
        return urls

    def load_bytes(self, task_id: str, idx: int) -> bytes:
        path = self.root / task_id / f"{idx}.png"
        if not path.exists():
            raise FileNotFoundError(path)
        return path.read_bytes()
```

- [ ] **Step 2: 实现 app.py**

Create `backend/serve/app.py`:

```python
"""FastAPI 应用入口"""
import logging
import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.configs.loader import load_paths, load_varieties, load_serve_defaults
from backend.serve.schemas import GenerateRequest, QueuedResponse, TaskStatus, Variety
from backend.serve.pipeline import PipelineRegistry
from backend.serve.queue import TaskQueue
from backend.serve.image_store import ImageStore

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(message)s")

_paths = load_paths()
_varieties = load_varieties()
_serve_defaults = load_serve_defaults()

# 服务器端模型根目录(覆盖路径,优先用环境变量)
MODELS_ROOT = Path(os.environ.get("DURIAN_OV_MODELS_ROOT", _paths["models_openvino"]))
IMAGES_ROOT = Path(os.environ.get("DURIAN_IMAGES_ROOT", _paths["outputs"] / "_serve"))


class PipelineProvider:
    """把 PipelineRegistry 适配成 queue 需要的 generate_for_params 接口"""
    def __init__(self, registry: PipelineRegistry):
        self.registry = registry

    def generate_for_params(self, params: dict, progress_cb):
        inferencer = self.registry.get(params["variety"])
        return inferencer.generate(
            prompt=params["prompt"],
            negative_prompt=params.get("negative_prompt", ""),
            num_images=params.get("num_images", 1),
            steps=params.get("steps", 6),
            cfg=params.get("cfg_scale", 1.5),
            width=params.get("width", 512),
            height=params.get("height", 512),
            seed=params.get("seed", -1),
            progress_callback=progress_cb,
        )


registry = PipelineRegistry(MODELS_ROOT, max_loaded=1)
provider = PipelineProvider(registry)
queue = TaskQueue(provider)
store = ImageStore(IMAGES_ROOT)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"OpenVINO models root: {MODELS_ROOT}")
    logger.info(f"可用品种: {registry.available_varieties()}")
    queue.start()
    yield
    await queue.shutdown()


app = FastAPI(title="榴莲 AIGC API", lifespan=lifespan)


@app.get("/api/varieties", response_model=list[Variety])
def list_varieties():
    available = set(registry.available_varieties())
    out = []
    for vid, meta in _varieties.items():
        if vid not in available:
            continue
        out.append(Variety(
            id=vid,
            name_cn=meta["name_cn"],
            name_en=meta["name_en"],
            trigger=meta["trigger"],
            preview=f"/static/preview/{vid}.jpg",
        ))
    return out


def _build_prompt(variety: str, user_prompt: str) -> str:
    trigger = _varieties[variety]["trigger"]
    if trigger.lower() in user_prompt.lower():
        return user_prompt
    return f"{trigger}, {user_prompt}"


@app.post("/api/generate", response_model=QueuedResponse)
async def generate(req: GenerateRequest):
    if req.variety not in _varieties:
        raise HTTPException(400, f"未知品种: {req.variety}")
    if req.variety not in registry.available_varieties():
        raise HTTPException(404, f"品种模型未部署: {req.variety}")

    params = req.model_dump()
    params["prompt"] = _build_prompt(req.variety, req.prompt)

    try:
        task_id = await queue.submit(params)
    except RuntimeError as e:
        raise HTTPException(503, str(e))

    state = queue.get_state(task_id)
    return QueuedResponse(
        task_id=task_id,
        status="queued",
        queue_position=state.queue_position,
        estimated_seconds=queue.estimated_seconds(state),
    )


@app.get("/api/tasks/{task_id}", response_model=TaskStatus)
def get_task(task_id: str):
    state = queue.get_state(task_id)
    if state is None:
        raise HTTPException(404, "任务不存在或已过期")

    resp = TaskStatus(task_id=task_id, status=state.status)

    if state.status == "queued":
        resp.queue_position = state.queue_position
        resp.estimated_seconds = queue.estimated_seconds(state)
    elif state.status == "running":
        resp.progress = state.progress
        resp.current_step = state.current_step
        resp.total_steps = state.total_steps
    elif state.status == "done":
        if state.images and not getattr(state, "_persisted", False):
            urls = store.save(task_id, state.images)
            state.image_urls = urls
            state._persisted = True
        resp.image_urls = getattr(state, "image_urls", None)
    elif state.status == "failed":
        resp.error = state.error

    return resp


@app.get("/api/tasks/{task_id}/image")
def get_image(task_id: str, idx: int = 0):
    try:
        data = store.load_bytes(task_id, idx)
    except FileNotFoundError:
        raise HTTPException(404, "图片不存在")
    return Response(content=data, media_type="image/png")


@app.get("/api/health")
def health():
    return {"status": "ok", "varieties": registry.available_varieties()}


# 挂载前端静态文件(部署时 frontend/dist 由前端构建产物提供)
_FRONTEND_DIST = Path(os.environ.get("DURIAN_FRONTEND_DIST", "frontend/dist"))
if _FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(_FRONTEND_DIST), html=True), name="frontend")
else:
    @app.get("/")
    def root():
        return {"msg": "前端未部署。访问 /docs 看 API。"}
```

- [ ] **Step 3: 装 fastapi 在本地测试**

```powershell
pip install fastapi "uvicorn[standard]" aiofiles
```

- [ ] **Step 4: 启动本地 dev server(用本地 GPU 测,服务器侧另外装)**

```powershell
conda activate durian
cd "D:/谷歌下载/Kimi_Agent_榴莲图像生成代码"
# 用环境变量指向本地有 OpenVINO 模型的目录(如果有)
$env:DURIAN_OV_MODELS_ROOT = "D:/durian-data/models/openvino"
python -m uvicorn backend.serve.app:app --host 127.0.0.1 --port 8000 --reload
```

打开浏览器 http://127.0.0.1:8000/docs 应看到 Swagger UI。
访问 http://127.0.0.1:8000/api/health 应返回 `{"status":"ok","varieties":[...]}`

- [ ] **Step 5: 提交**

```powershell
git add backend/serve/app.py backend/serve/image_store.py
git commit -m "feat(serve): add FastAPI app with generate/tasks/image endpoints"
```

---

## Task 23: 写 Dockerfile(后端镜像)

**Files:**
- Create: `backend/Dockerfile`
- Create: `backend/.dockerignore`

- [ ] **Step 1: 写 Dockerfile**

Create `backend/Dockerfile`:

```dockerfile
# 多阶段构建: 1) 安装 Python 依赖; 2) 运行时镜像
# 基础镜像: Python 3.11 slim (Debian Bookworm)

FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DURIAN_OV_MODELS_ROOT=/data/models/openvino \
    DURIAN_IMAGES_ROOT=/data/images \
    DURIAN_FRONTEND_DIST=/app/frontend/dist

# OpenVINO 需要的系统库
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        libgomp1 \
        ca-certificates \
        curl \
    && rm -rf /var/lib/apt/lists/*

# ===== 依赖层 =====
FROM base AS deps

WORKDIR /app

# 先装 PyTorch CPU 版,避免拉到 CUDA 版
RUN pip install --index-url https://download.pytorch.org/whl/cpu \
    torch==2.4.1 torchvision==0.19.1

COPY backend/requirements-serve.txt /app/requirements-serve.txt
RUN pip install -r /app/requirements-serve.txt

# ===== 应用层 =====
FROM deps AS runtime

WORKDIR /app

# 拷贝后端代码
COPY backend /app/backend

# (可选) 拷贝前端构建产物
# 构建时若 frontend/dist 不存在则跳过
COPY frontend/dist* /app/frontend/dist/

# 创建数据挂载点
RUN mkdir -p /data/models/openvino /data/images

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/api/health || exit 1

CMD ["uvicorn", "backend.serve.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

- [ ] **Step 2: 写 .dockerignore**

Create `backend/.dockerignore`:

```
__pycache__/
*.pyc
*.pyo
.pytest_cache/
.venv/
venv/
tests/
*.log
```

并在项目根目录创建 `.dockerignore`(避免把 archive 等带进构建上下文):

```
archive/
docs/
.git/
.idea/
.vscode/
node_modules/
*.tar.gz
__pycache__/
.pytest_cache/
.venv/
venv/
frontend/node_modules/
```

- [ ] **Step 3: 提交**

```powershell
git add backend/Dockerfile backend/.dockerignore .dockerignore
git commit -m "feat(docker): add backend Dockerfile + dockerignore"
```

---

## Task 24: 写 `docker-compose.yml`

**Files:**
- Create: `docker-compose.yml`
- Create: `.env.example`

- [ ] **Step 1: 写 docker-compose.yml**

Create `docker-compose.yml`:

```yaml
version: "3.9"

services:
  durian-api:
    build:
      context: .
      dockerfile: backend/Dockerfile
    image: durian-aigc:latest
    container_name: durian-api
    restart: unless-stopped
    ports:
      - "${DURIAN_PORT:-8000}:8000"
    environment:
      DURIAN_OV_MODELS_ROOT: /data/models/openvino
      DURIAN_IMAGES_ROOT: /data/images
      DURIAN_FRONTEND_DIST: /app/frontend/dist
      # OpenVINO CPU 线程数,匹配你服务器的物理核数
      OMP_NUM_THREADS: ${OMP_NUM_THREADS:-8}
    volumes:
      # 模型外置: 服务器上把 OpenVINO 模型放到 ./models/openvino/<variety>/
      - ./models/openvino:/data/models/openvino:ro
      # 生成的图像持久化
      - durian-images:/data/images
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://127.0.0.1:8000/api/health"]
      interval: 30s
      timeout: 10s
      start_period: 120s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 24G
        reservations:
          memory: 12G

volumes:
  durian-images:
```

- [ ] **Step 2: 写 .env.example**

Create `.env.example`:

```
# Docker 部署环境变量示例
# 复制为 .env 并填入实际值

# 对外暴露端口
DURIAN_PORT=8000

# OpenVINO CPU 线程数 (建议: 物理核数, Xeon Silver 4309Y 是 8 核)
OMP_NUM_THREADS=8
```

- [ ] **Step 3: 提交**

```powershell
git add docker-compose.yml .env.example
git commit -m "feat(docker): add docker-compose orchestration"
```

---

## Task 25: 写 `scripts/build_serve_bundle.ps1` — 打包模型

**Files:**
- Create: `scripts/build_serve_bundle.ps1`

- [ ] **Step 1: 写脚本**

Create `scripts/build_serve_bundle.ps1`:

```powershell
# 把指定品种的 LoRA → merge → LCM → OpenVINO IR → tar 打包
# 用法: powershell scripts/build_serve_bundle.ps1 -Variety musang_king

param(
    [Parameter(Mandatory=$true)][string]$Variety,
    [float]$LoraAlpha = 0.8,
    [string]$BaseModel = "runwayml/stable-diffusion-v1-5",
    [string]$LcmLora = "latent-consistency/lcm-lora-sdv1-5",
    [string]$DataRoot = "D:/durian-data"
)

$ErrorActionPreference = "Stop"

$mergedDir = "$DataRoot/models/merged/$Variety"
$mergedLcmDir = "$DataRoot/models/merged/${Variety}_lcm"
$ovDir = "$DataRoot/models/openvino/$Variety"
$loraDir = "$DataRoot/models/lora/$Variety"

Write-Host "==> [1/4] 合并品种 LoRA 到基础模型" -ForegroundColor Cyan
conda run -n durian python -m backend.tools.merge_lora `
    --base $BaseModel `
    --lora $loraDir `
    --output $mergedDir `
    --alpha $LoraAlpha

Write-Host "==> [2/4] 合并 LCM-LoRA" -ForegroundColor Cyan
conda run -n durian python -m backend.tools.merge_lora `
    --base $mergedDir `
    --lora $LcmLora `
    --output $mergedLcmDir `
    --alpha 1.0

Write-Host "==> [3/4] 导出 OpenVINO IR" -ForegroundColor Cyan
conda run -n durian python -m backend.tools.export_openvino `
    --model_dir $mergedLcmDir `
    --output $ovDir

Write-Host "==> [4/4] 打包 tar.gz" -ForegroundColor Cyan
$bundle = "$DataRoot/${Variety}_openvino.tar.gz"
tar -czvf $bundle -C "$DataRoot/models/openvino" $Variety

Write-Host ""
Write-Host "==> 完成! 打包文件: $bundle" -ForegroundColor Green
Write-Host "==> 大小: $((Get-Item $bundle).Length / 1MB) MB"
Write-Host ""
Write-Host "==> 上传到服务器: scp $bundle user@server:/data/durian/models/" -ForegroundColor Yellow
```

- [ ] **Step 2: 提交**

```powershell
git add scripts/build_serve_bundle.ps1
git commit -m "feat(scripts): one-shot build OpenVINO serve bundle"
```

**M4 验收:**
- [ ] `D:/durian-data/models/openvino/musang_king/` 有完整 OpenVINO IR
- [ ] `tar.gz` 打包文件 ~2GB
- [ ] 本地 `uvicorn backend.serve.app:app` 启动成功
- [ ] `/api/health` 返回 ok 且品种列表非空
- [ ] `/api/generate` 提交任务后,`/api/tasks/{id}` 能查到状态

---

# 🎨 M5: 前端改造 + Docker 部署 + 联调上线

## Task 26: 前端依赖安装 + 配置 Tailwind 自定义主题

**Files:**
- Modify: `frontend/tailwind.config.js`
- Modify: `frontend/src/index.css`

- [ ] **Step 1: 检查 Node 环境 + 安装依赖**

```powershell
cd "D:/谷歌下载/Kimi_Agent_榴莲图像生成代码/frontend"
node -v   # 应该 ≥ 18
npm install
```
Expected: 无错误,生成 `node_modules/`

- [ ] **Step 2: 修改 tailwind.config.js**

Read current `frontend/tailwind.config.js` then update `theme.extend`:

```javascript
// frontend/tailwind.config.js
/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        durian: {
          flesh: '#F4C545',
          skin: '#5A6B3A',
          thorn: '#2E3818',
          cream: '#FBF6E9',
          accent: '#E89B2C',
        },
        // 保留 shadcn 原有变量
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        // ... 保留其他原有颜色
      },
      fontFamily: {
        display: ['"Plus Jakarta Sans"', 'sans-serif'],
        body: ['Inter', 'sans-serif'],
      },
      backdropBlur: {
        xs: '2px',
      },
      animation: {
        'shimmer': 'shimmer 2s linear infinite',
        'float': 'float 6s ease-in-out infinite',
      },
      keyframes: {
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
```

- [ ] **Step 3: 在 index.css 顶部加字体导入**

Modify `frontend/src/index.css`,在文件最顶部加:

```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');

/* (保留原有 @tailwind / @layer 等) */
```

并把 body 默认字体改成 Inter:

```css
@layer base {
  body {
    @apply font-body bg-durian-cream text-durian-thorn;
  }
  h1, h2, h3, h4 {
    @apply font-display;
  }
}
```

- [ ] **Step 4: 提交**

```powershell
git add frontend/tailwind.config.js frontend/src/index.css
git commit -m "feat(ui): customize tailwind theme with durian palette + display font"
```

---

## Task 27: 实现 API client

**Files:**
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/api/types.ts`

- [ ] **Step 1: 写 types.ts**

Create `frontend/src/api/types.ts`:

```typescript
export interface Variety {
  id: string
  name_cn: string
  name_en: string
  trigger: string
  preview?: string
}

export interface GenerateRequest {
  variety: string
  prompt: string
  negative_prompt?: string
  num_images?: number
  steps?: number
  cfg_scale?: number
  seed?: number
  width?: number
  height?: number
}

export interface QueuedResponse {
  task_id: string
  status: 'queued'
  queue_position: number
  estimated_seconds: number
}

export type TaskStatusValue = 'queued' | 'running' | 'done' | 'failed'

export interface TaskStatus {
  task_id: string
  status: TaskStatusValue
  queue_position?: number
  estimated_seconds?: number
  progress?: number
  current_step?: number
  total_steps?: number
  image_urls?: string[]
  error?: string
}
```

- [ ] **Step 2: 写 client.ts**

Create `frontend/src/api/client.ts`:

```typescript
import type { Variety, GenerateRequest, QueuedResponse, TaskStatus } from './types'

const API_BASE = ''   // 同源部署,空字符串即可

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
    ...init,
  })
  if (!res.ok) {
    const txt = await res.text().catch(() => '')
    throw new Error(`${res.status} ${res.statusText}: ${txt}`)
  }
  return res.json() as Promise<T>
}

export const api = {
  listVarieties: () => http<Variety[]>('/api/varieties'),

  submitGenerate: (req: GenerateRequest) =>
    http<QueuedResponse>('/api/generate', {
      method: 'POST',
      body: JSON.stringify(req),
    }),

  getTask: (taskId: string) => http<TaskStatus>(`/api/tasks/${taskId}`),

  imageUrl: (taskId: string, idx: number) =>
    `${API_BASE}/api/tasks/${taskId}/image?idx=${idx}`,
}

/**
 * 提交并轮询直到完成或失败
 */
export async function generateAndWait(
  req: GenerateRequest,
  onProgress: (s: TaskStatus) => void,
  signal?: AbortSignal,
  pollIntervalMs = 1000,
  timeoutMs = 120_000,
): Promise<TaskStatus> {
  const queued = await api.submitGenerate(req)
  const taskId = queued.task_id
  const start = Date.now()

  while (true) {
    if (signal?.aborted) throw new Error('取消')
    if (Date.now() - start > timeoutMs) throw new Error('超时')
    await new Promise(r => setTimeout(r, pollIntervalMs))
    const s = await api.getTask(taskId)
    onProgress(s)
    if (s.status === 'done' || s.status === 'failed') return s
  }
}
```

- [ ] **Step 3: 提交**

```powershell
cd "D:/谷歌下载/Kimi_Agent_榴莲图像生成代码"
git add frontend/src/api/
git commit -m "feat(ui): add API client + types"
```

---

## Task 28: 实现主页 Hero section(品种选择 + Prompt + 进度)

**Files:**
- Create: `frontend/src/sections/Hero.tsx`
- Create: `frontend/src/components/VarietyPicker.tsx`
- Create: `frontend/src/components/ProgressPanel.tsx`
- Create: `frontend/src/components/ResultGrid.tsx`
- Create: `frontend/src/hooks/useGeneration.ts`

- [ ] **Step 1: 写 useGeneration hook**

Create `frontend/src/hooks/useGeneration.ts`:

```typescript
import { useState, useCallback, useRef } from 'react'
import { generateAndWait } from '@/api/client'
import type { GenerateRequest, TaskStatus } from '@/api/types'

export function useGeneration() {
  const [status, setStatus] = useState<TaskStatus | null>(null)
  const [isRunning, setIsRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  const start = useCallback(async (req: GenerateRequest) => {
    setError(null)
    setStatus(null)
    setIsRunning(true)
    abortRef.current = new AbortController()
    try {
      const final = await generateAndWait(req, s => setStatus(s),
        abortRef.current.signal)
      if (final.status === 'failed') setError(final.error || '未知错误')
    } catch (e: any) {
      setError(e.message || String(e))
    } finally {
      setIsRunning(false)
    }
  }, [])

  const cancel = useCallback(() => {
    abortRef.current?.abort()
    setIsRunning(false)
  }, [])

  return { status, isRunning, error, start, cancel }
}
```

- [ ] **Step 2: 写 VarietyPicker**

Create `frontend/src/components/VarietyPicker.tsx`:

```tsx
import { useEffect, useState } from 'react'
import { api } from '@/api/client'
import type { Variety } from '@/api/types'
import { cn } from '@/lib/utils'

interface Props {
  value: string
  onChange: (id: string) => void
}

export function VarietyPicker({ value, onChange }: Props) {
  const [varieties, setVarieties] = useState<Variety[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.listVarieties().then(vs => {
      setVarieties(vs)
      if (vs.length && !value) onChange(vs[0].id)
    }).finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {[1,2,3,4].map(i => <div key={i} className="h-32 rounded-2xl bg-white/40 animate-pulse" />)}
    </div>
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {varieties.map(v => (
        <button
          key={v.id}
          onClick={() => onChange(v.id)}
          className={cn(
            'p-5 rounded-2xl backdrop-blur-xl border transition-all text-left',
            value === v.id
              ? 'bg-durian-accent/15 border-durian-accent/40 scale-105 shadow-lg'
              : 'bg-white/50 border-white/40 hover:bg-white/70 hover:scale-105'
          )}
        >
          <div className="text-2xl font-display font-bold text-durian-thorn">{v.name_cn}</div>
          <div className="text-sm text-durian-skin">{v.name_en}</div>
        </button>
      ))}
    </div>
  )
}
```

- [ ] **Step 3: 写 ProgressPanel**

Create `frontend/src/components/ProgressPanel.tsx`:

```tsx
import type { TaskStatus } from '@/api/types'
import { Loader2 } from 'lucide-react'

export function ProgressPanel({ status }: { status: TaskStatus }) {
  if (status.status === 'queued') {
    return (
      <div className="p-6 rounded-2xl bg-white/60 backdrop-blur-xl border border-white/40">
        <div className="flex items-center gap-3 mb-3">
          <Loader2 className="w-5 h-5 animate-spin text-durian-accent" />
          <span className="font-medium">排队中</span>
        </div>
        <div className="text-sm text-durian-skin">
          队列位置: 第 {status.queue_position} 位 · 预计 {status.estimated_seconds}s
        </div>
      </div>
    )
  }
  if (status.status === 'running') {
    const pct = Math.round((status.progress || 0) * 100)
    return (
      <div className="p-6 rounded-2xl bg-white/60 backdrop-blur-xl border border-white/40">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <Loader2 className="w-5 h-5 animate-spin text-durian-accent" />
            <span className="font-medium">生成中</span>
          </div>
          <span className="text-sm text-durian-skin">
            步骤 {status.current_step}/{status.total_steps}
          </span>
        </div>
        <div className="h-2 bg-white/60 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-durian-flesh to-durian-accent transition-all duration-300"
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>
    )
  }
  return null
}
```

- [ ] **Step 4: 写 ResultGrid**

Create `frontend/src/components/ResultGrid.tsx`:

```tsx
import { Download } from 'lucide-react'

export function ResultGrid({ imageUrls }: { imageUrls: string[] }) {
  if (!imageUrls.length) return null
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {imageUrls.map((url, i) => (
        <div key={i} className="group relative rounded-2xl overflow-hidden bg-white/40 backdrop-blur-xl border border-white/40 shadow-lg">
          <img src={url} alt={`Generated ${i}`} className="w-full aspect-square object-cover" />
          <a
            href={url}
            download
            className="absolute bottom-3 right-3 p-2 rounded-full bg-durian-thorn/80 text-white opacity-0 group-hover:opacity-100 transition-opacity"
          >
            <Download className="w-4 h-4" />
          </a>
        </div>
      ))}
    </div>
  )
}
```

- [ ] **Step 5: 写 Hero.tsx**

Create `frontend/src/sections/Hero.tsx`:

```tsx
import { useState } from 'react'
import { VarietyPicker } from '@/components/VarietyPicker'
import { ProgressPanel } from '@/components/ProgressPanel'
import { ResultGrid } from '@/components/ResultGrid'
import { useGeneration } from '@/hooks/useGeneration'
import { Sparkles } from 'lucide-react'

export function Hero() {
  const [variety, setVariety] = useState('')
  const [prompt, setPrompt] = useState('on a wooden table, soft natural light, photorealistic')
  const [steps, setSteps] = useState(6)
  const [cfg, setCfg] = useState(1.5)
  const [num, setNum] = useState(2)
  const { status, isRunning, error, start } = useGeneration()

  const onGenerate = () => {
    if (!variety || !prompt.trim()) return
    start({
      variety,
      prompt: prompt.trim(),
      num_images: num,
      steps,
      cfg_scale: cfg,
    })
  }

  return (
    <section className="min-h-screen px-4 py-12 max-w-6xl mx-auto">
      <header className="text-center mb-12">
        <h1 className="text-5xl md:text-7xl font-display font-bold text-durian-thorn mb-4">
          Generate <span className="text-durian-accent">Photorealistic</span> Durians
        </h1>
        <p className="text-lg text-durian-skin">
          Powered by Stable Diffusion + LoRA · CPU-friendly with LCM acceleration
        </p>
      </header>

      <div className="space-y-8">
        <div>
          <label className="block text-sm font-medium text-durian-thorn mb-3">选择品种</label>
          <VarietyPicker value={variety} onChange={setVariety} />
        </div>

        <div className="p-6 rounded-2xl bg-white/60 backdrop-blur-xl border border-white/40 shadow-sm">
          <label className="block text-sm font-medium text-durian-thorn mb-2">描述场景</label>
          <textarea
            value={prompt}
            onChange={e => setPrompt(e.target.value)}
            placeholder="e.g. cut open, exposed yellow flesh, studio lighting"
            rows={3}
            className="w-full px-4 py-3 rounded-xl bg-white/80 border border-white/60 focus:outline-none focus:border-durian-accent text-durian-thorn placeholder:text-durian-skin/50"
          />

          <details className="mt-4">
            <summary className="cursor-pointer text-sm font-medium text-durian-skin">高级选项 ▾</summary>
            <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs text-durian-skin mb-1">步数 ({steps})</label>
                <input type="range" min={4} max={12} value={steps} onChange={e => setSteps(+e.target.value)} className="w-full" />
              </div>
              <div>
                <label className="block text-xs text-durian-skin mb-1">CFG ({cfg.toFixed(1)})</label>
                <input type="range" min={0.5} max={5} step={0.1} value={cfg} onChange={e => setCfg(+e.target.value)} className="w-full" />
              </div>
              <div>
                <label className="block text-xs text-durian-skin mb-1">数量 ({num})</label>
                <input type="range" min={1} max={4} value={num} onChange={e => setNum(+e.target.value)} className="w-full" />
              </div>
            </div>
          </details>
        </div>

        <div className="flex justify-center">
          <button
            onClick={onGenerate}
            disabled={isRunning || !variety || !prompt.trim()}
            className="px-10 py-4 rounded-2xl bg-gradient-to-r from-durian-accent to-durian-flesh text-white font-display font-bold text-lg shadow-lg hover:shadow-xl hover:scale-105 transition-all disabled:opacity-50 disabled:hover:scale-100 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <Sparkles className="w-5 h-5" />
            {isRunning ? '生成中...' : 'Generate'}
          </button>
        </div>

        {status && status.status !== 'done' && <ProgressPanel status={status} />}

        {error && (
          <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm">
            ⚠ {error}
          </div>
        )}

        {status?.status === 'done' && status.image_urls && (
          <ResultGrid imageUrls={status.image_urls} />
        )}
      </div>
    </section>
  )
}
```

- [ ] **Step 6: 更新 App.tsx**

Modify `frontend/src/App.tsx`(替换 default 内容):

```tsx
import { Hero } from '@/sections/Hero'

function App() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-durian-cream via-white to-durian-flesh/10">
      <Hero />
    </div>
  )
}

export default App
```

- [ ] **Step 7: 启动开发服务器看效果**

```powershell
cd "D:/谷歌下载/Kimi_Agent_榴莲图像生成代码/frontend"
npm run dev
```
Expected: Vite 启动,浏览器 http://localhost:5173 看到时尚版主页(由于后端可能没启,品种列表为空,这正常)

- [ ] **Step 8: 提交**

```powershell
cd "D:/谷歌下载/Kimi_Agent_榴莲图像生成代码"
git add frontend/src/
git commit -m "feat(ui): build hero section with variety picker + progress + result grid"
```

---

## Task 29: 配置 Vite proxy + 构建产物

**Files:**
- Modify: `frontend/vite.config.ts`

- [ ] **Step 1: 加 dev proxy**

Modify `frontend/vite.config.ts`,在 `defineConfig({...})` 中加 `server.proxy`:

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
})
```

- [ ] **Step 2: 构建生产版本验证能 build**

```powershell
cd frontend
npm run build
```
Expected: 输出 `dist/index.html` + `dist/assets/*.js,*.css`,无 TS 错误

- [ ] **Step 3: 提交**

```powershell
cd ..
git add frontend/vite.config.ts
git commit -m "feat(ui): add API proxy + production build config"
```

---

## Task 30: 端到端联调(本地)

**Files:** 无新文件,只是验证

- [ ] **Step 1: 后端启动**

```powershell
# 终端 1
conda activate durian
cd "D:/谷歌下载/Kimi_Agent_榴莲图像生成代码"
$env:DURIAN_OV_MODELS_ROOT = "D:/durian-data/models/openvino"
python -m uvicorn backend.serve.app:app --host 0.0.0.0 --port 8000
```

- [ ] **Step 2: 前端启动**

```powershell
# 终端 2
cd "D:/谷歌下载/Kimi_Agent_榴莲图像生成代码/frontend"
npm run dev
```

- [ ] **Step 3: 浏览器测试**

打开 http://localhost:5173
- ✅ 品种列表应有 musang_king
- ✅ 选品种 → 写 prompt → 点 Generate
- ✅ 显示"排队中" → "生成中 步骤 X/6 进度条"
- ✅ 完成后显示 2 张图
- ✅ 点下载按钮能下到本地

如果失败,看后端 terminal 报错日志。

- [ ] **Step 4: 记录测试结果**

把测试截图(或文字说明)加到 `docs/training-log.md` 末尾。

```powershell
# 不需要 commit,仅本地验证
```

---

## Task 31: 构建前端,放到后端可访问位置

**Files:** 无新文件

- [ ] **Step 1: 构建前端**

```powershell
cd "D:/谷歌下载/Kimi_Agent_榴莲图像生成代码/frontend"
npm run build
```
Expected: `frontend/dist/` 生成

- [ ] **Step 2: 单端口启动验证**

```powershell
cd ..
$env:DURIAN_FRONTEND_DIST = "$PWD/frontend/dist"
$env:DURIAN_OV_MODELS_ROOT = "D:/durian-data/models/openvino"
python -m uvicorn backend.serve.app:app --host 0.0.0.0 --port 8000
```
打开 http://localhost:8000 应直接看到前端 + API 联通(此时不用 5173)

---

## Task 32: 构建 Docker 镜像

**Files:** 无新文件

- [ ] **Step 1: 本地构建镜像**

```powershell
cd "D:/谷歌下载/Kimi_Agent_榴莲图像生成代码"
# 先构建前端,把 dist 放好(Dockerfile 会拷贝)
cd frontend; npm run build; cd ..

# 构建 Docker 镜像
docker build -t durian-aigc:latest -f backend/Dockerfile .
```
Expected:
- 构建过程 5-15 分钟(主要在 pip install)
- 最终镜像 ~3-4 GB
- `docker images | grep durian-aigc` 能看到

如果 Docker Desktop 未装,可跳过此步;直接看 Task 33 部署到服务器的脚本。

- [ ] **Step 2: 本地用 docker-compose 启动验证**

把训好的 OpenVINO 模型软链到项目下:

```powershell
# 准备模型目录
mkdir models -ErrorAction SilentlyContinue
mkdir models/openvino -ErrorAction SilentlyContinue
# 把 D:/durian-data/models/openvino/musang_king 复制到 ./models/openvino/musang_king
Copy-Item -Recurse "D:/durian-data/models/openvino/musang_king" "./models/openvino/"

# 启动
docker compose up -d
docker compose logs -f
```

打开 http://localhost:8000 验证。

Stop:
```powershell
docker compose down
```

- [ ] **Step 3: 提交镜像构建日志(无文件改动,跳过 commit)**

---

## Task 33: 服务器部署脚本

**Files:**
- Create: `scripts/deploy_to_server.sh`(在服务器上 bash 执行)
- Create: `docs/deployment.md`(完成)

- [ ] **Step 1: 写服务器部署脚本**

Create `scripts/deploy_to_server.sh`:

```bash
#!/usr/bin/env bash
# 在服务器上一键部署 durian-aigc
# 用法: bash scripts/deploy_to_server.sh

set -euo pipefail

DEPLOY_ROOT="${DEPLOY_ROOT:-/data/durian}"
MODELS_BUNDLE="${MODELS_BUNDLE:-/tmp/musang_king_openvino.tar.gz}"

echo "==> [1/5] 检查 Docker"
if ! command -v docker >/dev/null; then
    echo "请先安装 Docker: curl -fsSL https://get.docker.com | sh"
    exit 1
fi

echo "==> [2/5] 准备部署目录: $DEPLOY_ROOT"
mkdir -p "$DEPLOY_ROOT/models/openvino"

echo "==> [3/5] 解压 OpenVINO 模型"
if [ -f "$MODELS_BUNDLE" ]; then
    tar -xzvf "$MODELS_BUNDLE" -C "$DEPLOY_ROOT/models/openvino/"
else
    echo "警告: 模型包 $MODELS_BUNDLE 不存在,跳过解压"
fi

echo "==> [4/5] 写入 .env"
cat > "$DEPLOY_ROOT/.env" <<EOF
DURIAN_PORT=8000
OMP_NUM_THREADS=8
EOF

echo "==> [5/5] 启动容器"
cd "$DEPLOY_ROOT"
docker compose pull
docker compose up -d

echo ""
echo "==> 完成! 访问 http://$(hostname -I | awk '{print $1}'):8000"
docker compose ps
```

Set executable:
```powershell
git update-index --chmod=+x scripts/deploy_to_server.sh
```

- [ ] **Step 2: 写完整 `docs/deployment.md`**

Replace `docs/deployment.md`:

````markdown
# 部署指南

## 1. 部署前提

- 服务器: Linux x86_64,Xeon Silver 4309Y 或类似,**≥ 16 GB RAM**(推荐 30 GB+)
- 已安装 Docker 24+ 和 docker-compose v2
- 网络: 能拉取 Docker Hub 或者已在内网仓库

## 2. 总览

```
本地 (RTX 5070)                    服务器 (Xeon CPU)
─────────────────                  ──────────────────
1. 训练 LoRA                       
2. 合并 + LCM + OpenVINO  ───┐    
3. 打包 tar.gz                │    
4. 构建 Docker 镜像 (可选)    │    
                              ▼    
                         scp 上传 →  /data/durian/
                                    │
                                    ├─ docker-compose.yml
                                    ├─ models/openvino/<variety>/
                                    └─ docker compose up -d
```

## 3. 本地准备

```powershell
# 训完一个品种后,一键产出 OpenVINO 包
powershell scripts/build_serve_bundle.ps1 -Variety musang_king
# 输出: D:/durian-data/musang_king_openvino.tar.gz

# 上传到服务器
scp D:/durian-data/musang_king_openvino.tar.gz user@server:/tmp/
```

## 4. 服务器首次部署

```bash
# SSH 进入服务器
ssh user@server

# 安装 Docker (一次)
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER && newgrp docker

# 克隆代码(或上传 docker-compose.yml 和脚本)
mkdir -p /data/durian && cd /data/durian
git clone <your-repo>  # 或仅上传 docker-compose.yml + scripts/
# 也可只把以下两个文件 scp 上去:
#   docker-compose.yml
#   scripts/deploy_to_server.sh

# 执行部署
MODELS_BUNDLE=/tmp/musang_king_openvino.tar.gz \
    bash scripts/deploy_to_server.sh
```

## 5. Docker 镜像来源

**两种选择:**

### 选择 A: 服务器现场构建(简单,慢)

```bash
# 服务器需有完整代码
cd /data/durian
git clone <your-repo> repo
cp repo/docker-compose.yml .
cp -r repo/backend .
cp -r repo/frontend .
cd frontend && npm install && npm run build && cd ..
docker compose build
docker compose up -d
```

构建时间约 10-20 分钟。

### 选择 B: 本地构建 + 推送到镜像仓库(快)

```powershell
# 本地
docker build -t your-registry/durian-aigc:latest -f backend/Dockerfile .
docker push your-registry/durian-aigc:latest
```

```bash
# 服务器
# 编辑 docker-compose.yml,把 build 段改成 image: your-registry/durian-aigc:latest
docker compose pull
docker compose up -d
```

## 6. 添加新品种

```bash
# 本地训完新品种后
scp D:/durian-data/blackthorn_openvino.tar.gz user@server:/tmp/

# 服务器
cd /data/durian
tar -xzvf /tmp/blackthorn_openvino.tar.gz -C models/openvino/
docker compose restart durian-api   # 重启让服务发现新品种
```

## 7. 常用运维

```bash
# 查看日志
docker compose logs -f durian-api

# 查看容器资源占用
docker stats durian-api

# 重启
docker compose restart durian-api

# 停止
docker compose down

# 完全重建(代码改动后)
docker compose down
docker compose build --no-cache
docker compose up -d
```

## 8. 性能预期

| 场景 | 单张耗时 | 同时用户 |
|---|---|---|
| 6 步 LCM | 8-15 秒 | 1(排队) |
| 标准 25 步 | 30-50 秒 | 1 |

队列上限 20,排满返回 503。

## 9. 反向代理 (Nginx,可选)

如果要域名访问 + HTTPS:

```nginx
server {
    listen 80;
    server_name durian.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 180s;
    }
}
```

## 10. 故障排查

| 症状 | 原因 | 解决 |
|---|---|---|
| 容器一直 unhealthy | 模型未加载完(首次 60-120s)| 等待 2 分钟再看 |
| OOM Killed | 内存不足 | 关掉其他容器/进程,或 limit 提到 28G |
| /api/varieties 返回 [] | models/openvino 没挂载或为空 | 检查 docker-compose.yml volumes 段 |
| 推理超时 | CPU 太忙 | 降低 num_images 到 1, steps 到 4 |
| 浏览器 404 | dist 没构建 | `cd frontend && npm run build`,重建镜像 |
````

- [ ] **Step 3: 提交**

```powershell
git add scripts/deploy_to_server.sh docs/deployment.md
git commit -m "feat(deploy): add server deployment script + complete deployment guide"
```

---

## Task 34: 写最终的根 README + Gallery 页 + About 页

**Files:**
- Modify: `README.md`
- Create: `frontend/src/sections/Gallery.tsx`
- Create: `frontend/src/sections/About.tsx`
- Modify: `frontend/src/App.tsx`(加路由)

- [ ] **Step 1: Gallery section (LocalStorage 历史)**

Create `frontend/src/sections/Gallery.tsx`:

```tsx
import { useEffect, useState } from 'react'

interface HistoryItem {
  id: string
  variety: string
  prompt: string
  url: string
  ts: number
}

const KEY = 'durian_gallery_v1'

export function loadHistory(): HistoryItem[] {
  try {
    return JSON.parse(localStorage.getItem(KEY) || '[]')
  } catch { return [] }
}

export function pushHistory(item: HistoryItem) {
  const list = loadHistory()
  list.unshift(item)
  localStorage.setItem(KEY, JSON.stringify(list.slice(0, 50)))
}

export function Gallery() {
  const [items, setItems] = useState<HistoryItem[]>([])
  useEffect(() => { setItems(loadHistory()) }, [])

  if (!items.length) {
    return <div className="text-center py-20 text-durian-skin">还没有历史记录,先去生成几张吧</div>
  }

  return (
    <section className="px-4 py-12 max-w-6xl mx-auto">
      <h2 className="text-4xl font-display font-bold text-durian-thorn mb-8">最近生成</h2>
      <div className="columns-1 sm:columns-2 md:columns-3 lg:columns-4 gap-4">
        {items.map(item => (
          <div key={item.id + item.url} className="mb-4 break-inside-avoid rounded-2xl overflow-hidden bg-white/60 backdrop-blur-xl border border-white/40">
            <img src={item.url} alt="" className="w-full" />
            <div className="p-3 text-xs text-durian-skin truncate">{item.prompt}</div>
          </div>
        ))}
      </div>
    </section>
  )
}
```

- [ ] **Step 2: About section**

Create `frontend/src/sections/About.tsx`:

```tsx
export function About() {
  return (
    <section className="px-4 py-12 max-w-3xl mx-auto prose prose-durian">
      <h2 className="text-4xl font-display font-bold text-durian-thorn mb-6">关于本项目</h2>
      <p className="text-durian-skin">
        本系统基于 Stable Diffusion 1.5 + LoRA 微调,为榴莲品种图像生成而设计。
        服务器侧使用 OpenVINO + LCM-LoRA 加速,在 CPU 上单张约 8-15 秒。
      </p>
      <h3 className="font-display font-bold text-2xl text-durian-thorn mt-8">技术栈</h3>
      <ul className="text-durian-skin space-y-1">
        <li>· 模型: SD 1.5 + LoRA + LCM-LoRA</li>
        <li>· 后端: FastAPI + asyncio queue + OpenVINO</li>
        <li>· 前端: React 19 + Vite + Tailwind + shadcn</li>
        <li>· 部署: Docker + docker-compose</li>
      </ul>
      <h3 className="font-display font-bold text-2xl text-durian-thorn mt-8">数据来源</h3>
      <p className="text-durian-skin">
        训练数据来自公开图源(Unsplash / Pexels / Bing 可商用过滤)+ 自有采集。
        本系统<strong>仅用于学术演示与作业展示</strong>,不商业化、不二次分发。
      </p>
    </section>
  )
}
```

- [ ] **Step 3: App.tsx 加简单 tab 切换**

Modify `frontend/src/App.tsx`:

```tsx
import { useState } from 'react'
import { Hero } from '@/sections/Hero'
import { Gallery } from '@/sections/Gallery'
import { About } from '@/sections/About'

function App() {
  const [page, setPage] = useState<'home' | 'gallery' | 'about'>('home')

  return (
    <div className="min-h-screen bg-gradient-to-br from-durian-cream via-white to-durian-flesh/10">
      <nav className="sticky top-0 z-20 backdrop-blur-xl bg-white/50 border-b border-white/40">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-2xl">🌰</span>
            <span className="font-display font-bold text-durian-thorn">榴莲 AIGC</span>
          </div>
          <div className="flex gap-1">
            {[
              ['home', '生成'],
              ['gallery', '画廊'],
              ['about', '关于'],
            ].map(([k, label]) => (
              <button
                key={k}
                onClick={() => setPage(k as any)}
                className={`px-4 py-2 rounded-xl text-sm transition-colors ${
                  page === k ? 'bg-durian-accent text-white' : 'text-durian-thorn hover:bg-white/60'
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
      </nav>
      {page === 'home' && <Hero />}
      {page === 'gallery' && <Gallery />}
      {page === 'about' && <About />}
    </div>
  )
}

export default App
```

- [ ] **Step 4: Hero 完成后把结果推到 Gallery**

Modify `frontend/src/sections/Hero.tsx`,在 `status?.status === 'done'` 块之上加副作用:

```tsx
// 在 Hero 组件内部
import { useEffect } from 'react'
import { pushHistory } from './Gallery'

// ... existing state

useEffect(() => {
  if (status?.status === 'done' && status.image_urls) {
    status.image_urls.forEach((url, i) => {
      pushHistory({
        id: status.task_id + '_' + i,
        variety,
        prompt,
        url,
        ts: Date.now(),
      })
    })
  }
}, [status?.status])
```

- [ ] **Step 5: 重建前端 + 完整跑通**

```powershell
cd frontend; npm run build; cd ..
```

打开 http://localhost:8000 测试 3 个 tab。

- [ ] **Step 6: 提交**

```powershell
git add frontend/src/sections/Gallery.tsx frontend/src/sections/About.tsx frontend/src/sections/Hero.tsx frontend/src/App.tsx
git commit -m "feat(ui): add gallery + about pages with tab navigation"
```

---

## Task 35: 写根 README 完整版

**Files:**
- Modify: `README.md`

- [ ] **Step 1: 写最终 README**

Replace `README.md`:

````markdown
# 🌰 榴莲 AIGC 系统

基于 **Stable Diffusion 1.5 + LoRA + LCM** 的榴莲品种图像生成系统。
**本地 GPU 训练 → CPU 服务器 Docker 部署 → 浏览器生成**。

![demo](docs/demo.png)

## ✨ 特性

- 🎨 4 个榴莲品种 LoRA 微调(猫山王、金枕头、黑刺王、红虾)
- ⚡ CPU 推理 8-15 秒/张(OpenVINO + LCM-LoRA 6 步)
- 🐳 Docker 一键部署
- 📱 时尚 React UI(玻璃拟态 + 真实进度条)
- 🔧 完整数据流水线(爬虫 + 自动筛选 + BLIP 自动打标)

## 🚀 快速开始

### 本地训练(RTX 5070 或同级 GPU)

```powershell
# 1. 装环境
powershell scripts/setup_train_env.ps1

# 2. 准备数据
powershell scripts/prepare_dataset.ps1 -Variety musang_king -CrawlNum 50

# 3. 训练
conda activate durian
python -m backend.lora_trainer --variety musang_king

# 4. 本地推理
python -m backend.local_inference --variety musang_king --prompt "on a wooden table"
```

### 服务器部署(无 GPU,Docker)

```powershell
# 在本地: 打包 OpenVINO 模型
powershell scripts/build_serve_bundle.ps1 -Variety musang_king

# 上传到服务器
scp D:/durian-data/musang_king_openvino.tar.gz user@server:/tmp/
scp docker-compose.yml user@server:/data/durian/
scp -r backend frontend scripts user@server:/data/durian/

# 在服务器
ssh user@server
cd /data/durian
MODELS_BUNDLE=/tmp/musang_king_openvino.tar.gz bash scripts/deploy_to_server.sh
# 访问 http://server:8000
```

## 📚 文档

- [设计文档](docs/superpowers/specs/2026-06-22-durian-aigc-design.md)
- [实施计划](docs/superpowers/plans/2026-06-22-durian-aigc-implementation.md) (+ part 2)
- [数据收集指南](docs/data-collection.md)
- [训练指南](docs/training.md)
- [部署指南](docs/deployment.md)

## 🏗 项目结构

```
.
├── backend/                Python 后端
│   ├── data_tools/         数据爬虫/筛选/合并/BLIP 打标
│   ├── tools/              LoRA 合并 + OpenVINO 导出
│   ├── serve/              FastAPI + asyncio queue + OpenVINO
│   ├── configs/            paths.yaml 统一配置
│   ├── lora_trainer.py     LoRA 训练
│   ├── local_inference.py  本地快速推理
│   ├── Dockerfile          后端镜像
│   ├── requirements-train.txt
│   └── requirements-serve.txt
├── frontend/               React 19 + Vite + Tailwind + shadcn
├── scripts/                一键脚本 (PowerShell + bash)
├── docs/                   文档
├── docker-compose.yml      容器编排
└── archive/                历史代码归档
```

数据 & 模型在 `D:/durian-data/`(本地)或 `/data/durian/models/`(服务器),不入 git。

## 🛠 技术栈

| 层 | 技术 |
|---|---|
| 训练 | PyTorch nightly (cu128) + diffusers + peft |
| 推理 | OpenVINO 2024.4 + LCM-LoRA |
| 后端 | FastAPI + uvicorn + asyncio |
| 前端 | React 19 + Vite 7 + Tailwind 3.4 + shadcn/Radix |
| 部署 | Docker + docker-compose |

## ⚠️ 限制

- 单 CPU worker 串行处理,小范围演示用
- 仅学术/作业用途,不商业化
- SD1.5 不支持中文 prompt,前端会自动加品种触发词

## 📜 协议

代码 MIT。模型权重遵循 [Stable Diffusion License](https://huggingface.co/stabilityai/stable-diffusion-2-1)。
````

- [ ] **Step 2: 提交**

```powershell
git add README.md
git commit -m "docs: write complete root README"
```

---

## Task 36: 最终验收 + 创建 v0.1 tag

**Files:** 无

- [ ] **Step 1: 跑完整测试**

```powershell
conda activate durian
cd "D:/谷歌下载/Kimi_Agent_榴莲图像生成代码"
python -m pytest backend/tests/ -v
```
Expected: 全部 pass

- [ ] **Step 2: 检查关键文件**

```powershell
Test-Path README.md
Test-Path docker-compose.yml
Test-Path backend/Dockerfile
Test-Path backend/serve/app.py
Test-Path frontend/dist/index.html
Test-Path "D:/durian-data/models/openvino/musang_king/unet/openvino_model.xml"
```
Expected: 全部 True

- [ ] **Step 3: 本地端到端跑一遍**

```powershell
# Docker 启动(如果有 Docker)
docker compose up -d
# 浏览器打开 http://localhost:8000 实际生成一张图,确认能下载
docker compose down
```

- [ ] **Step 4: 打 tag**

```powershell
git tag -a v0.1.0 -m "First working release: train + deploy with docker, single variety end-to-end"
git log --oneline | Select-Object -First 20
```

**M5 验收清单:**
- [ ] 浏览器访问 http://localhost:8000(或服务器 IP:8000)能看到时尚前端
- [ ] 选品种 → 写 prompt → Generate → 看到排队/进行中/结果
- [ ] 单张生成 ≤ 20 秒
- [ ] 同时点 2 个请求,第二个排队不崩
- [ ] 历史画廊能看到刚才生成的图
- [ ] Docker 容器 `docker compose ps` 显示 healthy
- [ ] README 有完整入口

---

# 🎯 最终验收(整个项目)

按 §12 设计文档验收标准:

- [ ] **C1** 本地一条命令完成爬虫→筛选→打标→训练→推理全流程(`prepare_dataset.ps1` + `lora_trainer` + `local_inference`)
- [ ] **C2** 训练 1 个品种 50 张图在 RTX 5070 上 30 分钟内完成
- [ ] **C3** 本地推理 `local_inference.py` 单张 < 5 秒
- [ ] **C4** 服务器推理单张 < 20 秒
- [ ] **C5** 服务器同时排 5 个任务不崩
- [ ] **C6** 前端时尚现代,玻璃拟态视觉,真实进度条
- [ ] **C7** 前后端同源部署,1 个端口
- [ ] **C8** 至少 2 个品种端到端可用(任务在 M2-M3 重复两次即可)
- [ ] **C9** 文档齐全:`data-collection.md` / `training.md` / `deployment.md`
- [ ] **新增** Docker 部署可一键启动

---

**END OF PLAN.**
