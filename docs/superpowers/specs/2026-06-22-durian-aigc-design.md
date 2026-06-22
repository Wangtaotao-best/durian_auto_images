# 榴莲 AIGC 系统 — 完整设计文档

**日期:** 2026-06-22
**作者:** brainstorming session
**状态:** 待审阅

---

## 1. 项目目标

构建一个完整的"榴莲品种图像生成"系统,包含两个使用场景:

1. **本地训练 + 本地批量推理**:在本地工作站上微调 LoRA 模型,产出某品种榴莲的高质量图像数据集
2. **Web 服务部署**:将训练好的模型部署到无 GPU 的 CPU 服务器,提供"在浏览器输入提示词 → 生成榴莲图"的小范围演示服务(几人同时使用)

### 1.1 非目标(YAGNI)

- 不做用户系统 / 登录
- 不做商业级高并发(QPS > 1)
- 不做生成结果的持久化数据库(用文件系统即可)
- 不做模型版本管理 UI(命令行替换权重即可)
- 不做 SDXL / Flux 等更大模型(SD1.5 + LoRA 完全够本场景)

---

## 2. 硬件与角色

| 角色 | 配置 | 任务 |
|---|---|---|
| **本地机器** | RTX 5070 12GB / Win11 / PowerShell | LoRA 训练、本地快速推理、模型打包 |
| **部署服务器** | Xeon Silver 4309Y(8 核 16 线程,2.8-3.6 GHz)/ 30 GB RAM / 15 GB Swap / Linux / 无 GPU | Web 服务运行,CPU 推理 |

---

## 3. 整体架构

```
┌──────────────────────────────────────────────────────────────────┐
│  阶段 ①  本地机器 (RTX 5070 12GB)                                 │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│   ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐     │
│   │ 数据采集     │───▶│ BLIP 自动打标 │───▶│ 训练数据集       │     │
│   │ 爬虫+人工筛  │    │ + 人工补品种  │    │ images + .txt    │     │
│   └─────────────┘    └──────────────┘    └─────────────────┘     │
│          │                                       │                 │
│          ▼                                       ▼                 │
│   ┌─────────────────────────────────────────────────────┐         │
│   │           LoRA 训练 (PyTorch + CUDA 12.8)            │         │
│   │      Base: SD 1.5  +  LoRA rank=16, 50 epochs        │         │
│   └─────────────────────────────────────────────────────┘         │
│                              │                                     │
│         ┌────────────────────┴─────────────────────┐               │
│         ▼                                          ▼               │
│   ┌──────────────────┐                  ┌─────────────────────┐   │
│   │ 本地快速推理      │                  │ 模型打包(部署用)     │   │
│   │ local_inference  │                  │ Merge LoRA → 主模型 │   │
│   │ ~3 秒/张         │                  │ → 转 OpenVINO IR     │   │
│   └──────────────────┘                  │ → tar 打包          │   │
│                                          └─────────────────────┘   │
│                                                    │               │
└────────────────────────────────────────────────────┼───────────────┘
                                                     │ scp / U盘上传
                                                     ▼
┌──────────────────────────────────────────────────────────────────┐
│  阶段 ②  服务器 (Xeon 8C16T, 30GB RAM, 无 GPU)                    │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│   ┌──────────────────┐         ┌──────────────────────────────┐   │
│   │ React SPA        │  HTTP   │ FastAPI 后端                  │   │
│   │ (Vite 构建静态)  │◀───────▶│ + asyncio 任务队列            │   │
│   │ shadcn/Tailwind  │ 轮询    │ + OpenVINO + LCM-LoRA Pipeline│   │
│   └──────────────────┘         └──────────────────────────────┘   │
│                                                                    │
│   通信:                                                            │
│     POST /api/generate     → 立即返回 task_id                      │
│     GET  /api/tasks/{id}   → 排队中/进行中/完成/失败                │
│     GET  /api/tasks/{id}/image → 完成后下载图片                    │
│                                                                    │
│   性能目标: 单张 8-15 秒, 同时 1 张图,队列排队                      │
└──────────────────────────────────────────────────────────────────┘
```

---

## 4. 代码仓库整理

### 4.1 现状(混乱)

```
Kimi_Agent_榴莲图像生成代码/
├── durian-aigc/          ← 旧的代码副本(删)
├── durian-aigc-code/     ← 较新的代码副本(保留并改名)
├── durian-aigc.tar.gz    ← 代码压缩包(删)
├── app/                  ← React 前端(保留并改造)
├── models/lora/          ← 与 durian-aigc-code/models 重复(合并)
├── test.py               ← 散落测试脚本(整理)
├── generated_durian_*.png ← 旧产物(归档到 archive/)
└── ziUpcpXC              ← 杂项(检查后删)
```

### 4.2 目标结构

```
durian-aigc/
├── README.md                       ← 项目总入口
├── docs/
│   ├── superpowers/specs/          ← 设计文档
│   ├── data-collection.md          ← 数据收集指南
│   ├── training.md                 ← 训练指南
│   └── deployment.md               ← 部署指南
├── backend/                        ← 原 durian-aigc-code 改名
│   ├── requirements-train.txt      ← 训练环境(本地 GPU)
│   ├── requirements-serve.txt      ← 服务环境(CPU + OpenVINO)
│   ├── sd_base.py
│   ├── lora_trainer.py
│   ├── controlnet_generator.py
│   ├── batch_generate.py
│   ├── local_inference.py          ← 【新】本地快速推理脚本
│   ├── data_tools/                 ← 【新】数据准备工具
│   │   ├── scraper.py              ← 爬虫
│   │   ├── filter.py               ← 自动筛选(分辨率/水印)
│   │   ├── blip_caption.py         ← BLIP 自动打标
│   │   └── merge_dataset.py        ← 合并爬取+个人数据集
│   ├── serve/                      ← 【新】Web 服务
│   │   ├── app.py                  ← FastAPI 入口
│   │   ├── pipeline.py             ← OpenVINO + LCM 推理封装
│   │   ├── queue.py                ← 任务队列
│   │   └── schemas.py              ← Pydantic 模型
│   ├── tools/                      ← 【新】模型打包工具
│   │   ├── merge_lora.py           ← LoRA 合并到主模型
│   │   └── export_openvino.py      ← 导出 OpenVINO IR
│   └── configs/
├── frontend/                       ← 原 app/ 改名
│   ├── package.json
│   ├── src/
│   │   ├── sections/
│   │   │   ├── Hero.tsx            ← 主生成页
│   │   │   ├── Gallery.tsx         ← 历史画廊
│   │   │   └── About.tsx
│   │   ├── api/                    ← 【新】API 客户端
│   │   │   └── client.ts
│   │   └── components/ui/          ← shadcn 组件
│   └── ...
├── training_data/                  ← 训练数据(gitignore)
├── outputs/                        ← 训练/生成产物(gitignore)
└── archive/                        ← 旧文件归档
```

---

## 5. 数据集准备流程

### 5.1 品种范围

初版覆盖 4 个主流品种(可扩展):

| 品种 | 触发词(LoRA token) | 中文 | 特征 |
|---|---|---|---|
| Musang King | `musangking durian` | 猫山王 | 果肉金黄、果壳深绿尖刺 |
| Monthong | `monthong durian` | 金枕头 | 果肉浅黄、果柄长 |
| Black Thorn | `blackthorn durian` | 黑刺王 | 果肉橙黄、果壳带黑刺 |
| Red Prawn | `redprawn durian` | 红虾 | 果肉橙红、味甜 |

### 5.2 数据采集

**目标:每品种 30-80 张高质量图,合计 150-300 张**

#### 5.2.1 图源清单

| 来源 | 用途 | 备注 |
|---|---|---|
| Unsplash / Pexels / Pixabay | 主要图源 | CC0 免费商用 |
| Wikimedia Commons | 学术用 | CC-BY,需署名 |
| 必应/谷歌图片(过滤"可重复使用") | 补充 | 仅学术演示 |
| **用户自有数据集** | **必加** | 用户已声明拥有部分自采图 |

#### 5.2.2 关键词模板

`<品种英文> durian` / `<品种中文> 榴莲` / `<品种> 切开` / `<品种> 果肉` / `<品种> 整果`

#### 5.2.3 筛选标准(`data_tools/filter.py` 自动过滤)

- 分辨率 ≥ 512×512
- 长宽比 0.5 - 2.0(过滤奇怪比例)
- 单文件 < 10MB
- pHash 去重(相似图剔除)
- 自动检测水印(简单边角检测)
- **人工最终筛选**:把过滤后的图放到 `candidates/<品种>/`,人工删除明显不对的

#### 5.2.4 爬虫脚本设计(`data_tools/scraper.py`)

```python
# 伪代码
from icrawler.builtin import BingImageCrawler, GoogleImageCrawler

def scrape(variety_en, variety_cn, n=200, out_dir):
    for keyword in [f"{variety_en} durian", f"{variety_cn}榴莲", ...]:
        crawler = BingImageCrawler(storage={"root_dir": out_dir})
        crawler.crawl(keyword=keyword, max_num=n // 4,
                      min_size=(512, 512), filters={"license": "commercial"})
```

依赖:`icrawler`(MIT 协议,成熟稳定)。

#### 5.2.5 个人数据集合并(`data_tools/merge_dataset.py`)

用户的自有数据放到 `personal_data/<品种>/`,脚本统一:
- 重命名(`<品种>_user_001.jpg`)
- resize 到 512 短边
- 与爬虫数据 pHash 去重
- 输出到 `training_data/<品种>/`

### 5.3 数据标注(BLIP 自动 + 人工补)

#### 5.3.1 BLIP 自动打标(`data_tools/blip_caption.py`)

模型:`Salesforce/blip-image-captioning-large`(990MB,本地跑)

流程:
1. 遍历 `training_data/<品种>/*.jpg`
2. 每张图喂 BLIP,得到英文描述,例如:`"a close up of a durian fruit on a wooden table"`
3. **自动拼接品种触发词**:最终 caption =
   `"<触发词>, <BLIP 输出>, high quality, detailed"`
   例:`"musangking durian, a close up of a durian fruit on a wooden table, high quality, detailed"`
4. 写到同名 `.txt`:`img_001.jpg` ↔ `img_001.txt`

#### 5.3.2 人工补正(可选,提升 5-10%)

打开 `training_data/<品种>/captions.csv`(脚本会生成),人工浏览检查:
- 错误描述(BLIP 偶尔会把榴莲识别成菠萝)
- 补充品种特征词(果肉颜色、刺的形状)

预计每品种 1-2 小时手工时间,如赶时间可跳过。

### 5.4 最终数据集结构

```
training_data/
├── musang_king/
│   ├── img_001.jpg
│   ├── img_001.txt           ← caption
│   ├── img_002.jpg
│   ├── img_002.txt
│   └── ...                   ← 30-80 张
├── monthong/
├── blackthorn/
└── red_prawn/
```

---

## 6. 本地训练

### 6.1 关键问题:RTX 5070 兼容性

RTX 5070 是 Blackwell 架构(SM 12.0),**老版本 PyTorch/CUDA 跑不起来**。
项目原 `requirements.txt` 中的 `torch>=2.0.0` 在 5070 上会报 `CUDA error: no kernel image available for execution on the device`。

#### 6.1.1 新的 `requirements-train.txt`

```
# === 必须装 PyTorch nightly 或 ≥ 2.6,匹配 CUDA 12.8 ===
# 安装命令(单独执行):
#   pip install --pre torch torchvision torchaudio \
#     --index-url https://download.pytorch.org/whl/nightly/cu128

# Stable Diffusion 生态
diffusers>=0.30.0
transformers>=4.44.0
accelerate>=0.33.0
peft>=0.12.0

# 注意:bitsandbytes 在 Windows + 5070 上不稳定,改用 fp16 训练,不用 int8
# bitsandbytes>=0.43.0    ← 暂不启用

# 数据处理
Pillow>=10.0.0
opencv-python>=4.10.0
imagehash>=4.3.1          # pHash 去重
numpy>=1.26.0
tqdm>=4.66.0
safetensors>=0.4.0

# 数据采集
icrawler>=0.6.7

# 工具
omegaconf>=2.3.0
tensorboard>=2.17.0
```

#### 6.1.2 安装步骤(本地)

```powershell
conda create -n durian python=3.11
conda activate durian

# 1. 装 PyTorch nightly (CUDA 12.8)
pip install --pre torch torchvision torchaudio `
    --index-url https://download.pytorch.org/whl/nightly/cu128

# 2. 装其余依赖
pip install -r backend/requirements-train.txt

# 3. 验证 5070 能识别
python -c "import torch; print(torch.cuda.get_device_name(0), torch.cuda.is_available())"
# 期望输出: NVIDIA GeForce RTX 5070  True
```

### 6.2 LoRA 训练配置

| 参数 | 值 | 说明 |
|---|---|---|
| 基础模型 | `runwayml/stable-diffusion-v1-5` | 项目已用 |
| LoRA rank | 16 | 平衡质量/大小 |
| LoRA alpha | 32 | rank × 2 经验值 |
| 学习率 | 1e-4 | LoRA 标准 |
| Batch size | 1(梯度累积 4)| 12GB 显存够用 |
| 训练步数 | 1500-3000 步 | 50 张图 × 50 epoch 约 2500 步 |
| 分辨率 | 512×512 | SD1.5 原生 |
| 混合精度 | fp16 | 5070 加速 |
| Optimizer | AdamW 8bit → 改 AdamW(因 bitsandbytes 暂不启用)| |

### 6.3 训练命令

```powershell
# 单品种训练
python backend/lora_trainer.py `
    --variety musang_king `
    --data_dir training_data/musang_king `
    --output_dir backend/models/lora/musang_king `
    --epochs 50 `
    --rank 16 `
    --learning_rate 1e-4 `
    --resolution 512 `
    --mixed_precision fp16

# 批量训练所有品种(写个 .ps1 脚本循环)
```

### 6.4 训练性能预估(RTX 5070 12GB)

| 数据规模 | epoch | 总步数 | 预计时间 | 显存占用 |
|---|---|---|---|---|
| 30 张 | 50 | 1500 | **~15 分钟** | ~9 GB |
| 50 张 | 50 | 2500 | **~25 分钟** | ~9 GB |
| 80 张 | 50 | 4000 | **~40 分钟** | ~9 GB |

训练产物:`backend/models/lora/<品种>/pytorch_lora_weights.safetensors`,约 25-40 MB。

### 6.5 训练监控

- TensorBoard:`tensorboard --logdir backend/models/lora/<品种>/logs`
- 每 500 步保存 checkpoint + 生成 4 张验证图
- Loss 曲线应平稳下降,不应大幅震荡;若震荡降学习率到 5e-5

---

## 7. 本地快速推理脚本(`local_inference.py`)

### 7.1 设计目标

让你在本地能用一条命令快速试模型,**不启动 Gradio、不启动 Web,3 秒出一张图**。

### 7.2 命令行接口

```powershell
# 基础生成
python backend/local_inference.py `
    --variety musang_king `
    --prompt "on a wooden table, soft natural light" `
    --num 4 `
    --output outputs/test/

# 高级参数
python backend/local_inference.py `
    --variety musang_king `
    --prompt "cut open, exposed yellow flesh, studio lighting" `
    --negative "blurry, low quality, distorted" `
    --steps 30 `
    --cfg 7.5 `
    --seed 42 `
    --width 512 --height 512 `
    --num 1
```

### 7.3 内部实现

- 复用 `sd_base.py:StableDiffusionBase`
- 自动注入对应品种的触发词:`prompt = f"{TRIGGER[variety]}, {user_prompt}"`
- 自动加载该品种的 LoRA 权重
- 用 Euler-A 30 步,fp16
- 输出文件名:`<variety>_<timestamp>_<seed>_<idx>.png`

预估:**3 秒/张**(5070 + fp16 + 30 步)。

---

## 8. 服务器部署

### 8.1 推理引擎选择:OpenVINO + LCM-LoRA

**为什么选这套组合?**

| 选项 | 单张耗时(Xeon 16线程, 512×512) | 备注 |
|---|---|---|
| 原生 PyTorch CPU(30 步) | 2-5 分钟 | 不可用 |
| ONNX Runtime CPU | 60-90 秒 | 中等 |
| **OpenVINO INT8 + LCM(6 步)** | **8-15 秒** ⭐ | 推荐 |
| OpenVINO FP16 + 标准 25 步 | 30-50 秒 | 备选 |

**OpenVINO** 是 Intel 出的 CPU 推理优化框架,对 Xeon 有 AVX-512 指令集深度优化。
**LCM(Latent Consistency Model)LoRA** 把扩散步数从 25-50 步降到 4-8 步,且**与你训的品种 LoRA 兼容叠加**。

### 8.2 模型导出流程(在本地完成)

```powershell
# Step 1: 把品种 LoRA 合并进基础 SD1.5 主模型
python backend/tools/merge_lora.py `
    --base runwayml/stable-diffusion-v1-5 `
    --lora backend/models/lora/musang_king/pytorch_lora_weights.safetensors `
    --output backend/models/merged/musang_king/ `
    --alpha 0.8

# Step 2: 加载 LCM-LoRA 并再合并
python backend/tools/merge_lora.py `
    --base backend/models/merged/musang_king/ `
    --lora latent-consistency/lcm-lora-sdv1-5 `
    --output backend/models/merged/musang_king_lcm/ `
    --alpha 1.0

# Step 3: 导出 OpenVINO IR 格式
python backend/tools/export_openvino.py `
    --model_dir backend/models/merged/musang_king_lcm/ `
    --output backend/models/openvino/musang_king/ `
    --dtype fp16

# Step 4: 打包
tar -czvf musang_king_openvino.tar.gz backend/models/openvino/musang_king/
# 文件大小约 1.8-2.2 GB
```

> 多品种时,可以**只导出一份基础 SD1.5 + LCM 的 OpenVINO 模型**,然后**运行时动态加载不同品种的 LoRA 权重**(OpenVINO 支持运行时 LoRA 叠加,但相对复杂)。
> 初版**简化方案:每个品种导出一份完整模型**(共 4 × 2GB = 8GB,30GB 内存足够,磁盘空间够即可)。

### 8.3 上传步骤(本地 → 服务器)

```bash
# 在本地
scp musang_king_openvino.tar.gz user@server:/data/durian/models/

# 在服务器
cd /data/durian/models/
tar -xzvf musang_king_openvino.tar.gz
```

### 8.4 服务器环境

#### 8.4.1 `requirements-serve.txt`

```
# Web 框架
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
pydantic>=2.8.0
python-multipart>=0.0.9

# 推理引擎(纯 CPU)
openvino>=2024.4
optimum-intel[openvino]>=1.20.0
diffusers>=0.30.0      # 调度器/Pipeline 包装
transformers>=4.44.0
torch>=2.3.0+cpu       # CPU only 版本

# 图像
Pillow>=10.0.0
numpy>=1.26.0

# 工具
tqdm
loguru
```

安装(服务器):
```bash
pip install --index-url https://download.pytorch.org/whl/cpu torch torchvision
pip install -r backend/requirements-serve.txt
```

#### 8.4.2 内存预算(30GB RAM)

| 项 | 预估 | 累计 |
|---|---|---|
| 系统 + Python | 2 GB | 2 |
| OpenVINO 加载一份模型 | 6-8 GB | 10 |
| 推理峰值 临时缓冲 | 3-4 GB | 14 |
| FastAPI + 队列 + 静态文件 | 0.5 GB | 14.5 |
| 多品种切换(轮换加载) | +6 GB | 20.5 |
| **预留缓冲** | 10 GB | 30 ✅ |

策略:**单实例服务,同时只加载 1 个品种模型**;切换品种时卸载旧的、加载新的(加载耗时 30-60 秒,首次切换有延迟)。

### 8.5 FastAPI 后端设计

#### 8.5.1 API 规格

##### POST `/api/generate`

请求:
```json
{
  "variety": "musang_king",
  "prompt": "on a wooden table, soft natural light",
  "negative_prompt": "blurry, low quality",
  "num_images": 1,
  "steps": 6,
  "cfg_scale": 1.5,
  "seed": -1,
  "width": 512,
  "height": 512
}
```

响应(立即返回,不等生成):
```json
{
  "task_id": "abc123",
  "status": "queued",
  "queue_position": 2,
  "estimated_seconds": 25
}
```

##### GET `/api/tasks/{task_id}`

响应(几种状态):
```json
// 排队中
{"task_id":"abc123","status":"queued","queue_position":1,"estimated_seconds":12}

// 进行中
{"task_id":"abc123","status":"running","progress":0.5,"current_step":3,"total_steps":6}

// 完成
{"task_id":"abc123","status":"done","image_urls":["/api/tasks/abc123/image?idx=0"]}

// 失败
{"task_id":"abc123","status":"failed","error":"out of memory"}
```

##### GET `/api/tasks/{task_id}/image?idx=0`

返回 PNG 图片二进制。

##### GET `/api/varieties`

返回可用品种列表(读 `models/openvino/` 目录):
```json
[
  {"id":"musang_king","name_cn":"猫山王","name_en":"Musang King","preview":"/static/preview/musang_king.jpg"},
  ...
]
```

#### 8.5.2 任务队列实现(`serve/queue.py`)

```python
# 设计要点(伪代码)
import asyncio
from collections import OrderedDict

class TaskQueue:
    def __init__(self, pipeline):
        self.queue = asyncio.Queue(maxsize=20)   # 最多排队 20 个
        self.tasks = OrderedDict()               # task_id -> TaskState
        self.pipeline = pipeline
        self.worker_task = asyncio.create_task(self._worker())

    async def submit(self, params) -> str:
        task_id = generate_id()
        state = TaskState(id=task_id, status="queued", params=params)
        self.tasks[task_id] = state
        await self.queue.put(task_id)
        return task_id

    async def _worker(self):
        # 单 worker,顺序执行 — CPU 推理同时只能跑一个
        while True:
            task_id = await self.queue.get()
            state = self.tasks[task_id]
            state.status = "running"
            try:
                # 在 executor 里跑,不阻塞事件循环
                images = await asyncio.get_event_loop().run_in_executor(
                    None, self.pipeline.generate, state.params,
                    lambda step: setattr(state, "current_step", step)  # 进度回调
                )
                state.images = images
                state.status = "done"
            except Exception as e:
                state.status = "failed"
                state.error = str(e)

    def get_state(self, task_id) -> TaskState:
        return self.tasks.get(task_id)
```

**关键点:**
- 单 worker,串行处理(CPU 推理无法并发)
- 队列上限 20,满了拒绝新请求(返回 503)
- 任务结果保留 30 分钟后自动清理(避免内存膨胀)
- 进度回调通过 `callback_on_step_end` 接入 diffusers pipeline

#### 8.5.3 启动命令

```bash
# 服务器上
cd /data/durian/backend
uvicorn serve.app:app --host 0.0.0.0 --port 8000 --workers 1

# 后台运行(systemd 或 nohup)
nohup uvicorn serve.app:app --host 0.0.0.0 --port 8000 --workers 1 \
    > /var/log/durian.log 2>&1 &
```

> ⚠ **必须 `--workers 1`**:多 worker 会各自加载模型,内存爆炸。

---

## 9. 前端改造(沿用 `app/`)

### 9.1 改动原则

- **保留** 现有 React 19 + Vite + Tailwind + shadcn 技术栈
- **不引入** 新组件库
- 在现有结构上新建 3 个 section + 1 个 API 模块

### 9.2 视觉风格规范

#### 9.2.1 色板(Tailwind 自定义)

```js
// frontend/tailwind.config.js
theme: {
  extend: {
    colors: {
      durian: {
        flesh: '#F4C545',      // 果肉黄
        skin:  '#5A6B3A',      // 果壳墨绿
        thorn: '#2E3818',      // 深绿刺
        cream: '#FBF6E9',      // 浅米背景
        accent:'#E89B2C',      // 强调橙
      }
    },
    fontFamily: {
      display: ['"Plus Jakarta Sans"', 'sans-serif'],
      body: ['Inter', 'sans-serif'],
    }
  }
}
```

#### 9.2.2 设计语言

- **玻璃拟态卡片**:`backdrop-blur-xl bg-white/60 border border-white/40`
- **大留白**:页面主体 max-w-6xl,垂直 spacing 充足
- **微动效**:hover scale-105 + shadow 渐变;骨架屏用 shimmer 动画
- **字体层级**:标题 Plus Jakarta Sans Bold 48-72px,正文 Inter 16px
- **图标**:沿用 `lucide-react`(已装)

### 9.3 页面结构

#### 9.3.1 主页(`src/sections/Hero.tsx`)

```
┌──────────────────────────────────────────────────────────┐
│ Header  [Logo 榴莲AIGC]    Gallery  About    [GitHub图标] │
├──────────────────────────────────────────────────────────┤
│                                                            │
│   ▼ 大标题 "Generate Photorealistic Durians"               │
│   ▼ 副标题:Powered by Stable Diffusion + LoRA            │
│                                                            │
│   ┌────────────────────────────────────────┐               │
│   │  品种选择(4 个圆角卡片,带预览图)        │               │
│   │  [猫山王]  [金枕头]  [黑刺王]  [红虾]    │               │
│   └────────────────────────────────────────┘               │
│                                                            │
│   ┌────────────────────────────────────────┐               │
│   │ Prompt 输入框(大,占主视野)            │               │
│   │ "Describe the scene..."                │               │
│   │                                         │               │
│   │ [高级选项展开 ▾]                        │               │
│   │    - Negative prompt                   │               │
│   │    - Steps slider (4-12)               │               │
│   │    - CFG slider                        │               │
│   │    - Seed input                        │               │
│   └────────────────────────────────────────┘               │
│                                                            │
│        [ ✨ Generate ]   <— 大主按钮                        │
│                                                            │
│   ┌────────────────────────────────────────┐               │
│   │ 进度区(生成时显示)                       │               │
│   │ - 排队位置:第 2 位                       │               │
│   │ - 预计时间:25 秒                         │               │
│   │ - 进度条 + 当前扩散步数 3/6             │               │
│   └────────────────────────────────────────┘               │
│                                                            │
│   ┌────────────────────────────────────────┐               │
│   │ 结果展示区(4 列网格,点击大图)            │               │
│   │ [img] [img] [img] [img]                │               │
│   │ 每张下方:下载按钮 / 重新生成             │               │
│   └────────────────────────────────────────┘               │
│                                                            │
└──────────────────────────────────────────────────────────┘
```

#### 9.3.2 画廊页(`src/sections/Gallery.tsx`)

- localStorage 存最近 50 张生成历史(task_id + 缩略图 + 参数)
- Masonry 瀑布流布局
- 点击放大,显示原始 prompt,可"用此 prompt 重新生成"

#### 9.3.3 关于页(`src/sections/About.tsx`)

- 项目介绍
- 技术栈说明
- 数据集来源声明
- 仅学术演示用免责声明

### 9.4 API 客户端(`src/api/client.ts`)

```typescript
// 核心逻辑伪代码
export async function generateImage(params: GenerateParams) {
  // 1. 提交任务
  const { task_id } = await fetch('/api/generate', {
    method: 'POST',
    body: JSON.stringify(params),
  }).then(r => r.json())

  // 2. 轮询进度(每 1 秒)
  while (true) {
    await sleep(1000)
    const state = await fetch(`/api/tasks/${task_id}`).then(r => r.json())
    onProgress(state)  // 回调更新 UI

    if (state.status === 'done') return state.image_urls
    if (state.status === 'failed') throw new Error(state.error)
  }
}
```

支持取消(`AbortController`)和超时(2 分钟兜底)。

### 9.5 部署方式

- 前端 `npm run build` → `dist/`
- 服务器把 `dist/` 当 FastAPI 静态文件挂载:
  ```python
  app.mount("/", StaticFiles(directory="frontend/dist", html=True))
  ```
- 这样**前后端同源**,无 CORS 问题,只用一个 8000 端口

---

## 10. 完整运行清单(从零到上线)

### 阶段 A:本地准备(一次性)

```powershell
# A1. 装训练环境
conda create -n durian python=3.11 -y
conda activate durian
pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128
pip install -r backend/requirements-train.txt

# A2. 整理目录(删旧)
# 详见 §4.2
```

### 阶段 B:数据准备(每个品种)

```powershell
# B1. 爬虫
python backend/data_tools/scraper.py --variety musang_king --num 200 --out raw/musang_king/

# B2. 自动过滤
python backend/data_tools/filter.py --in raw/musang_king/ --out candidates/musang_king/

# B3. 人工筛选(手工删除不对的图)

# B4. 合并个人数据集
python backend/data_tools/merge_dataset.py `
    --crawled candidates/musang_king/ `
    --personal personal_data/musang_king/ `
    --out training_data/musang_king/

# B5. BLIP 自动打标
python backend/data_tools/blip_caption.py --variety musang_king --dir training_data/musang_king/

# B6. (可选) 人工补正 caption
```

### 阶段 C:训练

```powershell
python backend/lora_trainer.py `
    --variety musang_king `
    --data_dir training_data/musang_king `
    --output_dir backend/models/lora/musang_king `
    --epochs 50 --rank 16
```

### 阶段 D:本地验证

```powershell
python backend/local_inference.py --variety musang_king --prompt "on a table" --num 4
# 检查 outputs/ 下的图,满意了进入 E
```

### 阶段 E:模型导出 + 上传

```powershell
# E1. 合并 LoRA + LCM
python backend/tools/merge_lora.py ...
python backend/tools/merge_lora.py ...    # LCM

# E2. 导出 OpenVINO
python backend/tools/export_openvino.py ...

# E3. 打包
tar -czvf musang_king_openvino.tar.gz backend/models/openvino/musang_king/

# E4. 上传
scp musang_king_openvino.tar.gz user@server:/data/durian/models/
```

### 阶段 F:服务器部署(一次性)

```bash
# F1. 装服务环境
ssh user@server
cd /data/durian
python -m venv venv && source venv/bin/activate
pip install --index-url https://download.pytorch.org/whl/cpu torch torchvision
pip install -r backend/requirements-serve.txt

# F2. 解包模型
cd /data/durian/models && tar -xzvf musang_king_openvino.tar.gz

# F3. 构建前端(本地或服务器均可,推荐本地构建后传 dist/)
# 本地:
cd frontend && npm install && npm run build
scp -r dist user@server:/data/durian/frontend/

# F4. 启动服务
cd /data/durian/backend
nohup uvicorn serve.app:app --host 0.0.0.0 --port 8000 --workers 1 \
    > /var/log/durian.log 2>&1 &

# F5. 测试
curl http://server:8000/api/varieties
# 浏览器打开 http://server:8000
```

---

## 11. 风险与已知坑

| 风险 | 影响 | 缓解 |
|---|---|---|
| RTX 5070 PyTorch 兼容性 | 训练根本跑不起来 | 强制 nightly + CUDA 12.8(§6.1) |
| 数据集版权 | 法律风险 | 仅学术演示,前端关于页明示 |
| BLIP 把榴莲识别成其它水果 | caption 质量差 | 人工抽查,品种触发词永远在前 |
| OpenVINO 转换失败 | 部署阻塞 | 备选 ONNX Runtime,慢一倍但稳定 |
| CPU 推理首次启动慢(模型加载 60 秒)| 第一个用户体验差 | 服务启动时预热加载,前端显示"服务初始化中" |
| 多人同时点"生成"超队列容量 | 503 错误 | 队列大小 20,前端提示"系统繁忙稍后再试" |
| LCM 与品种 LoRA 叠加效果不佳 | 出图质量降 | 调 LoRA alpha 0.6-1.0 找最佳点;若仍差,改用 25 步标准模式(30-50秒/张) |
| 服务器内存接近上限 | OOM kill | 单实例 + 单品种 + swap 15GB 兜底 |
| 用户描述含中文 | SD1.5 不支持中文 | 前端做"中→英"提示,或集成翻译 API |
| Windows 路径里的中文目录 | 部分库读不到 | 训练数据放纯英文路径,如 `D:/durian-data/` |

---

## 12. 验收标准

完成本设计的实现后,应满足:

- [ ] 本地能用一条命令完成爬虫→筛选→打标→训练→推理全流程
- [ ] 训练 1 个品种(50 张图)在 RTX 5070 上 30 分钟内完成
- [ ] 本地推理 `local_inference.py` 单张 < 5 秒
- [ ] 服务器推理单张 < 20 秒(标准 8-15 秒)
- [ ] 服务器同时排 5 个任务不崩
- [ ] 前端时尚现代,玻璃拟态视觉,真实进度条
- [ ] 前后端同源部署,1 个端口提供服务
- [ ] 至少 2 个品种端到端可用
- [ ] 文档齐全:数据/训练/部署三份独立 README

---

## 13. 实施阶段拆分(为下一步 writing-plans 准备)

建议分 5 个里程碑:

1. **M1 - 仓库整理 + 环境就绪**(~半天)
2. **M2 - 数据流水线**(~1-2 天)
3. **M3 - 训练 + 本地推理**(~1 天)
4. **M4 - 模型导出 + 服务器后端**(~1-2 天)
5. **M5 - 前端改造 + 联调上线**(~2-3 天)

每个里程碑结束都有可验证产物,可单独验收。

---

**文档完。请审阅。**

如有需要调整或补充的内容,告诉我具体在哪一节(例如 "§9.3.1 主页布局想加点别的" 或 "§5.2.1 还要加 XX 图源")。
确认无修改后,我会进入 `writing-plans` 阶段,把上述实施拆成可执行的逐步任务清单。
