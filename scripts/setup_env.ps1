# Environment patch script - install missing packages into existing sd_lora env
# Usage: powershell -ExecutionPolicy Bypass -File scripts/setup_env.ps1

Write-Host "==> Installing missing packages into sd_lora" -ForegroundColor Cyan

# Backend / inference deps
conda run -n sd_lora pip install fastapi "uvicorn[standard]" pydantic aiofiles loguru imagehash icrawler

# OpenVINO deps
conda run -n sd_lora pip install "optimum[openvino]>=1.20.0" openvino

# Testing deps
conda run -n sd_lora pip install pytest pytest-asyncio

Write-Host ""
Write-Host "==> Verifying environment" -ForegroundColor Cyan
conda run -n sd_lora python -c "import torch; print('PyTorch:', torch.__version__); print('CUDA:', torch.cuda.is_available()); print('Device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')"
conda run -n sd_lora python -c "import diffusers, peft, fastapi, openvino; print('All key packages imported successfully')"

Write-Host ""
Write-Host "==> Done! Activate with: conda activate sd_lora" -ForegroundColor Green
