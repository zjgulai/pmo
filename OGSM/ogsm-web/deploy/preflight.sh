#!/usr/bin/env bash
# 部署前检查。任何一项失败即中止，不带病上线。
#
#   ./preflight.sh            # 本地检查
#   ./preflight.sh --prod     # 生产环境（需 .env 已填）
set -uo pipefail

PROD=0
[ "${1:-}" = "--prod" ] && PROD=1

FAIL=0
ok()   { printf '\033[32m  ✓\033[0m %s\n' "$1"; }
bad()  { printf '\033[31m  ✗\033[0m %s\n' "$1"; FAIL=$((FAIL+1)); }
warn() { printf '\033[33m  !\033[0m %s\n' "$1"; }
hdr()  { printf '\n\033[1m%s\033[0m\n' "$1"; }

cd "$(dirname "$0")/.." || exit 1   # ogsm-web/

hdr "1. 必需文件"
for f in app/main.py app/rules.py app/models.py app/migrate.py \
         deploy/docker-compose.prod.yml deploy/.env.example \
         Dockerfile requirements.txt; do
  [ -f "$f" ] && ok "$f" || bad "缺少 $f"
done

hdr "2. Python 语法"
PY=""
for cand in ./.venv/bin/python python3 python; do
  if command -v "$cand" >/dev/null 2>&1 || [ -x "$cand" ]; then PY="$cand"; break; fi
done
if [ -n "$PY" ]; then
  if "$PY" -m py_compile app/*.py 2>/dev/null; then
    ok "全部模块可编译"
  else
    bad "存在语法错误"
  fi
else
  warn "找不到 Python，跳过语法检查"
fi

if [ "$PROD" = "1" ]; then
  hdr "3. 生产环境变量"
  if [ ! -f deploy/.env ]; then
    bad "deploy/.env 不存在。复制 deploy/.env.example 并填写"
  else
    # shellcheck disable=SC1091
    set -a; . deploy/.env; set +a
    [ -n "${POSTGRES_PASSWORD:-}" ] && [ "${#POSTGRES_PASSWORD}" -ge 16 ] \
      && ok "POSTGRES_PASSWORD 已设置（${#POSTGRES_PASSWORD} 字符）" \
      || bad "POSTGRES_PASSWORD 未设置或短于 16 字符"
    if [ "${OGSM_PMO_PASSWORD:-}" = "pmo" ]; then
      bad "OGSM_PMO_PASSWORD 仍是默认值 pmo"
    elif [ -n "${OGSM_PMO_PASSWORD:-}" ] && [ "${#OGSM_PMO_PASSWORD}" -ge 12 ]; then
      ok "OGSM_PMO_PASSWORD 已设置（${#OGSM_PMO_PASSWORD} 字符）"
    else
      bad "OGSM_PMO_PASSWORD 未设置或短于 12 字符"
    fi
    if [ -n "${SECRET_KEY:-}" ] && [ "${#SECRET_KEY}" -ge 32 ]; then
      ok "SECRET_KEY 已设置（${#SECRET_KEY} 字符）"
    else
      bad "SECRET_KEY 未设置或短于 32 字符（生成：openssl rand -hex 32）"
    fi
  fi

  hdr "4. 端口未被占用"
  if command -v ss >/dev/null 2>&1; then
    if ss -tln 2>/dev/null | grep -q ':18960 '; then
      warn "18960 已被占用——若是本服务上一次运行的残留，可继续；否则改端口"
    else
      ok "18960 空闲"
    fi
  else
    warn "无 ss 命令，跳过端口检查"
  fi

  hdr "5. docker network 不冲突"
  if docker network ls --format '{{.Name}}' 2>/dev/null | grep -qx 'pmo_net'; then
    warn "pmo_net 已存在（上次部署残留，可继续）"
  else
    ok "pmo_net 不存在，将新建"
  fi
fi

echo
if [ "$FAIL" -gt 0 ]; then
  printf '\033[31m部署前检查未通过：%d 项失败\033[0m\n' "$FAIL"
  exit 1
fi
printf '\033[32m部署前检查通过\033[0m\n'
