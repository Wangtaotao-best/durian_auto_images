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

# Backend 模式: openvino (CPU 服务器) 或 lora (本地 GPU 验证)
BACKEND_MODE = os.environ.get("DURIAN_BACKEND_MODE", "openvino").lower()

# 模型根目录:lora 模式默认指向 models/lora,openvino 模式默认指向 models/openvino
if BACKEND_MODE == "lora":
    _default_root = _paths["models_lora"]
    _root_env = "DURIAN_LORA_MODELS_ROOT"
else:
    _default_root = _paths["models_openvino"]
    _root_env = "DURIAN_OV_MODELS_ROOT"

MODELS_ROOT = Path(os.environ.get(_root_env, _default_root))
IMAGES_ROOT = Path(os.environ.get("DURIAN_IMAGES_ROOT", _paths["outputs"] / "_serve"))


class PipelineProvider:
    """把 PipelineRegistry 适配成 queue 需要的 generate_for_params 接口"""
    def __init__(self, registry: PipelineRegistry, mode: str):
        self.registry = registry
        # LoRA 模式默认 30 步 / cfg 7.5;OpenVINO+LCM 模式默认 6 步 / cfg 1.5
        if mode == "lora":
            self.default_steps = 30
            self.default_cfg = 7.5
        else:
            self.default_steps = 6
            self.default_cfg = 1.5

    def generate_for_params(self, params: dict, progress_cb):
        inferencer = self.registry.get(params["variety"])
        return inferencer.generate(
            prompt=params["prompt"],
            negative_prompt=params.get("negative_prompt", ""),
            num_images=params.get("num_images", 1),
            steps=params.get("steps") or self.default_steps,
            cfg=params.get("cfg_scale") or self.default_cfg,
            width=params.get("width", 512),
            height=params.get("height", 512),
            seed=params.get("seed", -1),
            progress_callback=progress_cb,
        )


registry = PipelineRegistry(MODELS_ROOT, max_loaded=1, mode=BACKEND_MODE)
provider = PipelineProvider(registry, mode=BACKEND_MODE)
queue = TaskQueue(provider)
store = ImageStore(IMAGES_ROOT)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Backend mode: {BACKEND_MODE} | models root: {MODELS_ROOT}")
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
