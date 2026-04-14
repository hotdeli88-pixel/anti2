# saengibu-portal — 학교생활기록부 포털

> 교사가 먼저 쓰고 → AI가 피드백. 외부 유출 금지 · Google 승인제 로그인 · 훈령 제555호 준수.

## 개요

한국 중·고등학교 교사의 생기부 작성·검토·NEIS 입력 전 과정을 지원하는 통합 포털.

- **보안 최우선**: 학교 구성원 외 접근 차단, 학생 정보 외부 유출 방지
- **Google 승인제 로그인**: 학교 도메인 이메일 + 관리자 수동 승인
- **AI는 피드백만**: 대신 써주지 않음, 훈령 2026 신설 조항 준수
- **1검 → 2검 → 3검 → NEIS 복사** 워크플로우 네이티브 지원

## 빠른 시작 (로컬 데모)

```bash
# 루트에서
cd apps/saengibu-portal

# 1. Postgres + Redis
docker compose -f docker-compose.dev.yml up -d

# 2. 의존성
cd ../..
uv sync
cd apps/saengibu-portal/frontend && pnpm install && cd ../..

# 3. Google OAuth Client ID 발급
#    https://console.cloud.google.com/ → 웹 애플리케이션 → 원본: http://localhost:3000
cp apps/saengibu-portal/backend/.env.example apps/saengibu-portal/backend/.env
cp apps/saengibu-portal/frontend/.env.example apps/saengibu-portal/frontend/.env.local
# 양쪽 파일에 같은 CLIENT_ID 설정

# 4. 마이그레이션 + 데모 시드
cd apps/saengibu-portal/backend
uv run --package saengibu-portal-backend alembic upgrade head
uv run --package saengibu-portal-backend saengibu demo-seed
cd ..

# 5. 백엔드·프론트 동시 실행 (2개 터미널)
make backend    # http://localhost:8000
make frontend   # http://localhost:3000
```

- 첫 로그인: 어떤 구글 계정이든 로그인 → `/pending` 으로 이동 (관리자 승인 대기)
- 시드된 `admin@sd.ms.kr` 계정으로 로그인하려면 해당 구글 계정이 있어야 함 (또는 `ALLOWED_EMAIL_DOMAINS`를 비워 모든 도메인 허용 후 자신의 구글 계정으로 로그인 → DB에서 `status='active'`, `role='admin'` 수동 설정)

## 기술 스택

| 레이어 | 선택 |
|---|---|
| Frontend | Next.js 15 (App Router) · TypeScript · Tailwind · Pretendard |
| Auth | Google OAuth 2.0 (`@react-oauth/google`) · httpOnly 쿠키 세션 · CSRF 이중 제출 |
| Backend | FastAPI 0.115+ · Python 3.11 · SQLAlchemy 2.0 async · Alembic |
| DB | PostgreSQL 16 + pgcrypto (RLS 전 테이블, 감사 해시 체인) |
| 보안 | CSP strict · HSTS · SameSite=Strict · TrustedHost |
| 옵션(후속) | pgvector · Celery · Casbin · Anthropic/OpenAI (LLM 외부 차단 기본) |

## 구조

```text
apps/saengibu-portal/
├── docker-compose.dev.yml     Postgres + Redis
├── Makefile                   up/down/migrate/seed/backend/frontend
├── backend/
│   ├── app/
│   │   ├── main.py            FastAPI 엔트리 (보안 미들웨어)
│   │   ├── core/              config · db · security · deps · cookies · logging
│   │   ├── models/            SQLAlchemy: school · user · student · record · review · feedback · guideline · audit
│   │   ├── schemas/           Pydantic v2
│   │   ├── api/v1/            auth · users · reviews · dashboard · content
│   │   ├── services/
│   │   │   ├── byte/          cp949_counter (NEIS 호환)
│   │   │   ├── workflow/      fsm (상태 머신)
│   │   │   ├── audit/         logger (해시 체인)
│   │   │   └── mask/          pii (전교 학생 사전)
│   │   └── cli.py             `saengibu init-school`, `demo-seed`
│   └── alembic/               0001 baseline · 0002 section_types · 0003 guidelines
├── frontend/
│   ├── app/                   login · pending · records · dashboard · settings
│   ├── components/            layout · ui · records
│   └── lib/                   api · queries · cn
└── docs/                      ARCHITECTURE · ERD · API · AI_PIPELINE · RBAC · WORKFLOW · FRONTEND
```

## API

- `POST /api/v1/auth/google` — Google ID Token 검증 · 세션 발급
- `GET  /api/v1/auth/me` · `POST /api/v1/auth/logout`
- `GET  /api/v1/users/pending` · `POST /api/v1/users/{id}/approval` (관리자)
- `GET  /api/v1/reviews/assigned?status_filter=` — 내 결재 대기
- `POST /api/v1/reviews/{id}/steps/{n}/decide` — 승인/반려
- `GET  /api/v1/dashboard/teacher` — 통계
- `GET  /api/v1/guidelines` · `GET /api/v1/school-decisions` — 안내·공지

## 보안 체크리스트

- [x] Google OAuth 2.0 + email_verified + 도메인 화이트리스트
- [x] 관리자 승인 게이트 (pending → active)
- [x] httpOnly + Secure + SameSite=Strict 쿠키 (JWT 저장소는 쿠키 전용)
- [x] CSRF 이중 제출 토큰 (x-csrf-token 헤더)
- [x] CSP strict + HSTS + X-Frame-Options: DENY
- [x] 모든 요청에 `SET LOCAL app.school_id` (RLS 준비)
- [x] 감사 로그 해시 체인 (SHA-256, prev_hash 연결)
- [x] 외부 LLM 호출 기본 차단 (`LLM_EXTERNAL_ENABLED=false`)
- [x] 학생 실명 마스킹 사전 (학교·학년도 전체)
- [ ] 도메인 테이블 RLS 정책 활성화 (후속 마이그레이션)
- [ ] 학생 성명·주민번호 컬럼 암호화 (pgcrypto)
- [ ] 감사 로그 S3 Object Lock
- [ ] Rate Limiting (Caddy/Nginx)

## 커밋 규칙

Conventional Commits, 범위는 `saengibu-portal`:

```
feat(saengibu-portal): Google OAuth 승인제 로그인
fix(saengibu-portal): Byte 카운터 CRLF 계산 오류
docs(saengibu-portal): 보안 체크리스트 보강
```

## 상세 문서

- [ARCHITECTURE.md](./docs/ARCHITECTURE.md) · [ERD.md](./docs/ERD.md) · [API.md](./docs/API.md)
- [AI_PIPELINE.md](./docs/AI_PIPELINE.md) · [RBAC.md](./docs/RBAC.md)
- [WORKFLOW_1_2_3_REVIEW.md](./docs/WORKFLOW_1_2_3_REVIEW.md) · [FRONTEND.md](./docs/FRONTEND.md)
- [backend/README.md](./backend/README.md) · [frontend/README.md](./frontend/README.md)
