# PROGRESS — 榴莲 AIGC 项目

> 本文件用于跨会话快速恢复上下文。最新更新:2026-06-24

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

- [ ] 把新训的 3 品种 LoRA 导出为 OpenVINO IR(每品种 ~6 分钟,共 ~20 分钟)
  - 命令:`powershell scripts/build_serve_bundle.ps1 -Variety {blackthorn,monthong,musang_king}`
- [ ] 上传 3 个 tar.gz 到服务器 + 跑 `scripts/deploy_to_server.sh`
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
