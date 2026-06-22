#!/usr/bin/env python3
"""
榴莲图像生成 - 快速启动脚本
整合 SD + LoRA + ControlNet 的完整 pipeline
"""

import argparse
import os
import sys
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))


def print_banner():
    """打印启动横幅"""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║     🥭 AIGC 榴莲图像数据集生成平台 🥭                          ║
║                                                               ║
║     Stable Diffusion + LoRA + ControlNet                     ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """)


def check_environment():
    """检查运行环境"""
    print("🔍 检查运行环境...")
    
    # 检查 Python 版本
    import sys
    if sys.version_info < (3, 8):
        print("❌ Python 版本需要 >= 3.8")
        return False
    print(f"✅ Python 版本: {sys.version.split()[0]}")
    
    # 检查 PyTorch
    try:
        import torch
        print(f"✅ PyTorch 版本: {torch.__version__}")
        
        # 检查 CUDA
        if torch.cuda.is_available():
            print(f"✅ CUDA 可用: {torch.cuda.get_device_name(0)}")
            print(f"   GPU 显存: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
        else:
            print("⚠️  CUDA 不可用，将使用 CPU 运行 (速度较慢)")
    except ImportError:
        print("❌ PyTorch 未安装")
        return False
    
    # 检查 diffusers
    try:
        import diffusers
        print(f"✅ Diffusers 版本: {diffusers.__version__}")
    except ImportError:
        print("❌ Diffusers 未安装")
        return False
    
    print()
    return True


def quick_generate(args):
    """快速生成模式"""
    print(f"🚀 快速生成模式: {args.variety}")
    print(f"   数量: {args.num}")
    print(f"   输出: {args.output}")
    print()
    
    from sd_base import StableDiffusionBase, DURIAN_PROMPT_TEMPLATES
    
    # 初始化模型
    print("📦 正在加载模型...")
    sd = StableDiffusionBase(device=args.device)
    sd.set_scheduler("euler_a")
    
    # 获取提示词
    if args.variety not in DURIAN_PROMPT_TEMPLATES:
        print(f"❌ 未知品种: {args.variety}")
        print(f"可用品种: {', '.join(DURIAN_PROMPT_TEMPLATES.keys())}")
        return
    
    template = DURIAN_PROMPT_TEMPLATES[args.variety]
    print(f"📝 品种: {template['name']}")
    print()
    
    # 生成图像
    print(f"🎨 正在生成 {args.num} 张图像...")
    images = sd.generate(
        prompt=template["prompt"],
        num_images=args.num,
        seed=args.seed,
        width=args.width,
        height=args.height,
        num_inference_steps=args.steps,
    )
    
    # 保存图像
    os.makedirs(args.output, exist_ok=True)
    saved = sd.save_images(images, args.output, prefix=args.variety)
    
    print()
    print(f"✅ 生成完成!")
    print(f"📁 输出目录: {os.path.abspath(args.output)}")
    print(f"🖼️  生成图像: {len(saved)} 张")


def train_lora(args):
    """训练 LoRA 模式"""
    print(f"🎯 LoRA 训练模式: {args.variety}")
    print(f"   训练数据: {args.data_dir}")
    print(f"   输出: {args.output}")
    print()
    
    from lora_trainer import train_durian_lora, DURIAN_TRAINING_CONFIGS
    
    # 检查训练数据
    if not os.path.exists(args.data_dir):
        print(f"❌ 训练数据目录不存在: {args.data_dir}")
        print("请准备训练图像并放置在指定目录")
        return
    
    # 获取配置
    config = DURIAN_TRAINING_CONFIGS.get(args.variety, {
        "instance_prompt": f"a photo of {args.variety} durian",
        "num_epochs": args.epochs,
        "learning_rate": args.lr,
    })
    
    print(f"📊 训练参数:")
    print(f"   Epochs: {config.get('num_epochs', args.epochs)}")
    print(f"   Learning Rate: {config.get('learning_rate', args.lr)}")
    print(f"   LoRA Rank: {args.rank}")
    print()
    
    # 开始训练
    print("🏃 开始训练...")
    train_durian_lora(
        image_dir=args.data_dir,
        instance_prompt=config["instance_prompt"],
        output_dir=args.output,
        variety_name=args.variety,
        num_epochs=config.get("num_epochs", args.epochs),
        learning_rate=config.get("learning_rate", args.lr),
        batch_size=args.batch_size,
        lora_r=args.rank,
    )
    
    print()
    print(f"✅ 训练完成!")
    print(f"📁 模型保存: {os.path.abspath(args.output)}/{args.variety}")


def generate_with_controlnet(args):
    """ControlNet 控制生成模式"""
    print(f"🎮 ControlNet 控制生成模式")
    print(f"   控制类型: {args.control_type}")
    print(f"   参考图像: {args.reference}")
    print()
    
    from controlnet_generator import ControlNetGenerator, DURIAN_CONTROLNET_PROMPTS
    
    # 检查参考图像
    if not os.path.exists(args.reference):
        print(f"❌ 参考图像不存在: {args.reference}")
        return
    
    # 初始化 ControlNet
    print("📦 正在加载 ControlNet...")
    generator = ControlNetGenerator(
        control_type=args.control_type,
        device=args.device,
    )
    
    # 获取提示词
    prompt_key = f"{args.variety}_{args.control_type}"
    if prompt_key in DURIAN_CONTROLNET_PROMPTS:
        prompt = DURIAN_CONTROLNET_PROMPTS[prompt_key]["prompt"]
    else:
        from sd_base import DURIAN_PROMPT_TEMPLATES
        prompt = DURIAN_PROMPT_TEMPLATES.get(args.variety, {}).get("prompt", "")
    
    # 生成图像
    print(f"🎨 正在生成 {args.num} 张图像...")
    images, control = generator.generate(
        prompt=prompt,
        control_image=args.reference,
        num_images=args.num,
        controlnet_conditioning_scale=args.control_scale,
        seed=args.seed,
    )
    
    # 保存结果
    os.makedirs(args.output, exist_ok=True)
    
    # 保存控制图像
    control_path = os.path.join(args.output, f"control_{args.control_type}.png")
    control.save(control_path)
    print(f"💾 控制图像已保存: {control_path}")
    
    # 保存生成的图像
    saved = generator.save_images(images, args.output, prefix=f"{args.variety}_controlled")
    
    print()
    print(f"✅ 生成完成!")
    print(f"📁 输出目录: {os.path.abspath(args.output)}")
    print(f"🖼️  生成图像: {len(saved)} 张")


def batch_generate(args):
    """批量生成模式"""
    print(f"📦 批量生成模式")
    print(f"   品种: {args.varieties}")
    print(f"   每品种数量: {args.num_per_variety}")
    print()
    
    from batch_generate import DurianDatasetGenerator
    
    # 解析品种列表
    varieties = [v.strip() for v in args.varieties.split(",")]
    
    # 创建生成器
    generator = DurianDatasetGenerator(
        output_base_dir=args.output,
        device=args.device,
    )
    
    # 生成数据集
    stats = generator.generate_dataset(
        varieties=varieties,
        images_per_variety=args.num_per_variety,
        use_lora=args.use_lora,
        use_controlnet=args.use_controlnet,
        seed_base=args.seed,
    )
    
    print()
    print(f"✅ 批量生成完成!")
    print(f"📁 输出目录: {os.path.abspath(args.output)}")


def interactive_mode():
    """交互模式"""
    print("🎮 进入交互模式\n")
    
    from sd_base import StableDiffusionBase, DURIAN_PROMPT_TEMPLATES
    
    # 初始化模型
    print("📦 正在加载模型...")
    sd = StableDiffusionBase()
    sd.set_scheduler("euler_a")
    print()
    
    while True:
        print("\n" + "="*50)
        print("请选择操作:")
        print("1. 快速生成")
        print("2. 自定义提示词生成")
        print("3. 查看支持的品种")
        print("0. 退出")
        print("="*50)
        
        choice = input("\n请输入选项: ").strip()
        
        if choice == "0":
            print("👋 再见!")
            break
        
        elif choice == "1":
            print("\n支持的品种:")
            for i, (key, val) in enumerate(DURIAN_PROMPT_TEMPLATES.items(), 1):
                print(f"  {i}. {val['name']} ({key})")
            
            variety = input("\n请输入品种代码: ").strip()
            if variety not in DURIAN_PROMPT_TEMPLATES:
                print("❌ 未知品种")
                continue
            
            try:
                num = int(input("生成数量 (默认 4): ") or "4")
            except:
                num = 4
            
            print(f"\n🎨 正在生成 {DURIAN_PROMPT_TEMPLATES[variety]['name']} 图像...")
            images = sd.generate(
                prompt=DURIAN_PROMPT_TEMPLATES[variety]["prompt"],
                num_images=num,
            )
            
            output_dir = f"output/interactive/{variety}"
            os.makedirs(output_dir, exist_ok=True)
            saved = sd.save_images(images, output_dir, prefix=variety)
            print(f"✅ 已保存到: {output_dir}")
        
        elif choice == "2":
            prompt = input("\n请输入提示词: ").strip()
            if not prompt:
                print("❌ 提示词不能为空")
                continue
            
            try:
                num = int(input("生成数量 (默认 4): ") or "4")
            except:
                num = 4
            
            print(f"\n🎨 正在生成图像...")
            images = sd.generate(prompt=prompt, num_images=num)
            
            output_dir = "output/interactive/custom"
            os.makedirs(output_dir, exist_ok=True)
            saved = sd.save_images(images, output_dir, prefix="custom")
            print(f"✅ 已保存到: {output_dir}")
        
        elif choice == "3":
            print("\n支持的品种:")
            for key, val in DURIAN_PROMPT_TEMPLATES.items():
                print(f"\n  {val['name']} ({key})")
                print(f"    提示词: {val['prompt'][:80]}...")
        
        else:
            print("❌ 无效选项")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="AIGC 榴莲图像数据集生成平台",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 快速生成
  python run.py quick --variety musang_king --num 10
  
  # 训练 LoRA
  python run.py train --variety musang_king --data_dir training_data/musang_king
  
  # ControlNet 生成
  python run.py controlnet --variety musang_king --reference ref.jpg
  
  # 批量生成
  python run.py batch --varieties musang_king,monthong,black_thorn --num_per_variety 50
  
  # 交互模式
  python run.py interactive
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 快速生成
    quick_parser = subparsers.add_parser("quick", help="快速生成模式")
    quick_parser.add_argument("--variety", type=str, default="musang_king",
                             help="品种代码 (默认: musang_king)")
    quick_parser.add_argument("--num", type=int, default=4,
                             help="生成数量 (默认: 4)")
    quick_parser.add_argument("--output", type=str, default="output/quick",
                             help="输出目录 (默认: output/quick)")
    quick_parser.add_argument("--seed", type=int, default=None,
                             help="随机种子")
    quick_parser.add_argument("--width", type=int, default=512,
                             help="图像宽度 (默认: 512)")
    quick_parser.add_argument("--height", type=int, default=512,
                             help="图像高度 (默认: 512)")
    quick_parser.add_argument("--steps", type=int, default=30,
                             help="推理步数 (默认: 30)")
    quick_parser.add_argument("--device", type=str, default="cuda",
                             help="运行设备 (默认: cuda)")
    
    # LoRA 训练
    train_parser = subparsers.add_parser("train", help="训练 LoRA 模型")
    train_parser.add_argument("--variety", type=str, required=True,
                             help="品种代码")
    train_parser.add_argument("--data_dir", type=str, required=True,
                             help="训练数据目录")
    train_parser.add_argument("--output", type=str, default="models/lora",
                             help="输出目录 (默认: models/lora)")
    train_parser.add_argument("--epochs", type=int, default=50,
                             help="训练轮数 (默认: 50)")
    train_parser.add_argument("--lr", type=float, default=1e-4,
                             help="学习率 (默认: 1e-4)")
    train_parser.add_argument("--rank", type=int, default=8,
                             help="LoRA 秩 (默认: 8)")
    train_parser.add_argument("--batch_size", type=int, default=1,
                             help="批次大小 (默认: 1)")
    
    # ControlNet 生成
    control_parser = subparsers.add_parser("controlnet", help="ControlNet 控制生成")
    control_parser.add_argument("--variety", type=str, default="musang_king",
                               help="品种代码 (默认: musang_king)")
    control_parser.add_argument("--reference", type=str, required=True,
                               help="参考图像路径")
    control_parser.add_argument("--control_type", type=str, default="canny",
                               choices=["canny", "hed", "openpose", "depth"],
                               help="控制类型 (默认: canny)")
    control_parser.add_argument("--num", type=int, default=4,
                               help="生成数量 (默认: 4)")
    control_parser.add_argument("--output", type=str, default="output/controlnet",
                               help="输出目录 (默认: output/controlnet)")
    control_parser.add_argument("--control_scale", type=float, default=0.8,
                               help="控制强度 (默认: 0.8)")
    control_parser.add_argument("--seed", type=int, default=None,
                               help="随机种子")
    control_parser.add_argument("--device", type=str, default="cuda",
                               help="运行设备 (默认: cuda)")
    
    # 批量生成
    batch_parser = subparsers.add_parser("batch", help="批量生成数据集")
    batch_parser.add_argument("--varieties", type=str, required=True,
                             help="品种列表，逗号分隔 (如: musang_king,monthong)")
    batch_parser.add_argument("--num_per_variety", type=int, default=100,
                             help="每品种数量 (默认: 100)")
    batch_parser.add_argument("--output", type=str, default="output/dataset",
                             help="输出目录 (默认: output/dataset)")
    batch_parser.add_argument("--use_lora", action="store_true",
                             help="使用 LoRA 模型")
    batch_parser.add_argument("--use_controlnet", action="store_true",
                             help="使用 ControlNet")
    batch_parser.add_argument("--seed", type=int, default=42,
                             help="随机种子 (默认: 42)")
    batch_parser.add_argument("--device", type=str, default="cuda",
                             help="运行设备 (默认: cuda)")
    
    # 交互模式
    subparsers.add_parser("interactive", help="交互模式")
    
    args = parser.parse_args()
    
    # 打印横幅
    print_banner()
    
    # 检查环境
    if not check_environment():
        print("\n❌ 环境检查失败，请安装依赖:")
        print("   pip install -r requirements.txt")
        return 1
    
    # 执行命令
    if args.command == "quick":
        quick_generate(args)
    elif args.command == "train":
        train_lora(args)
    elif args.command == "controlnet":
        generate_with_controlnet(args)
    elif args.command == "batch":
        batch_generate(args)
    elif args.command == "interactive":
        interactive_mode()
    else:
        parser.print_help()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
