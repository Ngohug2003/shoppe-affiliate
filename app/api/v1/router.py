from fastapi import APIRouter

from app.api.v1.routes.affiliate_catalog import router as affiliate_catalog_router
from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.telegram_webhook import router as telegram_webhook_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(affiliate_catalog_router)
api_router.include_router(auth_router)
api_router.include_router(health_router)
api_router.include_router(telegram_webhook_router)
