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
