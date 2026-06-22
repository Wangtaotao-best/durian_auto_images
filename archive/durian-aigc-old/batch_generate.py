"""
批量生成模块
整合 SD + LoRA + ControlNet 进行大规模数据生成
"""

import torch
from sd_base import StableDiffusionBase, DURIAN_PROMPT_TEMPLATES
from lora_trainer import LoRATrainer
from controlnet_generator import ControlNetGenerator, DurianControlNetPipeline
from PIL import Image
import os
import json
from pathlib import Path
from typing import List, Dict, Optional, Union
import logging
from datetime import datetime
from tqdm import tqdm
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DurianDatasetGenerator:
    """
    榴莲数据集生成器
    整合 SD + LoRA + ControlNet 的完整 pipeline
    """
    
    def __init__(
        self,
        base_model: str = "runwayml/stable-diffusion-v1-5",
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
        output_base_dir: str = "output/dataset",
    ):
        """
        初始化数据集生成器
        
        Args:
            base_model: 基础模型
            device: 运行设备
            output_base_dir: 输出基础目录
        """
        self.device = device
        self.output_base_dir = Path(output_base_dir)
        self.output_base_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化基础 SD
        logger.info("初始化基础 Stable Diffusion...")
        self.sd_base = StableDiffusionBase(
            model_id=base_model,
            device=device,
        )
        
        # 初始化 ControlNet
        logger.info("初始化 ControlNet...")
        try:
            self.controlnet = DurianControlNetPipeline(device=device)
        except Exception as e:
            logger.warning(f"ControlNet 初始化失败: {e}")
            self.controlnet = None
        
        # 加载的 LoRA 模型
        self.loaded_loras = {}
        
        logger.info("数据集生成器初始化完成")
    
    def load_lora(self, lora_path: str, variety_name: str):
        """
        加载 LoRA 模型
        
        Args:
            lora_path: LoRA 模型路径
            variety_name: 品种名称
        """
        logger.info(f"加载 LoRA 模型: {variety_name} from {lora_path}")
        
        # 使用 PEFT 加载 LoRA
        from peft import PeftModel
        
        # 将 LoRA 应用到 UNet
        self.sd_base.pipe.unet = PeftModel.from_pretrained(
            self.sd_base.pipe.unet,
            lora_path,
        )
        
        self.loaded_loras[variety_name] = lora_path
        logger.info(f"LoRA {variety_name} 加载完成")
    
    def unload_lora(self, variety_name: str):
        """
        卸载 LoRA 模型
        
        Args:
            variety_name: 品种名称
        """
        if variety_name in self.loaded_loras:
            logger.info(f"卸载 LoRA: {variety_name}")
            # 恢复到原始 UNet
            self.sd_base.pipe.unet = self.sd_base.pipe.unet.unload()
            del self.loaded_loras[variety_name]
    
    def generate_single_variety(
        self,
        variety: str,
        num_images: int = 100,
        use_lora: bool = True,
        use_controlnet: bool = False,
        control_image: Optional[str] = None,
        batch_size: int = 4,
        seed_start: int = 0,
    ) -> Dict[str, any]:
        """
        生成单个品种的图像
        
        Args:
            variety: 品种名称
            num_images: 生成数量
            use_lora: 是否使用 LoRA
            use_controlnet: 是否使用 ControlNet
            control_image: 控制图像路径
            batch_size: 批次大小
            seed_start: 起始随机种子
            
        Returns:
            生成结果统计
        """
        logger.info(f"开始生成 {variety} 品种图像，数量: {num_images}")
        
        # 获取提示词模板
        if variety not in DURIAN_PROMPT_TEMPLATES:
            raise ValueError(f"未知品种: {variety}")
        
        template = DURIAN_PROMPT_TEMPLATES[variety]
        prompt = template["prompt"]
        
        # 创建输出目录
        variety_dir = self.output_base_dir / variety
        variety_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载 LoRA（如果需要）
        lora_path = f"models/lora/{variety}/checkpoint-final"
        if use_lora and os.path.exists(lora_path):
            self.load_lora(lora_path, variety)
        
        # 生成图像
        generated_files = []
        failed_count = 0
        
        num_batches = (num_images + batch_size - 1) // batch_size
        
        for batch_idx in tqdm(range(num_batches), desc=f"生成 {variety}"):
            current_batch_size = min(batch_size, num_images - batch_idx * batch_size)
            seed = seed_start + batch_idx
            
            try:
                if use_controlnet and control_image and self.controlnet:
                    # 使用 ControlNet 生成
                    images, _ = self.controlnet.generators["canny"].generate(
                        prompt=prompt,
                        control_image=control_image,
                        num_images=current_batch_size,
                        seed=seed,
                    )
                else:
                    # 使用基础 SD 生成
                    images = self.sd_base.generate(
                        prompt=prompt,
                        num_images=current_batch_size,
                        seed=seed,
                    )
                
                # 保存图像
                start_idx = batch_idx * batch_size
                for i, img in enumerate(images):
                    filename = f"{variety}_{start_idx + i:05d}.png"
                    filepath = variety_dir / filename
                    img.save(filepath, "PNG")
                    generated_files.append(str(filepath))
                
            except Exception as e:
                logger.error(f"批次 {batch_idx} 生成失败: {e}")
                failed_count += current_batch_size
        
        # 卸载 LoRA
        if use_lora and variety in self.loaded_loras:
            self.unload_lora(variety)
        
        # 生成统计信息
        stats = {
            "variety": variety,
            "variety_name": template["name"],
            "num_requested": num_images,
            "num_generated": len(generated_files),
            "num_failed": failed_count,
            "output_dir": str(variety_dir),
            "generated_files": generated_files,
            "use_lora": use_lora,
            "use_controlnet": use_controlnet,
        }
        
        # 保存统计信息
        stats_file = variety_dir / "generation_stats.json"
        with open(stats_file, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        logger.info(f"{variety} 生成完成: {len(generated_files)}/{num_images}")
        return stats
    
    def generate_dataset(
        self,
        varieties: List[str],
        images_per_variety: int = 100,
        use_lora: bool = True,
        use_controlnet: bool = False,
        seed_base: int = 42,
    ) -> Dict[str, Dict]:
        """
        生成完整的数据集
        
        Args:
            varieties: 品种列表
            images_per_variety: 每个品种的图像数量
            use_lora: 是否使用 LoRA
            use_controlnet: 是否使用 ControlNet
            seed_base: 基础随机种子
            
        Returns:
            所有品种的生成统计
        """
        logger.info(f"开始生成数据集: {len(varieties)} 个品种")
        
        all_stats = {}
        
        for i, variety in enumerate(varieties):
            logger.info(f"\n{'='*50}")
            logger.info(f"处理品种 {i+1}/{len(varieties)}: {variety}")
            logger.info(f"{'='*50}\n")
            
            stats = self.generate_single_variety(
                variety=variety,
                num_images=images_per_variety,
                use_lora=use_lora,
                use_controlnet=use_controlnet,
                seed_start=seed_base + i * 10000,
            )
            
            all_stats[variety] = stats
        
        # 保存总体统计
        summary = {
            "generation_time": datetime.now().isoformat(),
            "total_varieties": len(varieties),
            "images_per_variety": images_per_variety,
            "total_images": sum(s["num_generated"] for s in all_stats.values()),
            "varieties": all_stats,
        }
        
        summary_file = self.output_base_dir / "dataset_summary.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n{'='*50}")
        logger.info("数据集生成完成!")
        logger.info(f"总计生成: {summary['total_images']} 张图像")
        logger.info(f"输出目录: {self.output_base_dir}")
        logger.info(f"{'='*50}\n")
        
        return all_stats
    
    def generate_with_variations(
        self,
        variety: str,
        num_base_images: int = 10,
        variations_per_image: int = 5,
    ) -> List[str]:
        """
        基于基础图像生成多样化变体
        
        Args:
            variety: 品种名称
            num_base_images: 基础图像数量
            variations_per_image: 每个基础图像的变体数量
            
        Returns:
            生成的文件路径列表
        """
        logger.info(f"生成 {variety} 多样化变体")
        
        # 首先生成基础图像
        base_stats = self.generate_single_variety(
            variety=variety,
            num_images=num_base_images,
            use_lora=True,
        )
        
        if not self.controlnet:
            logger.warning("ControlNet 不可用，跳过变体生成")
            return base_stats["generated_files"]
        
        # 基于每个基础图像生成变体
        all_files = base_stats["generated_files"].copy()
        variety_dir = Path(base_stats["output_dir"])
        
        for i, base_file in enumerate(base_stats["generated_files"]):
            logger.info(f"生成变体 {i+1}/{num_base_images}...")
            
            # 使用 ControlNet 生成变体
            variations = self.controlnet.generators["canny"].generate_variations(
                prompt=DURIAN_PROMPT_TEMPLATES[variety]["prompt"],
                control_image=base_file,
                num_variations=variations_per_image,
                control_scales=[0.5, 0.7, 0.9, 1.1, 1.3],
            )
            
            # 保存变体
            for j, (images, control, scale) in enumerate(variations):
                for k, img in enumerate(images):
                    filename = f"{variety}_base{i:03d}_var{j}_scale{scale:.1f}_{k}.png"
                    filepath = variety_dir / "variations" / filename
                    filepath.parent.mkdir(parents=True, exist_ok=True)
                    img.save(filepath, "PNG")
                    all_files.append(str(filepath))
        
        logger.info(f"变体生成完成，总计: {len(all_files)} 张图像")
        return all_files


def quick_generate(
    variety: str = "musang_king",
    num_images: int = 10,
    output_dir: str = "output/quick",
):
    """
    快速生成函数（不使用 LoRA，仅基础 SD）
    
    Args:
        variety: 品种名称
        num_images: 生成数量
        output_dir: 输出目录
    """
    logger.info("快速生成模式（基础 SD）")
    
    # 初始化基础 SD
    sd = StableDiffusionBase()
    sd.set_scheduler("euler_a")
    
    # 获取提示词
    if variety not in DURIAN_PROMPT_TEMPLATES:
        logger.error(f"未知品种: {variety}")
        return
    
    template = DURIAN_PROMPT_TEMPLATES[variety]
    prompt = template["prompt"]
    
    logger.info(f"生成 {num_images} 张 {template['name']} 图像...")
    
    # 生成图像
    images = sd.generate(
        prompt=prompt,
        num_images=num_images,
        seed=42,
        num_inference_steps=30,
    )
    
    # 保存图像
    saved = sd.save_images(images, output_dir, prefix=variety)
    
    logger.info(f"生成完成! 保存在: {output_dir}")
    return saved


def generate_full_dataset():
    """
    生成完整数据集的示例
    """
    # 创建生成器
    generator = DurianDatasetGenerator(
        output_base_dir="output/full_dataset",
    )
    
    # 定义要生成的品种
    varieties = ["musang_king", "monthong", "black_thorn", "sultan", "red_prawn"]
    
    # 生成数据集（不使用 LoRA，快速演示）
    stats = generator.generate_dataset(
        varieties=varieties,
        images_per_variety=20,  # 每个品种 20 张
        use_lora=False,  # 不使用 LoRA
        use_controlnet=False,  # 不使用 ControlNet
    )
    
    return stats


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="榴莲数据集生成工具")
    parser.add_argument("--mode", type=str, default="quick", 
                       choices=["quick", "full", "variety"],
                       help="生成模式")
    parser.add_argument("--variety", type=str, default="musang_king",
                       help="品种名称")
    parser.add_argument("--num", type=int, default=10,
                       help="生成数量")
    parser.add_argument("--output", type=str, default="output",
                       help="输出目录")
    
    args = parser.parse_args()
    
    if args.mode == "quick":
        quick_generate(args.variety, args.num, args.output)
    elif args.mode == "full":
        generate_full_dataset()
    elif args.mode == "variety":
        generator = DurianDatasetGenerator(output_base_dir=args.output)
        generator.generate_single_variety(
            variety=args.variety,
            num_images=args.num,
            use_lora=False,
        )
