import re
from fastapi import FastAPI
from langchain_core.messages import HumanMessage
from datetime import datetime
from fastapi import APIRouter

from ..graph.graph import build_graph
from ..graph.state import initialize_graph_state, GraphState
from ..schemas import TravelRequest, UserInput
from ..logger import get_logger


app = APIRouter()

logger = get_logger(service=__name__)


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
    days = (end_date - start_date).days + 1 # 利用 datetime 对象计算日期差值

    prompt = (
        f"生成{days}天的旅游计划: \n"
        f"- 出发地: {request.departure}\n"
        f"- 目的地: {request.destination}\n"
        f"- 旅行日期: {request.start_date}至{request.end_date}\n"
        f"- 兴趣偏好: {request.interests}\n"
        f"- 特殊要求：{'避开拥挤场所' if request.avoid_crowds else '无'}\n"
    )

    # 初始化图状态
    initialized_state: GraphState = initialize_graph_state()
    initialized_state["messages"].append(HumanMessage(content=prompt))
    initialized_state["max_iterations"] = 0 
    session["state"] = initialized_state
    logger.info(f"generate_plan: Initial State: {session['state']}")
    
    # 最终图状态
    final_state: GraphState = session["graph"].invoke(session["state"])
    logger.info(f"generate_plan: Final State: {final_state}")
    
    # 更新会话记录
    session["state"]= final_state

    # 提取并整理有效输出
    messages = final_state.get("messages", [])
    if not messages:
        return {"error": "未生成任何内容", "session_id": session_id}
    last_message = messages[-1]
    cleaned_output = clean_agent_output(last_message.content)
    
    return {"plan": cleaned_output, "session_id": session_id}


@app.post("/chat/{session_id}")
async def chat_endpoint(session_id: str, user_input: UserInput):
    session = get_session(session_id)
    
    # 附加当前计划作为上下文
    user_msg_content = user_input.message
    context_message = ""
    if session["state"].get("current_plan"):
        context_message = f"当前旅游计划：{session['state']['current_plan']}\n"
    
    full_user_msg = f"{context_message}, 用户问题：{user_msg_content}"
    
    # 初始化图状态
    if "messages" not in session["state"] or not isinstance(session["state"]["messages"], list):
        session["state"]["messages"] = []
    session["state"]["messages"].append(HumanMessage(content=full_user_msg))
    session["state"]["max_iterations"] = session["state"].get("max_iterations", 0) + 1
    logger.info(f"chat_endpoint: Initial State: {session['state']}")

    # 最终图状态
    final_state: GraphState = session["graph"].invoke(session["state"])
    logger.info(f"chat_endpoint: Final State: {final_state}")

    # 更新会话记录
    session["state"]= final_state

    # 提取并整理有效输出
    messages = final_state.get("messages", [])
    if not messages:
        return {"error": "未生成任何内容", "session_id": session_id}
    last_message = messages[-1]
    cleaned_output = clean_agent_output(last_message.content)
    
    return {"response": cleaned_output, "session_id": session_id}


def clean_agent_output(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"Action\s*:\s*`?\w+`?\s*Action Input\s*:\s*`?\{.*?`?\}?\s*Observation\s*:\s*.*?(?=\n\n|\Z)", "", text, flags=re.DOTALL)
    text = re.sub(r"<tool_code>.*?<\/tool_code>", "", text, flags=re.DOTALL) # 移除可能的 XML 标签
    text = re.sub(r"tool_code`.*?`", "", text, flags=re.DOTALL) # 移除可能的 markdown 标签
    return re.sub(r"\n\s*\n", "\n\n", text).strip()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)