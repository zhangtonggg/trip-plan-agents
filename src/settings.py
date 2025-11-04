import os
from typing import List

from starlette.config import Config
from pydantic_settings import BaseSettings

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(root_dir, ".env")
config = Config(env_path)


class Settings(BaseSettings):
    HOST: str = config("HOST", default="127.0.0.1")
    PORT: int = config("PORT", cast=int, default=5000)

    ORIGINS_STR: str = config(
        "ORIGINS", default="http://localhost:5173,http://127.0.0.1:5173"
    )
    ORIGINS: List[str] = ORIGINS_STR.split(",")

    QWEN_API_KEY: str = config("QWEN_API_KEY", default="")
    QWEN_API_URL: str = config(
        "QWEN_API_URL", default="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    QWEN_MODEL_NAME: str = config("QWEN_MODEL_NAME", default="qwen3-235b-a22b")


settings = Settings()
