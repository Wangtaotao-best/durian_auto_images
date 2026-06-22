"""本地快速推理 - 加载基础 SD + LoRA, 3 秒/张"""
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from backend.configs.loader import load_paths, load_varieties

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")


def inject_trigger(trigger: str, user_prompt: str) -> str:
    if trigger.lower() in user_prompt.lower():
        return user_prompt
    return f"{trigger}, {user_prompt}"


def build_output_name(variety: str, seed: int, idx: int) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{variety}_{ts}_{seed}_{idx}.png"


def generate(variety: str, user_prompt: str, num_images: int = 1,
             steps: int = 30, cfg: float = 7.5, seed: Optional[int] = None,
             width: int = 512, height: int = 512,
             negative: str = "blurry, low quality, distorted, deformed",
             output_dir: Optional[Path] = None):
    import torch
    from diffusers import StableDiffusionPipeline, EulerAncestralDiscreteScheduler

    paths = load_paths()
    varieties = load_varieties()
    if variety not in varieties:
        raise ValueError(f"未知品种: {variety}")
    trigger = varieties[variety]["trigger"]

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32

    logger.info(f"加载基础模型到 {device}")
    pipe = StableDiffusionPipeline.from_pretrained(
        "runwayml/stable-diffusion-v1-5",
        torch_dtype=dtype,
        safety_checker=None,
        requires_safety_checker=False,
    ).to(device)
    pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(pipe.scheduler.config)

    # 加载 LoRA (PEFT 格式: 目录内包含 adapter_model.safetensors + adapter_config.json)
    lora_dir = paths["models_lora"] / variety
    if not lora_dir.exists():
        raise FileNotFoundError(f"找不到 LoRA: {lora_dir}")
    logger.info(f"加载 LoRA: {lora_dir}")
    from peft import PeftModel
    pipe.unet = PeftModel.from_pretrained(pipe.unet, str(lora_dir))

    if device == "cuda":
        pipe.enable_attention_slicing()

    full_prompt = inject_trigger(trigger, user_prompt)
    logger.info(f"Prompt: {full_prompt}")

    if seed is None:
        import random
        seed = random.randint(0, 2**31)
    generator = torch.Generator(device=device).manual_seed(seed)

    result = pipe(
        prompt=full_prompt,
        negative_prompt=negative,
        num_inference_steps=steps,
        guidance_scale=cfg,
        width=width, height=height,
        num_images_per_prompt=num_images,
        generator=generator,
    )

    output_dir = Path(output_dir) if output_dir else paths["outputs"] / variety
    output_dir.mkdir(parents=True, exist_ok=True)

    saved = []
    for i, img in enumerate(result.images):
        out_path = output_dir / build_output_name(variety, seed, i)
        img.save(out_path)
        saved.append(out_path)
        logger.info(f"保存: {out_path}")
    return saved


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--variety", required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--negative", default="blurry, low quality, distorted, deformed")
    parser.add_argument("--num", type=int, default=1)
    parser.add_argument("--steps", type=int, default=30)
    parser.add_argument("--cfg", type=float, default=7.5)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--width", type=int, default=512)
    parser.add_argument("--height", type=int, default=512)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    generate(args.variety, args.prompt, args.num, args.steps, args.cfg,
             args.seed, args.width, args.height, args.negative, args.output)


if __name__ == "__main__":
    main()
