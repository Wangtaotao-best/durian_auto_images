"""把 LoRA 权重 fuse 进基础 SD 主模型,导出为完整 pipeline 目录"""
import argparse
import logging
from pathlib import Path

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")


def validate_paths(base, lora, output):
    from pathlib import Path
    base_p = Path(base)
    lora_p = Path(lora)
    if not base_p.exists() and not str(base).startswith(("hf://", "runwayml/", "stabilityai/", "latent-consistency/")):
        raise FileNotFoundError(f"基础模型路径不存在: {base}")
    if not lora_p.exists():
        raise FileNotFoundError(f"LoRA 路径不存在: {lora}")


def merge(base_model: str, lora_path: str, output_dir: Path, alpha: float = 0.8):
    import torch
    from diffusers import StableDiffusionPipeline
    from peft import PeftModel
    import gc

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"加载基础模型: {base_model}")
    pipe = StableDiffusionPipeline.from_pretrained(
        base_model,
        torch_dtype=torch.float32,
        safety_checker=None,
        requires_safety_checker=False,
    )

    logger.info(f"用 PEFT 方式加载 LoRA: {lora_path} (alpha={alpha})")
    # PEFT LoRA: 先加载到 UNet
    unet = pipe.unet
    peft_model = PeftModel.from_pretrained(unet, lora_path, adapter_name="default")
    peft_model = peft_model.merge_and_unload()
    pipe.unet = peft_model

    # 把 pipeline 转为 float16 减小体积
    pipe = pipe.to(dtype=torch.float16)

    logger.info(f"保存合并后的 pipeline 到: {output_dir}")
    pipe.save_pretrained(str(output_dir))

    # 清理
    del pipe, peft_model, unet
    gc.collect()

    logger.info("合并完成")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--lora", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--alpha", type=float, default=0.8)
    args = parser.parse_args()

    merge(args.base, args.lora, args.output, args.alpha)


if __name__ == "__main__":
    main()
