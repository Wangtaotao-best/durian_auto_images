#!/usr/bin/env bash
# 在服务器上一键部署 durian-aigc (Docker)
# 用法 (任选其一):
#
#   # 1. 单个模型包
#   MODELS_BUNDLE=/tmp/musang_king_openvino.tar.gz bash scripts/deploy_to_server.sh
#
#   # 2. 多个模型包目录(脚本会自动解压所有 *_openvino.tar.gz)
#   MODELS_DIR=/tmp/durian_bundles bash scripts/deploy_to_server.sh
#
#   # 3. 模型已手动解压到 /data/durian/models/openvino/<variety>/,直接启动:
#   bash scripts/deploy_to_server.sh
#
# 环境变量:
#   DEPLOY_ROOT      默认 /data/durian
#   MODELS_BUNDLE    单个 tar.gz 路径(可选)
#   MODELS_DIR       存放多个 *_openvino.tar.gz 的目录(可选,优先于 MODELS_BUNDLE)

set -euo pipefail

DEPLOY_ROOT="${DEPLOY_ROOT:-/data/durian}"
MODELS_DIR="${MODELS_DIR:-}"
MODELS_BUNDLE="${MODELS_BUNDLE:-}"

echo "==> [1/5] 检查 Docker"
if ! command -v docker >/dev/null; then
    echo "ERROR: Docker 未安装。请先 curl -fsSL https://get.docker.com | sh"
    exit 1
fi
if ! docker compose version >/dev/null 2>&1; then
    echo "ERROR: docker compose v2 不可用 (需要 Docker 20.10+)"
    exit 1
fi
echo "    Docker: $(docker --version)"
echo "    Compose: $(docker compose version --short)"

echo "==> [2/5] 准备部署目录: $DEPLOY_ROOT"
mkdir -p "$DEPLOY_ROOT/models/openvino"

echo "==> [3/5] 解压 OpenVINO 模型"
extracted_count=0

if [ -n "$MODELS_DIR" ] && [ -d "$MODELS_DIR" ]; then
    for bundle in "$MODELS_DIR"/*_openvino.tar.gz; do
        [ -f "$bundle" ] || continue
        echo "    解压: $(basename "$bundle")"
        tar -xzf "$bundle" -C "$DEPLOY_ROOT/models/openvino/"
        extracted_count=$((extracted_count + 1))
    done
elif [ -n "$MODELS_BUNDLE" ] && [ -f "$MODELS_BUNDLE" ]; then
    echo "    解压: $(basename "$MODELS_BUNDLE")"
    tar -xzf "$MODELS_BUNDLE" -C "$DEPLOY_ROOT/models/openvino/"
    extracted_count=1
fi

if [ "$extracted_count" -eq 0 ]; then
    existing=$(ls "$DEPLOY_ROOT/models/openvino/" 2>/dev/null | wc -l || echo 0)
    if [ "$existing" -gt 0 ]; then
        echo "    无新包,使用已有模型 ($existing 个):"
        ls "$DEPLOY_ROOT/models/openvino/" | sed 's/^/      - /'
    else
        echo "    WARNING: 既没有新包,$DEPLOY_ROOT/models/openvino/ 下也没有模型"
        echo "    服务会启动但 /api/varieties 返回空,稍后用:"
        echo "      tar -xzf <bundle>.tar.gz -C $DEPLOY_ROOT/models/openvino/"
        echo "      docker compose restart durian-api"
    fi
else
    echo "    共解压 $extracted_count 个模型包"
    ls "$DEPLOY_ROOT/models/openvino/" | sed 's/^/      - /'
fi

echo "==> [4/5] 写入 .env"
if [ ! -f "$DEPLOY_ROOT/.env" ]; then
    # 自动检测物理核数
    CORES=$(nproc 2>/dev/null || echo 8)
    cat > "$DEPLOY_ROOT/.env" <<EOF
DURIAN_PORT=8000
OMP_NUM_THREADS=$CORES
EOF
    echo "    已创建 $DEPLOY_ROOT/.env (OMP_NUM_THREADS=$CORES)"
else
    echo "    已存在 $DEPLOY_ROOT/.env, 跳过"
    cat "$DEPLOY_ROOT/.env"
fi

echo "==> [5/5] 启动容器"
cd "$DEPLOY_ROOT"
docker compose up -d --build

echo ""
echo "==> 完成! 检查容器状态:"
docker compose ps

IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "<server-ip>")
echo ""
echo "============================================================"
echo "  访问: http://$IP:8000"
echo "  健康检查: curl http://$IP:8000/api/health"
echo "  品种列表: curl http://$IP:8000/api/varieties"
echo "  查看日志: docker compose logs -f durian-api"
echo "  停止服务: docker compose down"
echo "============================================================"
echo ""
echo "首次启动需要 60-180 秒加载第一个 OpenVINO 模型,"
echo "用 'docker compose ps' 看 STATUS 从 starting -> healthy 即可用。"
