from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(prefix="/misc", tags=["meta"])

@router.get("/version")
def version():
    return {
        "app_version": settings.APP_VERSION or "dev",
        "app_channel": settings.APP_CHANNEL or "web",
    }

