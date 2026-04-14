"""FastAPI entrypoint. Routes registered in app/api/__init__.py."""
from contextlib import asynccontextmanager

from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="saengibu-portal",
    version="0.1.0",
    description="학교생활기록부 포털 API",
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
