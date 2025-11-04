from contextlib import asynccontextmanager
from typing import Any

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
from starlette.routing import Route

from .settings import settings

origins = settings.ORIGINS or [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


def _create_application(
    router: APIRouter,
    **kwargs: Any,
) -> FastAPI:
    application: FastAPI = FastAPI(**kwargs)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,  # Or ["*"] to allow all origins
        allow_credentials=True,
        allow_methods=["*"],  # Allows all HTTP methods
        allow_headers=["*"],  # Allows all headers
    )

    application.include_router(router)

    return application


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("App Routes:")
    print(app.routes)
    print("Registered Routes:")
    for route in app.routes:
        # print(f"{route}: {route.__class__}")
        if isinstance(route, (APIRoute, Route)):
            methods = ",".join(route.methods)
            print(f"{methods:10} {route.path} -> {route.name}")
    yield


def create_application(router: APIRouter) -> FastAPI:
    app = _create_application(router=router, lifespan=lifespan)
    return app
