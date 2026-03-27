from fastapi import FastAPI

from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.api.v1.query import router as query_router
from app.api.v1.strategy import router as strategy_router
from app.api.v1.upload import router as upload_router
from app.core.config import settings
from app.db.init_db import ensure_default_admin
from app.db.session import SessionLocal

app = FastAPI(title=settings.app_name)
app.include_router(health_router, prefix="/api")
app.include_router(upload_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(strategy_router, prefix="/api")
app.include_router(query_router, prefix="/api")


@app.on_event("startup")
def startup() -> None:
    db = SessionLocal()
    try:
        ensure_default_admin(db)
    finally:
        db.close()


@app.get("/")
def root() -> dict[str, str]:
    return {"message": settings.app_name}
