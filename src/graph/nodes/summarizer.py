import os
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage
from langchain_qwq import ChatQwen
from typing import Dict, Any
from dotenv import load_dotenv

from ..state import GraphState
from ...logger import get_logger

logger = get_logger(service=__name__)

load_dotenv()

chat = ChatQwen(
    temperature=0.1,
    api_key=os.getenv("QWEN_API_KEY"),
    model_name=os.getenv("QWEN_MODEL_NAME", "qwen-turbo"),
    streaming=True,
    max_tokens=2048,
    base_url=os.getenv("QWEN_API_URL"),
)

def summarizer_node(state: GraphState) -> Dict[str, Any]:
    state_updates = GraphState()    
    messages = state.get("messages", [])

    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是旅游规划助手。根据对话历史和所有工具调用结果，生成自然语言回答：
            - 如果有工具调用结果，请基于这些结果，并结合用户之前的提问进行详细、清晰的回答。
            - 如果没有工具结果，请直接回答用户的问题，或者告知用户无法获取所需信息。
            - 回答需简洁清晰、友好，并且不暴露工具调用的内部过程。
            - 如果用户要求生成旅游计划，请生成详细的行程安排。
            - 你的回答应该以用户的原始意图为导向，结合所有可用的信息进行总结。
            """
        ),
        MessagesPlaceholder(variable_name="messages"),
    ])
    chain = prompt | chat
    logger.info(f"summarizer_node: Input messages to LLM: {messages}")

    response = chain.invoke({"messages": messages})
    logger.info(f"summarizer_node: LLM response: {response}")

    new_messages = messages + [response]
    state_updates["messages"] = new_messages
    
    initial_human_message = next((m for m in messages if isinstance(m, HumanMessage)), None)
    if initial_human_message and "生成" in initial_human_message.content and "旅游计划" in initial_human_message.content:
        state_updates["current_plan"] = response.content
    else:
        state_updates["current_plan"] = state.get("current_plan", "")
    
    state_updates["tool_results"] = {}

    return state_updates