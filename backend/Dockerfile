# Multi-stage build: base -> deps -> runtime
# Base image: Python 3.11 slim (Debian Bookworm)

FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DURIAN_OV_MODELS_ROOT=/data/models/openvino \
    DURIAN_IMAGES_ROOT=/data/images \
    DURIAN_FRONTEND_DIST=/app/frontend/dist

# OpenVINO system libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        libgomp1 \
        ca-certificates \
        curl \
    && rm -rf /var/lib/apt/lists/*

# ===== Dependencies stage =====
FROM base AS deps

WORKDIR /app

# Install PyTorch CPU first to avoid pulling CUDA
RUN pip install --index-url https://download.pytorch.org/whl/cpu \
    torch==2.4.1 torchvision==0.19.1

COPY backend/requirements-serve.txt /app/requirements-serve.txt
RUN pip install -r /app/requirements-serve.txt

# ===== Runtime stage =====
FROM deps AS runtime

WORKDIR /app

# Copy backend code
COPY backend /app/backend

# (Optional) Copy frontend build artifacts
# If frontend/dist does not exist at build time, this step is skipped
COPY frontend/dist* /app/frontend/dist/

# Create mount points for data
RUN mkdir -p /data/models/openvino /data/images

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/api/health || exit 1

CMD ["uvicorn", "backend.serve.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
