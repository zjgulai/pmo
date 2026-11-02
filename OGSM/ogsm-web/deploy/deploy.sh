#!/usr/bin/env bash
# 生产部署脚本。在服务器上执行：/opt/pmo/OGSM/ogsm-web/deploy/deploy.sh
#
# 设计原则：
# - 幂等：重复执行结果一致
# - 可回滚：镜像按 tag 保留，上一版 tag 写在 .last_tag
# - 不干扰他人：只操作 pmo project，不碰任何其他容器/network
set -euo pipefail

cd "$(dirname "$0")/.." || exit 1   # ogsm-web/

COMPOSE="docker compose -f deploy/docker-compose.prod.yml"
TAG="${IMAGE_TAG:-$(date +%Y%m%d-%H%M%S)}"
export IMAGE_TAG="$TAG"

echo "▶ 部署前检查"
bash deploy/preflight.sh --prod

echo
echo "▶ 记录上一个可用 tag（用于回滚）"
if docker image inspect "pmo-web:$(cat deploy/.last_tag 2>/dev/null || echo none)" >/dev/null 2>&1; then
  echo "  上一版：$(cat deploy/.last_tag)"
else
  echo "  无可回滚的上一版（首次部署）"
fi

echo
echo "▶ 构建镜像 pmo-web:$TAG"
$COMPOSE build --pull web

echo
echo "▶ 启动 / 更新"
$COMPOSE up -d --remove-orphans

echo
echo "▶ 等待健康检查（最多 90s）"
# 注意：端口绑在 172.20.0.1（docker 网桥），不是 127.0.0.1。
# 用 127.0.0.1 会一直连不上，导致误判部署失败。
HEALTH_URL="http://172.20.0.1:18960/health"
for i in $(seq 1 45); do
  if curl -fsS -m 2 "$HEALTH_URL" >/dev/null 2>&1; then
    echo "  容器健康"
    break
  fi
  if [ "$i" = "45" ]; then
    echo "  ✗ 90s 内未健康，输出日志："
    $COMPOSE logs --tail=60 web
    exit 1
  fi
  sleep 2
done

echo
echo "▶ 记录本次 tag"
echo "$TAG" > deploy/.last_tag

echo
echo "▶ 当前状态"
$COMPOSE ps
echo
echo "✓ 部署完成：pmo-web:$TAG"
echo "  内外网验证：curl -I http://127.0.0.1:18960/"
