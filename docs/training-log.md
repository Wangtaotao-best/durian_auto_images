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

---

## 2026-06-24 — 用户自有数据集训练 3 品种

**操作**:用户提供 3 品种(blackthorn / monthong / musang_king)共 159 张图,完整训练流水线一次跑完。

**旧版备份**:`musang_king` 旧版 LoRA 备份到 `D:/durian-data/models/lora/musang_king_old_backup/`,旧 OpenVINO 包同样备份。

**数据流水线**:
1. 用户把图按品种放到 `D:/durian-data/personal/{品种}/`
2. `python -m backend.data_tools.merge_dataset --variety <V>` 自动 resize 短边到 512 + pHash 去重
3. `python -m backend.data_tools.blip_caption --variety <V>` BLIP 自动打标,触发词前缀

**训练配置**:默认 paths.yaml(SD1.5 + LoRA rank=8 alpha=32 + 50 epochs + fp16)
**训练硬件**:RTX 5070 12GB

**训练结果**:

| 品种 | 输入 | 去重后 | Final Loss | 训练时间 |
|---|---|---|---|---|
| blackthorn | 46 张 | 45 张 | 0.1248 | ~17 分钟 |
| monthong | 50 张 | 41 张 | 0.1840 | ~14 分钟 |
| musang_king | 63 张 | 63 张 | 0.1412 | ~22 分钟 |
| 合计 | 159 张 | 149 张 | — | ~53 分钟 |

**后处理**:统一扁平化路径(把 `<variety>/<variety>/checkpoint-final/` 内容上提到 `<variety>/`),中间 checkpoint 保留到 `<variety>_checkpoints/`。

**本地验证**:
- 三品种各生成 1 张图(seed=42, "on a wooden table, soft natural light, photorealistic")
- 每张 ~3 秒(30 步, fp16, EulerAncestral)
- 图像主体清晰为对应品种榴莲

**浏览器端到端验证**:
- 临时改后端为 `DURIAN_BACKEND_MODE=lora`(本地 GPU LoRA 直跑)
- 启动 FastAPI + Vite dev server,用户在 http://localhost:5173 测试 Generator section
- 三个品种均可生成,用户验证满意 ✅

**触发词**:
- `blackthorn durian`
- `monthong durian`
- `musangking durian`(注意:无下划线,沿用旧版以保持兼容)
