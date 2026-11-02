#!/usr/bin/env bash
# 生产验收脚本。部署后执行，输出可判定的检查表。
#
#   ./verify.sh                    # 默认 https://pmo.luteos.com
#   ./verify.sh http://127.0.0.1:18960
set -uo pipefail

BASE="${1:-https://pmo.luteos.com}"
FAIL=0
ok()   { printf '\033[32m  ✓\033[0m %s\n' "$1"; }
bad()  { printf '\033[31m  ✗\033[0m %s\n' "$1"; FAIL=$((FAIL+1)); }
hdr()  { printf '\n\033[1m%s\033[0m\n' "$1"; }

code() { curl -s -o /dev/null -w '%{http_code}' -m 10 "$1" 2>/dev/null; }

echo "验收目标：$BASE"

hdr "1. 可访问性"
c=$(code "$BASE/health"); [ "$c" = "200" ] && ok "/health 200" || bad "/health 期望 200，实际 $c"

for p in / /board /baselines /lines /experts /metrics /docs /login; do
  c=$(code "$BASE$p")
  [ "$c" = "200" ] && ok "$p 200" || bad "$p 期望 200，实际 $c"
done

hdr "2. 静态资源（页面能返回 200 不等于能看）"
for asset in /static/style.css; do
  ac=$(code "$BASE$asset")
  if [ "$ac" = "200" ]; then
    ok "$asset 200"
  else
    bad "$asset 期望 200，实际 $ac —— 页面会退化成无样式纯文本"
  fi
done
# CSS 必须真的被引用且真的返回 CSS 类型
ctype=$(curl -s -o /dev/null -w '%{content_type}' -m 10 "$BASE/static/style.css" 2>/dev/null)
case "$ctype" in
  text/css*) ok "style.css Content-Type=$ctype" ;;
  *) bad "style.css Content-Type 异常：$ctype" ;;
esac
if curl -s -m 10 "$BASE/" 2>/dev/null | grep -q 'static/style.css'; then
  ok "页面已引用 style.css"
else
  bad "页面未引用 style.css"
fi

hdr "3. HTTPS 与证书"
if [[ "$BASE" == https://* ]]; then
  host=$(echo "$BASE" | sed -E 's#https://([^/:]+).*#\1#')
  if echo | openssl s_client -servername "$host" -connect "$host:443" 2>/dev/null | grep -q 'Verify return code: 0'; then
    ok "证书链校验通过"
  else
    bad "证书链校验失败（可能是通配符证书与域名不匹配）"
  fi
  if curl -sI -m 10 "$BASE/" 2>/dev/null | grep -qi '^strict-transport-security'; then
    ok "HSTS 头存在"
  else
    bad "缺 HSTS 头"
  fi
  if curl -sI -m 10 "$BASE/" 2>/dev/null | grep -qi '^content-security-policy'; then
    ok "CSP 头存在"
  else
    bad "缺 CSP 头"
  fi
  # HTTP 跳转（从服务器内网回环无法出公网，改用 resolve 强制走本机 nginx）
  http_code=$(curl -s -o /dev/null -w '%{http_code}' -m 10 \
    --resolve "$host:80:127.0.0.1" "http://$host/" 2>/dev/null)
  [ "$http_code" = "301" ] || [ "$http_code" = "308" ] \
    && ok "HTTP→HTTPS 跳转 $http_code" || bad "HTTP 未跳转（$http_code）"
fi

hdr "3. 结构校验（区分部署缺陷与业务缺口）"
body=$(curl -s -m 10 "$BASE/" 2>/dev/null)
summary=$(echo "$body" | grep -o '结构校验[：:][^<]*' | head -1)
if [ -n "$summary" ]; then
  echo "  $summary"
  errs=$(echo "$summary" | grep -oE '[0-9]+ 错误' | grep -oE '[0-9]+')
  if [ "${errs:-0}" = "0" ]; then
    ok "0 错误"
  else
    # 结构类错误码（部署缺陷）：C1 C2 C4 C6 C7 C10 C11
    # 业务缺口类（C9 P0 零证据）：部署本身没问题，是业务还没做
    struct=$(echo "$body" | grep -oE '<code>C(1|2|4|6|7|10|11)</code>' | wc -l | tr -d ' ')
    biz=$(echo "$body" | grep -oE '<code>C9</code>' | wc -l | tr -d ' ')
    if [ "$struct" = "0" ]; then
      ok "结构校验无部署缺陷（$errs 个错误全部是 C9 业务缺口）"
      echo "     业务缺口 $biz 条：产线无建设证据。这不阻断部署，但阻断 G 结算。"
    else
      bad "存在 $struct 个结构类错误（部署缺陷），必须修复后才算验收通过"
    fi
  fi
else
  bad "页面上找不到结构校验读数——校验器未运行"
fi

hdr "4. 认证边界"
c=$(code "$BASE/admin")
[ "$c" = "303" ] || [ "$c" = "302" ] || [ "$c" = "401" ] \
  && ok "/admin 未登录被拒（$c）" \
  || bad "/admin 未登录未拒绝（$c）——存在未授权访问"

hdr "5. 数据完整性"
for probe in 'm-l1-cac@2' 'ai_answer_snapshot_id' 'S0.6'; do
  if echo "$body" | grep -qF "$probe"; then ok "含 $probe"; else bad "缺 $probe"; fi
done
# Know（知识生产）在专家对齐页，首页 HTML 不含该词；单独检查 /experts
experts_body=$(curl -s -m 10 "$BASE/experts" 2>/dev/null)
if echo "$experts_body" | grep -qF 'Know'; then ok "含 Know（/experts 页）"; else bad "缺 Know（/experts 页）"; fi

# 基线必须全部待填（不含假数据）
if echo "$body" | grep -q '基线未锁定\|待填'; then
  ok "基线为待填状态（未塞假数据）"
else
  bad "基线状态异常——生产库不应含预设数值"
fi

hdr "6. 敏感信息不泄露"
if curl -s -m 10 "$BASE/health" 2>/dev/null | grep -qiE 'password|secret|postgres://'; then
  bad "/health 泄露敏感信息"
else
  ok "/health 未泄露敏感信息"
fi
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
