#!/usr/bin/env bash
# 生产验收脚本 (V2)。部署后执行，验证路由、CSS/SVG 静态资源、14 个产品项目与 /reports 实测报告直读。
#
#   ./verify.sh                    # 默认 https://pmo.luteos.com
#   ./verify.sh http://172.20.0.1:18960
set -uo pipefail

BASE="${1:-https://pmo.luteos.com}"
FAIL=0
ok()   { printf '\033[32m  ✓\033[0m %s\n' "$1"; }
bad()  { printf '\033[31m  ✗\033[0m %s\n' "$1"; FAIL=$((FAIL+1)); }
hdr()  { printf '\n\033[1m%s\033[0m\n' "$1"; }

code() { curl -s -o /dev/null -w '%{http_code}' -m 10 "$1" 2>/dev/null; }

echo "验收目标：$BASE"

hdr "1. 核心路由可访问性"
c=$(code "$BASE/health"); [ "$c" = "200" ] && ok "/health 200" || bad "/health 期望 200，实际 $c"

for p in / /projects /roadmap /sites /present /docs /login /api/export.csv; do
  c=$(code "$BASE$p")
  [ "$c" = "200" ] && ok "$p 200" || bad "$p 期望 200，实际 $c"
done

hdr "2. 静态资源与原版 SVG 导图"
for asset in /static/style.css /static/ogsm-mindmap.svg; do
  ac=$(code "$BASE$asset")
  if [ "$ac" = "200" ]; then
    ok "$asset 200"
  else
    bad "$asset 期望 200，实际 $ac"
  fi
done
ctype=$(curl -s -o /dev/null -w '%{content_type}' -m 10 "$BASE/static/style.css" 2>/dev/null)
case "$ctype" in
  text/css*) ok "style.css Content-Type=$ctype" ;;
  *) bad "style.css Content-Type 异常：$ctype" ;;
esac

hdr "3. HTTPS 与证书"
if [[ "$BASE" == https://* ]]; then
  host=$(echo "$BASE" | sed -E 's#https://([^/:]+).*#\1#')
  if echo | openssl s_client -servername "$host" -connect "$host:443" 2>/dev/null | grep -q 'Verify return code: 0'; then
    ok "证书链校验通过"
  else
    bad "证书链校验失败"
  fi
  http_code=$(curl -s -o /dev/null -w '%{http_code}' -m 10 \
    --resolve "$host:80:127.0.0.1" "http://$host/" 2>/dev/null)
  [ "$http_code" = "301" ] || [ "$http_code" = "308" ] \
    && ok "HTTP→HTTPS 跳转 $http_code" || bad "HTTP 未跳转（$http_code）"
fi

hdr "4. 14 大产品项目与工作台完整性"
body=$(curl -s -m 10 "$BASE/" 2>/dev/null)
for probe in 'Emily' 'Clone' 'Vicky' 'GEO' 'Radar' 'Echo' 'Market' 'Source' 'Signal' '守衡' 'Daisy' 'Main' 'Shopify' 'PMO'; do
  if grep -qF "$probe" <<< "$body"; then ok "含产品项目：$probe"; else bad "缺产品项目：$probe"; fi
done

hdr "5. /reports 实测报告在线直读"
rc=$(code "$BASE/reports-view/Echo/Echo-%E9%A1%B9%E7%9B%AE%E6%88%90%E6%9E%9C%E6%80%BB%E7%BB%93-20261102.html")
[ "$rc" = "200" ] && ok "/reports-view/Echo 实测报告直读 200" || bad "/reports-view/Echo 返回 $rc"

hdr "6. 认证与安全边界"
c=$(code "$BASE/admin")
[ "$c" = "303" ] || [ "$c" = "302" ] || [ "$c" = "401" ] \
  && ok "/admin 未登录被拒（$c）" \
  || bad "/admin 未登录未拒绝（$c）"
if curl -s -m 10 "$BASE/docs/../.env" 2>/dev/null | grep -qiE 'PASSWORD|SECRET'; then
  bad "路径穿越读取 .env 成功"
else
  ok "路径穿越被阻断"
fi

echo
if [ "$FAIL" -gt 0 ]; then
  printf '\033[31m验收未通过：%d 项失败\033[0m\n' "$FAIL"
  exit 1
fi
printf '\033[32m验收全部通过\033[0m\n'
