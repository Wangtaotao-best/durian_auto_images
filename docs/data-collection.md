# 数据收集与标注指南

> **环境提示:** 本文档中的所有命令请在 `sd_lora` conda 环境中执行，即先运行 `conda activate sd_lora` 后再运行各命令。

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
