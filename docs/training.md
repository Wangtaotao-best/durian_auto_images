# 训练指南

> **环境提示**: 本指南命令请在 `sd_lora` conda 环境中执行。

## 1. 前置

- 已完成 M1 环境安装 (`scripts/setup_train_env.ps1`)
- 已为目标品种准备好训练数据 (`D:/durian-data/training/<variety>/`)
- 已安装 RTX 5070 (12GB) 显卡

## 2. 基本训练

```powershell
conda activate sd_lora
python -m backend.lora_trainer --variety musang_king
```

默认参数 (在 `backend/configs/paths.yaml` 中):
- 基础模型: SD 1.5
- LoRA rank: 16, alpha: 32
- 学习率: 1e-4
- epochs: 50
- 分辨率: 512×512
- 混合精度: fp16

## 3. 自定义参数

```powershell
python -m backend.lora_trainer `
    --variety musang_king `
    --epochs 80 `
    --rank 32 `
    --learning_rate 5e-5
```

## 4. 性能预估 (RTX 5070 12GB)

| 数据量 | epoch | 耗时 | 显存 |
|---|---|---|---|
| 30 张 | 50 | ~15 min | ~9 GB |
| 50 张 | 50 | ~25 min | ~9 GB |
| 80 张 | 50 | ~40 min | ~9 GB |

## 5. 训练产物

- `D:/durian-data/models/lora/<variety>/pytorch_lora_weights.safetensors` (~30 MB)
- 中间 checkpoint(若开启)

## 6. 本地验证

```powershell
python -m backend.local_inference `
    --variety musang_king `
    --prompt "on a wooden table, soft natural light" `
    --num 4
```

输出在 `D:/durian-data/outputs/<variety>/`。

## 7. 常见问题

**Q: CUDA out of memory**
A: 降低 `--rank` 到 8, 或降低 `--resolution` 到 384。

**Q: 模型下载慢**
A: 设置环境变量 `set HF_ENDPOINT=https://hf-mirror.com`。

**Q: 训出来效果差**
A: 检查训练数据质量 + caption 是否准确(打开 captions.csv 人工抽查)。

**Q: PEFT LoRA 与 diffusers load_lora_weights 不兼容**
A: 本项目的 LoRA 是 PEFT 原生格式 (adapter_config.json + adapter_model.safetensors)。
   diffusers 的 `pipe.load_lora_weights()` 期望 diffusers 原生格式,加载 PEFT 格式会报
   "Target modules not found"。
   解决方案: 使用 `PeftModel.from_pretrained(pipe.unet, lora_dir)` 加载。
   见 `backend/local_inference.py` 中的实现。
