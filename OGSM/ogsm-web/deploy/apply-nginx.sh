#!/usr/bin/env bash
# 把 pmo.luteos.com 接进共享边缘 nginx（容器 ai_video_nginx）。
#
# 关键结构约束（2026-11-02 首次尝试踩到）：
#   ai_video_locations.conf 被 video.luteos.com 的 server 块整体 include，
#   只能放 location / upstream，**不能放 server 指令**。
#   因此 pmo 的 server 块必须写入 nginx.conf 的 http 层级末尾。
#
# 安全策略：
# 1. 先备份（带时间戳），备份留在 backup/
# 2. 幂等：已包含标记则跳过
# 3. 只插入，不改任何已有 server 块
# 4. reload 前 nginx -t 校验；失败自动还原
#
# 用法（服务器上，需 sudo）：
#   sudo bash deploy/apply-nginx.sh
#   sudo bash deploy/apply-nginx.sh --remove
set -euo pipefail

CONF_DIR=/opt/ai-video/deploy/lighthouse
TARGET="$CONF_DIR/nginx.conf"
EDGE=ai_video_nginx
SNIP="$(dirname "$0")/nginx-pmo.conf"
MARK="# >>> pmo.luteos.com (managed by OGSM deploy) >>>"
ENDMARK="# <<< pmo.luteos.com <<<"

[ "$(id -u)" = "0" ] || { echo "需要 sudo"; exit 1; }
[ -f "$TARGET" ] || { echo "✗ 找不到 $TARGET"; exit 1; }
[ -f "$SNIP" ] || { echo "✗ 找不到 $SNIP"; exit 1; }

if [ "${1:-}" = "--remove" ]; then
  echo "▶ 移除 pmo 配置块"
  mkdir -p "$CONF_DIR/backup"
  cp "$TARGET" "$CONF_DIR/backup/nginx.conf.$(date +%Y%m%d-%H%M%S)"
  python3 - "$TARGET" "$MARK" "$ENDMARK" <<'PY'
import sys, re
path, mark, endmark = sys.argv[1:4]
t = open(path, encoding="utf-8").read()
t2 = re.sub(r"\n*" + re.escape(mark) + r".*?" + re.escape(endmark) + r"\n?", "\n", t, flags=re.S)
open(path, "w", encoding="utf-8").write(t2)
print("  已移除" if t2 != t else "  无需移除")
PY
  docker exec "$EDGE" nginx -t && docker exec "$EDGE" nginx -s reload
  echo "✓ 已撤销"; exit 0
fi

if grep -qF "$MARK" "$TARGET"; then
  echo "▶ pmo 配置块已存在，跳过（如需更新：先 --remove 再重跑）"
else
  echo "▶ 备份 $TARGET"
  mkdir -p "$CONF_DIR/backup"
  BAK="$CONF_DIR/backup/nginx.conf.$(date +%Y%m%d-%H%M%S)"
  cp "$TARGET" "$BAK"
  echo "  备份：$BAK"

  echo "▶ 插入 pmo server 块（http 层级末尾）"
  # nginx.conf 最后一个 } 关闭 http 块。在它之前插入。
  python3 - "$TARGET" "$SNIP" "$MARK" "$ENDMARK" <<'PY'
import sys
path, snip, mark, endmark = sys.argv[1:5]
text = open(path, encoding="utf-8").read()
block = open(snip, encoding="utf-8").read().strip()

idx = text.rstrip().rfind("}")   # http 块的收尾花括号
if idx < 0:
    raise SystemExit("✗ 找不到 http 块的收尾花括号，拒绝修改")

indented = "\n".join(("    " + l) if l.strip() else "" for l in block.splitlines())
new = text[:idx] + "\n    " + mark + "\n" + indented + "\n    " + endmark + "\n" + text[idx:]
open(path, "w", encoding="utf-8").write(new)
print("  已插入")
PY
fi

echo "▶ 校验 nginx 配置"
if ! docker exec "$EDGE" nginx -t; then
  echo "✗ 校验失败，还原"
  [ -n "${BAK:-}" ] && cp "$BAK" "$TARGET" && docker exec "$EDGE" nginx -t
  exit 1
fi

echo "▶ reload 边缘 nginx（不断连接）"
docker exec "$EDGE" nginx -s reload

echo
echo "✓ 接入完成"
