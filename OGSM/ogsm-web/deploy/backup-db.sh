#!/usr/bin/env bash
# ABI PMO 数据库每日定时自动备份脚本（建议 crontab: 0 3 * * * /opt/pmo/OGSM/ogsm-web/deploy/backup-db.sh）
#
# 备份内容：
# 1. pmo-db 容器 PostgreSQL 完整 pg_dump .sql.gz 备份
# 2. pmo-web 全库结构化 JSON 备份
# 自动保留最近 30 天备份，清理过期文件。
set -euo pipefail

BACKUP_DIR="/opt/pmo/backups"
mkdir -p "$BACKUP_DIR"
STAMP="$(date +%Y%m%d-%H%M%S)"

echo "[$(date -Iseconds)] 开始备份 pmo-db PostgreSQL 数据库..."
docker exec pmo-db pg_dump -U ogsm -d ogsm | gzip -9 > "$BACKUP_DIR/pmo_pg_${STAMP}.sql.gz"

echo "[$(date -Iseconds)] 导出结构化 JSON 快照..."
curl -fsS http://172.20.0.1:18960/api/backup.json | gzip -9 > "$BACKUP_DIR/pmo_json_${STAMP}.json.gz"

# 清理 30 天前的旧备份
find "$BACKUP_DIR" -type f -name "pmo_*" -mtime +30 -delete

ls -lh "$BACKUP_DIR" | tail -5
echo "[$(date -Iseconds)] 备份完成。"
