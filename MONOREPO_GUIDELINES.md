# GitHub `anti2` 모노레포(Monorepo) 마이그레이션 및 운영 지침

이 문서는 현재 프로젝트(`claude-code-harness`)를 `https://github.com/hotdeli88-pixel/anti2` 저장소의 모노레포로 통합하고 관리하기 위한 지침입니다. 현재 사용 중인 Python 패키지 관리자 `uv`의 'Workspace' 기능을 적극적으로 활용하는 구조로 설계되었습니다.

---

## 1. 디렉토리 구조 (Architecture)

모노레포는 여러 애플리케이션(Application)과 공통 라이브러리 및 패키지(Package)를 하나의 단일 저장소(`anti2`)에서 관리합니다. 

권장하는 디렉토리 구조는 다음과 같습니다:

```text
anti2/
├── .github/                  # GitHub Actions 워크플로우 (CI/CD 파이프라인)
├── apps/                     # 실행 가능한 실제 애플리케이션 (API 서버, 웹 서비스 등)
│   ├── claude-code-harness/  # <- 현재 프로젝트를 이 폴더 내부로 이동
│   └── another-app/          # 추후 추가될 다른 형태의 애플리케이션들
├── packages/                 # 여러 앱에서 공유하여 사용할 공통 모듈 (유틸리티, 데이터베이스 등)
│   ├── core-utils/
│   └── db-models/
├── .python-version           # 최상위 파이썬 버전 명시 (예: 3.11 등)
├── pyproject.toml            # 전체를 아우르는 최상위 Workspace 환경 정의 파일
├── uv.lock                   # 최상위 통합 종속성 Lock 파일
├── README.md                 # 모노레포 전체 소개, 구동 방법 등에 대한 문서
└── .gitignore                # 전역 Git 무시 목록
```

---

## 2. 종속성 및 패키지 관리 (`uv` Workspace)

현재 프로젝트에서 채택하고 있는 빌드 툴인 `uv`는 빌트인으로 Workspace 기능을 제공합니다. 앱이 여러 개로 나뉘더라도 최상위 루트 디렉토리에서 전체 의존성 잠금을 통합 관리할 수 있으므로, 버전 충돌을 방지할 수 있습니다.

**[최상위 디렉토리(anti2의 Root)의 `pyproject.toml` 설정 예시]**

```toml
[project]
name = "anti2-workspace"
version = "0.1.0"
description = "Monorepo workspace for anti2 projects"
requires-python = ">=3.11"

[tool.uv.workspace]
members = [
    "apps/*",
    "packages/*"
]
```

**[현재 애플리케이션 프로젝트 이동 및 설정 수정]**
`claude-code-harness` 디렉토리 전체를 `apps/` 안으로 옮진 후, 해당 앱 고유의 의존성을 자신의 `pyproject.toml`에 유지합니다. 예를 들어 공통 패키지를 사용할 경우 `workspace = true` 참조 기능을 설정합니다.

```toml
# apps/claude-code-harness/pyproject.toml 의 예시

[project]
name = "claude-code-harness"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.128.0",
    "uvicorn>=0.40.0",
    "core-utils",  # 모노레포 내의 다른 패키지를 참조
]

[tool.uv.sources]
# 로컬 워크스페이스에 있는 패키지를 우선 사용한다는 선언
core-utils = { workspace = true }
```

---

## 3. 마이그레이션 워크플로우 (이동 방법)

현재 스탠드얼론 저장소(또는 파일군)를 `anti2` 모노레포로 무사히 통합시키기 위해서는 다음 과정을 따릅니다.

1. **저장소 내려받기 및 분기 생성**
   ```bash
   git clone https://github.com/hotdeli88-pixel/anti2.git anti2_monorepo
   cd anti2_monorepo
   git checkout -b chore/init-monorepo
   ```
2. **구조 생성 및 이동**
   루트에 `apps`, `packages` 폴더를 생성하고, `claude-code-harness` 프로젝트 파일들(`pyproject.toml`, `uv.lock`, 소스 코드 등 전체)을 `apps/claude-code-harness/` 밑으로 통째로 복사합니다.
3. **최상위 파일 설정**
   복사한 후 루트 디렉토리(`./anti2_monorepo/`)에 `tool.uv.workspace`가 정의된 최상위 `pyproject.toml`을 새롭게 생성합니다.
4. **Lock 파일 갱신 및 동기화**
   기존 하위의 종속성을 루트로 끌어올리기 위해 새로 Lock을 생성합니다.
   ```bash
   uv lock
   uv sync
   ```

---

## 4. CI/CD 및 Github Actions 구성 전략

모노레포는 코드베이스가 거대해지기 때문에, 변경 사항이 없는 앱까지 불필요하게 빌드 및 배포되어선 안 됩니다.

*   **경로 기반 트리거 방식 (Paths Filter 적용)**
    GitHub Action 작성 시, 특정 앱 소스나 해당 앱이 바라보는 `packages/` 소스가 변경될 때만 파이프라인이 돌도록 구성해야 합니다.
    ```yaml
    # .github/workflows/deploy-claude-harness.yml
    on:
      push:
        branches: [ "main" ]
        paths:
          - 'apps/claude-code-harness/**'  # 이 앱 코드가 바뀔 때
          - 'packages/core-utils/**'       # 참조 중인 유틸이 바뀔 때
          - 'uv.lock'                      # 종속성이 바뀔 때
    ```
*   **포매팅 & 린팅 통일화**
    `uv` 와 함께 `ruff`를 최상위에 설치하여, 저장소에 포함된 모든 코드가 동일한 컨벤션을 가지도록 강제합니다.

---

## 5. 개발 편의성 및 워크플로우 팁

*   **루트 디렉토리 운영**: 앱이 여러 개라고 각각의 디렉토리에 들어가 다중으로 venv를 설정할 필요가 없습니다. 모노레포를 한 번만 클론받은 뒤, 최상위에서 `uv sync`를 실행하면 전체 워크스페이스 코드가 담긴 단일 파이썬 환경이 구성됩니다.
*   **어플리케이션 특정 실행**: 특정 앱만 구동하거나 테스트를 실행할 때, 루트 위치에서 `--project` 또는 `--package` 플래그를 활용할 수 있습니다.
    ```bash
    # claude-code-harness 앱으로 uvicorn 서버 실행 예
    uv run --package claude-code-harness uvicorn main:app
    ```
*   **PR 생성 규칙 정리**: `anti2` 저장소에서 Pull Request를 올릴 때는 제목에 범위를 명시하는 `Conventional Commits` 룰 적용을 권장합니다.
    *   예시: `feat(claude-code-harness): 새 엔드포인트 추가`
    *   예시: `fix(core-utils): 시간 포매팅 버그 수정`
