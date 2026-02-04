#!/bin/bash

# AI-Media2Doc 镜像构建和推送脚本
# 用途：一键构建并推送 backend 和 frontend 镜像到私有 Harbor 仓库

set -e  # 遇到错误立即退出

# 配置
HARBOR_REGISTRY="www.harbor.wymhealth.cloud:8443/app"
BACKEND_IMAGE_NAME="ai-media2doc-backend"
FRONTEND_IMAGE_NAME="ai-media2doc-frontend"
VERSION="${1:-latest}"  # 默认版本为 latest，可通过第一个参数指定

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

echo_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo_error "Docker 未运行，请先启动 Docker"
    exit 1
fi

echo_info "========================================="
echo_info "AI-Media2Doc 镜像构建和推送"
echo_info "版本: ${VERSION}"
echo_info "目标仓库: ${HARBOR_REGISTRY}"
echo_info "========================================="
echo ""

# 构建镜像
echo_info "步骤 1/4: 构建 Docker 镜像..."
docker-compose build

# 后端镜像
echo_info "步骤 2/4: 打标签并推送后端镜像..."
BACKEND_LOCAL_TAG="${BACKEND_IMAGE_NAME}:local"
BACKEND_HARBOR_TAG="${HARBOR_REGISTRY}/${BACKEND_IMAGE_NAME}:${VERSION}"

echo_info "  - 本地镜像: ${BACKEND_LOCAL_TAG}"
echo_info "  - 目标镜像: ${BACKEND_HARBOR_TAG}"

docker tag ${BACKEND_LOCAL_TAG} ${BACKEND_HARBOR_TAG}
echo_info "  正在推送后端镜像..."
docker push ${BACKEND_HARBOR_TAG}
echo_info "  ✓ 后端镜像推送成功"
echo ""

# 前端镜像
echo_info "步骤 3/4: 打标签并推送前端镜像..."
FRONTEND_LOCAL_TAG="${FRONTEND_IMAGE_NAME}:local"
FRONTEND_HARBOR_TAG="${HARBOR_REGISTRY}/${FRONTEND_IMAGE_NAME}:${VERSION}"

echo_info "  - 本地镜像: ${FRONTEND_LOCAL_TAG}"
echo_info "  - 目标镜像: ${FRONTEND_HARBOR_TAG}"

docker tag ${FRONTEND_LOCAL_TAG} ${FRONTEND_HARBOR_TAG}
echo_info "  正在推送前端镜像..."
docker push ${FRONTEND_HARBOR_TAG}
echo_info "  ✓ 前端镜像推送成功"
echo ""

# 完成
echo_info "步骤 4/4: 清理临时资源..."
echo_info "========================================="
echo_info "✓ 所有镜像构建和推送完成！"
echo_info "========================================="
echo ""
echo_info "已推送的镜像："
echo_info "  1. ${BACKEND_HARBOR_TAG}"
echo_info "  2. ${FRONTEND_HARBOR_TAG}"
echo ""
echo_info "使用方式："
echo_info "  修改 docker-compose.yaml 中的镜像地址为："
echo_info "    backend:  ${HARBOR_REGISTRY}/${BACKEND_IMAGE_NAME}:${VERSION}"
echo_info "    frontend: ${HARBOR_REGISTRY}/${FRONTEND_IMAGE_NAME}:${VERSION}"
