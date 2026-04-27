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
uv sync
```

개발 도구까지 포함:

```bash
uv pip install --package saengibu-portal-backend -e .[dev]
```

### Frontend

```bash
cd apps/saengibu-portal/frontend
pnpm install
cd ..
```

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
