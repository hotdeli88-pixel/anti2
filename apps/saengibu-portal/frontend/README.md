# saengibu-portal frontend

Next.js 15 App Router + TypeScript + Tailwind + TanStack Query + Zustand.

## 실행

```bash
cd apps/saengibu-portal/frontend
pnpm install
pnpm dev           # http://localhost:3000
```

## 빌드

```bash
pnpm build
pnpm start
```

## 구조

- `app/` — App Router 라우트
- `components/` — 공용 컴포넌트
- `features/` — 도메인 기능 (에디터, 피드백 패널 등)

## 설계 문서

- [../docs/FRONTEND.md](../docs/FRONTEND.md) — 상세 페이지·컴포넌트 구조

## 환경 변수

```
NEXT_PUBLIC_API_BASE=http://localhost:8000/api/v1
```
