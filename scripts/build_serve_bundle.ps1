# 把指定品种的 LoRA -> merge -> LCM -> OpenVINO IR -> tar 打包
# 用法: powershell -ExecutionPolicy Bypass -File scripts/build_serve_bundle.ps1 -Variety musang_king

param(
    [Parameter(Mandatory=$true)][string]$Variety,
    [float]$LoraAlpha = 0.8,
    [string]$BaseModel = "runwayml/stable-diffusion-v1-5",
    [string]$LcmLora = "latent-consistency/lcm-lora-sdv1-5",
    [string]$DataRoot = "D:/durian-data"
)

$ErrorActionPreference = "Stop"

$mergedDir = "$DataRoot/models/merged/$Variety"
$mergedLcmDir = "$DataRoot/models/merged/${Variety}_lcm"
$ovDir = "$DataRoot/models/openvino/$Variety"
$loraDir = "$DataRoot/models/lora/$Variety"

Write-Host "==> [1/4] 合并品种 LoRA 到基础模型" -ForegroundColor Cyan
conda run -n sd_lora python -m backend.tools.merge_lora `
    --base $BaseModel `
    --lora $loraDir `
    --output $mergedDir `
    --alpha $LoraAlpha
if ($LASTEXITCODE -ne 0) { throw "Step 1 failed" }

Write-Host "==> [2/4] 合并 LCM-LoRA" -ForegroundColor Cyan
conda run -n sd_lora python -m backend.tools.merge_lora `
    --base $mergedDir `
    --lora $LcmLora `
    --output $mergedLcmDir `
    --alpha 1.0
if ($LASTEXITCODE -ne 0) { throw "Step 2 failed" }

Write-Host "==> [3/4] 导出 OpenVINO IR" -ForegroundColor Cyan
conda run -n sd_lora python -m backend.tools.export_openvino `
    --model_dir $mergedLcmDir `
    --output $ovDir
if ($LASTEXITCODE -ne 0) { throw "Step 3 failed" }

Write-Host "==> [4/4] 打包 tar.gz" -ForegroundColor Cyan
$bundle = "$DataRoot/${Variety}_openvino.tar.gz"
# 优先用 Windows 自带 tar (System32),它支持 Windows 盘符;避免 Git Bash 的 /usr/bin/tar
$winTar = "$env:SystemRoot/System32/tar.exe"
$tarBin = if (Test-Path $winTar) { $winTar } else { (Get-Command tar -ErrorAction SilentlyContinue).Source }
if (-not $tarBin) { throw "tar.exe not found" }
& $tarBin -czf $bundle -C "$DataRoot/models/openvino" $Variety
if ($LASTEXITCODE -ne 0) { throw "Step 4 failed" }

Write-Host ""
Write-Host "==> 完成! 打包文件: $bundle" -ForegroundColor Green
$sizeMB = [math]::Round((Get-Item $bundle).Length / 1MB, 2)
Write-Host "==> 大小: ${sizeMB} MB"
Write-Host ""
Write-Host "==> 上传到服务器: scp $bundle user@server:/data/durian/models/" -ForegroundColor Yellow
