# 🌰 榴莲 AIGC 系统

基于 **Stable Diffusion 1.5 + LoRA + LCM-LoRA** 的榴莲品种图像生成系统。
**本地 GPU(RTX 5070)训练 → CPU 服务器 Docker 部署 → 浏览器在线生成**。

## ✨ 特性

- 🎨 LoRA 微调榴莲品种特征(已交付:猫山王;可扩展到金枕头、黑刺王、红虾)
- ⚡ CPU 推理 8-15 秒/张(OpenVINO + LCM-LoRA 6 步)
- 🐳 Docker 一键部署到无 GPU 服务器
- 📱 React + Tailwind 现代深色 UI,带在线生成器(嵌入项目展示页)
- 🔧 完整数据流水线(爬虫 + 自动筛选 + BLIP 自动打标)
- 📊 本地推理 ~3-4 秒/张(RTX 5070)

## 🚀 快速开始

### 一、本地训练(可选 — 已带训好的 musang_king LoRA)

```powershell
# 1. 装/补环境(复用现有 sd_lora conda 环境)
powershell scripts/setup_env.ps1

# 2. 准备数据(详见 docs/data-collection.md)
powershell scripts/prepare_dataset.ps1 -Variety musang_king -CrawlNum 50

# 3. 训练 LoRA(RTX 5070,约 25 分钟)
conda activate sd_lora
python -m backend.lora_trainer --variety musang_king

# 4. 本地推理验证
python -m backend.local_inference --variety musang_king --prompt "on a wooden table"
# 输出: D:/durian-data/outputs/musang_king/*.png
```

### 二、打包服务器模型(本地完成)

```powershell
# 一键: LoRA → 合并主模型 → 合并 LCM-LoRA → 导出 OpenVINO → 打 tar.gz
powershell scripts/build_serve_bundle.ps1 -Variety musang_king
# 输出: D:/durian-data/musang_king_openvino.tar.gz (~1.3 GB)
```

### 三、服务器部署(Docker)

```bash
# 上传模型 + 代码到服务器
scp D:/durian-data/musang_king_openvino.tar.gz user@server:/tmp/
scp -r docker-compose.yml backend frontend scripts .env.example user@server:/data/durian/

# SSH 到服务器,一键部署
ssh user@server
cd /data/durian
MODELS_BUNDLE=/tmp/musang_king_openvino.tar.gz bash scripts/deploy_to_server.sh

# 等 ~2 分钟模型加载后访问 http://<server-ip>:8000
```

### 四、本地开发(前端 + 后端联调)

```powershell
# 终端 1: 启动后端
conda activate sd_lora
$env:DURIAN_OV_MODELS_ROOT = "D:/durian-data/models/openvino"
python -m uvicorn backend.serve.app:app --host 127.0.0.1 --port 8000

# 终端 2: 启动前端(自动 proxy /api 到 8000)
cd frontend
npm run dev
# 浏览器打开 http://localhost:5173
```

## 📚 文档

- [设计文档](docs/superpowers/specs/2026-06-22-durian-aigc-design.md)
- [实施计划 Part 1](docs/superpowers/plans/2026-06-22-durian-aigc-implementation.md) · [Part 2](docs/superpowers/plans/2026-06-22-durian-aigc-implementation-part2.md)
- [执行偏差](docs/superpowers/plans/execution-context.md)(实际执行时与计划的偏差表)
- [数据收集指南](docs/data-collection.md)
- [训练指南](docs/training.md)
- [部署指南](docs/deployment.md)
- [训练记录](docs/training-log.md)

## 🏗 项目结构

```
.
├── backend/                       Python 后端
│   ├── data_tools/                数据爬虫/筛选/合并/BLIP 打标
│   │   ├── scraper.py             Bing 图像爬虫
│   │   ├── filter.py              分辨率/长宽比/pHash 过滤
│   │   ├── merge_dataset.py       合并爬虫+个人数据集
│   │   └── blip_caption.py        BLIP 自动打标
│   ├── tools/                     模型转换
│   │   ├── merge_lora.py          PEFT/Diffusers LoRA 合并
│   │   └── export_openvino.py     OpenVINO IR 导出
│   ├── serve/                     FastAPI Web 服务
│   │   ├── app.py                 主应用 (REST API)
│   │   ├── pipeline.py            OpenVINO + LCM Pipeline 封装
│   │   ├── queue.py               异步任务队列
│   │   ├── schemas.py             Pydantic 模型
│   │   └── image_store.py         生成图持久化
│   ├── configs/
│   │   ├── paths.yaml             统一路径 + 品种 + 训练默认
│   │   └── loader.py
│   ├── tests/                     21 个单元测试
│   ├── lora_trainer.py            LoRA 训练
│   ├── local_inference.py         本地快速推理(PEFT-compatible)
│   ├── Dockerfile                 多阶段 CPU 镜像
│   ├── requirements-train.txt     训练依赖(GPU)
│   └── requirements-serve.txt     服务依赖(CPU)
├── frontend/                      React 19 + Vite 7 + Tailwind + shadcn
│   ├── src/sections/
│   │   ├── Hero.tsx               展示页 (深色 + 粒子动效)
│   │   ├── Generator.tsx          ⭐ 在线生成器 (嵌入)
│   │   ├── TechStack.tsx
│   │   ├── Workflow.tsx
│   │   ├── DurianGallery.tsx
│   │   ├── DatasetStats.tsx
│   │   └── Footer.tsx
│   ├── src/api/                   API client + types
│   └── src/hooks/useGeneration.ts 异步生成 + 轮询
├── scripts/                       PowerShell + bash 一键脚本
│   ├── setup_env.ps1
│   ├── prepare_dataset.ps1
│   ├── build_serve_bundle.ps1
│   └── deploy_to_server.sh
├── docs/                          全套文档
├── docker-compose.yml             容器编排 (单 worker, 24G mem limit)
├── .dockerignore
└── archive/                       旧代码归档

# 数据 & 模型存放(项目外,不入 git):
D:/durian-data/                    本地
├── raw/<variety>/                 爬虫原始
├── candidates/<variety>/          自动过滤后
├── personal/<variety>/            用户自有(手动放)
├── training/<variety>/            训练数据 + .txt caption
├── outputs/<variety>/             本地推理结果
└── models/
    ├── lora/<variety>/            训练产物(adapter_model.safetensors)
    ├── merged/<variety>/          合并 LCM 后的 SD pipeline
    └── openvino/<variety>/        OpenVINO IR (服务器用)

# 服务器:
/data/durian/models/openvino/<variety>/    部署的 OpenVINO 模型
```

## 🛠 技术栈

| 层 | 技术 |
|---|---|
| 训练 | PyTorch 2.12 nightly (cu128) + diffusers + peft |
| 推理 | OpenVINO 2024.4 + LCM-LoRA (6 步) |
| 后端 | FastAPI + uvicorn + asyncio queue(单 worker)|
| 前端 | React 19 + Vite 7 + Tailwind 3.4 + shadcn/Radix |
| 部署 | Docker + docker compose v2 |

## 📊 性能

| 场景 | 速度 |
|---|---|
| LoRA 训练 (RTX 5070, 50 张图, 50 epoch) | ~25 分钟 |
| 本地推理 (RTX 5070, fp16, Euler-A 30 步) | **~3-4 秒/张** ✅ |
| OpenVINO 模型打包 (本地一次性) | ~6 分钟 |
| 服务器推理 (Xeon 16T, LCM 6 步) | 8-15 秒/张(目标)|
| 服务器并发 | 单 worker 串行,队列上限 20 |

## ⚠️ 已知限制

- 单 CPU worker 串行处理,适合小范围(几人同时演示)
- 仅学术/作业用途,不商业化
- SD1.5 不支持中文 prompt,前端自动加品种英文触发词
- 项目根目录含中文,某些工具偶尔报 PATH 问题(数据/模型已外置到 `D:/durian-data/` 规避)

## 🔬 关键工程决策

1. **PEFT LoRA 加载方案**: 现有 LoRA 是 PEFT 原生格式,`pipe.load_lora_weights()` 不兼容。改用 `PeftModel.from_pretrained(pipe.unet, lora_dir).merge_and_unload()`。
2. **`merge_lora.py` 双格式支持**: 自动检测 `adapter_config.json` 决定走 PEFT 还是 Diffusers 路径,兼容品种 LoRA 与 LCM-LoRA。
3. **数据/模型外置**: 全部放 `D:/durian-data/`(英文路径)避免中文路径库兼容性问题。
4. **异步任务队列**: 单 worker + asyncio.Queue,匹配 CPU 推理无法并发的物理约束,前端轮询展示真实进度。
5. **沿用现有 React 展示页**: 不替换,在 Hero 与 TechStack 之间插入 `Generator` section 作为"立即试用"区,视觉与现有深色主题协调。

## 📜 协议

代码 MIT。模型权重遵循 [Stable Diffusion License](https://huggingface.co/runwayml/stable-diffusion-v1-5)。
数据集仅用于学术演示,不商业化、不二次分发。
