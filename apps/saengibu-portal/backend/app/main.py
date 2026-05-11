"""FastAPI entrypoint with hardened security middleware."""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.api import api_router
from app.core.config import get_settings
from app.core.db import check_db
from app.core.logging import configure_logging, log


configure_logging()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=()",
        )
        # HSTS: HTTPS 배포 시에만 유의미
        if get_settings().environment != "development":
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=63072000; includeSubDomains; preload",
            )
        return response


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    log.info(
        "startup",
        app=settings.app_name,
        env=settings.environment,
        rules_version=settings.rules_version,
    )
    yield
    log.info("shutdown")


app = FastAPI(
    title="saengibu-portal",
    version="0.1.0",
    description="학교생활기록부 포털 API (교사 전용, 승인제, 외부 유출 금지)",
    lifespan=lifespan,
    docs_url="/docs" if get_settings().environment == "development" else None,
    redoc_url=None,
    openapi_url="/openapi.json" if get_settings().environment == "development" else None,
)

_settings = get_settings()

app.add_middleware(SecurityHeadersMiddleware)

if _settings.cors_origins_list:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["authorization", "content-type", "x-csrf-token"],
        max_age=600,
    )

if _settings.environment != "development":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=_settings.cors_origins_list or ["*"],
    )


@app.exception_handler(StarletteHTTPException)
async def http_exc(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, dict) else {"title": str(exc.detail)}
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "type": detail.get("type", "http.error"),
            "title": detail.get("title", "요청을 처리할 수 없습니다"),
            "detail": detail.get("detail"),
            "status": exc.status_code,
            "instance": str(request.url.path),
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exc(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "type": "validation.error",
            "title": "요청 형식이 올바르지 않습니다",
            "detail": exc.errors(),
            "status": 422,
            "instance": str(request.url.path),
        },
    )


@app.get("/health")
async def health() -> dict:
    db = await check_db()
    return {"status": "ok" if db.get("ok") else "degraded", "db": db}


app.include_router(api_router)
