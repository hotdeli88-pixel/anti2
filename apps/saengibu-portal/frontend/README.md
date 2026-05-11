# saengibu-portal frontend

Next.js 15 App Router + TypeScript + Tailwind + Pretendard +
TanStack Query + Zustand + Google Identity Services (`@react-oauth/google`).

## 실행

```bash
cd apps/saengibu-portal/frontend
pnpm install
cp .env.example .env.local
# NEXT_PUBLIC_GOOGLE_CLIENT_ID 를 실제 값으로 교체

# 백엔드 기동 후
pnpm dev    # http://localhost:3000
```

## 환경 변수 (.env.local)

```
NEXT_PUBLIC_API_BASE=/api/v1
NEXT_PUBLIC_GOOGLE_CLIENT_ID=<백엔드와 동일한 클라이언트 ID>.apps.googleusercontent.com

# 백엔드 URL (기본: http://localhost:8000)
BACKEND_URL=http://localhost:8000
```

Next 의 `rewrites()`가 `/api/v1/*` 를 BACKEND_URL 로 프록시합니다.
이로써 프론트 ↔ 백엔드가 **동일 오리진**처럼 보여 CORS 불필요하고
httpOnly 쿠키가 자연스럽게 전달됩니다.

## 구조

```text
frontend/
├── app/
│   ├── layout.tsx            Providers (Query + GoogleOAuth)
│   ├── page.tsx              / → /records 리디렉트
│   ├── login/page.tsx        Google 로그인
│   ├── pending/page.tsx      승인 대기 안내
│   ├── records/page.tsx      ★ 메인 (HTML 프로토타입 이식)
│   ├── dashboard/page.tsx    대시보드
│   └── settings/page.tsx     내 정보
├── components/
│   ├── layout/               Sidebar · Header · AppShell
│   ├── ui/                   Button · Badge · Card · Tabs · Table
│   └── records/              StatsCards · ApprovalTable · GuidelinesPanel · DecisionsPanel
├── lib/
│   ├── api.ts                fetch 래퍼 (credentials: include, CSRF 헤더)
│   ├── queries.ts            TanStack Query 훅
│   └── cn.ts                 clsx + tailwind-merge
└── types/record.ts           공용 타입
```

## 보안

- `next.config.ts`에 strict CSP · HSTS · X-Frame-Options · Permissions-Policy 설정
- 로그인 토큰은 **localStorage에 저장하지 않음** — httpOnly 쿠키 전용
- 외부 도메인 스크립트는 Google (accounts.google.com) 만 허용
- 모든 mutation 요청은 `x-csrf-token` 헤더 포함

## 디자인

HTML 프로토타입 (하마룸 스타일, 민트 `#13C3C3`) 그대로 이식.
Pretendard Variable 웹폰트, Tailwind 디자인 토큰으로 변환.
Tab 전환 애니메이션·카드 hover 리프트 재현.

## 테스트

```bash
pnpm test
pnpm typecheck
pnpm lint
```
