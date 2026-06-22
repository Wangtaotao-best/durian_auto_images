# 榴莲 AIGC 系统 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将设计文档 `2026-06-22-durian-aigc-design.md` 完整落地为可运行系统:本地训练 LoRA + 本地快速推理 + CPU 服务器 Web 部署 + Docker 容器化部署。

**Architecture:** 一个 monorepo,`backend/` 同时承担"训练侧 Python 程序"和"推理服务",`frontend/` 沿用现有 React SPA。训练在 RTX 5070 上跑 PyTorch+CUDA;部署服务器无 GPU,通过 OpenVINO + LCM-LoRA 把 CPU 推理压到 8-15 秒/张;前端用异步任务 + 轮询通信。**部署使用 Docker**,包含 backend + frontend 一体化镜像。

**Tech Stack:** PyTorch nightly (cu128) / diffusers / peft / OpenVINO 2024.4 / FastAPI / asyncio / React 19 / Vite 7 / Tailwind / shadcn-Radix / icrawler / BLIP / **Docker + docker-compose**

**项目根目录:** `D:/谷歌下载/Kimi_Agent_榴莲图像生成代码/`
**所有命令均在 Windows PowerShell 中执行**(服务器侧除外,会注明 SSH/bash)。

---

## 里程碑总览

| 里程碑 | 任务范围 | 任务编号 | 预估时间 |
|---|---|---|---|
| **M1** | 仓库整理 + 环境就绪 | Task 1-5 | 半天 |
| **M2** | 数据流水线(爬虫/过滤/合并/BLIP)| Task 6-11 | 1-2 天 |
| **M3** | 训练 + 本地推理 | Task 12-15 | 1 天 |
| **M4** | 模型导出 + 服务器后端 | Task 16-25 | 1-2 天 |
| **M5** | 前端改造 + Docker 部署 + 联调上线 | Task 26-36 | 2-3 天 |

⚠️ **重要约定:**
- 项目路径含中文,某些 Python 库可能报错。**训练数据集和模型输出建议放在纯英文盘路径**,例如 `D:/durian-data/`。本计划在 M1 Task 2 处理这一点。
- 每个任务结束前必须 `git add` + `git commit`,提交信息用 Conventional Commits 风格。
- 测试驱动开发(TDD)适用于 `data_tools/` 和 `serve/` 模块;训练/导出/部署任务采用 "smoke 验收"。

---

# 🏁 M1: 仓库整理 + 环境就绪

## Task 1: 备份与初始化 Git 仓库

**Files:**
- Create: `.gitignore`
- Create: `archive/README.md`

- [ ] **Step 1: 初始化 git**

Run:
```powershell
cd "D:/谷歌下载/Kimi_Agent_榴莲图像生成代码"
git init
git config user.name "durian-dev"
git config user.email "durian@local"
```
Expected: `Initialized empty Git repository in ...`

- [ ] **Step 2: 写 `.gitignore`**

Create `.gitignore`:

```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
.venv/
venv/
.env

# Node
node_modules/
dist/
.vite/

# Models & data (太大,不入库)
models/
training_data/
raw/
candidates/
personal_data/
outputs/
*.safetensors
*.ckpt
*.bin
*.onnx
openvino_models/

# OS
.DS_Store
Thumbs.db

# IDE
.idea/
.vscode/
*.swp

# Logs
*.log
logs/

# Archive
archive/old_*.tar.gz

# Personal large files
generated_durian_*.png
*.tar.gz
ziUpcpXC
```

- [ ] **Step 3: 创建 archive 目录,移动旧文件**

```powershell
New-Item -ItemType Directory archive -Force
Move-Item durian-aigc archive/durian-aigc-old
Move-Item durian-aigc.tar.gz archive/
Move-Item generated_durian_0.png,generated_durian_1.png,generated_durian_2.png,generated_durian_3.png archive/ -ErrorAction SilentlyContinue
Move-Item ziUpcpXC archive/ -ErrorAction SilentlyContinue
Move-Item test.py archive/ -ErrorAction SilentlyContinue
```

Create `archive/README.md`:
```markdown
# 归档目录

存放项目重构前的旧版本和散落文件,仅供历史参考。

- `durian-aigc-old/`: 旧的代码副本(已被 `backend/` 取代)
- `durian-aigc.tar.gz`: 代码压缩包
- `generated_durian_*.png`: 旧的生成样本
- `test.py`: 散落的根目录测试脚本
```

- [ ] **Step 4: 首次提交**

```powershell
git add .gitignore archive/README.md
git commit -m "chore: initial commit with gitignore and archive structure"
```
Expected: `1 file changed` or `2 files changed`

---

## Task 2: 创建标准目录结构 + 数据外置

**Files:**
- Create: `backend/`, `frontend/`, `docs/`, `scripts/`
- Create: `D:/durian-data/` (项目外的数据/模型目录)

- [ ] **Step 1: 创建项目内空目录**

```powershell
cd "D:/谷歌下载/Kimi_Agent_榴莲图像生成代码"
New-Item -ItemType Directory backend, scripts -Force
New-Item -ItemType Directory backend/data_tools, backend/serve, backend/tools, backend/configs, backend/tests -Force
```

- [ ] **Step 2: 把旧代码搬到 backend/**

```powershell
# 把 durian-aigc-code/ 的内容搬到 backend/
Get-ChildItem durian-aigc-code/ -Exclude __pycache__,models | ForEach-Object {
    Move-Item $_.FullName backend/
}
# 旧 __pycache__ 直接删
Remove-Item durian-aigc-code/__pycache__ -Recurse -Force -ErrorAction SilentlyContinue
# 旧 models/ 搬到外部
Remove-Item durian-aigc-code -Recurse -Force
```

- [ ] **Step 3: 重命名 app/ → frontend/**

```powershell
Rename-Item app frontend
```

- [ ] **Step 4: 在 D 盘根目录创建数据/模型外置目录**

```powershell
New-Item -ItemType Directory "D:/durian-data/raw","D:/durian-data/candidates","D:/durian-data/personal","D:/durian-data/training","D:/durian-data/models/lora","D:/durian-data/models/merged","D:/durian-data/models/openvino","D:/durian-data/outputs" -Force
```

- [ ] **Step 5: 项目里建符号链接(可选,方便相对路径访问)**

```powershell
# 用 mklink 建符号链接 (PowerShell 中需要管理员权限,如果不便就用绝对路径)
# 备选: 不建链接,所有脚本统一用配置文件指向 D:/durian-data/
```

如果创建链接遇权限问题,跳过 — 后续脚本通过 `configs/paths.yaml` 指定绝对路径。

- [ ] **Step 6: 把根目录旧的 models/lora 搬到外置目录**

```powershell
if (Test-Path models/lora/musang_king) {
    Move-Item models/lora/musang_king "D:/durian-data/models/lora/" -Force
}
Remove-Item models -Recurse -Force -ErrorAction SilentlyContinue
```

- [ ] **Step 7: 提交**

```powershell
git add backend/ frontend/ scripts/
git commit -m "refactor: restructure repo into backend/frontend monorepo layout"
```

---

## Task 3: 写 `configs/paths.yaml` 统一路径配置

**Files:**
- Create: `backend/configs/paths.yaml`
- Create: `backend/configs/__init__.py`
- Create: `backend/configs/loader.py`
- Create: `backend/tests/test_paths.py`

- [ ] **Step 1: 写失败测试**

Create `backend/tests/__init__.py` (空文件)
Create `backend/tests/test_paths.py`:

```python
"""测试路径配置加载"""
from pathlib import Path
import pytest
from backend.configs.loader import load_paths


def test_load_paths_returns_dict():
    paths = load_paths()
    assert isinstance(paths, dict)


def test_paths_has_required_keys():
    paths = load_paths()
    required = ["data_root", "raw", "candidates", "training", "models_lora",
                "models_merged", "models_openvino", "outputs"]
    for key in required:
        assert key in paths, f"missing key: {key}"


def test_paths_are_path_objects():
    paths = load_paths()
    assert isinstance(paths["data_root"], Path)


def test_data_root_is_durian_data():
    paths = load_paths()
    assert paths["data_root"].name == "durian-data"
```

- [ ] **Step 2: 运行测试验证失败**

```powershell
cd "D:/谷歌下载/Kimi_Agent_榴莲图像生成代码"
python -m pytest backend/tests/test_paths.py -v
```
Expected: FAIL — `ModuleNotFoundError: backend.configs.loader`

- [ ] **Step 3: 写 `paths.yaml`**

Create `backend/configs/paths.yaml`:

```yaml
# 数据/模型外置存储位置
# Windows 本机:
data_root: "D:/durian-data"

# 各子目录(相对 data_root)
subdirs:
  raw: "raw"
  candidates: "candidates"
  personal: "personal"
  training: "training"
  models_lora: "models/lora"
  models_merged: "models/merged"
  models_openvino: "models/openvino"
  outputs: "outputs"

# 4 个品种的元信息
varieties:
  musang_king:
    trigger: "musangking durian"
    name_cn: "猫山王"
    name_en: "Musang King"
    keywords:
      - "musang king durian"
      - "猫山王榴莲"
      - "猫山王 切开"
  monthong:
    trigger: "monthong durian"
    name_cn: "金枕头"
    name_en: "Monthong"
    keywords:
      - "monthong durian"
      - "金枕头榴莲"
      - "monthong cut open"
  blackthorn:
    trigger: "blackthorn durian"
    name_cn: "黑刺王"
    name_en: "Black Thorn"
    keywords:
      - "black thorn durian"
      - "黑刺榴莲"
  red_prawn:
    trigger: "redprawn durian"
    name_cn: "红虾"
    name_en: "Red Prawn"
    keywords:
      - "red prawn durian"
      - "红虾榴莲"

# 训练默认值
training_defaults:
  base_model: "runwayml/stable-diffusion-v1-5"
  resolution: 512
  rank: 16
  alpha: 32
  learning_rate: 0.0001
  epochs: 50
  batch_size: 1
  mixed_precision: "fp16"

# 服务器推理默认值
serve_defaults:
  base_model: "runwayml/stable-diffusion-v1-5"
  steps: 6
  cfg_scale: 1.5
  width: 512
  height: 512
  scheduler: "lcm"
```

- [ ] **Step 4: 写 `loader.py`**

Create `backend/configs/__init__.py` (空文件)
Create `backend/configs/loader.py`:

```python
"""配置加载器 - 统一路径与超参数"""
from pathlib import Path
import yaml

_THIS_DIR = Path(__file__).parent
_PATHS_YAML = _THIS_DIR / "paths.yaml"


def _read_yaml() -> dict:
    with open(_PATHS_YAML, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_paths() -> dict:
    """加载路径配置,返回 {key: Path 对象}"""
    cfg = _read_yaml()
    root = Path(cfg["data_root"])
    out = {"data_root": root}
    for key, sub in cfg["subdirs"].items():
        out[key] = root / sub
    return out


def load_varieties() -> dict:
    """加载品种元信息"""
    return _read_yaml()["varieties"]


def load_training_defaults() -> dict:
    return _read_yaml()["training_defaults"]


def load_serve_defaults() -> dict:
    return _read_yaml()["serve_defaults"]
```

- [ ] **Step 5: 安装 pyyaml + 运行测试**

```powershell
pip install pyyaml pytest
python -m pytest backend/tests/test_paths.py -v
```
Expected: 4 passed

- [ ] **Step 6: 提交**

```powershell
git add backend/configs/ backend/tests/
git commit -m "feat(configs): add unified paths.yaml + loader with tests"
```

---

## Task 4: 安装训练环境(本地 RTX 5070)

**Files:**
- Create: `backend/requirements-train.txt`
- Create: `scripts/setup_train_env.ps1`

- [ ] **Step 1: 写 `requirements-train.txt`**

Create `backend/requirements-train.txt`:

```
# 注意: PyTorch 不在此文件,需单独装 nightly 版以支持 RTX 5070 Blackwell (sm_120)
# 安装命令: pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128

# Stable Diffusion 生态
diffusers>=0.30.0
transformers>=4.44.0
accelerate>=0.33.0
peft>=0.12.0
safetensors>=0.4.0

# 数据处理
Pillow>=10.0.0
opencv-python>=4.10.0
imagehash>=4.3.1
numpy>=1.26.0
tqdm>=4.66.0

# 数据采集
icrawler>=0.6.7

# 工具
omegaconf>=2.3.0
tensorboard>=2.17.0
pyyaml>=6.0
pytest>=8.0.0
```

- [ ] **Step 2: 写安装脚本**

Create `scripts/setup_train_env.ps1`:

```powershell
# 训练环境一键安装脚本 (Windows + RTX 5070)
# 用法: powershell -ExecutionPolicy Bypass -File scripts/setup_train_env.ps1

Write-Host "==> 步骤 1/3: 创建 conda 环境 'durian' (Python 3.11)" -ForegroundColor Cyan
conda create -n durian python=3.11 -y
if ($LASTEXITCODE -ne 0) { Write-Host "conda 环境创建失败,可能已存在,继续..." }

Write-Host "==> 步骤 2/3: 在 'durian' 环境中安装 PyTorch nightly + CUDA 12.8" -ForegroundColor Cyan
conda run -n durian pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128
if ($LASTEXITCODE -ne 0) { Write-Host "PyTorch 安装失败" -ForegroundColor Red; exit 1 }

Write-Host "==> 步骤 3/3: 安装其余训练依赖" -ForegroundColor Cyan
conda run -n durian pip install -r backend/requirements-train.txt
if ($LASTEXITCODE -ne 0) { Write-Host "依赖安装失败" -ForegroundColor Red; exit 1 }

Write-Host ""
Write-Host "==> 验证 GPU 可用..." -ForegroundColor Cyan
conda run -n durian python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}'); print(f'Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')"

Write-Host ""
Write-Host "==> 安装完成! 使用 'conda activate durian' 进入环境" -ForegroundColor Green
```

- [ ] **Step 3: 运行安装**

```powershell
cd "D:/谷歌下载/Kimi_Agent_榴莲图像生成代码"
powershell -ExecutionPolicy Bypass -File scripts/setup_train_env.ps1
```
Expected: 最后输出 `Device: NVIDIA GeForce RTX 5070` 和 `CUDA available: True`

如果失败,常见原因:
- conda 不在 PATH → 用 Miniconda 自带的 Anaconda Prompt 运行
- PyTorch nightly 偶尔不可用 → 改用 `--index-url https://download.pytorch.org/whl/cu124` 试稳定版

- [ ] **Step 4: 提交**

```powershell
git add backend/requirements-train.txt scripts/setup_train_env.ps1
git commit -m "feat(env): add training env setup with PyTorch nightly cu128 for RTX 5070"
```

---

## Task 5: 写项目根目录 README + docs 框架

**Files:**
- Create: `README.md`
- Create: `docs/data-collection.md` (占位,M2 填内容)
- Create: `docs/training.md` (占位)
- Create: `docs/deployment.md` (占位)

- [ ] **Step 1: 写根 README**

Create `README.md`:

````markdown
# 榴莲 AIGC 系统

基于 Stable Diffusion 1.5 + LoRA + ControlNet 的榴莲品种图像生成系统,
包含本地训练 + CPU 服务器 Web 部署完整流程。

## 项目结构

```
.
├── backend/        Python 后端 (训练 + 推理服务)
│   ├── data_tools/  数据采集与标注
│   ├── tools/       模型合并与导出
│   ├── serve/       FastAPI Web 服务
│   ├── configs/     路径与超参数配置
│   └── tests/       单元测试
├── frontend/       React 19 + Vite + Tailwind + shadcn
├── docs/           设计、训练、部署文档
├── scripts/        一键脚本
└── archive/        历史代码归档
```

数据与模型外置在 `D:/durian-data/`,不进入 git。

## 快速开始

1. **本地训练环境**: `powershell scripts/setup_train_env.ps1`
2. **数据准备**: 见 `docs/data-collection.md`
3. **训练**: 见 `docs/training.md`
4. **部署**: 见 `docs/deployment.md`

## 文档

- 设计文档: `docs/superpowers/specs/2026-06-22-durian-aigc-design.md`
- 实施计划: `docs/superpowers/plans/2026-06-22-durian-aigc-implementation.md`
````

- [ ] **Step 2: 创建文档占位**

Create `docs/data-collection.md`:
```markdown
# 数据收集与标注指南

> 详细内容在 M2 完成后补全。
```

Create `docs/training.md`:
```markdown
# 训练指南

> 详细内容在 M3 完成后补全。
```

Create `docs/deployment.md`:
```markdown
# 部署指南

> 详细内容在 M4-M5 完成后补全。
```

- [ ] **Step 3: 提交**

```powershell
git add README.md docs/data-collection.md docs/training.md docs/deployment.md
git commit -m "docs: add root README and documentation placeholders"
```

**M1 验收:**
- [ ] `git log --oneline` 有 5 个 commit
- [ ] `D:/durian-data/` 已创建且有子目录
- [ ] `conda activate durian` + `python -c "import torch; print(torch.cuda.is_available())"` 输出 `True`
- [ ] `python -m pytest backend/tests/ -v` 全部通过

---

# 📦 M2: 数据流水线

## Task 6: 实现 `data_tools/scraper.py` — 图像爬虫

**Files:**
- Create: `backend/data_tools/__init__.py`
- Create: `backend/data_tools/scraper.py`
- Create: `backend/tests/test_scraper.py`

- [ ] **Step 1: 写失败测试**

Create `backend/tests/test_scraper.py`:

```python
"""测试爬虫模块的纯函数部分(不真实联网)"""
import pytest
from backend.data_tools.scraper import build_keywords, sanitize_output_dir
from pathlib import Path


def test_build_keywords_for_known_variety():
    keywords = build_keywords("musang_king")
    assert len(keywords) >= 2
    assert any("musang" in k.lower() for k in keywords)


def test_build_keywords_unknown_variety_raises():
    with pytest.raises(KeyError):
        build_keywords("nonexistent_variety")


def test_sanitize_output_dir_creates_path(tmp_path):
    out = sanitize_output_dir(tmp_path / "raw" / "musang_king")
    assert out.exists()
    assert out.is_dir()
```

- [ ] **Step 2: 运行测试,确认失败**

```powershell
python -m pytest backend/tests/test_scraper.py -v
```
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: 实现 scraper.py**

Create `backend/data_tools/__init__.py` (空)
Create `backend/data_tools/scraper.py`:

```python
"""图像爬虫 - 从 Bing/Google 批量下载特定品种榴莲图片"""
import argparse
import logging
from pathlib import Path
from typing import List

from backend.configs.loader import load_varieties, load_paths

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")


def build_keywords(variety: str) -> List[str]:
    """获取品种对应的搜索关键词列表"""
    varieties = load_varieties()
    if variety not in varieties:
        raise KeyError(f"未知品种: {variety}, 可选: {list(varieties.keys())}")
    return varieties[variety]["keywords"]


def sanitize_output_dir(path: Path) -> Path:
    """确保输出目录存在"""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def scrape_variety(variety: str, num_per_keyword: int = 50, out_dir: Path = None) -> int:
    """爬取一个品种的图像"""
    try:
        from icrawler.builtin import BingImageCrawler
    except ImportError:
        raise RuntimeError("请先 pip install icrawler")

    paths = load_paths()
    if out_dir is None:
        out_dir = paths["raw"] / variety
    out_dir = sanitize_output_dir(out_dir)

    keywords = build_keywords(variety)
    total_downloaded = 0

    for idx, kw in enumerate(keywords):
        logger.info(f"[{variety}] 关键词 {idx+1}/{len(keywords)}: '{kw}'")
        sub_dir = out_dir / f"kw_{idx:02d}"
        sub_dir.mkdir(exist_ok=True)
        crawler = BingImageCrawler(storage={"root_dir": str(sub_dir)})
        crawler.crawl(
            keyword=kw,
            max_num=num_per_keyword,
            min_size=(512, 512),
            file_idx_offset=0,
        )
        downloaded = len(list(sub_dir.glob("*")))
        logger.info(f"[{variety}] 关键词 '{kw}' 下载了 {downloaded} 张")
        total_downloaded += downloaded

    logger.info(f"[{variety}] 总计下载 {total_downloaded} 张到 {out_dir}")
    return total_downloaded


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--variety", required=True, help="品种名 (musang_king/monthong/blackthorn/red_prawn)")
    parser.add_argument("--num", type=int, default=50, help="每个关键词下载数")
    parser.add_argument("--out", type=Path, default=None, help="输出目录,默认 D:/durian-data/raw/<variety>/")
    args = parser.parse_args()

    scrape_variety(args.variety, args.num, args.out)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 运行测试通过**

```powershell
python -m pytest backend/tests/test_scraper.py -v
```
Expected: 3 passed

- [ ] **Step 5: Smoke 测试 — 实际爬一个品种**

```powershell
conda activate durian
python -m backend.data_tools.scraper --variety musang_king --num 10
```
Expected: `D:/durian-data/raw/musang_king/kw_00/` 等子目录中有图片

如果 BingImageCrawler 报错,改用谷歌或必应国内镜像;也可手工准备图像跳过此步。

- [ ] **Step 6: 提交**

```powershell
git add backend/data_tools/ backend/tests/test_scraper.py
git commit -m "feat(data): add image scraper with bing crawler + unit tests"
```

---

## Task 7: 实现 `data_tools/filter.py` — 自动筛选

**Files:**
- Create: `backend/data_tools/filter.py`
- Create: `backend/tests/test_filter.py`

- [ ] **Step 1: 写失败测试**

Create `backend/tests/test_filter.py`:

```python
"""测试图像过滤逻辑"""
import pytest
from PIL import Image
from pathlib import Path
from backend.data_tools.filter import (
    check_resolution,
    check_aspect_ratio,
    check_file_size,
    compute_phash,
    filter_image,
)


@pytest.fixture
def tmp_image(tmp_path):
    def _make(w=600, h=600, fmt="JPEG"):
        p = tmp_path / f"img_{w}x{h}.{fmt.lower()}"
        Image.new("RGB", (w, h), color=(255, 200, 100)).save(p, fmt)
        return p
    return _make


def test_resolution_pass(tmp_image):
    assert check_resolution(tmp_image(600, 600), min_size=512) is True


def test_resolution_fail(tmp_image):
    assert check_resolution(tmp_image(400, 400), min_size=512) is False


def test_aspect_ratio_pass(tmp_image):
    assert check_aspect_ratio(tmp_image(600, 800)) is True


def test_aspect_ratio_fail_too_wide(tmp_image):
    assert check_aspect_ratio(tmp_image(2000, 500)) is False


def test_file_size_ok(tmp_image):
    assert check_file_size(tmp_image(), max_mb=10) is True


def test_phash_returns_string(tmp_image):
    h = compute_phash(tmp_image())
    assert isinstance(h, str)
    assert len(h) == 16


def test_filter_image_passes_good(tmp_image):
    ok, reason = filter_image(tmp_image(800, 800))
    assert ok is True
    assert reason == "ok"


def test_filter_image_rejects_small(tmp_image):
    ok, reason = filter_image(tmp_image(300, 300))
    assert ok is False
    assert "resolution" in reason
```

- [ ] **Step 2: 运行测试确认失败**

```powershell
python -m pytest backend/tests/test_filter.py -v
```
Expected: FAIL

- [ ] **Step 3: 实现 filter.py**

Create `backend/data_tools/filter.py`:

```python
"""图像自动筛选 - 分辨率/长宽比/文件大小/pHash 去重"""
import argparse
import logging
import shutil
from pathlib import Path
from typing import Tuple

from PIL import Image
import imagehash

from backend.configs.loader import load_paths

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")

MIN_RESOLUTION = 512
MAX_FILE_MB = 10
MIN_ASPECT = 0.5
MAX_ASPECT = 2.0
PHASH_THRESHOLD = 5   # 海明距离 < 5 视为重复


def check_resolution(img_path: Path, min_size: int = MIN_RESOLUTION) -> bool:
    try:
        with Image.open(img_path) as im:
            return im.width >= min_size and im.height >= min_size
    except Exception:
        return False


def check_aspect_ratio(img_path: Path,
                       min_ratio: float = MIN_ASPECT,
                       max_ratio: float = MAX_ASPECT) -> bool:
    try:
        with Image.open(img_path) as im:
            r = im.width / im.height
            return min_ratio <= r <= max_ratio
    except Exception:
        return False


def check_file_size(img_path: Path, max_mb: float = MAX_FILE_MB) -> bool:
    return img_path.stat().st_size <= max_mb * 1024 * 1024


def compute_phash(img_path: Path) -> str:
    with Image.open(img_path) as im:
        return str(imagehash.phash(im))


def filter_image(img_path: Path) -> Tuple[bool, str]:
    """对一张图做所有检查,返回 (是否通过, 理由)"""
    if not check_resolution(img_path):
        return False, f"resolution < {MIN_RESOLUTION}"
    if not check_aspect_ratio(img_path):
        return False, f"aspect_ratio out of [{MIN_ASPECT}, {MAX_ASPECT}]"
    if not check_file_size(img_path):
        return False, f"file > {MAX_FILE_MB}MB"
    return True, "ok"


def filter_directory(in_dir: Path, out_dir: Path) -> dict:
    """筛选整个目录,通过的拷贝到 out_dir;去重基于 pHash"""
    in_dir, out_dir = Path(in_dir), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    stats = {"total": 0, "passed": 0, "rejected": 0, "duplicates": 0}
    seen_hashes = {}

    # 递归遍历 in_dir 中所有图片
    image_files = []
    for ext in ("*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG", "*.webp"):
        image_files.extend(in_dir.rglob(ext))

    for img_path in image_files:
        stats["total"] += 1
        ok, reason = filter_image(img_path)
        if not ok:
            stats["rejected"] += 1
            logger.debug(f"REJECT {img_path.name}: {reason}")
            continue

        # pHash 去重
        try:
            h = compute_phash(img_path)
        except Exception as e:
            stats["rejected"] += 1
            logger.warning(f"无法计算 pHash {img_path}: {e}")
            continue

        # 检查与已通过图像的相似度
        is_dup = False
        for seen_h in seen_hashes:
            if imagehash.hex_to_hash(h) - imagehash.hex_to_hash(seen_h) < PHASH_THRESHOLD:
                is_dup = True
                break
        if is_dup:
            stats["duplicates"] += 1
            continue

        seen_hashes[h] = img_path
        # 复制到输出目录,统一命名
        out_name = f"img_{stats['passed']:04d}{img_path.suffix.lower()}"
        shutil.copy(img_path, out_dir / out_name)
        stats["passed"] += 1

    logger.info(f"筛选完成: {stats}")
    return stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--variety", required=True)
    parser.add_argument("--in_dir", type=Path, default=None)
    parser.add_argument("--out_dir", type=Path, default=None)
    args = parser.parse_args()

    paths = load_paths()
    in_dir = args.in_dir or (paths["raw"] / args.variety)
    out_dir = args.out_dir or (paths["candidates"] / args.variety)
    filter_directory(in_dir, out_dir)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 运行测试通过**

```powershell
python -m pytest backend/tests/test_filter.py -v
```
Expected: 8 passed

- [ ] **Step 5: Smoke 测试**

```powershell
python -m backend.data_tools.filter --variety musang_king
```
Expected: 输出 `筛选完成: {'total': X, 'passed': Y, 'rejected': Z, 'duplicates': W}`

- [ ] **Step 6: 提交**

```powershell
git add backend/data_tools/filter.py backend/tests/test_filter.py
git commit -m "feat(data): add image filter (resolution/aspect/size/phash dedup) with tests"
```

---

## Task 8: 实现 `data_tools/merge_dataset.py` — 合并爬虫+个人数据

**Files:**
- Create: `backend/data_tools/merge_dataset.py`
- Create: `backend/tests/test_merge.py`

- [ ] **Step 1: 写失败测试**

Create `backend/tests/test_merge.py`:

```python
"""测试数据集合并"""
import pytest
from PIL import Image
from pathlib import Path
from backend.data_tools.merge_dataset import resize_image, merge_sources


@pytest.fixture
def make_img(tmp_path):
    def _f(name, w=800, h=800):
        p = tmp_path / name
        Image.new("RGB", (w, h), color=(200, 150, 100)).save(p, "JPEG")
        return p
    return _f


def test_resize_image_short_side(tmp_path, make_img):
    src = make_img("orig.jpg", 1200, 800)
    out = resize_image(src, tmp_path / "out.jpg", target_short=512)
    with Image.open(out) as im:
        assert min(im.size) == 512


def test_merge_two_sources(tmp_path, make_img):
    crawl_dir = tmp_path / "crawl"
    crawl_dir.mkdir()
    personal_dir = tmp_path / "personal"
    personal_dir.mkdir()
    out_dir = tmp_path / "out"

    make_img("crawl/a.jpg", 700, 700)
    make_img("crawl/b.jpg", 700, 700)
    make_img("personal/x.jpg", 700, 700)

    stats = merge_sources("musang_king", crawl_dir, personal_dir, out_dir)
    assert stats["total"] == 3
    assert len(list(out_dir.glob("*.jpg"))) == 3
```

- [ ] **Step 2: 运行测试确认失败**

```powershell
python -m pytest backend/tests/test_merge.py -v
```

- [ ] **Step 3: 实现 merge_dataset.py**

Create `backend/data_tools/merge_dataset.py`:

```python
"""合并爬虫候选 + 个人数据集 → 训练数据"""
import argparse
import logging
import shutil
from pathlib import Path

from PIL import Image
import imagehash

from backend.configs.loader import load_paths

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")

PHASH_THRESHOLD = 5


def resize_image(src: Path, dst: Path, target_short: int = 512) -> Path:
    """按短边等比缩放到 target_short"""
    with Image.open(src) as im:
        im = im.convert("RGB")
        w, h = im.size
        if min(w, h) > target_short:
            scale = target_short / min(w, h)
            new_size = (int(w * scale), int(h * scale))
            im = im.resize(new_size, Image.LANCZOS)
        dst.parent.mkdir(parents=True, exist_ok=True)
        im.save(dst, "JPEG", quality=92)
    return dst


def merge_sources(variety: str, crawl_dir: Path, personal_dir: Path,
                  out_dir: Path, target_short: int = 512) -> dict:
    """合并两个源到 out_dir,自动 resize + pHash 去重"""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    stats = {"total": 0, "added": 0, "duplicates": 0, "from_crawl": 0, "from_personal": 0}
    seen = {}
    idx = 0

    def _process(src_dir: Path, tag: str):
        nonlocal idx
        if not src_dir or not Path(src_dir).exists():
            return
        for src in sorted(Path(src_dir).rglob("*")):
            if src.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
                continue
            stats["total"] += 1
            try:
                h = str(imagehash.phash(Image.open(src)))
            except Exception:
                continue
            is_dup = any(
                imagehash.hex_to_hash(h) - imagehash.hex_to_hash(sh) < PHASH_THRESHOLD
                for sh in seen
            )
            if is_dup:
                stats["duplicates"] += 1
                continue
            seen[h] = True
            dst = out_dir / f"{variety}_{tag}_{idx:04d}.jpg"
            try:
                resize_image(src, dst, target_short)
                idx += 1
                stats["added"] += 1
                stats[f"from_{tag}"] += 1
            except Exception as e:
                logger.warning(f"处理失败 {src}: {e}")

    _process(crawl_dir, "crawl")
    _process(personal_dir, "personal")
    logger.info(f"合并完成 {variety}: {stats}")
    return stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--variety", required=True)
    parser.add_argument("--crawl_dir", type=Path, default=None)
    parser.add_argument("--personal_dir", type=Path, default=None)
    parser.add_argument("--out_dir", type=Path, default=None)
    args = parser.parse_args()

    paths = load_paths()
    crawl_dir = args.crawl_dir or (paths["candidates"] / args.variety)
    personal_dir = args.personal_dir or (paths["personal"] / args.variety)
    out_dir = args.out_dir or (paths["training"] / args.variety)
    merge_sources(args.variety, crawl_dir, personal_dir, out_dir)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 运行测试通过**

```powershell
python -m pytest backend/tests/test_merge.py -v
```
Expected: 2 passed

- [ ] **Step 5: 提交**

```powershell
git add backend/data_tools/merge_dataset.py backend/tests/test_merge.py
git commit -m "feat(data): merge crawled and personal datasets with resize + dedup"
```

---

## Task 9: 实现 `data_tools/blip_caption.py` — BLIP 自动打标

**Files:**
- Create: `backend/data_tools/blip_caption.py`
- Create: `backend/tests/test_blip_caption.py`

- [ ] **Step 1: 写失败测试(只测纯函数)**

Create `backend/tests/test_blip_caption.py`:

```python
"""测试 caption 拼接逻辑(不真实加载 BLIP 模型)"""
from backend.data_tools.blip_caption import build_full_caption


def test_build_caption_prefixes_trigger():
    cap = build_full_caption("musangking durian", "a fruit on a table")
    assert cap.startswith("musangking durian")
    assert "a fruit on a table" in cap
    assert "high quality" in cap


def test_build_caption_no_double_period():
    cap = build_full_caption("musangking durian", "a fruit.")
    assert cap.count("..") == 0
```

- [ ] **Step 2: 运行测试确认失败**

```powershell
python -m pytest backend/tests/test_blip_caption.py -v
```

- [ ] **Step 3: 实现 blip_caption.py**

Create `backend/data_tools/blip_caption.py`:

```python
"""BLIP 自动给训练图打英文 caption,并拼接品种触发词"""
import argparse
import csv
import logging
from pathlib import Path

from backend.configs.loader import load_varieties, load_paths

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")


def build_full_caption(trigger: str, blip_text: str) -> str:
    """拼接最终 caption: <触发词>, <BLIP 文本>, high quality, detailed"""
    blip_text = blip_text.strip().rstrip(".")
    return f"{trigger}, {blip_text}, high quality, detailed"


def caption_directory(variety: str, dir_path: Path,
                      model_id: str = "Salesforce/blip-image-captioning-large") -> int:
    """对目录中所有图打 caption,生成同名 .txt 文件 + 汇总 captions.csv"""
    try:
        import torch
        from PIL import Image
        from transformers import BlipProcessor, BlipForConditionalGeneration
    except ImportError as e:
        raise RuntimeError(f"缺少依赖: {e}")

    varieties = load_varieties()
    trigger = varieties[variety]["trigger"]
    device = "cuda" if torch.cuda.is_available() else "cpu"

    logger.info(f"加载 BLIP 模型 {model_id} 到 {device}")
    processor = BlipProcessor.from_pretrained(model_id)
    model = BlipForConditionalGeneration.from_pretrained(model_id).to(device)
    model.eval()

    dir_path = Path(dir_path)
    image_files = sorted(
        [p for p in dir_path.iterdir()
         if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")]
    )

    captions_csv = dir_path / "captions.csv"
    count = 0
    with open(captions_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["image", "blip_text", "final_caption"])
        for img_path in image_files:
            try:
                image = Image.open(img_path).convert("RGB")
                inputs = processor(image, return_tensors="pt").to(device)
                with torch.no_grad():
                    out = model.generate(**inputs, max_length=50, num_beams=4)
                blip_text = processor.decode(out[0], skip_special_tokens=True)
                final = build_full_caption(trigger, blip_text)
                # 写同名 .txt
                txt_path = img_path.with_suffix(".txt")
                txt_path.write_text(final, encoding="utf-8")
                writer.writerow([img_path.name, blip_text, final])
                count += 1
                if count % 10 == 0:
                    logger.info(f"已处理 {count}/{len(image_files)}")
            except Exception as e:
                logger.warning(f"caption 失败 {img_path}: {e}")

    logger.info(f"完成: {count} 张图打标,汇总写入 {captions_csv}")
    return count


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--variety", required=True)
    parser.add_argument("--dir", type=Path, default=None)
    args = parser.parse_args()

    paths = load_paths()
    dir_path = args.dir or (paths["training"] / args.variety)
    caption_directory(args.variety, dir_path)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 运行测试通过**

```powershell
python -m pytest backend/tests/test_blip_caption.py -v
```
Expected: 2 passed

- [ ] **Step 5: Smoke 测试(下载 BLIP 模型,可能要 5 分钟)**

```powershell
conda activate durian
python -m backend.data_tools.blip_caption --variety musang_king
```
Expected: 训练目录里每张图旁边出现同名 `.txt` 文件,内容形如:
`musangking durian, a close up of a durian fruit on a wooden table, high quality, detailed`

- [ ] **Step 6: 提交**

```powershell
git add backend/data_tools/blip_caption.py backend/tests/test_blip_caption.py
git commit -m "feat(data): add BLIP auto-captioning with trigger word prefix"
```

---

## Task 10: 写数据流水线一键脚本

**Files:**
- Create: `scripts/prepare_dataset.ps1`

- [ ] **Step 1: 写脚本**

Create `scripts/prepare_dataset.ps1`:

```powershell
# 一键完成数据准备流水线
# 用法: powershell scripts/prepare_dataset.ps1 -Variety musang_king -CrawlNum 50

param(
    [Parameter(Mandatory=$true)][string]$Variety,
    [int]$CrawlNum = 50,
    [switch]$SkipCrawl,
    [switch]$SkipCaption
)

$ErrorActionPreference = "Stop"

Write-Host "==> 品种: $Variety" -ForegroundColor Cyan

if (-not $SkipCrawl) {
    Write-Host "==> [1/4] 爬取图像" -ForegroundColor Cyan
    conda run -n durian python -m backend.data_tools.scraper --variety $Variety --num $CrawlNum
}

Write-Host "==> [2/4] 自动筛选" -ForegroundColor Cyan
conda run -n durian python -m backend.data_tools.filter --variety $Variety

Write-Host "==> [3/4] 合并爬虫 + 个人数据" -ForegroundColor Cyan
conda run -n durian python -m backend.data_tools.merge_dataset --variety $Variety

if (-not $SkipCaption) {
    Write-Host "==> [4/4] BLIP 自动打标" -ForegroundColor Cyan
    conda run -n durian python -m backend.data_tools.blip_caption --variety $Variety
}

Write-Host ""
Write-Host "==> 完成! 训练数据在 D:/durian-data/training/$Variety/" -ForegroundColor Green
Write-Host "==> 提示: 可手工浏览 captions.csv 校正个别 caption" -ForegroundColor Yellow
```

- [ ] **Step 2: 提交**

```powershell
git add scripts/prepare_dataset.ps1
git commit -m "feat(scripts): add one-shot dataset preparation pipeline"
```

---

## Task 11: 补全 `docs/data-collection.md`

**Files:**
- Modify: `docs/data-collection.md`

- [ ] **Step 1: 写文档**

Replace `docs/data-collection.md` content:

````markdown
# 数据收集与标注指南

## 1. 概览

本指南覆盖从原始图像采集到 BLIP 自动打标的完整流程。
目标:每个品种 30-80 张高质量训练图。

数据存放位置:`D:/durian-data/`(项目外,不入 git)

```
D:/durian-data/
├── raw/<variety>/           # 爬虫原始下载
├── candidates/<variety>/    # 自动筛选通过的
├── personal/<variety>/      # 你自己收集的图(手动放入)
├── training/<variety>/      # 最终训练数据 + .txt caption
```

## 2. 品种与触发词

| 品种 ID | 触发词 (caption 前缀) | 中文 |
|---|---|---|
| musang_king | `musangking durian` | 猫山王 |
| monthong | `monthong durian` | 金枕头 |
| blackthorn | `blackthorn durian` | 黑刺王 |
| red_prawn | `redprawn durian` | 红虾 |

## 3. 一键流程

```powershell
# 处理一个品种(自动爬虫 50 张 + 过滤 + 合并 + BLIP 打标)
powershell scripts/prepare_dataset.ps1 -Variety musang_king -CrawlNum 50

# 只重跑后面几步(不爬)
powershell scripts/prepare_dataset.ps1 -Variety musang_king -SkipCrawl
```

## 4. 加入你自己的数据

把你的图放到 `D:/durian-data/personal/<variety>/`,任何格式(jpg/png/webp),任意尺寸都行。
脚本会自动 resize 短边到 512、去重、加入训练集。

文件名建议含品种英文(便于排查),例如:
`musang_king_my_001.jpg`、`monthong_kitchen_a.png`

## 5. 分步使用

```powershell
# 仅爬
python -m backend.data_tools.scraper --variety musang_king --num 50

# 仅筛选
python -m backend.data_tools.filter --variety musang_king

# 仅合并
python -m backend.data_tools.merge_dataset --variety musang_king

# 仅打标
python -m backend.data_tools.blip_caption --variety musang_king
```

## 6. 人工检查 (可选, 推荐)

打开 `D:/durian-data/training/<variety>/captions.csv`,浏览自动生成的 caption。
BLIP 偶尔把榴莲错认为菠萝/西瓜,可直接编辑对应 `.txt` 文件修正。
品种触发词永远在 caption 最前面,即使 BLIP 误判,触发词也能引导 LoRA 学到品种特征。

## 7. 数据集大小建议

- **最低能用**: 20 张/品种
- **推荐**: 50 张/品种
- **质量上限**: 80 张/品种(再多收益递减)

## 8. 版权与合规

- 本项目仅用于学术、毕业作业、技术演示
- 爬虫优先使用 CC0/CC-BY 协议图源(Bing 已自带过滤)
- 不商用、不传播、不二次分发训练数据
- 在前端"关于"页明示数据来源
````

- [ ] **Step 2: 提交**

```powershell
git add docs/data-collection.md
git commit -m "docs: complete data collection guide"
```

**M2 验收:**
- [ ] `D:/durian-data/training/musang_king/` 有 ≥ 10 张图,每张配 `.txt`
- [ ] `captions.csv` 文件存在,内容合理
- [ ] `python -m pytest backend/tests/ -v` 全过

---

# 🎓 M3: 训练 + 本地推理

## Task 12: 适配现有 `lora_trainer.py` 兼容新路径配置

**Files:**
- Modify: `backend/lora_trainer.py`(读 paths.yaml,接受新命令行参数)
- Create: `backend/tests/test_lora_trainer.py`(只测纯函数)

- [ ] **Step 1: 写测试**

Create `backend/tests/test_lora_trainer.py`:

```python
"""测试训练辅助函数"""
from backend.lora_trainer import resolve_output_dir, resolve_data_dir
from pathlib import Path


def test_resolve_data_dir_from_variety(tmp_path, monkeypatch):
    paths = {"training": tmp_path}
    (tmp_path / "musang_king").mkdir()
    result = resolve_data_dir("musang_king", None, paths)
    assert result == tmp_path / "musang_king"


def test_resolve_data_dir_explicit_override(tmp_path):
    explicit = tmp_path / "custom"
    explicit.mkdir()
    paths = {"training": tmp_path / "default"}
    result = resolve_data_dir("musang_king", explicit, paths)
    assert result == explicit
```

- [ ] **Step 2: 修改 `lora_trainer.py` 的 main()**

在 `backend/lora_trainer.py` 文件末尾(原 main 函数处)替换为:

```python
def resolve_data_dir(variety: str, override: Path, paths: dict) -> Path:
    if override:
        return Path(override)
    return paths["training"] / variety


def resolve_output_dir(variety: str, override: Path, paths: dict) -> Path:
    if override:
        return Path(override)
    return paths["models_lora"] / variety


def main():
    import argparse
    from backend.configs.loader import load_paths, load_training_defaults

    defaults = load_training_defaults()
    paths = load_paths()

    parser = argparse.ArgumentParser()
    parser.add_argument("--variety", required=True)
    parser.add_argument("--data_dir", type=Path, default=None)
    parser.add_argument("--output_dir", type=Path, default=None)
    parser.add_argument("--epochs", type=int, default=defaults["epochs"])
    parser.add_argument("--rank", type=int, default=defaults["rank"])
    parser.add_argument("--learning_rate", type=float, default=defaults["learning_rate"])
    parser.add_argument("--resolution", type=int, default=defaults["resolution"])
    parser.add_argument("--mixed_precision", default=defaults["mixed_precision"])
    parser.add_argument("--base_model", default=defaults["base_model"])
    args = parser.parse_args()

    data_dir = resolve_data_dir(args.variety, args.data_dir, paths)
    output_dir = resolve_output_dir(args.variety, args.output_dir, paths)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 使用既有的训练入口函数(注意保留原有训练循环)
    # 假设原文件有 train_lora() 函数;若没有,在此调用 LoRATrainer 类
    from backend.lora_trainer import LoRATrainer  # 利用现有类
    trainer = LoRATrainer(
        base_model=args.base_model,
        rank=args.rank,
        alpha=defaults["alpha"],
        learning_rate=args.learning_rate,
        mixed_precision=args.mixed_precision,
    )
    trainer.train(
        data_dir=str(data_dir),
        instance_prompt=load_varieties_trigger(args.variety),
        output_dir=str(output_dir),
        num_epochs=args.epochs,
        resolution=args.resolution,
    )


def load_varieties_trigger(variety: str) -> str:
    from backend.configs.loader import load_varieties
    return load_varieties()[variety]["trigger"]


if __name__ == "__main__":
    main()
```

> 注意:`LoRATrainer` 类如果原文件中没有,需保留原文件中的训练循环逻辑,只替换 main 入口。
> 此 Task 假设原 `lora_trainer.py` 提供了某个可调用类/函数;如果原文件结构是过程式的,请把训练循环包成 `LoRATrainer` 类,接口签名同上。

- [ ] **Step 3: 运行测试**

```powershell
python -m pytest backend/tests/test_lora_trainer.py -v
```
Expected: 2 passed

- [ ] **Step 4: 提交**

```powershell
git add backend/lora_trainer.py backend/tests/test_lora_trainer.py
git commit -m "refactor(train): integrate lora_trainer with paths.yaml + new CLI"
```

---

## Task 13: 真实训练一个品种(smoke)

**Files:** 无新文件,只是运行训练

- [ ] **Step 1: 检查训练数据**

```powershell
ls "D:/durian-data/training/musang_king/" | Measure-Object
```
Expected: 至少 10 张 jpg + 10 个 txt + captions.csv

- [ ] **Step 2: 启动训练**

```powershell
conda activate durian
cd "D:/谷歌下载/Kimi_Agent_榴莲图像生成代码"
python -m backend.lora_trainer --variety musang_king --epochs 50 --rank 16
```
Expected:
- 5070 GPU 占用 ~9GB
- 训练进度条逐 epoch 推进
- 25-40 分钟后完成
- `D:/durian-data/models/lora/musang_king/pytorch_lora_weights.safetensors` 生成

如果 OOM,降 batch_size 或 rank。
如果模型下载慢,设置 `set HF_ENDPOINT=https://hf-mirror.com` 再跑。

- [ ] **Step 3: 验证权重文件**

```powershell
Get-ChildItem "D:/durian-data/models/lora/musang_king/" -Recurse
```
Expected: 至少看到 `pytorch_lora_weights.safetensors`,大小 ~30MB

- [ ] **Step 4: 提交(只记录 checkpoint 元信息,权重本身被 gitignore)**

```powershell
# 训练产物在 D:/durian-data/,不入库;不需要 commit
# 但可以写一个训练日志:
echo "Trained musang_king on $(date), 50 epochs, rank=16" >> docs/training-log.md
git add docs/training-log.md
git commit -m "chore: log first successful LoRA training (musang_king)"
```

---

## Task 14: 实现 `local_inference.py`

**Files:**
- Create: `backend/local_inference.py`
- Create: `backend/tests/test_local_inference.py`

- [ ] **Step 1: 写测试**

Create `backend/tests/test_local_inference.py`:

```python
"""测试本地推理脚本的辅助函数"""
from backend.local_inference import inject_trigger, build_output_name


def test_inject_trigger_prefixes():
    out = inject_trigger("musangking durian", "on a table")
    assert out.startswith("musangking durian")
    assert "on a table" in out


def test_inject_trigger_idempotent_if_already_present():
    out = inject_trigger("musangking durian", "musangking durian, on a table")
    # 不要重复加触发词
    assert out.count("musangking durian") == 1


def test_build_output_name_format():
    name = build_output_name("musang_king", 12345, 0)
    assert "musang_king" in name
    assert "12345" in name
    assert name.endswith("_0.png")
```

- [ ] **Step 2: 实现 local_inference.py**

Create `backend/local_inference.py`:

```python
"""本地快速推理 - 加载基础 SD + LoRA,3 秒/张"""
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from backend.configs.loader import load_paths, load_varieties

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")


def inject_trigger(trigger: str, user_prompt: str) -> str:
    if trigger.lower() in user_prompt.lower():
        return user_prompt
    return f"{trigger}, {user_prompt}"


def build_output_name(variety: str, seed: int, idx: int) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{variety}_{ts}_{seed}_{idx}.png"


def generate(variety: str, user_prompt: str, num_images: int = 1,
             steps: int = 30, cfg: float = 7.5, seed: Optional[int] = None,
             width: int = 512, height: int = 512,
             negative: str = "blurry, low quality, distorted, deformed",
             output_dir: Optional[Path] = None):
    import torch
    from diffusers import StableDiffusionPipeline, EulerAncestralDiscreteScheduler

    paths = load_paths()
    varieties = load_varieties()
    if variety not in varieties:
        raise ValueError(f"未知品种: {variety}")
    trigger = varieties[variety]["trigger"]

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32

    logger.info(f"加载基础模型到 {device}")
    pipe = StableDiffusionPipeline.from_pretrained(
        "runwayml/stable-diffusion-v1-5",
        torch_dtype=dtype,
        safety_checker=None,
        requires_safety_checker=False,
    ).to(device)
    pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(pipe.scheduler.config)

    # 加载 LoRA
    lora_dir = paths["models_lora"] / variety
    if not lora_dir.exists():
        raise FileNotFoundError(f"找不到 LoRA: {lora_dir}")
    logger.info(f"加载 LoRA: {lora_dir}")
    pipe.load_lora_weights(str(lora_dir))

    if device == "cuda":
        pipe.enable_attention_slicing()

    full_prompt = inject_trigger(trigger, user_prompt)
    logger.info(f"Prompt: {full_prompt}")

    if seed is None:
        import random
        seed = random.randint(0, 2**31)
    generator = torch.Generator(device=device).manual_seed(seed)

    result = pipe(
        prompt=full_prompt,
        negative_prompt=negative,
        num_inference_steps=steps,
        guidance_scale=cfg,
        width=width, height=height,
        num_images_per_prompt=num_images,
        generator=generator,
    )

    output_dir = Path(output_dir) if output_dir else paths["outputs"] / variety
    output_dir.mkdir(parents=True, exist_ok=True)

    saved = []
    for i, img in enumerate(result.images):
        out_path = output_dir / build_output_name(variety, seed, i)
        img.save(out_path)
        saved.append(out_path)
        logger.info(f"保存: {out_path}")
    return saved


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--variety", required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--negative", default="blurry, low quality, distorted, deformed")
    parser.add_argument("--num", type=int, default=1)
    parser.add_argument("--steps", type=int, default=30)
    parser.add_argument("--cfg", type=float, default=7.5)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--width", type=int, default=512)
    parser.add_argument("--height", type=int, default=512)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    generate(args.variety, args.prompt, args.num, args.steps, args.cfg,
             args.seed, args.width, args.height, args.negative, args.output)


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: 运行测试**

```powershell
python -m pytest backend/tests/test_local_inference.py -v
```
Expected: 3 passed

- [ ] **Step 4: Smoke 测试 — 真实生成 4 张图**

```powershell
conda activate durian
python -m backend.local_inference --variety musang_king --prompt "on a wooden table, soft light" --num 4
```
Expected:
- 单张 ~3 秒
- `D:/durian-data/outputs/musang_king/` 出现 4 张 PNG
- 图像主体确实是榴莲(开头几次可能效果一般,看 LoRA 训得怎么样)

- [ ] **Step 5: 提交**

```powershell
git add backend/local_inference.py backend/tests/test_local_inference.py
git commit -m "feat(infer): local inference script with LoRA + trigger injection"
```

---

## Task 15: 补全 `docs/training.md`

**Files:**
- Modify: `docs/training.md`

- [ ] **Step 1: 写文档**

Replace `docs/training.md`:

````markdown
# 训练指南

## 1. 前置

- 已完成 M1 环境安装 (`scripts/setup_train_env.ps1`)
- 已为目标品种准备好训练数据 (`D:/durian-data/training/<variety>/`)
- 已安装 RTX 5070 (12GB) 显卡

## 2. 基本训练

```powershell
conda activate durian
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
````

- [ ] **Step 2: 提交**

```powershell
git add docs/training.md
git commit -m "docs: complete training guide"
```

**M3 验收:**
- [ ] 至少 1 个品种 LoRA 训练完成
- [ ] `local_inference.py` 能产出可识别的榴莲图
- [ ] 单张 < 5 秒

---

# 🔧 M4: 模型导出 + 服务器后端

> M4-M5 内容写在第二份文件 `2026-06-22-durian-aigc-implementation-part2.md`(由于长度限制)。
> 见同目录下 part2.md。
