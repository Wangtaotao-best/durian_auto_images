#!/usr/bin/env python3
"""
Gradio Web UI for 榴莲图像生成
提供图形化界面进行图像生成
"""

import gradio as gr
import torch
from PIL import Image
import os
import sys
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from sd_base import StableDiffusionBase, DURIAN_PROMPT_TEMPLATES
from controlnet_generator import ControlNetGenerator

# 全局模型缓存
_models = {}


def get_base_model(device="cuda"):
    """获取或创建基础模型"""
    key = f"base_{device}"
    if key not in _models:
        _models[key] = StableDiffusionBase(device=device)
        _models[key].set_scheduler("euler_a")
    return _models[key]


def get_controlnet_model(control_type="canny", device="cuda"):
    """获取或创建 ControlNet 模型"""
    key = f"controlnet_{control_type}_{device}"
    if key not in _models:
        _models[key] = ControlNetGenerator(control_type=control_type, device=device)
    return _models[key]


def generate_basic(
    variety,
    num_images,
    width,
    height,
    steps,
    guidance_scale,
    seed,
    progress=gr.Progress(),
):
    """基础生成功能"""
    try:
        # 获取模型
        progress(0, desc="加载模型...")
        sd = get_base_model()
        
        # 获取提示词
        if variety not in DURIAN_PROMPT_TEMPLATES:
            return [], f"错误: 未知品种 {variety}"
        
        template = DURIAN_PROMPT_TEMPLATES[variety]
        prompt = template["prompt"]
        
        progress(0.2, desc="生成图像...")
        
        # 生成图像
        images = sd.generate(
            prompt=prompt,
            width=width,
            height=height,
            num_inference_steps=steps,
            guidance_scale=guidance_scale,
            seed=seed if seed >= 0 else None,
            num_images=num_images,
        )
        
        progress(1.0, desc="完成!")
        
        # 保存图像
        output_dir = f"output/webui/{variety}"
        os.makedirs(output_dir, exist_ok=True)
        saved_paths = sd.save_images(images, output_dir, prefix=f"{variety}_webui")
        
        info = f"✅ 成功生成 {len(images)} 张 {template['name']} 图像\n"
        info += f"📁 保存位置: {os.path.abspath(output_dir)}"
        
        return images, info
        
    except Exception as e:
        return [], f"❌ 错误: {str(e)}"


def generate_controlnet(
    variety,
    control_image,
    control_type,
    control_scale,
    num_images,
    steps,
    guidance_scale,
    seed,
    progress=gr.Progress(),
):
    """ControlNet 生成功能"""
    try:
        if control_image is None:
            return [], "❌ 请上传参考图像"
        
        progress(0, desc="加载 ControlNet...")
        generator = get_controlnet_model(control_type)
        
        # 获取提示词
        if variety not in DURIAN_PROMPT_TEMPLATES:
            return [], f"错误: 未知品种 {variety}"
        
        template = DURIAN_PROMPT_TEMPLATES[variety]
        prompt = template["prompt"]
        
        progress(0.2, desc="生成图像...")
        
        # 生成图像
        images, control = generator.generate(
            prompt=prompt,
            control_image=control_image,
            num_images=num_images,
            num_inference_steps=steps,
            guidance_scale=guidance_scale,
            controlnet_conditioning_scale=control_scale,
            seed=seed if seed >= 0 else None,
        )
        
        progress(1.0, desc="完成!")
        
        # 保存图像
        output_dir = f"output/webui/controlnet/{variety}"
        os.makedirs(output_dir, exist_ok=True)
        saved_paths = generator.save_images(images, output_dir, prefix=f"{variety}_{control_type}")
        
        info = f"✅ 成功生成 {len(images)} 张图像\n"
        info += f"📁 保存位置: {os.path.abspath(output_dir)}\n"
        info += f"🎮 控制类型: {control_type}, 强度: {control_scale}"
        
        return images, info
        
    except Exception as e:
        return [], f"❌ 错误: {str(e)}"


def create_ui():
    """创建 Gradio UI"""
    
    # 品种选项
    variety_choices = [
        (f"{v['name']} ({k})", k)
        for k, v in DURIAN_PROMPT_TEMPLATES.items()
    ]
    
    with gr.Blocks(title="AIGC 榴莲图像生成器", theme=gr.themes.Soft()) as demo:
        
        gr.Markdown("""
        # 🥭 AIGC 榴莲图像数据集生成平台
        
        基于 **Stable Diffusion + LoRA + ControlNet** 技术
        """)
        
        with gr.Tab("基础生成"):
            with gr.Row():
                with gr.Column(scale=1):
                    # 输入参数
                    variety_basic = gr.Dropdown(
                        choices=variety_choices,
                        value="musang_king",
                        label="榴莲品种",
                    )
                    
                    with gr.Row():
                        num_images_basic = gr.Slider(
                            minimum=1, maximum=8, value=4, step=1,
                            label="生成数量",
                        )
                    
                    with gr.Row():
                        width_basic = gr.Slider(
                            minimum=256, maximum=1024, value=512, step=64,
                            label="宽度",
                        )
                        height_basic = gr.Slider(
                            minimum=256, maximum=1024, value=512, step=64,
                            label="高度",
                        )
                    
                    steps_basic = gr.Slider(
                        minimum=10, maximum=50, value=30, step=1,
                        label="推理步数",
                    )
                    
                    guidance_basic = gr.Slider(
                        minimum=1, maximum=15, value=7.5, step=0.5,
                        label="引导比例 (Guidance Scale)",
                    )
                    
                    seed_basic = gr.Number(
                        value=-1,
                        label="随机种子 (-1 表示随机)",
                        precision=0,
                    )
                    
                    generate_btn_basic = gr.Button(
                        "🎨 生成图像",
                        variant="primary",
                        size="lg",
                    )
                
                with gr.Column(scale=2):
                    # 输出
                    output_gallery_basic = gr.Gallery(
                        label="生成的图像",
                        columns=2,
                        rows=2,
                        height="auto",
                        object_fit="contain",
                    )
                    output_info_basic = gr.Textbox(
                        label="生成信息",
                        lines=3,
                    )
        
        with gr.Tab("ControlNet 控制生成"):
            with gr.Row():
                with gr.Column(scale=1):
                    # 输入参数
                    variety_control = gr.Dropdown(
                        choices=variety_choices,
                        value="musang_king",
                        label="榴莲品种",
                    )
                    
                    control_image = gr.Image(
                        type="pil",
                        label="参考图像 (用于结构控制)",
                    )
                    
                    control_type = gr.Dropdown(
                        choices=[
                            ("Canny 边缘", "canny"),
                            ("HED 软边缘", "hed"),
                            ("深度图", "depth"),
                        ],
                        value="canny",
                        label="控制类型",
                    )
                    
                    control_scale = gr.Slider(
                        minimum=0.1, maximum=2.0, value=0.8, step=0.1,
                        label="控制强度",
                    )
                    
                    num_images_control = gr.Slider(
                        minimum=1, maximum=8, value=4, step=1,
                        label="生成数量",
                    )
                    
                    steps_control = gr.Slider(
                        minimum=10, maximum=50, value=30, step=1,
                        label="推理步数",
                    )
                    
                    guidance_control = gr.Slider(
                        minimum=1, maximum=15, value=7.5, step=0.5,
                        label="引导比例",
                    )
                    
                    seed_control = gr.Number(
                        value=-1,
                        label="随机种子 (-1 表示随机)",
                        precision=0,
                    )
                    
                    generate_btn_control = gr.Button(
                        "🎮 控制生成",
                        variant="primary",
                        size="lg",
                    )
                
                with gr.Column(scale=2):
                    # 输出
                    output_gallery_control = gr.Gallery(
                        label="生成的图像",
                        columns=2,
                        rows=2,
                        height="auto",
                        object_fit="contain",
                    )
                    output_info_control = gr.Textbox(
                        label="生成信息",
                        lines=4,
                    )
        
        with gr.Tab("品种信息"):
            gr.Markdown("## 支持的榴莲品种")
            
            for key, info in DURIAN_PROMPT_TEMPLATES.items():
                with gr.Accordion(f"{info['name']} ({key})", open=False):
                    gr.Markdown(f"""
                    **英文名**: {key.replace('_', ' ').title()}
                    
                    **提示词**:
                    ```
                    {info['prompt']}
                    ```
                    """)
        
        # 事件绑定
        generate_btn_basic.click(
            fn=generate_basic,
            inputs=[
                variety_basic,
                num_images_basic,
                width_basic,
                height_basic,
                steps_basic,
                guidance_basic,
                seed_basic,
            ],
            outputs=[output_gallery_basic, output_info_basic],
        )
        
        generate_btn_control.click(
            fn=generate_controlnet,
            inputs=[
                variety_control,
                control_image,
                control_type,
                control_scale,
                num_images_control,
                steps_control,
                guidance_control,
                seed_control,
            ],
            outputs=[output_gallery_control, output_info_control],
        )
        
        gr.Markdown("""
        ---
        
        💡 **提示**: 
        - 首次生成需要下载模型，请耐心等待
        - 使用 GPU 可大幅提升生成速度
        - 设置随机种子可复现相同结果
        """)
    
    return demo


def main():
    """主函数"""
    print("🚀 启动 AIGC 榴莲图像生成 Web UI")
    print("📱 请在浏览器中打开显示的 URL")
    print()
    
    demo = create_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
    )


if __name__ == "__main__":
    main()
