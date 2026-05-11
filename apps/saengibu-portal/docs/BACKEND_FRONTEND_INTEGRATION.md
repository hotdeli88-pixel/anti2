# BACKEND_FRONTEND_INTEGRATION — 통신·인증·배포 가이드

> 프론트(Next.js 15) ↔ 백엔드(FastAPI) 연결 방식, 동일 오리진 프록시,
> 인증/세션/CSRF 흐름, 배포 시 고려사항을 한 번에 정리.

## 0. 전체 토폴로지

### 개발 환경 (동일 오리진 프록시)

```
[브라우저 http://localhost:3000]
        │
        │ 동일 오리진 모든 요청
        ▼
[Next.js dev server :3000]
        │
        │ /api/v1/*  → rewrite
        ▼
[FastAPI :8000]
        ├── PostgreSQL :5432
        └── Redis :6379
```

### 프로덕션 옵션 A — 동일 도메인 (권장)

```
https://portal.school.kr/
  │
  ├─ /          → Next.js (Vercel / Node / Caddy)
  └─ /api/v1/*  → FastAPI (reverse proxy)
```

**장점**: CORS 불필요, httpOnly 쿠키 자연 전달, CSP 설정 단순.

### 프로덕션 옵션 B — 분리 도메인

```
https://app.school.kr       → Next.js
https://api.school.kr       → FastAPI
```

**필요**: CORS `allow_credentials=true` + `SameSite=None; Secure` 쿠키 + 프론트 서브도메인 일치.

---

## 1. 동일 오리진 프록시 (핵심 메커니즘)

### `frontend/next.config.ts`

```ts
async rewrites() {
  return [
    { source: "/api/:path*", destination: `${API_PROXY}/api/:path*` },
  ];
},
```

- `API_PROXY = process.env.BACKEND_URL ?? "http://localhost:8000"`
- 브라우저는 `/api/v1/standards` 로 요청 → Next 서버가 `http://localhost:8000/api/v1/standards` 로 내부 프록시 → 응답을 그대로 반환.
- **브라우저 입장에서는 `3000` 한 오리진**만 존재. 쿠키·CSP·CORS 모두 편리해짐.

### 클라이언트 호출 규칙

`frontend/lib/api.ts`:

```ts
const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "/api/v1";
// → 브라우저에서 항상 "/api/v1/..."로 호출. 절대 URL 금지.
fetch(`${API_BASE}${path}`, { credentials: "include", ... });
```

---

## 2. 인증 흐름 (Google OAuth + 승인제)

### 2-1. 시퀀스

```
[Frontend /login]
   │  Google 버튼 클릭
   ▼
[Google GIS] → ID Token (JWT) 리턴
   │
   ▼
[Frontend] POST /api/v1/auth/google
           body: { credential: <id_token> }
           credentials: include
   │
   ▼
[Backend auth.py::google_login]
   ├─ google-auth로 ID Token 서명 검증
   ├─ issuer (accounts.google.com), email_verified 확인
   ├─ ALLOWED_EMAIL_DOMAINS 화이트리스트 체크
   ├─ users 조회/생성
   │   ├─ 신규: status='pending' + UserApproval row
   │   └─ 기존: google_sub/picture 갱신
   ├─ active_roles_from_user() 메모리 필터
   ├─ JWT 생성 (sub, sid, roles, csrf, iat, exp)
   └─ Set-Cookie: saengibu_session (httpOnly) + csrf_token (JS 읽기 가능)
   │
   ▼
[Frontend]
   ├─ me.status === 'pending' → router.push('/pending')
   └─ me.status === 'active'  → router.push('/records')
```

### 2-2. 쿠키 정책 (`backend/app/core/cookies.py`)

| 쿠키 | httpOnly | SameSite | Secure | 용도 |
|---|---|---|---|---|
| `saengibu_session` | **true** | strict | `COOKIE_SECURE` 설정값 | JWT 본체 (XSS로 탈취 불가) |
| `csrf_token` | **false** | strict | 동일 | JS가 읽어 `x-csrf-token` 헤더에 실음 |

### 2-3. CSRF 이중 제출 (Double Submit)

- POST/PATCH/DELETE 등 **non-safe 메서드** 호출 시:
  1. 프론트가 `csrf_token` 쿠키 값을 읽어 `x-csrf-token` 헤더에 설정 (`lib/api.ts`)
  2. 백엔드 `deps.py:_load_session`이 JWT 내 `csrf` 클레임과 헤더 값 일치 확인
  3. 불일치 시 **403** `auth.csrf_mismatch`

### 2-4. 세션 로테이션 (C-4)

- 세션 발급 시점 기준 잔여 수명 **25% 미만**이면 다음 요청 응답에 새 JWT + 새 CSRF Set-Cookie.
- 구현: `core/security.py:should_rotate_session()` + `core/deps.py:_load_session()`.
- 효과: 탈취된 CSRF 토큰의 공격 윈도우 축소.

---

## 3. 환경 변수 매트릭스

| 변수 | 어디 | 용도 |
|---|---|---|
| `DATABASE_URL` | backend/.env | asyncpg DSN |
| `SESSION_SECRET` | backend/.env | JWT HMAC 서명 키 (32자+) |
| `COOKIE_SECURE` | backend/.env | 개발 `false`, 프로덕션 `true` |
| `COOKIE_SAMESITE` | backend/.env | 기본 `strict`, 분리 도메인이면 `none` |
| `COOKIE_DOMAIN` | backend/.env | 분리 도메인 배포 시 공용 루트 도메인 설정 (예: `.school.kr`) |
| `GOOGLE_CLIENT_ID` | backend/.env + frontend/.env.local | **양쪽 동일해야 함** |
| `ALLOWED_EMAIL_DOMAINS` | backend/.env | 학교 도메인 화이트리스트 |
| `CORS_ORIGINS` | backend/.env | 분리 도메인 배포 시 프론트 URL (콤마 구분) |
| `NEXT_PUBLIC_API_BASE` | frontend/.env.local | 기본 `/api/v1` (동일 오리진) |
| `NEXT_PUBLIC_GOOGLE_CLIENT_ID` | frontend/.env.local | 구글 로그인 버튼용, 백엔드와 동일 ID |
| `BACKEND_URL` | frontend/.env.local | Next rewrite 대상 (기본 `http://localhost:8000`) |

**`NEXT_PUBLIC_` 접두사**는 브라우저 번들에 포함됨 (시크릿 넣지 말 것).

---

## 4. CORS 설정

### 동일 오리진 (개발·프로덕션 A)

```ini
# backend/.env
CORS_ORIGINS=
```

→ `backend/app/main.py`에서 `cors_origins_list`가 빈 리스트이므로 `CORSMiddleware` 미장착.

### 분리 도메인 (프로덕션 B)

```ini
CORS_ORIGINS=https://app.school.kr,https://admin.school.kr
COOKIE_DOMAIN=.school.kr
COOKIE_SECURE=true
COOKIE_SAMESITE=lax   # 'none'은 서브도메인 간에도 허용하나 CSRF 보호 약화
```

`main.py` 미들웨어 체인:

```python
CORSMiddleware(
    allow_origins=cors_origins_list,
    allow_credentials=True,   # ← 쿠키 전송에 필수
    allow_methods=["GET","POST","PATCH","DELETE","OPTIONS"],
    allow_headers=["authorization","content-type","x-csrf-token"],
)
```

---

## 5. 데이터 흐름 예시

### 5-1. 읽기: 성취기준 조회

```
[브라우저] useStandards({ grade: 1, subject: "수학" })
    │
    ▼
[lib/api.ts] fetch("/api/v1/standards?grade=1&subject=%EC%88%98%ED%95%99")
             credentials: "include"
    │
    ▼ (Next rewrite)
[FastAPI] GET /api/v1/standards
    ├─ Depends(current_user) → 세션·CSRF 불필요(GET)
    ├─ SET LOCAL app.school_id = <user.school_id>   (RLS 준비)
    ├─ SELECT * FROM achievement_standards WHERE ...
    └─ Response: { items: [...], next_cursor: "..." }
    │
    ▼
[TanStack Query] queryKey ["standards", filter] 에 캐시 (staleTime 10분)
```

### 5-2. 쓰기: 결재 승인

```
[브라우저] useApprove().mutate({ reviewId, stepNo: 1 })
    │
    ▼
[lib/api.ts]
   ├─ getCsrfToken() → csrf_token 쿠키 읽기
   └─ POST /api/v1/reviews/{id}/steps/1/decide
      headers: {
        "content-type": "application/json",
        "x-csrf-token": <csrf>,
      }
      body: { "decision": "approved" }
      credentials: "include"
    │
    ▼
[FastAPI reviews.py::decide_step]
   ├─ current_user → JWT 검증 → CSRF 일치 → user/roles 로드
   ├─ review + record 조회, step_no 범위 검증 (422)
   ├─ record.status 유효성 (409)
   ├─ expected_role ∈ user.roles (403)
   ├─ FSM.next_status(record.status, APPROVE)
   ├─ step.decision='approved', step.decided_at=now
   ├─ write_audit(...)  (해시 체인 보존)
   └─ db.commit() → { status: "review_2" }
    │
    ▼
[TanStack Query] onSuccess → invalidate ["approvals","dashboard"]
```

---

## 6. Frontend 훅 ↔ Backend 라우터 매핑

| 프론트 훅 (`lib/queries.ts`) | HTTP | 백엔드 경로 (`api/v1/`) |
|---|---|---|
| `useMe()` | GET | `/auth/me` |
| `useGoogleLogin()` | POST | `/auth/google` |
| `useLogout()` | POST | `/auth/logout` |
| `useDashboardStats()` | GET | `/dashboard/teacher` |
| `useApprovals(status?)` | GET | `/reviews/assigned?status_filter=` |
| `useApprove()` | POST | `/reviews/{id}/steps/{n}/decide` |
| `useReject()` | POST | 동일, `body.decision="rejected"` |
| `useGuidelines()` | GET | `/guidelines` |
| `useSchoolDecisions()` | GET | `/school-decisions` |
| `useStandards(filter)` | GET | `/standards?...&cursor=&limit=` |
| `useStandard(id)` | GET | `/standards/{id}` |
| `useStandardLevels(id)` | GET | `/standards/{id}/levels` |
| `useDomainLevels(f)` | GET | `/domain-levels` |
| `useCurricula()` | GET | `/curricula` |

새 훅 추가 시 **이 표를 같이 업데이트** (`docs/API.md`와 함께).

---

## 7. 에러 응답 (RFC 7807)

모든 백엔드 에러는 동일 구조:

```json
{
  "type": "auth.csrf_mismatch",
  "title": "CSRF 토큰 불일치",
  "detail": null,
  "status": 403,
  "instance": "/api/v1/reviews/abc/steps/1/decide"
}
```

프론트 `ApiError` 에서 `.problem.type` 으로 분기 (예: `auth.account_pending` → `/pending` 리다이렉트).

### 주요 `type` 카탈로그

| type | 상태 | 프론트 처리 |
|---|---|---|
| `auth.unauthenticated` | 401 | `/login` |
| `auth.invalid_token` | 401 | 세션 쿠키 삭제 + `/login` |
| `auth.csrf_mismatch` | 403 | 페이지 새로고침 |
| `auth.account_pending` | 403 | `/pending` |
| `rbac.forbidden` | 403 | Toast "권한 없음" |
| `workflow.invalid_transition` | 409 | Toast + 목록 갱신 |
| `review.invalid_step_no` | 422 | Toast |
| `validation.error` | 422 | 폼 필드 하이라이트 |

---

## 8. 타입 동기화 (Pydantic → TypeScript)

현재는 **수동 동기화**:
- 백엔드 `schemas/standards.py` → 프론트 `types/standards.ts`

자동화 옵션 (후속 PR):

```bash
# 개발 환경에서
curl http://localhost:8000/openapi.json > openapi.json
npx openapi-typescript openapi.json -o frontend/types/openapi.d.ts
```

CI에서 diff 감지 → PR 차단으로 스키마 drift 방지 가능.

---

## 9. 쿠키 디버깅 체크리스트

로그인 후 쿠키가 전달되지 않으면:

1. **브라우저 DevTools → Application → Cookies → `http://localhost:3000`**
   - `saengibu_session` 있음? (httpOnly 🔒)
   - `csrf_token` 있음? (httpOnly 없음 — JS가 읽을 수 있어야 함)
2. **Network 탭 → 요청 헤더**에 `Cookie:` 들어 있나?
3. `fetch` 호출에 `credentials: "include"` 있나? (`lib/api.ts`에 기본 적용됨)
4. POST/PATCH 요청에 `x-csrf-token` 헤더 있나?
5. `backend/.env` 의 `COOKIE_DOMAIN` 이 비어 있고 localhost면 정상, 도메인 지정 시 정확한지 확인.

---

## 10. 로컬 API 직접 호출 (curl)

Swagger UI (`http://localhost:8000/docs`) 가 가장 편하지만, 스크립트 검증 시:

```bash
# 1. 로그인은 구글 토큰이 필요하므로 스크립트로 테스트 시 DB 직접 활성화 후
#    세션 발급을 스킵하고 내부 토큰 방식을 검토. 또는 프론트에서 로그인 후 쿠키 복사.

# 브라우저에서 로그인 후 DevTools → Application → Cookies 에서
# saengibu_session 과 csrf_token 값 복사해 다음과 같이:

SESSION="eyJ..."
CSRF="abcd..."

curl -s http://localhost:8000/api/v1/auth/me \
  -H "Cookie: saengibu_session=$SESSION; csrf_token=$CSRF" \
  | jq

curl -s "http://localhost:8000/api/v1/standards?grade=1&subject=수학" \
  -H "Cookie: saengibu_session=$SESSION; csrf_token=$CSRF" \
  | jq
```

POST 요청은 `-H "x-csrf-token: $CSRF"` 필수.

---

## 11. 보안 체크리스트 (배포 전)

- [ ] `SESSION_SECRET` 최소 32자 랜덤, **교체 시 모든 세션 무효화**
- [ ] `COOKIE_SECURE=true` + HTTPS 강제 (HSTS 활성화됨)
- [ ] `ALLOWED_EMAIL_DOMAINS` 학교 도메인으로 설정
- [ ] `CORS_ORIGINS` 에 프로덕션 프론트 URL만 포함
- [ ] 프로덕션 환경에서 `/docs`·`/openapi.json` 비활성 (이미 `environment != development` 조건부)
- [ ] `TrustedHostMiddleware` 의 `allowed_hosts` 실제 도메인만
- [ ] PostgreSQL SSL 강제 + 슈퍼유저 제한
- [ ] Google OAuth 동의 화면 게시 상태 "프로덕션" 으로 승인
- [ ] 로그 보관 주기 설정 (준영구 감사 로그 + 일반 로그 30일)

---

## 12. 배포 예시 — 단일 서버 (동일 도메인)

```
[Caddy]
  portal.school.kr
    ├── handle /api/*    → reverse_proxy localhost:8000
    └── handle           → reverse_proxy localhost:3000

[Docker Compose]
  nextjs-frontend (pnpm start)
  fastapi-backend (uvicorn)
  postgres-16
  redis-7
```

Caddyfile 최소 예:

```caddy
portal.school.kr {
    encode gzip
    handle /api/* {
        reverse_proxy localhost:8000
    }
    handle {
        reverse_proxy localhost:3000
    }
    header {
        Strict-Transport-Security "max-age=63072000; includeSubDomains; preload"
        X-Content-Type-Options "nosniff"
    }
}
```

Next.js가 이미 CSP/HSTS/X-Frame-Options 헤더를 송출하므로 중복 설정 주의.

---

## 13. 관측성 (현재 기본 구조)

- **백엔드 로그**: `structlog` JSON (stdout)
- **프론트 로그**: `console.error` + next.js 로그
- **감사 로그**: `audit_logs` 테이블 (해시 체인)
- **메트릭**: Prometheus 미도입 (후속 PR에서 Stage 1~5 latency·LLM 비용 추가 예정)

---

## 14. FAQ

### Q. CORS 에러가 납니다.
- 동일 오리진 권장 (`/api/:path*` rewrite). 분리 도메인 시 `CORS_ORIGINS` + `COOKIE_SAMESITE=none` + `COOKIE_SECURE=true` 3종 세트 확인.

### Q. 로그인 성공 후 `/auth/me` 가 401.
- 쿠키가 전송되지 않음. `credentials: "include"` 확인 + `COOKIE_DOMAIN` 설정 검토.

### Q. 같은 기기에서 두 계정 동시 로그인.
- 권장하지 않음 (쿠키는 도메인당 1개 세션). 브라우저 프로필 분리 사용.

### Q. 개발 환경에서 `COOKIE_SECURE=true` 로 설정하면?
- HTTP localhost 에서 브라우저가 쿠키 저장 거부. 반드시 `false`.

### Q. Next.js 빌드 시 `NEXT_PUBLIC_GOOGLE_CLIENT_ID` 가 비어 있으면?
- 런타임에 `login/page.tsx` 에서 "구글 로그인 비활성" 배너 표시 (M-7). 빌드는 통과.

### Q. 여러 학교를 동시에 서비스?
- 현 설계는 단일 학교 기본. `users.school_id` 기반 멀티 테넌시 지원이나 실제 RLS 정책 활성화는 후속 스프린트(조사 필요 항목).

---

## 15. 관련 문서

- [LOCAL_SETUP.md](./LOCAL_SETUP.md) — 최초 환경 구축
- [ARCHITECTURE.md](./ARCHITECTURE.md) — C4 Level 1~2
- [API.md](./API.md) — 엔드포인트 상세
- [RBAC.md](./RBAC.md) — 권한 모델
- [WORKFLOW_1_2_3_REVIEW.md](./WORKFLOW_1_2_3_REVIEW.md) — 결재 상태 머신
- [AI_PIPELINE.md](./AI_PIPELINE.md) — AI 피드백 엔진
