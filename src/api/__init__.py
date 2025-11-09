from fastapi import APIRouter
from .agent import app

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(app, tags=["shop"])

router = APIRouter(prefix="/api")
router.include_router(v1_router)