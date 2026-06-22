# AIGC 榴莲图像数据集生成平台

基于 **Stable Diffusion + LoRA + ControlNet** 的榴莲品种图像生成系统。

## 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                    榴莲图像生成 Pipeline                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   输入样本    │───▶│  LoRA 微调   │───▶│  ControlNet  │  │
│  │  (10-50张)   │    │  品种特征    │    │  结构控制    │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                   │                   │           │
│         ▼                   ▼                   ▼           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Stable Diffusion 生成引擎                 │  │
│  │         (扩散模型 + 去噪过程 + 文本编码器)              │  │
│  └──────────────────────────────────────────────────────┘  │
│                              │                              │
│                              ▼                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              批量生成高质量榴莲图像                     │  │
│  │         (多样化角度/光线/背景/品种特征)                 │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 环境要求

### 硬件要求
- **GPU**: NVIDIA GPU，显存 >= 8GB (推荐 12GB+)
- **内存**: >= 16GB
- **存储**: >= 50GB 可用空间

### 软件环境
- Python >= 3.8
- CUDA >= 11.7 (如果使用 GPU)
- PyTorch >= 2.0

## 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境
conda create -n durian-aigc python=3.10
conda activate durian-aigc

# 安装 PyTorch (根据你的 CUDA 版本选择)
# CUDA 11.8
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# CUDA 12.1
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 安装其他依赖
pip install -r requirements.txt
```

### 2. 快速生成（无需训练）

使用基础 Stable Diffusion 直接生成：

```bash
# 生成 10 张猫山王榴莲图像
python batch_generate.py --mode quick --variety musang_king --num 10 --output output/quick

# 生成 20 张金枕头榴莲图像
python batch_generate.py --mode quick --variety monthong --num 20 --output output/quick
```

### 3. 完整数据集生成

```bash
# 生成多个品种的完整数据集
python batch_generate.py --mode full
```

## 详细使用指南

### 一、基础生成 (sd_base.py)

```python
from sd_base import StableDiffusionBase, DURIAN_PROMPT_TEMPLATES

# 初始化模型
sd = StableDiffusionBase(
    model_id="runwayml/stable-diffusion-v1-5",
    device="cuda"
)

# 设置采样器
sd.set_scheduler("euler_a")

# 生成图像
images = sd.generate(
    prompt=DURIAN_PROMPT_TEMPLATES["musang_king"]["prompt"],
    width=512,
    height=512,
    num_inference_steps=30,
    guidance_scale=7.5,
    seed=42,
    num_images=4,
)

# 保存图像
sd.save_images(images, output_dir="output/base", prefix="durian")
```

### 二、LoRA 训练 (lora_trainer.py)

#### 1. 准备训练数据

```
training_data/
├── musang_king/
│   ├── img_001.jpg
│   ├── img_002.jpg
│   └── ... (10-50 张图像)
├── monthong/
│   └── ...
└── ...
```

#### 2. 训练 LoRA 模型

```python
from lora_trainer import train_durian_lora

# 训练猫山王 LoRA
train_durian_lora(
    image_dir="training_data/musang_king",
    instance_prompt="a photo of musangking durian, golden yellow flesh",
    output_dir="models/lora",
    variety_name="musang_king",
    num_epochs=100,
    learning_rate=1e-4,
    batch_size=1,
    lora_r=8,
)
```

#### 3. 训练参数说明

| 参数 | 说明 | 推荐值 |
|------|------|--------|
| `num_epochs` | 训练轮数 | 50-100 |
| `learning_rate` | 学习率 | 1e-4 ~ 5e-4 |
| `lora_r` | LoRA 秩 | 4-16 |
| `batch_size` | 批次大小 | 1-4 |

### 三、ControlNet 控制生成 (controlnet_generator.py)

```python
from controlnet_generator import ControlNetGenerator

# 初始化 ControlNet (Canny 边缘控制)
generator = ControlNetGenerator(
    control_type="canny",
    device="cuda"
)

# 使用参考图像生成
images, control = generator.generate(
    prompt="professional photo of Musang King durian...",
    control_image="reference_durian.jpg",
    num_images=4,
    controlnet_conditioning_scale=0.8,
)

# 保存结果
generator.save_images(images, "output/controlnet", prefix="controlled")
```

### 四、批量生成 (batch_generate.py)

```python
from batch_generate import DurianDatasetGenerator

# 创建生成器
generator = DurianDatasetGenerator(
    output_base_dir="output/my_dataset"
)

# 生成单个品种
generator.generate_single_variety(
    variety="musang_king",
    num_images=100,
    use_lora=True,  # 使用 LoRA
    use_controlnet=False,
)

# 生成完整数据集
generator.generate_dataset(
    varieties=["musang_king", "monthong", "black_thorn"],
    images_per_variety=100,
    use_lora=True,
    use_controlnet=False,
)
```

## 支持的榴莲品种

| 品种代码 | 中文名 | 英文名 | 特征 |
|----------|--------|--------|------|
| `musang_king` | 猫山王 | Musang King (D197) | 金黄色果肉，甜中带苦 |
| `monthong` | 金枕头 | Monthong (D159) | 淡黄色果肉，甜度高 |
| `black_thorn` | 黑刺 | Black Thorn (D200) | 深橙色果肉，口感细腻 |
| `sultan` | 苏丹王 | Sultan (D24) | 淡黄色果肉，性价比高 |
| `red_prawn` | 红虾 | Red Prawn (D175) | 橙红色果肉，甜度极高 |

## 文件结构

```
durian-aigc/
├── sd_base.py                 # 基础 SD 生成
├── lora_trainer.py            # LoRA 训练
├── controlnet_generator.py    # ControlNet 控制生成
├── batch_generate.py          # 批量生成
├── requirements.txt           # 依赖列表
├── configs/
│   └── generation_config.yaml # 配置文件
├── models/                    # 模型目录
│   └── lora/                  # LoRA 模型
├── training_data/             # 训练数据
├── output/                    # 输出目录
└── README.md                  # 说明文档
```

## 高级配置

### 修改生成参数

编辑 `configs/generation_config.yaml`：

```yaml
generation:
  width: 512          # 图像宽度
  height: 512         # 图像高度
  num_inference_steps: 30  # 推理步数
  guidance_scale: 7.5      # 引导比例
```

### 自定义提示词

```python
# 在代码中自定义
from sd_base import StableDiffusionBase

sd = StableDiffusionBase()

my_prompt = """
professional product photography of [品种] durian,
[颜色] flesh, [质地] texture,
[背景描述],
[光线描述],
8k ultra HD, highly detailed
"""

images = sd.generate(prompt=my_prompt, num_images=4)
```

## 性能优化

### 1. 内存优化

```python
# 启用 attention slicing
sd.pipe.enable_attention_slicing()

# 启用 xformers (如果已安装)
sd.pipe.enable_xformers_memory_efficient_attention()

# 使用半精度
sd = StableDiffusionBase(dtype=torch.float16)
```

### 2. 批量生成优化

```python
# 增大批次大小
generator.generate_single_variety(
    variety="musang_king",
    num_images=100,
    batch_size=4,  # 一次生成 4 张
)
```

## 常见问题

### Q: CUDA 内存不足

**A**: 
- 减小 `batch_size` 到 1
- 使用 `enable_attention_slicing()`
- 减小图像尺寸到 384x384
- 使用 CPU 运行 (较慢)

### Q: 生成的图像质量不佳

**A**:
- 增加 `num_inference_steps` 到 50
- 调整 `guidance_scale` (7-12)
- 使用训练好的 LoRA 模型
- 提供更详细的提示词

### Q: LoRA 训练失败

**A**:
- 确保训练图像 >= 10 张
- 降低 `learning_rate` 到 5e-5
- 减少 `num_epochs` 到 50
- 检查图像格式是否正确

## 模型下载

首次运行时会自动从 Hugging Face 下载：

- `runwayml/stable-diffusion-v1-5` (~4GB)
- `lllyasviel/sd-controlnet-canny` (~1.2GB)
- `lllyasviel/sd-controlnet-hed` (~1.2GB)

如需手动下载：

```bash
# 使用 huggingface-cli
huggingface-cli download runwayml/stable-diffusion-v1-5

# 或使用 git
git lfs install
git clone https://huggingface.co/runwayml/stable-diffusion-v1-5
```

## 许可证

本项目基于 Apache 2.0 许可证开源。

使用的模型遵循各自的原许可证：
- Stable Diffusion: CreativeML Open RAIL-M
- ControlNet: Apache 2.0

## 引用

```bibtex
@misc{durian-aigc,
  title={AIGC Durian Image Dataset Generation},
  author={Your Name},
  year={2024},
  howpublished={\url{https://github.com/yourname/durian-aigc}}
}
```
