from fastapi import APIRouter

router = APIRouter(prefix="/ping", tags=["ping"])  # lightweight health endpoints


@router.get("/", summary="Ping", description="Simple liveness probe. Returns 'ok'.")
def ping():
    return {"status": "ok"}


@router.get("/healthz", summary="Healthcheck")
def healthz():
    # место для будущих проверок БД, кэша и т.п.
    return {"app": "ok"}
