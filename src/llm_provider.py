# src/llm_provider.py

import os
import sys
from typing import Literal

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_qwq import ChatQwen
from pydantic import SecretStr

# from langchain_huggingface import ChatHuggingFace, HuggingFacePipeline
# # from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
# import torch

# # 添加项目根目录到路径以导入配置
# current_dir = os.path.dirname(os.path.abspath(__file__))
# project_root = os.path.dirname(current_dir)
# sys.path.insert(0, project_root)

# # 尝试加载配置文件
# CONFIG_LOADED = False


# # 尝试加载.env文件
# try:
#     from dotenv import load_dotenv

#     load_dotenv()
#     print("--- 已加载.env环境配置 ---")
# except ImportError:
#     print("--- 未安装python-dotenv，跳过.env文件加载 ---")


# def get_config_value(key, default=None):
#     """获取配置值，优先级：config.py > 环境变量 > 默认值"""
#     return os.getenv(key, default)


def get_llm(
    api_key: str = "",
    model_name: str | None = None,
    api_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
    max_tokens: int = 16384,
    temperature: float = 0.2,
    api_provider: Literal["google", "qwen", "qwen3", "local"] = "qwen",
    model_path: str | None = None,
):
    if not api_key:
        raise ValueError("API Key 不能为空，请检查环境变量 LLM_API_KEY 是否设置正确。")

    print(f"--- 使用LLM提供商: {api_provider} ---")

    if api_provider == "google":
        if not model_name:
            model_name = "gemini-1.5-flash-latest"
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=temperature,
        )

    elif api_provider in ["qwen3", "qwen"]:
        if not model_name:
            model_name = "qwen3-235b-a22b"

        print(f"--- 使用千问3模型: {model_name} ---")

        return ChatQwen(
            model=model_name,
            api_key=SecretStr(api_key.strip()),
            base_url=api_base_url,
            max_tokens=max_tokens,
            temperature=temperature,
            enable_thinking=False,
            # request_timeout=300,
            max_retries=3,
        )
    else:
        raise ValueError(
            f"未知的LLM提供商: '{api_provider}'。支持的提供商有 'google', 'qwen', 'qwen3', 'local'。"
        )
