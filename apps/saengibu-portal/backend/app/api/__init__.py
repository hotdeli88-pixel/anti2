from fastapi import APIRouter

from app.api.v1 import (
    auth as auth_v1,
    content as content_v1,
    dashboard as dashboard_v1,
    reviews as reviews_v1,
    standards as standards_v1,
    users as users_v1,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_v1.router)
api_router.include_router(users_v1.router)
api_router.include_router(reviews_v1.router)
api_router.include_router(dashboard_v1.router)
api_router.include_router(content_v1.router)
api_router.include_router(standards_v1.router)
api_router.include_router(standards_v1.domain_router)
api_router.include_router(standards_v1.curricula_router)
