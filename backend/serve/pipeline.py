"""推理 pipeline 服务侧封装 — 支持两种 backend:
- openvino: CPU 服务器生产环境(LCM 6 步)
- lora: 本地 GPU 验证(SD1.5 + LoRA 30 步)

通过环境变量 DURIAN_BACKEND_MODE 切换(默认 openvino)
"""
import logging
import os
from pathlib import Path
from typing import Callable, List, Optional
from PIL import Image

logger = logging.getLogger(__name__)


BACKEND_MODE = os.environ.get("DURIAN_BACKEND_MODE", "openvino").lower()


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


class LoRAInferencer:
    """本地 GPU LoRA 推理(用于浏览器端到端验证,与 OpenVINO 接口对齐)"""

    def __init__(self, lora_dir: Path,
                 base_model: str = "runwayml/stable-diffusion-v1-5"):
        self.lora_dir = Path(lora_dir)
        self.base_model = base_model
        self.pipe = None
        self.device = None

    def load(self):
        import torch
        from diffusers import StableDiffusionPipeline, EulerAncestralDiscreteScheduler
        from peft import PeftModel

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        dtype = torch.float16 if self.device == "cuda" else torch.float32

        logger.info(f"加载基础 SD1.5 到 {self.device} ({dtype})")
        self.pipe = StableDiffusionPipeline.from_pretrained(
            self.base_model,
            torch_dtype=dtype,
            safety_checker=None,
            requires_safety_checker=False,
        ).to(self.device)
        self.pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(
            self.pipe.scheduler.config
        )

        logger.info(f"加载 PEFT LoRA: {self.lora_dir}")
        self.pipe.unet = PeftModel.from_pretrained(
            self.pipe.unet, str(self.lora_dir), adapter_name="default"
        )

        if self.device == "cuda":
            self.pipe.enable_attention_slicing()

        logger.info("LoRA pipeline 加载完成")

    def unload(self):
        del self.pipe
        self.pipe = None
        import gc
        gc.collect()
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass

    def generate(self, prompt: str, negative_prompt: str = "",
                 num_images: int = 1, steps: int = 30, cfg: float = 7.5,
                 width: int = 512, height: int = 512, seed: int = -1,
                 progress_callback: Optional[Callable[[int, int], None]] = None
                 ) -> List[Image.Image]:
        if self.pipe is None:
            raise RuntimeError("Pipeline 未加载")
        import torch
        if seed < 0:
            import random
            seed = random.randint(0, 2**31)
        generator = torch.Generator(device=self.device).manual_seed(seed)

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
    """管理多品种 pipeline,单实例,LRU 切换。
    根据 DURIAN_BACKEND_MODE 选择 OpenVINOInferencer 或 LoRAInferencer。
    """

    def __init__(self, models_root: Path, max_loaded: int = 1,
                 mode: Optional[str] = None):
        self.models_root = Path(models_root)
        self.max_loaded = max_loaded
        self.mode = (mode or BACKEND_MODE).lower()
        self._loaded: dict = {}
        self._lru: list = []
        logger.info(f"PipelineRegistry mode={self.mode}, root={self.models_root}")

    def _make_inferencer(self, model_dir: Path):
        if self.mode == "lora":
            return LoRAInferencer(model_dir)
        return OpenVINOInferencer(model_dir)

    def get(self, variety: str):
        if variety in self._loaded:
            self._lru.remove(variety)
            self._lru.append(variety)
            return self._loaded[variety]

        while len(self._loaded) >= self.max_loaded:
            evict = self._lru.pop(0)
            logger.info(f"卸载 pipeline: {evict}")
            self._loaded[evict].unload()
            del self._loaded[evict]

        model_dir = self.models_root / variety
        if not model_dir.exists():
            raise FileNotFoundError(f"找不到模型: {model_dir}")
        inferencer = self._make_inferencer(model_dir)
        inferencer.load()
        self._loaded[variety] = inferencer
        self._lru.append(variety)
        return inferencer

    def available_varieties(self) -> List[str]:
        if not self.models_root.exists():
            return []
        names = []
        for p in sorted(self.models_root.iterdir()):
            if not p.is_dir():
                continue
            # 过滤备份目录与中间 checkpoint 目录
            if p.name.endswith("_backup") or p.name.endswith("_checkpoints"):
                continue
            if p.name.endswith("_old_backup"):
                continue
            # LoRA 模式校验是否有 adapter_model.safetensors
            if self.mode == "lora":
                if not (p / "adapter_model.safetensors").exists():
                    continue
            names.append(p.name)
        return names
