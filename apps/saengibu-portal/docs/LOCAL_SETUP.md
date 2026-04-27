# LOCAL_SETUP — 로컬 환경 구축 가이드

> macOS/Linux/WSL 기준. Windows 네이티브 PowerShell은 경로 구분자 `\`로 치환.
> 목표: `http://localhost:3000` 에서 로그인 후 `/records` 화면까지 확인.

## 1. 사전 요구사항

| 도구 | 버전 | 확인 |
|---|---|---|
| Python | ≥ 3.11 | `python3 --version` |
| uv | ≥ 0.5 | `uv --version` (`pipx install uv` 또는 `curl -LsSf https://astral.sh/uv/install.sh \| sh`) |
| Node.js | ≥ 20.0 | `node -v` |
| pnpm | ≥ 9.0 | `corepack enable && corepack prepare pnpm@latest --activate` |
| Docker | Compose v2 | `docker compose version` |
| Google Cloud 콘솔 계정 | — | OAuth Client ID 발급용 |

## 1-a. macOS / Mac mini 빠른 준비

Mac mini에서는 저장소를 OneDrive/Dropbox 동기화 폴더보다 일반 개발 경로(`~/Projects` 등)에 두는 것을 권장한다. iCloud Drive 동기화 경로(`~/Documents`)도 권한·심볼릭 링크 이슈로 피한다.

```bash
mkdir -p ~/Projects
cd ~/Projects

xcode-select --install   # 이미 있으면 무시됨

# Homebrew가 없다면 먼저 설치
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 핵심 도구 설치 (Apple Silicon / Intel 공통)
brew install git python@3.11 uv node@20 openssl

# Docker는 daemon이 필요하므로 cask로 Docker Desktop 설치
brew install --cask docker
open -a Docker            # Docker Desktop 실행
docker compose version    # v2 정상 출력 확인
```

**pnpm은 Homebrew 전역 설치보다 Corepack으로 프로젝트 버전에 맞춰 활성화**한다.

```bash
corepack enable
corepack prepare pnpm@9.15.9 --activate   # frontend/package.json의 packageManager와 동일
pnpm --version                            # 9.15.9 확인
```

`pnpm@latest`는 lockfile을 의도치 않게 갱신할 수 있으므로 피한다. `frontend/package.json`의 `packageManager` 필드가 단일 진실의 원천(SoT).

**Apple Silicon Mac**: `postgres:16-alpine`, `redis:7-alpine` 이미지가 멀티아키텍처 지원이므로 `platform: linux/amd64` 강제 불필요. Docker Desktop **리소스는 최소 CPU 4개, 메모리 4GB+** 권장 (Settings → Resources).

**pyenv 사용자**: shell PATH 우선순위로 인해 `.python-version`(`3.11`)과 다른 Python이 잡힐 수 있음. uv는 자체 Python 관리 기능이 있으므로 다음 권장:

```bash
uv python install 3.11    # uv가 관리하는 Python 3.11 설치
python3 --version         # 3.11.x 확인
```

## 2. 저장소 준비

```bash
git clone https://github.com/hotdeli88-pixel/anti2.git
cd anti2

# 루트에서 uv workspace 동기화 (backend 의존성 포함)
uv sync
```

`apps/saengibu-portal/` 이 작업 디렉터리. 이하 경로는 모두 여기 기준.

```bash
cd apps/saengibu-portal
```

## 2-a. Git 줄바꿈 / 권한 확인

크로스플랫폼(WSL ↔ macOS) 작업 시 LF 정책을 유지하려면:

```bash
git config --global core.autocrlf input   # macOS/Linux는 항상 LF로 체크인
git config --global core.eol lf
```

저장소에는 `.gitattributes`(`* text=auto eol=lf`)가 적용되어 있다. **clone/pull 직후** 다음 명령으로 의도치 않은 CRLF·실행권한 오염을 점검한다:

```bash
# CRLF로 추적된 파일 확인 (정상 시 출력 없음)
git ls-files --eol | grep -E 'i/crlf' || echo "OK: 모든 텍스트 LF"

# 실행 비트 켜진 파일 확인 (스크립트 외에는 출력 없어야 정상)
git ls-files -s | awk '$1 == "100755" { print }'
```

CRLF가 남아 있으면 정규화 커밋 분리:

```bash
git add --renormalize .
git commit -m "chore: normalize line endings"
```

## 3. Google OAuth Client ID 발급

1. <https://console.cloud.google.com/> → 프로젝트 생성 (또는 기존 선택)
2. **API 및 서비스 → OAuth 동의 화면**
   - 사용자 유형: 내부(학교 G Workspace) 권장, 외부 가능
   - 범위: `openid email profile`
3. **API 및 서비스 → 사용자 인증 정보 → 사용자 인증 정보 만들기 → OAuth 클라이언트 ID**
   - 애플리케이션 유형: **웹 애플리케이션**
   - 이름: `saengibu-portal (local)`
   - **승인된 JavaScript 원본**: `http://localhost:3000`
   - **리디렉션 URI**: 설정 불필요 (GIS one-tap 방식)
4. 발급된 **클라이언트 ID** (`1234-xxxxx.apps.googleusercontent.com`) 복사

## 4-0. 기존 작업 환경에서 새 머신으로 이동하는 경우

이미 다른 머신(WSL/Linux/Mac)에서 개발하던 사람이 **Mac mini 등 새 환경으로 옮기는 경우** 3절(OAuth 신규 발급)을 생략할 수 있다.

| 시크릿 | 재사용 가능? | 권고 |
|---|---|---|
| `GOOGLE_CLIENT_ID` | ✅ 재사용 | 로컬 origin이 양쪽 동일하게 `http://localhost:3000`이므로 기존 클라이언트 ID 그대로 사용. backend `.env` + frontend `.env.local` 양쪽 동일하게 설정. |
| `SESSION_SECRET` | ⚠️ 재생성 권장 | 새로 생성해도 로컬 DB 데이터는 유지되며 기존 브라우저 쿠키만 무효화됨(재로그인 한 번이면 됨). 굳이 옮길 필요 없음. |
| `DATABASE_URL` | ✅ 동일 | 로컬 Docker Compose는 양쪽 동일 (`postgresql+asyncpg://saengibu:saengibu@localhost:5432/saengibu`). |
| `ALLOWED_EMAIL_DOMAINS` | ✅ 동일 | 학교 도메인 정책이 같다면 그대로. |

**`.env`는 절대 Git에 커밋하지 않는다.** 안전한 인계 방법:

- **1Password / Bitwarden** 보안 항목에 `backend/.env` 전체 복사 → 새 머신에서 붙여넣기 (권장)
- **GPG 암호화**: `gpg -c backend/.env` → 암호화된 파일을 클라우드/USB → `gpg -d backend/.env.gpg > backend/.env`
- 같은 LAN 내 `scp`: `scp backend/.env macmini.local:~/Projects/anti2/apps/saengibu-portal/backend/.env`
- 위 모두 불가능하면 `.env.example` 따라 직접 입력 (4절)

❌ Slack/이메일/메신저 평문, GitHub Issue/PR 본문, 스크린샷 — 모두 금지.

## 4. 환경 변수 파일

### 4-1. Backend

```bash
cp backend/.env.example backend/.env
```

`backend/.env` 에서 다음을 수정:

```ini
ENVIRONMENT=development
DATABASE_URL=postgresql+asyncpg://saengibu:saengibu@localhost:5432/saengibu

# 반드시 32자 이상의 랜덤 문자열로 교체
SESSION_SECRET=<openssl rand -base64 48 결과로 교체>

# 개발용은 false, HTTPS 배포 시 true
COOKIE_SECURE=false
COOKIE_SAMESITE=strict

# 3단계에서 발급받은 값
GOOGLE_CLIENT_ID=1234-xxxxx.apps.googleusercontent.com

# 학교 도메인만 가입 허용 (비워두면 모든 도메인 허용 = dev 편의)
ALLOWED_EMAIL_DOMAINS=

# 외부 LLM 차단 기본값 (Sprint 0에서는 건드리지 않음)
LLM_EXTERNAL_ENABLED=false
```

Secret 생성 예:

```bash
openssl rand -base64 48
# 또는
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

### 4-2. Frontend

```bash
cp frontend/.env.example frontend/.env.local
```

`frontend/.env.local`:

```ini
NEXT_PUBLIC_API_BASE=/api/v1
NEXT_PUBLIC_GOOGLE_CLIENT_ID=1234-xxxxx.apps.googleusercontent.com
BACKEND_URL=http://localhost:8000
```

**Client ID 는 backend/frontend 양쪽 동일해야 한다.**

## 5. Postgres + Redis 기동

```bash
docker compose -f docker-compose.dev.yml up -d
docker compose -f docker-compose.dev.yml ps
```

컨테이너 상태:

```
saengibu-pg     Up (healthy)   0.0.0.0:5432->5432/tcp
saengibu-redis  Up             0.0.0.0:6379->6379/tcp
```

Postgres 접속 확인:

```bash
docker exec -it saengibu-pg psql -U saengibu -d saengibu -c "SELECT 1"
```

## 6. 의존성 설치

### Backend (루트에서 이미 `uv sync` 했다면 건너뛰기)

```bash
# 프로젝트 루트에서
cd ../..         # anti2/
uv sync --frozen   # uv.lock 그대로 재현 (불일치 시 실패하므로 핸드오프에 권장)
```

개발 도구까지 포함:

```bash
uv pip install --package saengibu-portal-backend -e .[dev]
```

### Frontend

```bash
cd apps/saengibu-portal/frontend
pnpm install --frozen-lockfile   # pnpm-lock.yaml 그대로 재현
cd ..
```

> **lockfile mismatch로 실패 시**: 의존성을 의도적으로 추가/변경한 경우라면 `--frozen` 플래그를 빼고 설치한 뒤 lockfile을 별도 커밋한다. 핸드오프(다른 머신에서 동일 환경 재현)에서는 항상 `--frozen` 사용.

## 7. 마이그레이션 + 시드

```bash
# apps/saengibu-portal/
make migrate       # alembic 0001~0011 전체 적용
make seed          # 성당중학교 + 담임 + 학생 4명 + 결재 4건 시드
```

또는 수동:

```bash
cd backend
uv run --package saengibu-portal-backend alembic upgrade head
uv run --package saengibu-portal-backend saengibu demo-seed
cd ..
```

검증:

```bash
docker exec -it saengibu-pg psql -U saengibu -d saengibu -c "\
  SELECT school_level, grade, subject_code, count(*) \
    FROM achievement_standards \
   GROUP BY 1,2,3 ORDER BY 1,2,3;"
```

다음과 유사하게 출력되어야 함:
```
 school_level | grade | subject_code | count
--------------+-------+--------------+-------
 middle       |     1 | 국어         |     5
 middle       |     1 | 수학         |     6
 middle       |     1 | 영어         |     4
 middle       |     1 | 과학         |     2
 ...
```

## 8. 서버 기동 (터미널 2개 필요)

**터미널 A — 백엔드**:

```bash
cd apps/saengibu-portal
make backend
# → Uvicorn running on http://0.0.0.0:8000
```

`http://localhost:8000/health` 접속 → `{"status":"ok","db":{"ok":true}}` 확인.

**터미널 B — 프론트**:

```bash
cd apps/saengibu-portal
make frontend
# → Next.js ready on http://localhost:3000
```

## 9. 첫 로그인 (승인제)

1. 브라우저에서 `http://localhost:3000` → `/login` 리다이렉트
2. **Google 계정으로 로그인** 클릭 → 구글 계정 선택
   - `ALLOWED_EMAIL_DOMAINS=` 가 비어 있으면 어떤 구글 계정이든 허용
3. 첫 로그인이므로 `/pending` 이동 (관리자 승인 대기)

### 관리자 승인

현재 시드된 관리자(`admin@sd.ms.kr`) 계정의 구글 로그인이 어려우면,
**직접 DB에서 본인 계정을 활성화**하는 것이 가장 빠릅니다.

```bash
docker exec -it saengibu-pg psql -U saengibu -d saengibu
```

```sql
-- 본인 이메일 확인 + 활성화
UPDATE users SET status = 'active' WHERE email = '본인구글이메일@gmail.com';

-- 관리자 역할 부여 (승인 큐를 UI로 쓰려면)
INSERT INTO role_assignments (user_id, role, started_at)
SELECT id, 'admin', now() FROM users WHERE email = '본인구글이메일@gmail.com';
INSERT INTO role_assignments (user_id, role, started_at)
SELECT id, 'homeroom', now() FROM users WHERE email = '본인구글이메일@gmail.com';
\q
```

브라우저 새로고침 → `/records` 이동 → 승인 대기열 확인 가능.

## 10. 주요 화면 확인

| URL | 설명 |
|---|---|
| `/login` | 구글 로그인 |
| `/pending` | 관리자 승인 대기 |
| `/dashboard` | 홈 (통계 카드 + 내 결재 대기) |
| `/records` | 결재 대기열 (시드 4건) |
| `/writer` | 세특 작성 진입 |
| `/writer/new/subject` | 6단계 위저드 |
| `/homeroom` | 담임 전용 영역 카드 |
| `/library` | 성취기준 동적 로딩 + 5단계 Drawer |
| `/board` | 공지·게시판 |
| `/settings` | 내 정보 + 보안 상태 |

OpenAPI 문서: `http://localhost:8000/docs` (개발 환경만 노출)

## 11. 자주 발생하는 문제

### `database "saengibu" does not exist`
- 최초 `docker compose up` 직후 healthcheck 완료 전 `make migrate` 시도. 10초 후 재시도.

### `invalid session token: …`
- `SESSION_SECRET` 바뀐 후 브라우저 쿠키 잔존. 시크릿 창 또는 DevTools → Application → Cookies 삭제.

### 로그인 후 `/pending` 무한루프
- `users.status`가 `pending` 상태 유지. DB에서 `status='active'` 로 업데이트.

### `google_client_id is not configured`
- `backend/.env`의 `GOOGLE_CLIENT_ID` 비어 있음 또는 서버 재기동 안 됨. `make backend` 재실행.

### 포트 충돌 (3000/5432/6379/8000)
- `docker compose ps` / `lsof -i :PORT` 로 기존 프로세스 종료.

### macOS: `corepack enable` 권한 오류
- Homebrew Node(`brew install node@20`) 사용 시 사용자 권한으로 동작. 공식 Node 인스톨러로 설치한 경우 `/usr/local/bin` shim 권한 충돌이 날 수 있음 → Node 설치 방식을 Homebrew로 통일 권장.

### macOS: `docker-compose: command not found`
- 본 프로젝트는 Compose v2 (`docker compose`, 공백) 사용. Docker Desktop for Mac 실행 후 `docker compose version` 출력 확인. 구형 `docker-compose`(하이픈)는 사용 안 함.

### macOS: 로컬 `psql` 명령이 없음
- 별도 PostgreSQL 클라이언트 설치 불필요. 본 가이드의 `docker exec -it saengibu-pg psql ...` 명령을 그대로 사용하면 컨테이너 내부 `psql`이 동작. 호스트에서 직접 쓰고 싶다면 `brew install libpq && brew link --force libpq`.

### macOS: pull 직후 `git status`에 dirty 파일이 잔뜩 뜸
- 라인엔딩(CRLF) 또는 실행권한 차이. 2-a 절의 점검 명령으로 원인 확인 후 `git add --renormalize .` 정규화.

### Alembic 다운그레이드 필요
```bash
cd backend
uv run --package saengibu-portal-backend alembic downgrade base
uv run --package saengibu-portal-backend alembic upgrade head
```

## 12. 완전 초기화 (데이터 전부 삭제)

```bash
# Postgres 볼륨까지 제거
docker compose -f docker-compose.dev.yml down -v

# 재기동 + 마이그레이션 + 시드
docker compose -f docker-compose.dev.yml up -d
sleep 8
make migrate
make seed
```

## 13. 검증 체크리스트

- [ ] `curl http://localhost:8000/health` → `{"status":"ok"}`
- [ ] `curl http://localhost:8000/docs` → Swagger UI 로드
- [ ] `http://localhost:3000/login` → 구글 버튼 표시
- [ ] 구글 로그인 성공 → `/pending` 이동
- [ ] DB에서 `status='active'` 업데이트 후 새로고침 → `/records` 승인 대기 테이블 표시
- [ ] `/library` → 학년·과목 필터 조작 시 네트워크 요청 발생 (`/api/v1/standards?...`)
- [ ] `make verify-standards` → `data/reports/coverage_YYYY-MM-DD.md` 생성

## 14. 다음 단계

- `BACKEND_FRONTEND_INTEGRATION.md` — 통신 구조·프록시·인증 흐름 상세
- `docs/ARCHITECTURE.md` — C4 Level 1~2
- `docs/API.md` — 엔드포인트 명세
- `docs/AI_PIPELINE.md` — 6단계 피드백 엔진
