FROM python:3.11-slim

# 메타데이터
LABEL maintainer="wonjo-linc"
LABEL description="OneDrive-GoogleDrive Sync Service"

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 cron 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY src/ ./src/
COPY main.py .
COPY scripts/ ./scripts/

# 스크립트 실행 권한 부여
RUN chmod +x scripts/*.sh

# 로그 및 설정 디렉토리 생성
RUN mkdir -p /app/logs /app/config

# 크론 로그 파일 생성
RUN touch /var/log/cron.log

# 환경 변수 기본값 설정
ENV SYNC_SCHEDULE="0 */6 * * *" \
    SYNC_DIRECTION="bidirectional" \
    LOG_LEVEL="INFO" \
    PYTHONUNBUFFERED=1

# 헬스체크
HEALTHCHECK --interval=1h --timeout=30s --start-period=5s --retries=3 \
    CMD test -f /app/logs/last_sync.log || exit 1

# 엔트리포인트 설정
ENTRYPOINT ["/app/scripts/entrypoint.sh"]

# 기본 명령어
CMD ["cron", "-f"]
