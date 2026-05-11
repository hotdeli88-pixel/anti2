FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# uv 설치
RUN pip install "uv>=0.5.0"

# Workspace 루트의 lock 사용하는 구조라 매니페스트만 먼저 복사
COPY pyproject.toml /app/pyproject.toml
COPY README.md /app/README.md

RUN uv pip install --system -e .[dev]

COPY . /app

# 비-root 사용자
RUN useradd -u 1000 -ms /bin/bash app
USER app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
