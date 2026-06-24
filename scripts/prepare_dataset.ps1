# Dataset preparation pipeline (Filter -> Merge -> BLIP caption)
# Usage: powershell scripts/prepare_dataset.ps1 -Variety musang_king -SkipCrawl

param(
    [Parameter(Mandatory=$true)][string]$Variety,
    [int]$CrawlNum = 50,
    [switch]$SkipCrawl,
    [switch]$SkipCaption
)

$ErrorActionPreference = "Stop"

Write-Host "==> Variety: $Variety" -ForegroundColor Cyan

if (-not $SkipCrawl) {
    Write-Host "==> [1/4] Crawl images" -ForegroundColor Cyan
    conda run -n sd_lora python -m backend.data_tools.scraper --variety $Variety --num $CrawlNum
}

Write-Host "==> [2/4] Filter (resolution / ratio / phash dedup)" -ForegroundColor Cyan
conda run -n sd_lora python -m backend.data_tools.filter --variety $Variety

Write-Host "==> [3/4] Merge personal + crawled, resize" -ForegroundColor Cyan
conda run -n sd_lora python -m backend.data_tools.merge_dataset --variety $Variety

if (-not $SkipCaption) {
    Write-Host "==> [4/4] BLIP auto-captioning" -ForegroundColor Cyan
    conda run -n sd_lora python -m backend.data_tools.blip_caption --variety $Variety
}

Write-Host ""
Write-Host "==> Done. Training data: D:/durian-data/training/$Variety/" -ForegroundColor Green
Write-Host "==> Tip: review captions.csv to spot-check labels" -ForegroundColor Yellow