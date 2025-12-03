#!/bin/bash
set -e

echo "=========================================="
echo "OneDrive-GoogleDrive Sync Container"
echo "=========================================="

# 환경 변수 확인
echo "Checking environment variables..."
if [ -z "$ONEDRIVE_CLIENT_ID" ] || [ -z "$ONEDRIVE_CLIENT_SECRET" ]; then
    echo "ERROR: OneDrive credentials not set!"
    echo "Please set ONEDRIVE_CLIENT_ID and ONEDRIVE_CLIENT_SECRET"
    exit 1
fi

# Google Drive credentials 확인
if [ ! -f "/app/config/credentials.json" ]; then
    echo "WARNING: Google Drive credentials.json not found!"
    echo "Please mount credentials.json to /app/config/credentials.json"
fi

echo "Environment variables OK"

# 크론 스케줄 설정
echo "Setting up cron schedule: $SYNC_SCHEDULE"
echo "$SYNC_SCHEDULE /app/scripts/sync.sh >> /var/log/cron.log 2>&1" > /etc/cron.d/sync-cron

# 크론 파일 권한 설정
chmod 0644 /etc/cron.d/sync-cron

# 크론탭 등록
crontab /etc/cron.d/sync-cron

echo "Cron schedule configured"

# 초기 동기화 실행 (선택적)
if [ "${RUN_ON_START:-false}" = "true" ]; then
    echo "Running initial sync..."
    /app/scripts/sync.sh
fi

echo "=========================================="
echo "Container started successfully"
echo "Sync schedule: $SYNC_SCHEDULE"
echo "Sync direction: $SYNC_DIRECTION"
echo "=========================================="

# 크론 로그 출력
tail -f /var/log/cron.log &

# 메인 프로세스 실행
exec "$@"
