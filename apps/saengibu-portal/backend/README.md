# saengibu-portal backend

FastAPI 백엔드. `saengibu-portal-backend` uv workspace member.
Google OAuth 2.0 + 승인제, httpOnly 쿠키 세션, CSRF, Postgres RLS, 감사 해시 체인.

## 실행

```bash
# 1. Postgres·Redis 기동 (루트에서)
cd apps/saengibu-portal
docker compose -f docker-compose.dev.yml up -d

# 2. 환경 변수
cp backend/.env.example backend/.env
#   - SESSION_SECRET 32자+ 랜덤으로 교체
#   - GOOGLE_CLIENT_ID 구글 Cloud에서 발급한 값
#   - ALLOWED_EMAIL_DOMAINS=sd.ms.kr  (또는 학교 도메인)

# 3. 의존성 동기화 (루트에서)
cd ../..
uv sync

# 4. 마이그레이션
cd apps/saengibu-portal/backend
uv run --package saengibu-portal-backend alembic upgrade head

# 5. 데모 시드 (성당중학교 + 담임 + 학생 4명 + 결재 대기 4건)
uv run --package saengibu-portal-backend saengibu demo-seed

# 6. 서버 기동
uv run --package saengibu-portal-backend uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 7. 헬스체크
curl http://localhost:8000/health
# → {"status":"ok","db":{"ok":true}}
```

## Google OAuth 설정

1. https://console.cloud.google.com/ → API 및 서비스 → 사용자 인증 정보
2. OAuth 2.0 클라이언트 ID 생성 (웹 애플리케이션)
3. 승인된 JavaScript 원본: `http://localhost:3000`
4. 리디렉션 URI는 **설정 불필요** (GIS one-tap 방식 사용)
5. 발급된 **클라이언트 ID**를 `backend/.env` 의 `GOOGLE_CLIENT_ID` 와
   `frontend/.env.local` 의 `NEXT_PUBLIC_GOOGLE_CLIENT_ID` 양쪽에 설정

## 인증 흐름

```
[Frontend] Google 로그인 버튼 → ID Token 받음
    │
    ▼
POST /api/v1/auth/google { credential: <idToken> }
    │
    ▼
[Backend]
  1. google-auth로 ID Token 서명·발행자·audience 검증
  2. 학교 도메인 화이트리스트 확인
  3. users 조회/생성 (신규는 status='pending')
  4. JWT 발급 → httpOnly + SameSite=Strict 쿠키로 Set-Cookie
  5. CSRF 토큰도 동시 발급 (일반 쿠키, JS 읽기 가능 → x-csrf-token 헤더)
    │
    ▼
Frontend:
  - me.status === 'pending' → /pending 페이지
  - me.status === 'active'  → /records 페이지
```

## API

- `POST /api/v1/auth/google` — Google ID Token 검증·세션 발급
- `GET  /api/v1/auth/me` — 현재 사용자 (pending 포함 반환)
- `POST /api/v1/auth/logout` — 세션 쿠키 삭제
- `GET  /api/v1/users/pending` — 승인 대기 목록 (관리자)
- `POST /api/v1/users/{id}/approval` — 승인/반려 (관리자)
- `GET  /api/v1/reviews/assigned` — 내 결재 대기 목록
- `POST /api/v1/reviews/{review_id}/steps/{step_no}/decide` — 승인/반려
- `GET  /api/v1/dashboard/teacher` — 교사 대시보드 통계
- `GET  /api/v1/guidelines` — 기재요령 안내 (전 학교 공용)
- `GET  /api/v1/school-decisions` — 학교 결정사항

## 보안 체크리스트

- [x] 모든 세션 토큰은 httpOnly + Secure + SameSite=Strict 쿠키
- [x] CSRF: JWT 클레임에 csrf 값 포함 + `x-csrf-token` 헤더 이중 제출 검증
- [x] 구글 ID Token 발행자·email_verified 검증
- [x] 학교 이메일 도메인 화이트리스트
- [x] 관리자 승인 게이트 (pending → active)
- [x] 모든 요청에 PG `SET LOCAL app.school_id` (RLS 준비)
- [x] 감사 로그 해시 체인 (prev_hash → content_hash SHA-256)
- [x] CSP / X-Frame-Options / HSTS / Referrer-Policy
- [x] 외부 LLM 기본 차단 (`LLM_EXTERNAL_ENABLED=false`)
- [ ] 모든 도메인 테이블에 RLS 정책 (후속 마이그레이션에서 활성화)
- [ ] 컬럼 암호화 (학생 성명·교직원 번호) — 배포 전 pgcrypto 적용
- [ ] WAF/Rate Limit — 배포 시 Caddy/Nginx 레이어
- [ ] 감사 로그 S3 Object Lock (WORM) — 운영 단계

## 테스트

```bash
uv run --package saengibu-portal-backend pytest
```

## 린트

```bash
uv run --package saengibu-portal-backend ruff check .
uv run --package saengibu-portal-backend ruff format .
uv run --package saengibu-portal-backend mypy app
```
