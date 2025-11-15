from fastapi import APIRouter
from .health import router as health_router
from .documents import router as documents_router
from .analysis import router as analysis_router

# Create main v1 router
api_router = APIRouter(prefix="/api/v1")

# Include sub-routers
api_router.include_router(health_router)
api_router.include_router(documents_router)
api_router.include_router(analysis_router)

__all__ = ["api_router"]
