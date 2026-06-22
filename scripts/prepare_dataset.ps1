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
    conda run -n sd_lora python -m backend.data_tools.scraper --variety $Variety --num $CrawlNum
}

Write-Host "==> [2/4] 自动筛选" -ForegroundColor Cyan
conda run -n sd_lora python -m backend.data_tools.filter --variety $Variety

Write-Host "==> [3/4] 合并爬虫 + 个人数据" -ForegroundColor Cyan
conda run -n sd_lora python -m backend.data_tools.merge_dataset --variety $Variety

if (-not $SkipCaption) {
    Write-Host "==> [4/4] BLIP 自动打标" -ForegroundColor Cyan
    conda run -n sd_lora python -m backend.data_tools.blip_caption --variety $Variety
}

Write-Host ""
Write-Host "==> 完成! 训练数据在 D:/durian-data/training/$Variety/" -ForegroundColor Green
Write-Host "==> 提示: 可手工浏览 captions.csv 校正个别 caption" -ForegroundColor Yellow
