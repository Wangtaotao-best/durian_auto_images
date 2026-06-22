#!/usr/bin/env bash
# 在服务器上一键部署 durian-aigc (Docker)
# 用法:
#   MODELS_BUNDLE=/tmp/musang_king_openvino.tar.gz bash scripts/deploy_to_server.sh
#
# 环境变量:
#   DEPLOY_ROOT      默认 /data/durian
#   MODELS_BUNDLE    OpenVINO 模型 tar.gz 路径 (可选;若不存在则跳过解压)

set -euo pipefail

DEPLOY_ROOT="${DEPLOY_ROOT:-/data/durian}"
MODELS_BUNDLE="${MODELS_BUNDLE:-/tmp/musang_king_openvino.tar.gz}"

echo "==> [1/5] 检查 Docker"
if ! command -v docker >/dev/null; then
    echo "请先安装 Docker: curl -fsSL https://get.docker.com | sh"
    exit 1
fi
if ! docker compose version >/dev/null 2>&1; then
    echo "请安装 docker compose v2 (Docker 20.10+)"
    exit 1
fi

echo "==> [2/5] 准备部署目录: $DEPLOY_ROOT"
mkdir -p "$DEPLOY_ROOT/models/openvino"

echo "==> [3/5] 解压 OpenVINO 模型"
if [ -f "$MODELS_BUNDLE" ]; then
    tar -xzvf "$MODELS_BUNDLE" -C "$DEPLOY_ROOT/models/openvino/"
    echo "    已解压: $MODELS_BUNDLE"
else
    echo "    跳过(模型包 $MODELS_BUNDLE 不存在)"
    echo "    如稍后准备好,执行:"
    echo "      tar -xzvf <bundle.tar.gz> -C $DEPLOY_ROOT/models/openvino/"
    echo "      docker compose restart durian-api"
fi

echo "==> [4/5] 写入 .env"
if [ ! -f "$DEPLOY_ROOT/.env" ]; then
    cat > "$DEPLOY_ROOT/.env" <<EOF
DURIAN_PORT=8000
OMP_NUM_THREADS=8
EOF
    echo "    已创建 $DEPLOY_ROOT/.env"
else
    echo "    已存在 $DEPLOY_ROOT/.env, 跳过"
fi

echo "==> [5/5] 启动容器"
cd "$DEPLOY_ROOT"
docker compose up -d --build

echo ""
echo "==> 完成! 检查容器状态:"
docker compose ps

IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "<server-ip>")
echo ""
echo "==> 访问 http://$IP:8000"
echo "==> 健康检查: curl http://$IP:8000/api/health"
echo "==> 查看日志: docker compose logs -f durian-api"
