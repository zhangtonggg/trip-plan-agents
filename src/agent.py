import re
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage
from .graph.state import initialize_graph_state, GraphState # 导入 GraphState 类型
from datetime import datetime

from .schemas import TravelRequest
from .logger import get_logger
from .graph.graph import build_graph

logger = get_logger(service=__name__)

app = FastAPI()

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

user_sessions = {}
def get_session(session_id: str):
    if session_id not in user_sessions:
        initial_state = initialize_graph_state()
        user_sessions[session_id] = {
            "graph": build_graph(), 
            "state": initial_state  
        }
    return user_sessions[session_id]


@app.post("/generate_plan/{session_id}")
async def generate_plan(session_id: str, request: TravelRequest):
    session = get_session(session_id)
    start_date = datetime.strptime(request.start_date, "%Y-%m-%d")
    end_date = datetime.strptime(request.end_date, "%Y-%m-%d")
    days = (end_date - start_date).days + 1

    prompt = (
        f"生成{days}天的旅游计划: \n"
        f"- 出发地: {request.departure}\n"
        f"- 目的地: {request.destination}\n"
        f"- 旅行日期: {request.start_date}至{request.end_date}\n"
        f"- 兴趣偏好: {request.interests}\n"
        f"- 特殊要求：{'避开拥挤场所' if request.avoid_crowds else '无'}\n"
    )
    
    initialized_state: GraphState = initialize_graph_state()
    initialized_state["messages"].append(HumanMessage(content=prompt))
    initialized_state["max_iterations"] = 0 
    session["state"] = initialized_state

    logger.info(f"generate_plan: Initial state for graph: {session['state']}")
    
    result = session["graph"].invoke(session["state"])
    logger.info(f"generate_plan: Final graph result: {result}")
    
    final_state: GraphState = result 
    messages = final_state.get("messages", [])
    
    if not messages:
        return {"error": "未生成任何内容", "session_id": session_id}
    
    last_message = messages[-1]
    cleaned_output = clean_agent_output(last_message.content)
    
    session["state"]["current_plan"] = cleaned_output
    session["state"]["messages"] = messages
    
    return {"plan": cleaned_output, "session_id": session_id}


@app.post("/chat/{session_id}")
async def chat_endpoint(session_id: str, user_input: dict):
    session = get_session(session_id)
    user_msg_content = user_input["message"]
    
    # 附加当前计划作为上下文
    context_message = ""
    if session["state"].get("current_plan"):
        context_message = f"当前计划：{session['state']['current_plan']}\n"
    
    full_user_msg = f"{context_message}用户问题：{user_msg_content}"
    
    # 更新状态并运行graph
    # 确保 messages 列表存在，并添加新的 HumanMessage
    if "messages" not in session["state"] or not isinstance(session["state"]["messages"], list):
        session["state"]["messages"] = []
    
    session["state"]["messages"].append(HumanMessage(content=full_user_msg))
    session["state"]["max_iterations"] = session["state"].get("max_iterations", 0) + 1  # 增加迭代计数
    
    print(f"chat_endpoint: State before invoke: {session['state']}")
    result = session["graph"].invoke(session["state"])
    print(f"chat_endpoint: Final graph result: {result}")
    
    # LangGraph的invoke方法会直接返回最终状态，如果GraphState是TypedDict
    final_state: GraphState = result
    
    messages = final_state.get("messages", [])
    if not messages:
        return {"error": "未生成任何内容", "session_id": session_id}
        
    # 清理输出并返回
    last_message = messages[-1]
    cleaned_output = clean_agent_output(last_message.content)
    
    # 更新会话的 messages 列表
    session["state"]["messages"] = messages
    
    return {"response": cleaned_output}


# ------------------------- 辅助函数 -------------------------
def clean_agent_output(text: str) -> str:
    """清理输出，移除工具调用痕迹"""
    if not text:
        return ""
    # 移除工具调用标记 (可能需要更复杂的正则来处理不同LLM的输出格式)
    # 这个正则可能无法完全清除所有工具调用痕迹，具体取决于LLM的输出格式
    text = re.sub(r"Action\s*:\s*`?\w+`?\s*Action Input\s*:\s*`?\{.*?`?\}?\s*Observation\s*:\s*.*?(?=\n\n|\Z)", "", text, flags=re.DOTALL)
    text = re.sub(r"<tool_code>.*?<\/tool_code>", "", text, flags=re.DOTALL) # 移除可能的 XML 标签
    text = re.sub(r"tool_code`.*?`", "", text, flags=re.DOTALL) # 移除可能的 markdown 标签
    # 移除多余空行
    return re.sub(r"\n\s*\n", "\n\n", text).strip()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)