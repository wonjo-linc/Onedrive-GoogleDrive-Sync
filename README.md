# OneDrive-GoogleDrive Sync

**실시간 양방향 파일 동기화** - Microsoft 365 Business와 Google Workspace 간 파일 동기화

## 기능

- 🔐 사용자별 로그인 (Azure AD / Google OAuth)
- 📁 개인별 폴더 매핑 설정
- ⚡ 실시간 동기화 (Webhook 기반)
- 📊 웹 대시보드 모니터링
- 🔄 양방향 동기화
- 💾 청크 기반 파일 전송 (대용량 파일 지원)
- 🔁 자동 재시도 (안정성)

## 요구사항

- Docker & Docker Compose
- Microsoft 365 Business 계정
- Google Workspace 계정
- 도메인 (Webhook용)

## 빠른 시작

### 1. 환경 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집 (API 자격증명 입력)
nano .env
```

### 2. API 자격증명 설정

#### Azure AD (Microsoft 365)
1. [Azure Portal](https://portal.azure.com) → App registrations
2. New registration
3. Redirect URI: `https://sync.lincsolution.net/auth/callback/microsoft`
4. API permissions: `Files.ReadWrite.All`, `Sites.ReadWrite.All`
5. Client ID와 Secret을 `.env`에 저장

#### Google Workspace
1. [Google Cloud Console](https://console.cloud.google.com)
2. APIs & Services → Enable APIs → Google Drive API
3. Credentials → OAuth 2.0 Client ID
4. Redirect URI: `https://sync.lincsolution.net/auth/callback/google`
5. Client ID와 Secret을 `.env`에 저장

### 3. Docker 실행

```bash
# 컨테이너 빌드 및 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 상태 확인
curl http://localhost:8000/health
```

### 4. Nginx Proxy Manager 설정

1. Proxy Host 추가
2. Domain: `sync.lincsolution.net`
3. Forward to: `[Container IP]:8000`
4. SSL 활성화 (Let's Encrypt)

## API 문서

컨테이너 실행 후 다음 URL에서 API 문서 확인:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 주요 API 엔드포인트

```
# 인증
GET  /auth/login/microsoft
GET  /auth/login/google
GET  /auth/me

# 계정 연결
POST /accounts/connect/onedrive
POST /accounts/connect/gdrive
GET  /accounts

# 동기화 작업
POST /sync-jobs
GET  /sync-jobs
POST /sync-jobs/{id}/trigger

# 폴더 탐색
GET  /folders/onedrive/{account_id}?path=/
GET  /folders/gdrive/{account_id}?folder_id=root

# WebSocket
WS   /ws?token={jwt_token}
```

## 환경 변수

`.env` 파일 예시:

```env
# Azure AD
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_TENANT_ID=your-tenant-id

# Google Workspace
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret

# Security
SECRET_KEY=your-secret-key-min-32-chars
ENCRYPTION_KEY=your-encryption-key-44-chars

# Webhook
WEBHOOK_BASE_URL=https://sync.lincsolution.net
```

## 프로젝트 구조

```
Onedrive-GoogleDrive-Sync/
├── src/
│   ├── api/              # FastAPI 백엔드
│   ├── auth/             # OAuth 인증
│   ├── database/         # SQLAlchemy 모델
│   └── sync/             # 동기화 엔진
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## 배포 (Proxmox)

```bash
# 1. 이미지 빌드
docker build -t onedrive-gdrive-sync:latest .

# 2. 이미지 저장 및 전송
docker save onedrive-gdrive-sync:latest | gzip > sync.tar.gz
scp sync.tar.gz user@proxmox:/tmp/

# 3. 서버에서 로드
ssh user@proxmox
docker load < /tmp/sync.tar.gz

# 4. 설정 파일 전송
scp docker-compose.yml .env user@proxmox:/opt/onedrive-sync/

# 5. 실행
cd /opt/onedrive-sync
docker-compose up -d
```

## 모니터링

```bash
# 로그 확인
docker logs -f onedrive-gdrive-sync

# 컨테이너 상태
docker ps

# 리소스 사용량
docker stats onedrive-gdrive-sync

# 헬스체크
docker inspect --format='{{.State.Health.Status}}' onedrive-gdrive-sync
```

## 문제 해결

### 데이터베이스 초기화
```bash
docker-compose down
rm -rf data/sync.db
docker-compose up -d
```

### 로그 레벨 변경
```bash
# .env 파일에서
LOG_LEVEL=DEBUG

docker-compose restart
```

## 라이선스

MIT License

## 기여

Pull Request 환영합니다!

## 문의

이슈를 통해 문의해 주세요.
