# PROGRESS — 榴莲 AIGC 项目

> 本文件用于跨会话快速恢复上下文。最新更新:2026-06-22

## 当前状态

- **Tag**: `v0.1.0` — 端到端可运行(本地)/ 待部署(服务器)
- **分支**: `master`
- **远程**: 未配置(纯本地)
- **Working tree**: clean
- **累计 commits**: 28(从 `1dbb4dc initial` 到 `01549fb`)

## 已完成

- [x] **M1** 仓库结构 + sd_lora 环境(复用,不新建 durian)
- [x] **M2** 数据流水线(scraper/filter/merge/blip_caption + 一键 prepare_dataset.ps1)
- [x] **M3** 训练代码适配 paths.yaml + 本地推理脚本(`local_inference.py`,~4 秒/张)
- [x] **M4** OpenVINO 模型导出(1.3GB 包)+ FastAPI 后端(/api/generate, /api/tasks, 任务队列)
- [x] **M5** 前端 `Generator` section 嵌入(保留现有深色展示页)+ Docker 配置 + 部署脚本

## 关键产物路径

| 产物 | 路径 |
|---|---|
| 训练好的 LoRA | `D:/durian-data/models/lora/musang_king/` (~13 MB) |
| 合并后 SD pipeline | `D:/durian-data/models/merged/musang_king[_lcm]/` |
| OpenVINO IR | `D:/durian-data/models/openvino/musang_king/` (4 对 .xml/.bin) |
| 部署包 | `D:/durian-data/musang_king_openvino.tar.gz` (~1.3 GB) |
| 本地推理示例 | `D:/durian-data/outputs/musang_king/*.png` |

## 验证状态

| 项 | 结果 |
|---|---|
| 28 个 Python 单元测试 | ✅ 全过 (`pytest backend/tests/ -v`) |
| 本地 LoRA 推理 smoke | ✅ ~4 秒/张, RTX 5070, 图像可识别为榴莲 |
| OpenVINO 导出 smoke | ✅ 4 对 .xml/.bin 全部生成 |
| FastAPI 启动 smoke | ✅ `/api/health` → `{"status":"ok","varieties":["musang_king"]}` |
| 前端 build smoke | ✅ 1775 modules, 328KB JS, 0 errors |
| Docker 镜像本地构建 | ⏭ 跳过(按 execution-context.md §2,本地无 Docker)|
| 浏览器端到端真实点击生成 | ⏭ 未在本会话验证(交给用户手动验)|
| 服务器部署 | ⏭ 未做(交给用户 scp + ssh)|

## 待办

- [ ] 在本地浏览器实际点 Generate,验证完整 UX(8-15s 出图,真实进度条)
- [ ] 服务器 scp 模型包 + 代码,跑 `scripts/deploy_to_server.sh`
- [ ] 训练其他 3 个品种(monthong / blackthorn / red_prawn)
- [ ] 可选:配置远程 git 仓库(GitHub / GitLab)并 push

## 风险 & 注意事项

- **RTX 5070 兼容性**:必须用 PyTorch nightly cu128;现有 `sd_lora` 环境已配好(`torch 2.12.0.dev cu128`)
- **PEFT LoRA 加载**:现有 LoRA 是 PEFT 原生格式(adapter_model.safetensors + adapter_config.json),加载用 `PeftModel.from_pretrained(pipe.unet, lora_dir).merge_and_unload()`,**不是** `pipe.load_lora_weights()`
- **`merge_lora.py` 双格式**:自动检测 `adapter_config.json` 决定走 PEFT 还是 Diffusers 路径(LCM-LoRA 是 Diffusers 原生格式)
- **服务器单 worker**:`docker-compose.yml` 已限制 `uvicorn --workers 1`,**不要改大**(每 worker 加载一份模型会爆内存)
- **路径含中文**:项目根目录路径有中文,数据/模型必须放 `D:/durian-data/`(英文盘)
- **数据合规**:训练数据仅学术演示用,不商业、不二次分发

## 关键工程决策

1. 复用 `sd_lora` conda 环境,不新建 `durian`(execution-context.md §1)
2. 训练跳过,复用旧 LoRA(execution-context.md §3)
3. Docker 本地不构建,只交付配置文件(execution-context.md §2)
4. 不爬外网数据 / 不下 BLIP(execution-context.md §4)
5. 前端:保留现有 6 个 sections 不动,**新增** `Generator` section 嵌在 Hero 与 TechStack 之间

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
