from langgraph.graph import StateGraph, END, START
from .state import GraphState
from .nodes.router import router_node
from .nodes.tool_executor import tool_executor_node
from .nodes.summarizer import summarizer_node
from .tools import ALL_TOOLS


def should_continue(state: GraphState) -> str:
    next_node = state.get("next_node")
    if not next_node or next_node == "end":
        return "summarizer"  
    for t in ALL_TOOLS:
        if next_node == t.name:
            return "tool_executor" 
    return "summarizer"

def build_graph() -> StateGraph:
    builder = StateGraph(GraphState)
    # 添加节点
    builder.add_node("router", router_node)  
    builder.add_node("tool_executor", tool_executor_node) 
    builder.add_node("summarizer", summarizer_node)  

    # 定义边
    builder.add_edge(START, "router")  
    builder.add_edge("tool_executor", "router")  
    builder.add_edge("summarizer", END)  
    builder.add_conditional_edges(
        "router",
        should_continue,  
        {
            "summarizer": "summarizer", 
            "tool_executor": "tool_executor" 
        }
    )

    return builder.compile()

