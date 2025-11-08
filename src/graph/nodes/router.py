import os
from typing import Dict, Any
from dotenv import load_dotenv
from langchain_qwq import ChatQwen
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage
from ...logger import get_logger

from ..state import GraphState
from ..tools import ALL_TOOLS 

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

chat_with_tools = chat.bind_tools(ALL_TOOLS)

def router_node(state: GraphState) -> Dict[str, Any]:
    state_updates = GraphState()
    messages = state.get("messages", [])
    if state.get("max_iterations", 0) >= 20:
        state_updates["next_node"] = "summarizer"
        if not any(isinstance(msg, AIMessage) and msg.tool_calls for msg in messages):
            messages.append(AIMessage(content="看起来我尝试了很多次，但未能找到答案或完成任务。请总结当前信息并给出回答。"))
            state_updates["messages"] = messages
        return state_updates
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个智能决策助手，负责分析用户的请求和对话历史，决定是否需要调用外部工具来获取信息。
            
                    如果需要工具，请调用合适的工具，并提供所有必要的参数。
                    如果不需要工具，或者你认为可以根据当前信息直接回答，则直接回复用户。
                    
                    请记住：
                    - 在每次决策时，考虑对话的最新进展和用户意图。
                    - 如果需要工具，你将以工具调用的形式输出。
                    - 如果不需要工具，你将以自然语言文本的形式输出。
                    - 你的主要目标是有效地满足用户的旅游计划需求。
                    """
        ),
        MessagesPlaceholder(variable_name="messages")
    ])
    chain = prompt | chat_with_tools
    logger.info(f"router_node: Input messages to LLM: {messages}")

    try:
        response = chain.invoke({"messages": messages})
        logger.info(f"router_node: LLM response: {response}")
        
        new_messages = messages + [response]
        state_updates["messages"] = new_messages

        if response.tool_calls:
            tool_call = response.tool_calls[0] # 假设只调用第一个工具
            tool_name = tool_call.get("name") # 直接获取 'name' 键
            
            if tool_name:
                state_updates["next_node"] = tool_name
            else:
                logger.info(f"Warning: LLM returned tool_calls but the first tool_call has no 'name' key: {tool_call}")
                state_updates["next_node"] = "summarizer" 
        else:
            state_updates["next_node"] = "summarizer"
        
    except Exception as e:
        print(f"Error in router_node LLM call: {e}")
        state_updates["next_node"] = "summarizer"
        state_updates["messages"] = messages + [AIMessage(content=f"在决策过程中发生错误：{e}，我将尝试总结现有信息。")]

    return state_updates