# 快速开始指南

## 1. 环境准备

```bash
# 创建虚拟环境
conda create -n durian-aigc python=3.10
conda activate durian-aigc

# 安装依赖
pip install -r requirements.txt
```

## 2. 快速生成图像

### 方式一：命令行

```bash
# 生成 10 张猫山王榴莲图像
python run.py quick --variety musang_king --num 10

# 生成 5 张金枕头榴莲图像
python run.py quick --variety monthong --num 5 --output output/monthong
```

### 方式二：Web UI

```bash
# 启动图形界面
python webui.py

# 然后在浏览器打开 http://localhost:7860
```

### 方式三：Python API

```python
from sd_base import StableDiffusionBase, DURIAN_PROMPT_TEMPLATES

# 初始化模型
sd = StableDiffusionBase()

# 生成图像
images = sd.generate(
    prompt=DURIAN_PROMPT_TEMPLATES["musang_king"]["prompt"],
    num_images=4,
)

# 保存
sd.save_images(images, "output", prefix="durian")
```

## 3. 训练 LoRA 模型

### 准备训练数据

```
training_data/
└── musang_king/
    ├── img_001.jpg
    ├── img_002.jpg
    └── ... (10-50 张图像)
```

### 开始训练

```bash
python run.py train \
    --variety musang_king \
    --data_dir training_data/musang_king \
    --epochs 50
```

## 4. ControlNet 控制生成

```bash
python run.py controlnet \
    --variety musang_king \
    --reference reference_image.jpg \
    --control_type canny \
    --num 4
```

## 5. 批量生成数据集

```bash
python run.py batch \
    --varieties musang_king,monthong,black_thorn \
    --num_per_variety 100 \
    --output output/dataset
```

## 支持的品种

| 代码 | 名称 | 说明 |
|------|------|------|
| musang_king | 猫山王 | 金黄色果肉，甜中带苦 |
| monthong | 金枕头 | 淡黄色果肉，甜度高 |
| black_thorn | 黑刺 | 深橙色果肉，口感细腻 |
| sultan | 苏丹王 | 淡黄色果肉，性价比高 |
| red_prawn | 红虾 | 橙红色果肉，甜度极高 |

## 命令速查

```bash
# 查看帮助
python run.py --help

# 查看各命令帮助
python run.py quick --help
python run.py train --help
python run.py controlnet --help
python run.py batch --help

# 交互模式
python run.py interactive
```

## 常见问题

**Q: CUDA 内存不足？**
```bash
# 减小批次大小，使用 CPU
python run.py quick --variety musang_king --num 1 --device cpu
```

**Q: 首次运行很慢？**
- 首次会自动下载模型 (~4GB)，请耐心等待

**Q: 生成图像质量不佳？**
- 增加推理步数：`--steps 50`
- 使用训练好的 LoRA 模型
