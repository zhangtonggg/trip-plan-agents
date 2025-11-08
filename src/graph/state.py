from langchain_core.messages import BaseMessage
from typing import List, Optional, TypedDict, Dict, Any

class GraphState(TypedDict, total=False):
    messages: List[BaseMessage]
    current_plan: Optional[str]  
    use_tools: bool
    max_iterations: int
    next_node: Optional[str]
    tool_results: Dict[str, Any]

def initialize_graph_state() -> GraphState:
    return GraphState(
        messages=[],
        current_plan="",
        use_tools=True,
        max_iterations=0,
        next_node="",
        tool_results={}, 
    )