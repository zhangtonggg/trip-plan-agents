from .setup import create_application
from .api import router



app = create_application(router)


def main():
    import uvicorn

    from .settings import settings

    uvicorn.run(
        "src.app:app",
        host=settings.HOST,
        port=settings.PORT,
        log_level="info",
        reload=True,
    )


if __name__ == "__main__":
    main()
