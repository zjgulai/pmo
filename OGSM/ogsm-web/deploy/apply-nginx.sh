#!/usr/bin/env bash
# 把 pmo.luteos.com 接进共享边缘 nginx（容器 ai_video_nginx）。
#
# 安全策略：
# 1. 先备份原文件（带时间戳），备份留在 /opt/ai-video/deploy/lighthouse/backup/
# 2. 幂等：已包含 pmo 块则跳过
# 3. 只追加，不修改任何已有 server 块
# 4. reload 前用 nginx -t 校验；失败自动还原
#
# 用法（服务器上，需 sudo）：
#   sudo bash deploy/apply-nginx.sh
#   sudo bash deploy/apply-nginx.sh --remove   # 撤销
set -euo pipefail

CONF_DIR=/opt/ai-video/deploy/lighthouse
TARGET="$CONF_DIR/ai_video_locations.conf"
EDGE=ai_video_nginx
SNIP="$(dirname "$0")/nginx-pmo.conf"
MARK="# >>> pmo.luteos.com (managed by OGSM deploy) >>>"
ENDMARK="# <<< pmo.luteos.com <<<"

[ "$(id -u)" = "0" ] || { echo "需要 sudo"; exit 1; }
[ -f "$TARGET" ] || { echo "✗ 找不到 $TARGET"; exit 1; }

if [ "${1:-}" = "--remove" ]; then
  echo "▶ 移除 pmo 配置块"
  cp "$TARGET" "$TARGET.bak.$(date +%Y%m%d-%H%M%S)"
  "$(command -v python3)" - "$TARGET" "$MARK" "$ENDMARK" <<'PY'
import sys, re
path, mark, endmark = sys.argv[1:4]
t = open(path, encoding="utf-8").read()
t2 = re.sub(re.escape(mark) + r".*?" + re.escape(endmark) + r"\n?", "", t, flags=re.S)
open(path, "w", encoding="utf-8").write(t2)
print("  已移除" if t2 != t else "  无需移除")
PY
  docker exec "$EDGE" nginx -t && docker exec "$EDGE" nginx -s reload
  echo "✓ 已撤销"
  exit 0
fi

if grep -qF "$MARK" "$TARGET"; then
  echo "▶ pmo 配置块已存在，跳过追加（如需更新，先 --remove）"
else
  echo "▶ 备份 $TARGET"
  mkdir -p "$CONF_DIR/backup"
  BAK="$CONF_DIR/backup/ai_video_locations.conf.$(date +%Y%m%d-%H%M%S)"
  cp "$TARGET" "$BAK"
  echo "  备份：$BAK"

  echo "▶ 追加 pmo server 块"
  {
    echo ""
    echo "$MARK"
    cat "$SNIP"
    echo "$ENDMARK"
  } >> "$TARGET"
fi

echo "▶ 校验 nginx 配置"
if ! docker exec "$EDGE" nginx -t; then
  echo "✗ 配置校验失败，还原"
  [ -n "${BAK:-}" ] && cp "$BAK" "$TARGET"
  docker exec "$EDGE" nginx -t
  exit 1
fi

echo "▶ reload 边缘 nginx（不断连接）"
docker exec "$EDGE" nginx -s reload

echo
echo "✓ 接入完成。验证："
echo "  curl -I https://pmo.luteos.com/"
