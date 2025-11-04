from fastapi import APIRouter
from .trip_agent import shop_router

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(shop_router, tags=["shop"])

router = APIRouter(prefix="/api")
router.include_router(v1_router)