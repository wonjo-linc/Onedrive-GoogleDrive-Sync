#!/bin/bash
set -e

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_FILE="/app/logs/sync_$(date '+%Y%m%d').log"

echo "=========================================="
echo "[$TIMESTAMP] Starting sync..."
echo "=========================================="

# 로그 파일에도 기록
{
    echo "=========================================="
    echo "[$TIMESTAMP] Sync started"
    echo "Direction: $SYNC_DIRECTION"
    echo "Folder: ${SYNC_FOLDER:-All}"
    echo "=========================================="
    
    # Python 동기화 스크립트 실행
    cd /app
    
    if [ "$SYNC_DIRECTION" = "bidirectional" ]; then
        python main.py --bidirectional ${SYNC_FOLDER:+--folder "$SYNC_FOLDER"}
    elif [ "$SYNC_DIRECTION" = "onedrive-to-gdrive" ]; then
        python main.py --source onedrive --target gdrive ${SYNC_FOLDER:+--folder "$SYNC_FOLDER"}
    elif [ "$SYNC_DIRECTION" = "gdrive-to-onedrive" ]; then
        python main.py --source gdrive --target onedrive ${SYNC_FOLDER:+--folder "$SYNC_FOLDER"}
    else
        echo "ERROR: Invalid SYNC_DIRECTION: $SYNC_DIRECTION"
        exit 1
    fi
    
    SYNC_STATUS=$?
    
    echo "=========================================="
    if [ $SYNC_STATUS -eq 0 ]; then
        echo "[$TIMESTAMP] Sync completed successfully"
    else
        echo "[$TIMESTAMP] Sync failed with exit code: $SYNC_STATUS"
    fi
    echo "=========================================="
    
    # 마지막 동기화 시간 기록 (헬스체크용)
    echo "$TIMESTAMP" > /app/logs/last_sync.log
    
    exit $SYNC_STATUS
    
} 2>&1 | tee -a "$LOG_FILE"
