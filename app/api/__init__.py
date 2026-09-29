from app.api.routes import auth, tasks
from app.config import settings
from fastapi import APIRouter


api_router = APIRouter(prefix=settings.API_V1_PREFIX)

api_router.include_router(auth.router)
api_router.include_router(tasks.router)