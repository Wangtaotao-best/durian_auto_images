"""
Stable Diffusion 基础图像生成模块
用于榴莲图像的基础生成
"""

import torch
from diffusers import StableDiffusionPipeline, DDIMScheduler, EulerAncestralDiscreteScheduler
from PIL import Image
import os
from typing import Optional, List, Union
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StableDiffusionBase:
    """
    Stable Diffusion 基础生成类
    """
    
    def __init__(
        self,
        model_id: str = "runwayml/stable-diffusion-v1-5",
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
        dtype: torch.dtype = torch.float16,
    ):
        """
        初始化 Stable Diffusion 模型
        
        Args:
            model_id: Hugging Face 模型 ID 或本地路径
            device: 运行设备 (cuda/cpu)
            dtype: 数据类型
        """
        self.device = device
        self.dtype = dtype
        self.model_id = model_id
        
        logger.info(f"正在加载模型: {model_id}")
        logger.info(f"使用设备: {device}")
        
        # 加载 pipeline
        self.pipe = StableDiffusionPipeline.from_pretrained(
            model_id,
            torch_dtype=dtype,
            safety_checker=None,  # 禁用安全检查器以提高速度
            requires_safety_checker=False,
        )
        
        self.pipe = self.pipe.to(device)
        
        # 启用内存优化
        if device == "cuda":
            self.pipe.enable_attention_slicing()
            # 如果使用较新的 GPU，可以启用 xformers
            try:
                self.pipe.enable_xformers_memory_efficient_attention()
                logger.info("已启用 xformers 内存优化")
            except:
                logger.info("xformers 不可用，使用默认注意力机制")
        
        logger.info("模型加载完成")
    
    def set_scheduler(self, scheduler_type: str = "euler_a"):
        """
        设置采样器
        
        Args:
            scheduler_type: 采样器类型 (ddim/euler_a)
        """
        if scheduler_type == "ddim":
            self.pipe.scheduler = DDIMScheduler.from_config(self.pipe.scheduler.config)
        elif scheduler_type == "euler_a":
            self.pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(
                self.pipe.scheduler.config
            )
        logger.info(f"已设置采样器: {scheduler_type}")
    
    def generate(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 512,
        height: int = 512,
        num_inference_steps: int = 30,
        guidance_scale: float = 7.5,
        seed: Optional[int] = None,
        num_images: int = 1,
    ) -> List[Image.Image]:
        """
        生成图像
        
        Args:
            prompt: 正向提示词
            negative_prompt: 负向提示词
            width: 图像宽度
            height: 图像高度
            num_inference_steps: 推理步数
            guidance_scale: 引导比例
            seed: 随机种子
            num_images: 生成图像数量
            
        Returns:
            生成的图像列表
        """
        # 设置随机种子
        generator = None
        if seed is not None:
            generator = torch.Generator(device=self.device).manual_seed(seed)
        
        # 榴莲专用负向提示词
        default_negative = (
            "low quality, blurry, distorted, deformed, "
            "bad anatomy, extra limbs, missing limbs, "
            "watermark, signature, text, logo, "
            "oversaturated, underexposed"
        )
        
        if negative_prompt:
            negative_prompt = f"{default_negative}, {negative_prompt}"
        else:
            negative_prompt = default_negative
        
        logger.info(f"生成图像: {prompt}")
        logger.info(f"尺寸: {width}x{height}, 步数: {num_inference_steps}")
        
        # 生成图像
        with torch.autocast(self.device, dtype=self.dtype):
            images = self.pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                generator=generator,
                num_images_per_prompt=num_images,
            ).images
        
        logger.info(f"成功生成 {len(images)} 张图像")
        return images
    
    def save_images(
        self,
        images: List[Image.Image],
        output_dir: str = "output",
        prefix: str = "durian",
    ) -> List[str]:
        """
        保存生成的图像
        
        Args:
            images: 图像列表
            output_dir: 输出目录
            prefix: 文件名前缀
            
        Returns:
            保存的文件路径列表
        """
        os.makedirs(output_dir, exist_ok=True)
        saved_paths = []
        
        for i, img in enumerate(images):
            filename = f"{prefix}_{i:04d}.png"
            filepath = os.path.join(output_dir, filename)
            img.save(filepath, "PNG")
            saved_paths.append(filepath)
            logger.info(f"已保存: {filepath}")
        
        return saved_paths


# 榴莲专用提示词模板
DURIAN_PROMPT_TEMPLATES = {
    "musang_king": {
        "prompt": (
            "professional product photography of Musang King durian, "
            "golden yellow creamy flesh, vibrant color, "
            "split open showing thick pods, "
            "dark wooden table background, "
            "soft natural lighting from left, "
            "shallow depth of field, "
            "8k ultra HD, highly detailed"
        ),
        "name": "猫山王"
    },
    "monthong": {
        "prompt": (
            "professional product photography of Monthong durian, "
            "Thai golden pillow durian, "
            "pale yellow flesh, thick and plump, "
            "light linen background, "
            "bright natural lighting, "
            "clean and fresh style, "
            "8k ultra HD, highly detailed"
        ),
        "name": "金枕头"
    },
    "black_thorn": {
        "prompt": (
            "professional product photography of Black Thorn durian, "
            "deep orange flesh, intense color, "
            "premium Malaysian durian, "
            "black slate background, "
            "dramatic side lighting, "
            "luxury food photography style, "
            "8k ultra HD, highly detailed"
        ),
        "name": "黑刺"
    },
    "red_prawn": {
        "prompt": (
            "professional product photography of Red Prawn durian, "
            "vibrant orange-red flesh like shrimp, "
            "Udang Merah durian, "
            "dark ceramic plate, "
            "soft natural lighting, "
            "premium food photography, "
            "8k ultra HD, highly detailed"
        ),
        "name": "红虾"
    },
    "sultan": {
        "prompt": (
            "professional product photography of Sultan durian D24, "
            "pale yellow creamy flesh, "
            "olive green husk, "
            "rustic wooden table, "
            "warm natural lighting, "
            "food photography style, "
            "8k ultra HD, highly detailed"
        ),
        "name": "苏丹王"
    },
}


def test_base_generation():
    """
    测试基础生成功能
    """
    # 初始化模型
    sd = StableDiffusionBase()
    
    # 设置采样器
    sd.set_scheduler("euler_a")
    
    # 选择品种
    variety = "musang_king"
    template = DURIAN_PROMPT_TEMPLATES[variety]
    
    # 生成图像
    images = sd.generate(
        prompt=template["prompt"],
        width=512,
        height=512,
        num_inference_steps=30,
        guidance_scale=7.5,
        seed=42,
        num_images=2,
    )
    
    # 保存图像
    sd.save_images(images, output_dir="output/base", prefix=f"durian_{variety}")


if __name__ == "__main__":
    test_base_generation()
