# src/graph/nodes/summarizer.py
import os
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage, BaseMessage
from langchain_qwq import ChatQwen
from typing import Dict, Any, List
from dotenv import load_dotenv

from ..state import GraphState

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
    
    messages: List[BaseMessage] = state.get("messages", [])
    
    # 构建 summarizer 的提示
    summarizer_prompt = ChatPromptTemplate.from_messages([
        ("system", """你是旅游规划助手。根据对话历史和所有工具调用结果，生成自然语言回答：
            - 如果有工具调用结果，请基于这些结果，并结合用户之前的提问进行详细、清晰的回答。
            - 如果没有工具结果，请直接回答用户的问题，或者告知用户无法获取所需信息。
            - 回答需简洁清晰、友好，并且不暴露工具调用的内部过程。
            - 如果用户要求生成旅游计划，请生成详细的行程安排。
            - 你的回答应该以用户的原始意图为导向，结合所有可用的信息进行总结。
            """),
        MessagesPlaceholder(variable_name="messages"),
        # 移除了这里的 tool_results，因为现在 tool_results 已经作为 ToolMessage 包含在 messages 里了
        # 如果你希望模型额外关注 tool_results，可以保留这里，但它可能会重复
        # ("system", f"以下是独立存储的工具调用结果 (可能已在对话历史中)：{state.get("tool_results", {}) or '无'}")
    ])
    
    # 打印messages内容以便调试
    print(f"summarizer_node: Input messages to LLM: {messages}")

    response = chat.invoke(summarizer_prompt.format_messages(messages=messages))
    print(f"summarizer_node: LLM response: {response}")

    new_messages = messages + [AIMessage(content=response.content)]
    state_updates["messages"] = new_messages
    
    initial_human_message = next((m for m in messages if isinstance(m, HumanMessage)), None)
    if initial_human_message and "生成" in initial_human_message.content and "旅游计划" in initial_human_message.content:
        state_updates["current_plan"] = response.content
    else:
        state_updates["current_plan"] = state.get("current_plan", "")
    
    state_updates["tool_results"] = {} # 清空工具结果

    return state_updates