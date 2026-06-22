"""
LoRA (Low-Rank Adaptation) 训练模块
用于训练榴莲品种特定的 LoRA 模型
"""

import torch
from torch.utils.data import Dataset, DataLoader
from diffusers import StableDiffusionPipeline, DDPMScheduler
from transformers import CLIPTokenizer
from peft import LoraConfig, get_peft_model, PeftModel
from PIL import Image
import os
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging
from tqdm import tqdm
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DurianDataset(Dataset):
    """
    榴莲图像数据集
    """
    
    def __init__(
        self,
        image_dir: str,
        instance_prompt: str,
        tokenizer: CLIPTokenizer,
        size: int = 512,
        center_crop: bool = True,
    ):
        """
        初始化数据集
        
        Args:
            image_dir: 图像目录
            instance_prompt: 实例提示词
            tokenizer: CLIP 分词器
            size: 图像尺寸
            center_crop: 是否中心裁剪
        """
        self.image_dir = Path(image_dir)
        self.instance_prompt = instance_prompt
        self.tokenizer = tokenizer
        self.size = size
        self.center_crop = center_crop
        
        # 获取所有图像文件
        self.image_paths = []
        for ext in ["*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG"]:
            self.image_paths.extend(list(self.image_dir.glob(ext)))
        
        self.image_paths = sorted(self.image_paths)
        logger.info(f"找到 {len(self.image_paths)} 张训练图像")
        
        if len(self.image_paths) == 0:
            raise ValueError(f"在 {image_dir} 中没有找到图像文件")
    
    def __len__(self) -> int:
        return len(self.image_paths)
    
    def __getitem__(self, index: int) -> Dict[str, torch.Tensor]:
        # 加载图像
        image_path = self.image_paths[index]
        image = Image.open(image_path).convert("RGB")
        
        # 调整图像大小
        image = image.resize((self.size, self.size), Image.BILINEAR)
        
        # 转换为 tensor
        image = torch.from_numpy((image).copy()).float() / 255.0
        image = image.permute(2, 0, 1)  # HWC -> CHW
        
        # 归一化到 [-1, 1]
        image = image * 2.0 - 1.0
        
        # 编码提示词
        prompt_tokens = self.tokenizer(
            self.instance_prompt,
            padding="max_length",
            truncation=True,
            max_length=self.tokenizer.model_max_length,
            return_tensors="pt",
        )
        
        return {
            "pixel_values": image,
            "input_ids": prompt_tokens.input_ids.squeeze(0),
        }


class LoRATrainer:
    """
    LoRA 训练器
    """
    
    def __init__(
        self,
        pretrained_model_name: str = "runwayml/stable-diffusion-v1-5",
        output_dir: str = "./models/lora",
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
    ):
        """
        初始化 LoRA 训练器
        
        Args:
            pretrained_model_name: 预训练模型名称
            output_dir: 输出目录
            device: 运行设备
        """
        self.device = device
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"正在加载预训练模型: {pretrained_model_name}")
        
        # 加载 pipeline
        self.pipe = StableDiffusionPipeline.from_pretrained(
            pretrained_model_name,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        )
        self.pipe = self.pipe.to(device)
        
        # 获取各组件
        self.vae = self.pipe.vae
        self.unet = self.pipe.unet
        self.text_encoder = self.pipe.text_encoder
        self.tokenizer = self.pipe.tokenizer
        self.noise_scheduler = DDPMScheduler.from_config(
            self.pipe.scheduler.config
        )
        
        # 冻结 VAE 和文本编码器
        self.vae.requires_grad_(False)
        self.text_encoder.requires_grad_(False)
        
        logger.info("模型加载完成")
    
    def setup_lora(
        self,
        r: int = 8,
        lora_alpha: int = 32,
        target_modules: Optional[List[str]] = None,
    ):
        """
        设置 LoRA 配置
        
        Args:
            r: LoRA 秩
            lora_alpha: LoRA alpha 参数
            target_modules: 目标模块列表
        """
        if target_modules is None:
            # UNet 的注意力模块
            target_modules = [
                "to_q",
                "to_k", 
                "to_v",
                "to_out.0",
                "proj_in",
                "proj_out",
                "ff.net.0.proj",
                "ff.net.2",
            ]
        
        # 创建 LoRA 配置
        lora_config = LoraConfig(
            r=r,
            lora_alpha=lora_alpha,
            target_modules=target_modules,
            lora_dropout=0.0,
            bias="none",
        )
        
        # 将 LoRA 应用到 UNet
        self.unet = get_peft_model(self.unet, lora_config)
        
        logger.info(f"LoRA 配置完成: r={r}, alpha={lora_alpha}")
        logger.info(f"可训练参数: {self.unet.print_trainable_parameters()}")
    
    def train(
        self,
        train_dataloader: DataLoader,
        num_epochs: int = 100,
        learning_rate: float = 1e-4,
        save_steps: int = 500,
        mixed_precision: str = "fp16",
        gradient_accumulation_steps: int = 1,
        max_grad_norm: float = 1.0,
    ):
        """
        训练 LoRA 模型
        
        Args:
            train_dataloader: 训练数据加载器
            num_epochs: 训练轮数
            learning_rate: 学习率
            save_steps: 保存步数
            mixed_precision: 混合精度
            gradient_accumulation_steps: 梯度累积步数
            max_grad_norm: 最大梯度范数
        """
        # 优化器
        optimizer = torch.optim.AdamW(
            self.unet.parameters(),
            lr=learning_rate,
            betas=(0.9, 0.999),
            weight_decay=0.01,
        )
        
        # 学习率调度器
        lr_scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer,
            T_max=num_epochs * len(train_dataloader),
        )
        
        # 训练步数
        global_step = 0
        
        logger.info(f"开始训练: {num_epochs} epochs, lr={learning_rate}")
        
        for epoch in range(num_epochs):
            self.unet.train()
            epoch_loss = 0.0
            
            progress_bar = tqdm(
                train_dataloader,
                desc=f"Epoch {epoch+1}/{num_epochs}"
            )
            
            for step, batch in enumerate(progress_bar):
                # 将数据移到设备
                pixel_values = batch["pixel_values"].to(self.device)
                input_ids = batch["input_ids"].to(self.device)
                
                # VAE 编码
                with torch.no_grad():
                    latents = self.vae.encode(pixel_values).latent_dist.sample()
                    latents = latents * self.vae.config.scaling_factor
                
                # 添加噪声
                noise = torch.randn_like(latents)
                timesteps = torch.randint(
                    0,
                    self.noise_scheduler.config.num_train_timesteps,
                    (latents.shape[0],),
                    device=self.device,
                ).long()
                
                noisy_latents = self.noise_scheduler.add_noise(
                    latents, noise, timesteps
                )
                
                # 文本编码
                with torch.no_grad():
                    encoder_hidden_states = self.text_encoder(input_ids)[0]
                
                # 预测噪声
                noise_pred = self.unet(
                    noisy_latents,
                    timesteps,
                    encoder_hidden_states,
                ).sample
                
                # 计算损失
                loss = torch.nn.functional.mse_loss(noise_pred, noise)
                
                # 反向传播
                loss.backward()
                
                # 梯度裁剪
                if (step + 1) % gradient_accumulation_steps == 0:
                    torch.nn.utils.clip_grad_norm_(
                        self.unet.parameters(),
                        max_grad_norm,
                    )
                    optimizer.step()
                    lr_scheduler.step()
                    optimizer.zero_grad()
                    global_step += 1
                
                epoch_loss += loss.item()
                progress_bar.set_postfix({"loss": loss.item()})
                
                # 保存检查点
                if global_step > 0 and global_step % save_steps == 0:
                    self.save_checkpoint(global_step)
            
            avg_loss = epoch_loss / len(train_dataloader)
            logger.info(f"Epoch {epoch+1} 完成, 平均损失: {avg_loss:.4f}")
        
        # 保存最终模型
        self.save_checkpoint("final")
        logger.info("训练完成!")
    
    def save_checkpoint(self, step: Union[int, str]):
        """
        保存 LoRA 检查点
        
        Args:
            step: 训练步数
        """
        save_path = self.output_dir / f"checkpoint-{step}"
        save_path.mkdir(parents=True, exist_ok=True)
        
        # 保存 LoRA 权重
        self.unet.save_pretrained(save_path)
        
        logger.info(f"检查点已保存: {save_path}")
    
    def load_lora_weights(self, lora_path: str):
        """
        加载 LoRA 权重
        
        Args:
            lora_path: LoRA 权重路径
        """
        logger.info(f"加载 LoRA 权重: {lora_path}")
        self.unet.load_adapter(lora_path, adapter_name="default")


def train_durian_lora(
    image_dir: str,
    instance_prompt: str,
    output_dir: str,
    variety_name: str,
    num_epochs: int = 100,
    learning_rate: float = 1e-4,
    batch_size: int = 1,
    lora_r: int = 8,
):
    """
    训练榴莲品种 LoRA 模型的便捷函数
    
    Args:
        image_dir: 训练图像目录
        instance_prompt: 实例提示词
        output_dir: 输出目录
        variety_name: 品种名称
        num_epochs: 训练轮数
        learning_rate: 学习率
        batch_size: 批次大小
        lora_r: LoRA 秩
    """
    # 创建训练器
    trainer = LoRATrainer(
        output_dir=f"{output_dir}/{variety_name}"
    )
    
    # 设置 LoRA
    trainer.setup_lora(r=lora_r, lora_alpha=lora_r * 4)
    
    # 创建数据集
    dataset = DurianDataset(
        image_dir=image_dir,
        instance_prompt=instance_prompt,
        tokenizer=trainer.tokenizer,
    )
    
    # 创建数据加载器
    dataloader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=0,
    )
    
    # 开始训练
    trainer.train(
        train_dataloader=dataloader,
        num_epochs=num_epochs,
        learning_rate=learning_rate,
        save_steps=100,
    )


# 品种特定的训练配置
DURIAN_TRAINING_CONFIGS = {
    "musang_king": {
        "instance_prompt": (
            "a photo of musangking durian, golden yellow flesh, "
            "creamy texture, premium quality"
        ),
        "num_epochs": 100,
        "learning_rate": 1e-4,
    },
    "monthong": {
        "instance_prompt": (
            "a photo of monthong durian, pale yellow flesh, "
            "thick pods, Thai variety"
        ),
        "num_epochs": 100,
        "learning_rate": 1e-4,
    },
    "black_thorn": {
        "instance_prompt": (
            "a photo of black thorn durian, deep orange flesh, "
            "intense color, Malaysian premium"
        ),
        "num_epochs": 120,
        "learning_rate": 8e-5,
    },
}


if __name__ == "__main__":
    # 示例：训练猫山王 LoRA
    train_durian_lora(
        image_dir="training_data/musang_king",
        instance_prompt=DURIAN_TRAINING_CONFIGS["musang_king"]["instance_prompt"],
        output_dir="models/lora",
        variety_name="musang_king",
        num_epochs=50,
    )
