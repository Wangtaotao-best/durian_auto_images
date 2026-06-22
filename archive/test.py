# -*- coding: utf-8 -*-
import torch
from diffusers import StableDiffusionPipeline
from peft import PeftModel
from PIL import Image
import os


def generate_durian(
        lora_path: str,
        prompt: str,
        output_path: str = "output.png",
        num_images: int = 1,
        num_inference_steps: int = 30,
        guidance_scale: float = 7.5,
        seed: int = 42,
):
    """
    使用 LoRA 权重生成榴莲图像（PEFT 格式兼容版）
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"

    # 1. 加载基础模型
    print("加载基础模型...")
    pipe = StableDiffusionPipeline.from_pretrained(
        "runwayml/stable-diffusion-v1-5",
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
    )
    pipe = pipe.to(device)

    # 2. 加载 PEFT 格式的 LoRA 权重
    print(f"加载 LoRA 权重: {lora_path}")
    pipe.unet = PeftModel.from_pretrained(pipe.unet, lora_path)
    pipe.unet = pipe.unet.to(device)  # 确保在正确设备上
    pipe.unet.eval()

    # 可选：调整 LoRA 权重强度（alpha）
    # pipe.unet.set_adapters(["default"], adapter_weights=[0.8])

    # 3. 设置随机种子
    generator = torch.Generator(device=device).manual_seed(seed)

    # 4. 生成图像
    print(f"生成图像: {prompt}")
    images = pipe(
        prompt,
        num_inference_steps=num_inference_steps,
        guidance_scale=guidance_scale,
        num_images_per_prompt=num_images,
        generator=generator,
    ).images

    # 5. 保存
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    if num_images == 1:
        images[0].save(output_path)
        print(f"已保存: {output_path}")
    else:
        for i, img in enumerate(images):
            path = output_path.replace(".png", f"_{i}.png")
            img.save(path)
            print(f"已保存: {path}")

    return images


if __name__ == "__main__":
    # ========== 修改这里 ==========
    LORA_PATH = r"D:\谷歌下载\Kimi_Agent_榴莲图像生成代码\durian-aigc-code\models\lora\musang_king\checkpoint-final"

    PROMPT = (
        "a photo of musangking durian, golden yellow flesh, "
        "creamy texture, premium quality, highly detailed, 4k"
    )
    # =============================

    generate_durian(
        lora_path=LORA_PATH,
        prompt=PROMPT,
        output_path="generated_durian.png",
        num_images=4,
        num_inference_steps=30,
        guidance_scale=7.5,
        seed=42,
    )