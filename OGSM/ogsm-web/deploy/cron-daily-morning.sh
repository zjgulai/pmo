#!/usr/bin/env bash
# ABI PMO 门户每日晨间自动化脚本（建议 crontab: 30 8 * * * /opt/pmo/OGSM/ogsm-web/deploy/cron-daily-morning.sh）
#
# 自动完成三件事：
# 1. 探测各专家生产服务 API 与扫描 /reports 最新 HTML 报告，刷新项目在线状态与时间戳
# 2. 与飞书在线表《ABI OGSM 总览表》(FHQ0soq8ghbMQUtZOfYcWetUnIh) OpenAPI 双向对齐
# 3. 巡检 24 站点健康状态并扫描距截止日 <= 3 天的临期里程碑（仅当存在掉线或 3 天内临期项时推送飞书群提醒）
set -euo pipefail

BASE_URL="${1:-http://172.20.0.1:18960}"

echo "[$(date -Iseconds)] 1/3 采集各专家生产接口与扫描最新 /reports 报告..."
curl -fsS -X POST "$BASE_URL/api/auto/collect-metrics"
echo

echo "[$(date -Iseconds)] 2/3 与飞书在线表格 FHQ0soq8ghbMQUtZOfYcWetUnIh 双向同步..."
curl -fsS -X POST "$BASE_URL/api/feishu/sheet-sync" -H "Content-Type: application/json" -d '{"direction":"both"}'
echo

echo "[$(date -Iseconds)] 3/3 巡检 24 站点连通性与扫描 3 天内临期里程碑..."
PATROL_JSON=$(curl -fsS -X POST "$BASE_URL/api/auto/patrol" -H "Content-Type: application/json" -d '{"push_to_feishu":false,"days_threshold":3}')
echo "$PATROL_JSON"

if echo "$PATROL_JSON" | grep -qE '"down_sites_count":[1-9]|"due_soon_count":[1-9]'; then
  echo "[$(date -Iseconds)] 检测到站点掉线或 3 天内到期里程碑，触发飞书群提醒卡片推送..."
  curl -fsS -X POST "$BASE_URL/api/auto/patrol" -H "Content-Type: application/json" -d '{"push_to_feishu":true,"days_threshold":3}'
  echo
fi

echo "[$(date -Iseconds)] 晨间自动化完成。"
