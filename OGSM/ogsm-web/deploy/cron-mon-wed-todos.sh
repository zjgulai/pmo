#!/usr/bin/env bash
# ABI PMO 门户每周一、周三晨间飞书群 @三人 当期接棒待办催办脚本
# 建议 crontab: 0 9 * * 1,3 /usr/bin/flock -n /tmp/pmo-mon-wed-todos.lock /bin/bash /opt/pmo/OGSM/ogsm-web/deploy/cron-mon-wed-todos.sh >> /opt/pmo/logs/mon-wed-todos.log 2>&1
set -euo pipefail

BASE_URL="${1:-http://172.20.0.1:18960}"

echo "[$(date -Iseconds)] 1/2 同步飞书在线表（XhJUya 49项总览 + 5UK051 147道三棒接力工序）..."
curl -fsS -X POST "$BASE_URL/api/feishu/sheet-sync" -H "Content-Type: application/json" -d '{"direction":"push"}'
echo

echo "[$(date -Iseconds)] 2/2 向 ABI智能应用与算法组 群推送 @吴雨宁 @周健 @刘华丽 当期在手接棒待办卡片..."
curl -fsS -X POST "$BASE_URL/api/feishu/push-member-todos" -H "Content-Type: application/json" -d '{"push_to_feishu":true}'
echo

echo "[$(date -Iseconds)] 周一/周三三棒接力待办推送完成。"
