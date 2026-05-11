# anti2 Monorepo

`hotdeli88-pixel/anti2` 모노레포. `uv` workspace 기반으로 여러 애플리케이션과 공용 패키지를 단일 저장소에서 관리합니다.

현재 활성 프로젝트는 **saengibu-portal** 입니다. 한국 중·고등학교 교사의 학교생활기록부 작성·검토·NEIS 입력 흐름을 지원하는 Next.js + FastAPI 포털입니다.

## 구조

```text
anti2/
├── apps/                    # 실행 가능한 애플리케이션
│   └── saengibu-portal/     # 학교생활기록부 포털 (Next.js + FastAPI)
│       ├── backend/         # FastAPI 서비스 (uv workspace member)
│       ├── frontend/        # Next.js 15 App Router
│       └── docs/            # 설계 문서 (ARCHITECTURE·ERD·API·AI_PIPELINE·RBAC·WORKFLOW·FRONTEND)
├── packages/                # 공용 라이브러리/모듈
├── dev/active/              # 진행 중 프로젝트 플랜·컨텍스트·태스크
├── pyproject.toml           # uv workspace 루트
├── .python-version
└── MONOREPO_GUIDELINES.md   # 상세 운영 지침
```

## 활성 프로젝트

- **[saengibu-portal](./apps/saengibu-portal/)** — 학교생활기록부 포털 (훈령 제555호·2026 기재요령 준수). 플랜: [`dev/active/saengibu-portal-plan.md`](./dev/active/saengibu-portal-plan.md)

## macOS 빠른 시작

Mac에서는 동기화 폴더보다 `~/Projects` 같은 일반 개발 경로에 클론하는 것을 권장합니다.

```bash
mkdir -p ~/Projects
cd ~/Projects
git clone https://github.com/hotdeli88-pixel/anti2.git
cd anti2/apps/saengibu-portal
```

필수 도구:

- Python 3.11 이상
- `uv`
- Node.js 20 이상
- Corepack/pnpm 9.15.9
- Docker Desktop for Mac

Homebrew 기준 설치 예:

```bash
brew install git python@3.11 uv node@20
brew install --cask docker
open -a Docker

corepack enable
corepack prepare pnpm@9.15.9 --activate
```

프로젝트 의존성 설치:

```bash
make install
```

환경 변수 파일 생성:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

`GOOGLE_CLIENT_ID`와 `NEXT_PUBLIC_GOOGLE_CLIENT_ID`에는 같은 Google OAuth Client ID를 넣습니다. 개발 편의를 위해 `ALLOWED_EMAIL_DOMAINS=`는 비워둘 수 있습니다.

로컬 실행:

```bash
make up
make migrate
make seed

# 터미널 A
make backend

# 터미널 B
make frontend
```

- Frontend: <http://localhost:3000>
- Backend health: <http://localhost:8000/health>
- OpenAPI: <http://localhost:8000/docs>

## 검증

```bash
cd apps/saengibu-portal
make check
make build
```

GitHub Actions는 Ubuntu와 macOS에서 백엔드 단위 테스트, 프론트엔드 타입 체크, 프론트엔드 빌드를 실행합니다.

## 상세 지침

- [macOS/Linux/WSL 로컬 환경 구축](./apps/saengibu-portal/docs/LOCAL_SETUP.md)
- [saengibu-portal README](./apps/saengibu-portal/README.md)
- [모노레포 운영 지침](./MONOREPO_GUIDELINES.md)
