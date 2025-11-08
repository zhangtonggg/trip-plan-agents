
import os
import requests
from datetime import datetime
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from .state import GraphState
from .nodes.router import router_node
from .nodes.tool_executor import tool_executor_node
from .nodes.summarizer import summarizer_node
from .tools import ALL_TOOLS

# 4. 定义流程跳转逻辑
def should_continue(state: GraphState) -> str:
    """根据 router 结果决定下一步节点"""
    # 确保 next_node 存在且为字符串类型
    next_node = state.get("next_node")
    if not next_node or next_node == "end":
        return "summarizer"  # 直接生成回答
    # 检查 next_node 是否是ALL_TOOLS中的一个工具名称
    for t in ALL_TOOLS:
        if next_node == t.name:
            return "tool_executor" # 跳转到新的工具执行节点
    return "summarizer" # 如果不是工具名，也跳转到 summarizer (可能是未知工具名，或者逻辑错误)

def build_graph() -> StateGraph:
    builder = StateGraph(GraphState)
    # 添加节点
    builder.add_node("router", router_node)  # 决策节点
    builder.add_node("tool_executor", tool_executor_node) # 新的工具执行节点
    builder.add_node("summarizer", summarizer_node)  # 结果整理节点

    # 定义边
    builder.add_edge(START, "router")  # 入口 -> 决策节点
    builder.add_conditional_edges(
        "router",
        should_continue,  # 根据决策结果跳转
        {
            "summarizer": "summarizer", # 决策为 "end" 跳转到 summarizer
            "tool_executor": "tool_executor" # 决策为工具名 跳转到 tool_executor
        }
    )
    builder.add_edge("tool_executor", "router")  # 工具调用后回到决策节点，继续判断
    builder.add_edge("summarizer", END)  # 整理结果后结束

    return builder.compile()

