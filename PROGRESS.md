# PROGRESS — 榴莲 AIGC 项目

> 本文件用于跨会话快速恢复上下文。最新更新:2026-06-25

## 🚨 当前部署断点(服务器生成失败修复中)

**当前状态**:
- ✅ 服务器 Docker 镜像已成功构建:`durian-aigc:latest`
- ✅ 构建期自检通过:`OK: OVStableDiffusionPipeline`
- ✅ 容器已成功启动并可生成图片
- ✅ `/api/health` 和 `/api/varieties` 正常返回 3 个品种
- ✅ 端口映射正常:`0.0.0.0:8008->8000/tcp`
- ✅ OpenVINO Diffusers / optimum-intel / nncf 依赖链已修复并验证
- ✅ 前端已固定白底特写场景,隐藏英文 prompt,按钮改为「开始生成」

**已遇到并解决的服务器错误链**:
1. Docker Hub 超时:`python:3.11-slim` pull 超时 → 通过 Docker registry mirror 解决
2. 生成时 import 失败:`Could not import module 'OVStableDiffusionPipeline'`
3. 依赖冲突:`openvino==2024.4.0` 与 `optimum-intel[openvino]==1.20.0` 冲突 → 移除单独 openvino pin
4. 构建期失败:`cannot import name 'NNCFConfig' from 'nncf'` → 新增 `nncf==2.14.1`
5. Docker BuildKit 导出镜像阶段 EOF → 不加 `--no-cache` 重试构建,利用缓存成功导出镜像

**服务器已成功运行,后续维护方式**:

```bash
cd /opt/durian

# 查看状态
docker compose ps

# 查看日志
docker compose logs -f --tail 100 durian-api

# 仅重启服务(不重建镜像)
docker compose restart durian-api

# 停止/启动
docker compose down
docker compose up -d
```

**重要约定**:
- 下一次只改前端静态页面/文案/样式时,通常不需要重新构建镜像。
- 用 XFTP 覆盖 `/opt/durian/frontend/dist/` 后,优先尝试浏览器 `Ctrl+F5` 强刷;如仍旧页面,再 `docker compose restart durian-api`。
- 只有修改 `backend/` Python 代码、`backend/requirements-serve.txt`、`backend/Dockerfile`、`docker-compose.yml` 或依赖时,才需要 `docker compose build durian-api`。
- 只有依赖出问题或需要彻底重装 Python 包时,才使用 `docker compose build --no-cache durian-api`。

---

## 当前状态

- **Tag**: `v0.1.0` — 端到端可运行(本地三品种已验证 ✅)
- **分支**: `master`
- **Remote**: ✅ https://github.com/Wangtaotao-best/durian_auto_images
- **Working tree**: clean
- **累计 commits**: 30(+ 1 在 6/24)

## 已完成

- [x] **M1** 仓库结构 + sd_lora 环境(复用,不新建 durian)
- [x] **M2** 数据流水线(scraper/filter/merge/blip_caption + 一键 prepare_dataset.ps1)
- [x] **M3** 训练代码适配 paths.yaml + 本地推理脚本(`local_inference.py`,~3 秒/张)
- [x] **M4** OpenVINO 模型导出(1.3GB 包)+ FastAPI 后端(/api/generate, /api/tasks, 任务队列)
- [x] **M5** 前端 `Generator` section 嵌入(保留现有深色展示页)+ Docker 配置 + 部署脚本
- [x] **2026-06-24** 用户自有数据集训练 3 品种 LoRA(共 149 张图)
- [x] **2026-06-24** 后端添加 `DURIAN_BACKEND_MODE=lora` 分支,支持本地 GPU LoRA 直跑(浏览器端到端验证 ✅)
- [x] **2026-06-24** 前端 v0.3.0:移除 Workflow/DurianGallery/DatasetStats/Footer 装饰板块、改中文 8 个场景模板、按钮文字调整
- [x] **2026-06-24** GitHub 仓库初始化并推送(`Wangtaotao-best/durian_auto_images`)
- [x] **2026-06-24** 3 品种导出 OpenVINO IR + 打包(各 ~2.15 GB)
- [x] **2026-06-24** 3 个 tar.gz 上传到服务器 `/opt/durian_bundles/`
- [x] **2026-06-24** Docker 数据迁移到 `/opt/docker-data`(/ 分区 100% → 355 GB 可用)
- [x] **2026-06-24** 部署脚本前 4 步成功(目录、解压、.env 生成、端口 8008 就位)
- [x] **2026-06-25** 服务器容器已启动,`/api/health` 和 `/api/varieties` 正常返回 3 品种
- [x] **2026-06-25** 前端 footer 调整:移除「仅供学术演示」与 GitHub 链接,增加「开发人: 寒鸣」
- [x] **2026-06-25** 生成器场景固定为白底特写:隐藏英文 prompt,按钮改为「开始生成」,减少与训练集不一致导致的不稳定
- [x] **2026-06-25** 服务器镜像 `durian-aigc:latest` 成功构建,`OVStableDiffusionPipeline` 自检通过,容器已启动并成功生成图片
- [ ] **2026-06-25** 后续功能修改优先覆盖 `frontend/dist/` 或重启容器,一般不需要重新构建镜像

## 关键产物路径

| 产物 | 路径 |
|---|---|
| 训练好的 LoRA(3 品种) | `D:/durian-data/models/lora/{blackthorn,monthong,musang_king}/`(各 ~13 MB) |
| 训练 checkpoints 备份 | `D:/durian-data/models/lora/{品种}_checkpoints/` |
| 旧版 musang_king LoRA | `D:/durian-data/models/lora/musang_king_old_backup/` |
| 训练数据 + caption | `D:/durian-data/training/{品种}/` |
| 原始个人数据 | `D:/durian-data/personal/{品种}/` |
| 本地推理示例 | `D:/durian-data/outputs/{品种}/*.png` |
| OpenVINO IR(旧版 musang_king) | `D:/durian-data/models/openvino/musang_king_old_backup/` |
| 旧部署包 | `D:/durian-data/musang_king_openvino.tar.gz`(待用新版重做) |

## 三品种训练成果

| 品种 | 训练数据 | Final Loss | Epochs | LoRA 大小 | 本地推理 |
|---|---|---|---|---|---|
| blackthorn | 45 张 | 0.1248 | 50 | 13 MB | ~3 秒/张 ✅ |
| monthong | 41 张 | 0.1840 | 50 | 13 MB | ~3 秒/张 ✅ |
| musang_king | 63 张 | 0.1412 | 50 | 13 MB | ~3 秒/张 ✅ |

## 验证状态

| 项 | 结果 |
|---|---|
| 28 个 Python 单元测试 | ✅ 全过 |
| 三品种本地 LoRA 推理 smoke | ✅ ~3 秒/张, RTX 5070 |
| OpenVINO 导出(旧 musang_king) | ✅ 4 对 .xml/.bin |
| FastAPI 启动(LoRA 模式) | ✅ 加载 3 品种,健康检查 OK |
| 浏览器端到端(LoRA 模式) | ✅ 用户验证满意 |
| OpenVINO 导出(新 3 品种) | ⏭ 待办 |
| Docker 镜像本地构建 | ⏭ 跳过(本机无 Docker) |
| 服务器部署 | ⏭ 待办 |

## 待办

- [x] **服务器首件**:上传/覆盖 `backend/requirements-serve.txt` 与 `backend/Dockerfile`,执行 `docker compose build --no-cache durian-api`,确认出现 `OK: OVStableDiffusionPipeline`
- [x] 构建成功后启动容器,网页实际生成 1 张图验证
- [x] 新版 `frontend/dist/` 已随镜像构建生效,footer 显示「开发人: 寒鸣」且不显示 GitHub,生成器只显示固定「白底特写」场景
- [ ] 开防火墙 8008 + 云控制台安全组(若公网仍无法访问)
- [ ] 浏览器从公网 IP 测试出图
- [ ] (可选)清理 `/var/lib/docker.old.bak` 备份(确认稳定 1 周后)
- [ ] (可选)改造 DurianGallery / DatasetStats 显示真实数据
- [ ] (可选)前端展示页其它板块(Hero/Workflow/TechStack)按真实情况调整文案

## 风险 & 注意事项

- **RTX 5070 兼容性**:必须用 PyTorch nightly cu128;现有 `sd_lora` 环境已配好
- **PEFT LoRA 加载**:用 `PeftModel.from_pretrained(pipe.unet, lora_dir)`,不是 `pipe.load_lora_weights()`
- **`merge_lora.py` 双格式**:自动检测 PEFT vs Diffusers 原生(LCM-LoRA 是后者)
- **服务器单 worker**:`uvicorn --workers 1`,不要改大
- **路径含中文**:数据/模型必须放 `D:/durian-data/`
- **训练产物嵌套路径**:`lora_trainer.py` 会产出 `<output_dir>/<variety>/checkpoint-final/`,**部署前**需把 `checkpoint-final/` 的内容上提到 `<output_dir>/`(已在 6/24 处理 3 品种)
- **BLIP 模型已本地缓存**:`C:/Users/wangt/.cache/huggingface/hub/models--Salesforce--blip-image-captioning-large/`
- **数据合规**:训练数据仅学术演示用

## 关键工程决策

1. 复用 `sd_lora` conda 环境,不新建 `durian`
2. Docker 本地不构建,只交付配置文件
3. 前端:保留现有 6 个 sections,**新增** `Generator` section
4. 后端双模式:`DURIAN_BACKEND_MODE=openvino`(默认,生产)/`lora`(本地 GPU 验证)
5. 三品种统一扁平化:LoRA 产物上提到 `models/lora/<variety>/` 下

## 前端展示页 — 各板块真实状态(2026-06-24 澄清)

| 板块 | 真实功能 | 备注 |
|---|---|---|
| Hero | ❌ 装饰 | 滚动锚点 |
| **Generator** | ✅ **真实(`/api/*`)** | 唯一能真生成图的板块 |
| TechStack | ❌ 静态展示 | 技术栈介绍 |
| Workflow | ❌ 装饰 | 流程图卡片,无交互 |
| DurianGallery | ❌ 装饰 + 假图 | 品种介绍,public/durian_images 可能 404 |
| DatasetStats | ❌ 假数据 | 数字是设计稿值 |
| Footer | ❌ 静态 | 链接和版权 |

## 后端运行命令(本地验证 LoRA 模式)

```powershell
# 终端 1: 后端
cd "D:/谷歌下载/Kimi_Agent_榴莲图像生成代码"
$env:DURIAN_BACKEND_MODE = "lora"
conda run -n sd_lora python -m uvicorn backend.serve.app:app --host 127.0.0.1 --port 8000

# 终端 2: 前端 dev
cd "D:/谷歌下载/Kimi_Agent_榴莲图像生成代码/frontend"
npm run dev
# 浏览器: http://localhost:5173
```

服务器部署(OpenVINO 模式)走默认:不设 `DURIAN_BACKEND_MODE`,通过 docker-compose 启动。

## 文档索引

- 设计:`docs/superpowers/specs/2026-06-22-durian-aigc-design.md`
- 实施计划 Part 1:`docs/superpowers/plans/2026-06-22-durian-aigc-implementation.md`
- 实施计划 Part 2:`docs/superpowers/plans/2026-06-22-durian-aigc-implementation-part2.md`
- 执行偏差表:`docs/superpowers/plans/execution-context.md`
- 数据收集:`docs/data-collection.md`
- 训练:`docs/training.md`
- 部署:`docs/deployment.md`
- 训练日志:`docs/training-log.md`

## 下次会话恢复 prompt

```
请读取 PROGRESS.md、README.md、docs/superpowers/plans/execution-context.md,
检查 git log --oneline -10 和 git status,恢复上下文。
先总结当前状态,不要立刻改代码。
```
