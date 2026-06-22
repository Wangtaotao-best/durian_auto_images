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

1. **本地训练环境**: `powershell scripts/setup_env.ps1`
2. **数据准备**: 见 `docs/data-collection.md`
3. **训练**: 见 `docs/training.md`
4. **部署**: 见 `docs/deployment.md`

## 文档

- 设计文档: `docs/superpowers/specs/2026-06-22-durian-aigc-design.md`
- 实施计划: `docs/superpowers/plans/2026-06-22-durian-aigc-implementation.md`
