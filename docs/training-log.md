# 训练记录

## 2026-06-22 — musang_king (复用旧版本)

**操作**: 跳过真实训练,复用项目早期已训练好的 LoRA 权重。

**来源**:
- 原路径: `archive/durian-aigc-old/...`(或 `durian-aigc-code/models/lora/musang_king/checkpoint-final/`,M1 Task 2 已删)
- 现位置: `D:/durian-data/models/lora/musang_king/`

**文件**:
- `adapter_model.safetensors` (13.0 MB)
- `adapter_config.json`
- `README.md`

**Adapter 格式**: PEFT (peft_type: LORA, base_model_class: UNet2DConditionModel, rank=8, alpha=32)

**为什么跳过训练**:
- 时间紧,且已有训过的权重
- 用户在 execution-context.md §3 中明确要求"训练跳过"
- 该 LoRA 由项目前期所训,品种触发词:`musangking durian`

**何时需要重训**:
- 数据集大幅扩充时
- 生成质量明显不达预期时
- 需要新品种时(monthong / blackthorn / red_prawn)
