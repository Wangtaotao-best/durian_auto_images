"""
ControlNet 控制生成模块
用于精确控制榴莲图像的生成
"""

import torch
from diffusers import StableDiffusionControlNetPipeline, ControlNetModel, UniPCMultistepScheduler
from controlnet_aux import CannyDetector, OpenposeDetector, HEDdetector
from PIL import Image
import numpy as np
import cv2
import os
from typing import Optional, List, Union, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ControlNetGenerator:
    """
    ControlNet 图像生成器
    支持多种控制类型：Canny边缘、OpenPose姿态、HED软边缘
    """
    
    def __init__(
        self,
        base_model: str = "runwayml/stable-diffusion-v1-5",
        controlnet_model: Optional[str] = None,
        control_type: str = "canny",
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
    ):
        """
        初始化 ControlNet 生成器
        
        Args:
            base_model: 基础 SD 模型
            controlnet_model: ControlNet 模型路径
            control_type: 控制类型 (canny/openpose/hed)
            device: 运行设备
        """
        self.device = device
        self.control_type = control_type
        
        # 默认 ControlNet 模型
        if controlnet_model is None:
            controlnet_models = {
                "canny": "lllyasviel/sd-controlnet-canny",
                "openpose": "lllyasviel/sd-controlnet-openpose",
                "hed": "lllyasviel/sd-controlnet-hed",
                "depth": "lllyasviel/sd-controlnet-depth",
                "scribble": "lllyasviel/sd-controlnet-scribble",
            }
            controlnet_model = controlnet_models.get(control_type, controlnet_models["canny"])
        
        logger.info(f"正在加载 ControlNet 模型: {controlnet_model}")
        
        # 加载 ControlNet 模型
        controlnet = ControlNetModel.from_pretrained(
            controlnet_model,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        )
        
        # 加载 Pipeline
        self.pipe = StableDiffusionControlNetPipeline.from_pretrained(
            base_model,
            controlnet=controlnet,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            safety_checker=None,
            requires_safety_checker=False,
        )
        
        self.pipe = self.pipe.to(device)
        
        # 使用 UniPC 调度器
        self.pipe.scheduler = UniPCMultistepScheduler.from_config(
            self.pipe.scheduler.config
        )
        
        # 内存优化
        if device == "cuda":
            self.pipe.enable_attention_slicing()
            try:
                self.pipe.enable_xformers_memory_efficient_attention()
            except:
                pass
        
        # 初始化预处理器
        self._init_preprocessors()
        
        logger.info("ControlNet 加载完成")
    
    def _init_preprocessors(self):
        """初始化控制图像预处理器"""
        self.canny_detector = CannyDetector()
        self.hed_detector = HEDdetector.from_pretrained("lllyasviel/ControlNet")
        
        # OpenPose 需要额外安装
        try:
            self.openpose_detector = OpenposeDetector.from_pretrained("lllyasviel/ControlNet")
        except:
            logger.warning("OpenPose 检测器加载失败，请确保已安装相关依赖")
            self.openpose_detector = None
    
    def preprocess_image(
        self,
        image: Union[Image.Image, np.ndarray, str],
        control_type: Optional[str] = None,
        **kwargs
    ) -> Image.Image:
        """
        预处理控制图像
        
        Args:
            image: 输入图像
            control_type: 控制类型
            **kwargs: 预处理参数
            
        Returns:
            预处理后的控制图像
        """
        if control_type is None:
            control_type = self.control_type
        
        # 加载图像
        if isinstance(image, str):
            image = Image.open(image).convert("RGB")
        elif isinstance(image, np.ndarray):
            image = Image.fromarray(image)
        
        # 调整大小
        width = kwargs.get("width", 512)
        height = kwargs.get("height", 512)
        image = image.resize((width, height), Image.BILINEAR)
        
        # 转换为 numpy
        image_np = np.array(image)
        
        # 根据控制类型进行预处理
        if control_type == "canny":
            return self._canny_preprocess(image_np, **kwargs)
        elif control_type == "hed":
            return self._hed_preprocess(image_np, **kwargs)
        elif control_type == "openpose":
            return self._openpose_preprocess(image_np, **kwargs)
        elif control_type == "depth":
            return self._depth_preprocess(image_np, **kwargs)
        else:
            raise ValueError(f"不支持的 control_type: {control_type}")
    
    def _canny_preprocess(
        self,
        image: np.ndarray,
        low_threshold: int = 100,
        high_threshold: int = 200,
        **kwargs
    ) -> Image.Image:
        """Canny 边缘检测预处理"""
        # 使用 controlnet_aux 的 Canny 检测器
        canny_image = self.canny_detector(image, low_threshold, high_threshold)
        return canny_image
    
    def _hed_preprocess(self, image: np.ndarray, **kwargs) -> Image.Image:
        """HED 软边缘预处理"""
        hed_image = self.hed_detector(image)
        return hed_image
    
    def _openpose_preprocess(self, image: np.ndarray, **kwargs) -> Image.Image:
        """OpenPose 姿态预处理"""
        if self.openpose_detector is None:
            raise RuntimeError("OpenPose 检测器未加载")
        openpose_image = self.openpose_detector(image)
        return openpose_image
    
    def _depth_preprocess(self, image: np.ndarray, **kwargs) -> Image.Image:
        """深度图预处理 (简化版本)"""
        # 转换为灰度图作为简化的深度估计
        if len(image.shape) == 3:
            depth = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            depth = image
        
        # 归一化
        depth = cv2.normalize(depth, None, 0, 255, cv2.NORM_MINMAX)
        depth = np.stack([depth] * 3, axis=-1)
        
        return Image.fromarray(depth.astype(np.uint8))
    
    def generate(
        self,
        prompt: str,
        control_image: Union[Image.Image, np.ndarray, str],
        negative_prompt: str = "",
        width: int = 512,
        height: int = 512,
        num_inference_steps: int = 30,
        guidance_scale: float = 7.5,
        controlnet_conditioning_scale: float = 1.0,
        seed: Optional[int] = None,
        num_images: int = 1,
    ) -> Tuple[List[Image.Image], Image.Image]:
        """
        生成图像
        
        Args:
            prompt: 正向提示词
            control_image: 控制图像
            negative_prompt: 负向提示词
            width: 图像宽度
            height: 图像高度
            num_inference_steps: 推理步数
            guidance_scale: 引导比例
            controlnet_conditioning_scale: ControlNet 条件比例
            seed: 随机种子
            num_images: 生成图像数量
            
        Returns:
            (生成的图像列表, 控制图像)
        """
        # 预处理控制图像
        processed_control = self.preprocess_image(
            control_image,
            width=width,
            height=height,
        )
        
        # 设置随机种子
        generator = None
        if seed is not None:
            generator = torch.Generator(device=self.device).manual_seed(seed)
        
        # 默认负向提示词
        default_negative = (
            "low quality, blurry, distorted, deformed, "
            "bad anatomy, extra limbs, missing limbs, "
            "watermark, signature, text, logo"
        )
        
        if negative_prompt:
            negative_prompt = f"{default_negative}, {negative_prompt}"
        else:
            negative_prompt = default_negative
        
        logger.info(f"生成图像: {prompt}")
        logger.info(f"ControlNet 条件比例: {controlnet_conditioning_scale}")
        
        # 生成图像
        with torch.autocast(self.device, dtype=torch.float16 if self.device == "cuda" else torch.float32):
            images = self.pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
                image=processed_control,
                width=width,
                height=height,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                controlnet_conditioning_scale=controlnet_conditioning_scale,
                generator=generator,
                num_images_per_prompt=num_images,
            ).images
        
        logger.info(f"成功生成 {len(images)} 张图像")
        return images, processed_control
    
    def generate_variations(
        self,
        prompt: str,
        control_image: Union[Image.Image, str],
        num_variations: int = 4,
        control_scales: List[float] = [0.5, 0.8, 1.0, 1.2],
        **kwargs
    ) -> List[Tuple[List[Image.Image], Image.Image, float]]:
        """
        使用不同的 ControlNet 条件比例生成多样化图像
        
        Args:
            prompt: 提示词
            control_image: 控制图像
            num_variations: 变化数量
            control_scales: ControlNet 条件比例列表
            **kwargs: 其他生成参数
            
        Returns:
            生成结果列表 [(images, control_image, scale), ...]
        """
        results = []
        
        for scale in control_scales[:num_variations]:
            logger.info(f"使用 control_scale={scale} 生成...")
            images, control = self.generate(
                prompt=prompt,
                control_image=control_image,
                controlnet_conditioning_scale=scale,
                **kwargs
            )
            results.append((images, control, scale))
        
        return results
    
    def save_images(
        self,
        images: List[Image.Image],
        output_dir: str,
        prefix: str = "generated",
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


class DurianControlNetPipeline:
    """
    榴莲专用的 ControlNet 生成流水线
    """
    
    def __init__(self, device: str = "cuda" if torch.cuda.is_available() else "cpu"):
        self.device = device
        self.generators = {}
        
        # 初始化各种 ControlNet
        for control_type in ["canny", "hed", "depth"]:
            try:
                self.generators[control_type] = ControlNetGenerator(
                    control_type=control_type,
                    device=device,
                )
                logger.info(f"{control_type} ControlNet 初始化成功")
            except Exception as e:
                logger.warning(f"{control_type} ControlNet 初始化失败: {e}")
    
    def generate_with_edge_control(
        self,
        prompt: str,
        reference_image: Union[Image.Image, str],
        variety: str = "musang_king",
        output_dir: str = "output/controlnet",
        num_images: int = 4,
    ) -> List[str]:
        """
        使用边缘控制生成榴莲图像
        
        Args:
            prompt: 提示词
            reference_image: 参考图像
            variety: 品种名称
            output_dir: 输出目录
            num_images: 生成数量
            
        Returns:
            保存的文件路径列表
        """
        if "canny" not in self.generators:
            raise RuntimeError("Canny ControlNet 未初始化")
        
        generator = self.generators["canny"]
        
        # 生成图像
        images, control = generator.generate(
            prompt=prompt,
            control_image=reference_image,
            num_images=num_images,
            controlnet_conditioning_scale=0.8,
            num_inference_steps=30,
        )
        
        # 保存控制图像
        os.makedirs(output_dir, exist_ok=True)
        control_path = os.path.join(output_dir, f"{variety}_canny_control.png")
        control.save(control_path)
        
        # 保存生成的图像
        saved_paths = generator.save_images(
            images,
            output_dir,
            prefix=f"{variety}_canny",
        )
        
        return saved_paths


# 榴莲专用提示词模板
DURIAN_CONTROLNET_PROMPTS = {
    "musang_king_canny": {
        "prompt": (
            "professional photo of Musang King durian, "
            "golden yellow creamy flesh, premium quality, "
            "split open showing perfect pods, "
            "dark background, studio lighting, 8k"
        ),
        "control_type": "canny",
    },
    "monthong_hed": {
        "prompt": (
            "professional photo of Monthong durian, "
            "pale yellow thick flesh, Thai variety, "
            "clean background, bright lighting, 8k"
        ),
        "control_type": "hed",
    },
}


def test_controlnet_generation():
    """
    测试 ControlNet 生成功能
    """
    # 创建生成器
    generator = ControlNetGenerator(control_type="canny")
    
    # 加载参考图像（需要用户提供）
    reference_image = "training_data/reference_durian.jpg"
    
    if not os.path.exists(reference_image):
        logger.error(f"参考图像不存在: {reference_image}")
        logger.info("请提供参考图像路径")
        return
    
    # 生成图像
    prompt = DURIAN_CONTROLNET_PROMPTS["musang_king_canny"]["prompt"]
    
    images, control = generator.generate(
        prompt=prompt,
        control_image=reference_image,
        num_images=2,
        controlnet_conditioning_scale=0.8,
    )
    
    # 保存结果
    output_dir = "output/controlnet"
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存控制图像
    control.save(os.path.join(output_dir, "canny_control.png"))
    
    # 保存生成的图像
    generator.save_images(images, output_dir, prefix="durian_controlled")
    
    logger.info("测试完成!")


if __name__ == "__main__":
    test_controlnet_generation()
