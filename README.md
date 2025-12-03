# OneDrive-GoogleDrive Sync

**양방향 파일 동기화 도구** - OneDrive와 Google Drive 간 파일을 자동으로 동기화합니다.

## 기능

- ✅ OneDrive ↔ Google Drive 양방향 동기화
- 🔐 OAuth 2.0 보안 인증
- 📊 실시간 동기화 진행 상황 표시
- ⚡ 증분 동기화 지원 (변경된 파일만)
- 🔄 자동 충돌 해결

## 요구사항

- Python 3.8 이상
- OneDrive 계정
- Google Drive 계정
- Azure Portal 앱 등록 (OneDrive API)
- Google Cloud Console 프로젝트 (Drive API)

## 설치

```bash
# 리포지토리 클론
git clone https://github.com/wonjo-linc/Onedrive-GoogleDrive-Sync.git
cd Onedrive-GoogleDrive-Sync

# 의존성 설치
pip install -r requirements.txt
```

## 설정

### 1. OneDrive API 설정

1. [Azure Portal](https://portal.azure.com)에 접속
2. "App registrations" → "New registration"
3. Redirect URI: `http://localhost:8080/callback`
4. API permissions: `Files.ReadWrite.All`
5. Client ID와 Client Secret을 `.env` 파일에 저장

### 2. Google Drive API 설정

1. [Google Cloud Console](https://console.cloud.google.com)에 접속
2. 새 프로젝트 생성
3. "APIs & Services" → "Enable APIs" → "Google Drive API" 활성화
4. "Credentials" → "OAuth 2.0 Client ID" 생성
5. `credentials.json` 파일을 `config/` 폴더에 저장

### 3. 환경 변수 설정

`.env` 파일 생성:

```env
ONEDRIVE_CLIENT_ID=your_client_id
ONEDRIVE_CLIENT_SECRET=your_client_secret
ONEDRIVE_TENANT_ID=common
```

## 사용법

### Python 직접 실행

```bash
# 기본 동기화 (OneDrive → Google Drive)
python main.py --source onedrive --target gdrive

# 역방향 동기화 (Google Drive → OneDrive)
python main.py --source gdrive --target onedrive

# 양방향 동기화
python main.py --bidirectional

# 특정 폴더만 동기화
python main.py --source onedrive --target gdrive --folder "Documents"
```

### Docker 실행 (권장)

#### 1. 환경 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집 (API 자격증명 입력)
nano .env
```

#### 2. Google Drive credentials.json 준비

`config/credentials.json` 파일을 Google Cloud Console에서 다운로드하여 배치합니다.

#### 3. Docker Compose로 실행

```bash
# 컨테이너 빌드 및 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 컨테이너 중지
docker-compose down
```

#### 4. 환경 변수 커스터마이징

`.env` 파일에서 다음 변수를 설정할 수 있습니다:

```env
# 동기화 스케줄 (크론 형식)
SYNC_SCHEDULE=0 */6 * * *  # 6시간마다

# 동기화 방향
SYNC_DIRECTION=bidirectional  # bidirectional, onedrive-to-gdrive, gdrive-to-onedrive

# 특정 폴더만 동기화 (선택)
SYNC_FOLDER=Documents

# 컨테이너 시작 시 즉시 동기화 실행
RUN_ON_START=true

# 로그 레벨
LOG_LEVEL=INFO
```

#### 5. Proxmox/서버 배포

```bash
# Docker 이미지 빌드
docker build -t onedrive-gdrive-sync:latest .

# 이미지 저장 및 서버로 전송
docker save onedrive-gdrive-sync:latest | gzip > onedrive-gdrive-sync.tar.gz
scp onedrive-gdrive-sync.tar.gz user@server:/tmp/

# 서버에서 이미지 로드
ssh user@server
docker load < /tmp/onedrive-gdrive-sync.tar.gz

# docker-compose.yml과 .env 파일 전송
scp docker-compose.yml .env config/credentials.json user@server:/opt/onedrive-sync/

# 서버에서 실행
ssh user@server
cd /opt/onedrive-sync
docker-compose up -d
```


## 프로젝트 구조

```
Onedrive-GoogleDrive-Sync/
├── src/
│   ├── auth/              # 인증 모듈
│   ├── sync/              # 동기화 엔진
│   └── utils/             # 유틸리티
├── tests/                 # 테스트
├── config/                # 설정 파일
├── main.py                # 메인 실행 파일
└── requirements.txt       # 의존성
```

## 라이선스

MIT License

## 기여

Pull Request를 환영합니다!

## 문의

이슈를 통해 문의해 주세요.
