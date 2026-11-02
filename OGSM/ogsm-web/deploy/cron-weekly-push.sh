#!/usr/bin/env bash
# ABI PMO 门户每周定时自动化脚本（建议 crontab: 0 9 * * 5 /opt/pmo/OGSM/ogsm-web/deploy/cron-weekly-push.sh）
#
# 自动完成三件事：
# 1. 扫描 /reports 目录自动挂载各专家最新生成的实测 HTML 报告
# 2. 触发飞书群里程碑周报卡片推送（若在 .env 配置了 FEISHU_WEBHOOK_URL）
# 3. 保存本周进度快照作为下周对比基准
set -euo pipefail

BASE_URL="${1:-http://172.20.0.1:18960}"

echo "[$(date -Iseconds)] 1/3 扫描同步 /reports 目录最新实测报告..."
curl -fsS -X POST "$BASE_URL/api/sync-reports"
echo

echo "[$(date -Iseconds)] 2/3 触发飞书群周报卡片推送..."
curl -sS -X POST "$BASE_URL/api/feishu/push-weekly" -H "Content-Type: application/json" -d '{}'
echo

echo "[$(date -Iseconds)] 3/3 保存本周进度基准快照..."
curl -fsS -X POST "$BASE_URL/api/snapshot/save"
echo
echo "[$(date -Iseconds)] 完成。"
