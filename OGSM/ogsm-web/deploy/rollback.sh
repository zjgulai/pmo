#!/usr/bin/env bash
# 回滚到上一个可用镜像。不碰数据库（schema 迁移是向前兼容的）。
#
#   ./rollback.sh              # 回滚到 .last_tag
#   ./rollback.sh 20261102-101530   # 回滚到指定 tag
set -euo pipefail

cd "$(dirname "$0")/.." || exit 1

COMPOSE="docker compose -f deploy/docker-compose.prod.yml"

TARGET="${1:-$(cat deploy/.prev_tag 2>/dev/null || echo '')}"
if [ -z "$TARGET" ]; then
  echo "✗ 没有可回滚的目标。用法：./rollback.sh <tag>"
  echo "  可用镜像："
  docker images --format '  {{.Repository}}:{{.Tag}}  ({{.CreatedSince}})' | grep '^  pmo-web:' || echo "  （无）"
  exit 1
fi

if ! docker image inspect "pmo-web:$TARGET" >/dev/null 2>&1; then
  echo "✗ 镜像 pmo-web:$TARGET 不存在"
  docker images --format '  {{.Repository}}:{{.Tag}}  ({{.CreatedSince}})' | grep '^  pmo-web:'
  exit 1
fi

echo "▶ 回滚到 pmo-web:$TARGET"
export IMAGE_TAG="$TARGET"
$COMPOSE up -d --no-build web

echo "▶ 等待健康检查"
for i in $(seq 1 45); do
  curl -fsS -m 2 http://127.0.0.1:18960/health >/dev/null 2>&1 && { echo "  容器健康"; break; }
  [ "$i" = "45" ] && { echo "✗ 未健康，查看日志：$COMPOSE logs --tail=60 web"; exit 1; }
  sleep 2
done

echo "$TARGET" > deploy/.last_tag
echo "✓ 已回滚到 $TARGET"
echo "  注意：数据库 schema 未回滚（迁移设计为向前兼容）；若本次迁移不可逆，需单独处理"
