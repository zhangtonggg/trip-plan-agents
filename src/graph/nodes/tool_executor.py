import os
from langchain_core.messages import AIMessage, ToolMessage
from typing import Dict, Any, Optional

from ..state import GraphState
from ..tools import ALL_TOOLS 
from ...logger import get_logger

logger = get_logger(service=__name__)


def tool_executor_node(state: GraphState) -> Dict[str, Any]:
    state_updates = GraphState()
    
    messages = state.get("messages", [])
    
    last_ai_message: Optional[AIMessage] = None
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.tool_calls:
            last_ai_message = msg
            break

    if not last_ai_message:
        logger.info("Error: tool_executor_node called without a preceding AIMessage containing tool_calls.")
        state_updates["tool_results"] = {"error": "No tool calls found in previous AI message."}
        state_updates["next_node"] = "summarizer"
        return state_updates

    tool_calls = last_ai_message.tool_calls
    
    if not tool_calls:
        logger.info("Error: AIMessage found but no tool_calls. Forcing summarizer.")
        state_updates["tool_results"] = {"error": "AI message has no tool_calls."}
        state_updates["next_node"] = "summarizer"
        return state_updates

    first_tool_call = tool_calls[0]
    
    next_tool_name = first_tool_call.get("name") 
    tool_args = first_tool_call.get("args", {}) 
    
    if not next_tool_name:
        logger.info(f"Error: Invalid tool call received: {first_tool_call}. No 'name' key. Forcing summarizer.")
        state_updates["tool_results"] = {"error": "Invalid tool call format: missing 'name'."}
        state_updates["next_node"] = "summarizer"
        return state_updates

    tool_to_execute = None
    for t in ALL_TOOLS:
        if t.name == next_tool_name:
            tool_to_execute = t
            break

    if not tool_to_execute:
        logger.info(f"Error: Tool '{next_tool_name}' not found in ALL_TOOLS. Forcing summarizer.")
        state_updates["tool_results"] = {"error": f"Tool '{next_tool_name}' not found."}
        state_updates["next_node"] = "summarizer"
        return state_updates
    
    logger.info(f"tool_executor_node: Executing tool '{next_tool_name}' with args: {tool_args}")

    try:
        tool_result = tool_to_execute.invoke(tool_args)
        logger.info(f"tool_executor_node: Tool '{next_tool_name}' executed. Result: {tool_result}")

        state_updates["tool_results"] = {next_tool_name: tool_result}
        
        tool_call_id = first_tool_call.get("id")
        if not tool_call_id:
            tool_call_id = f"tool_call_{next_tool_name}_{os.urandom(4).hex()}"
            logger.info(f"Warning: Tool call ID not found in AI message, using '{tool_call_id}'.")


        new_messages = messages + [
            ToolMessage(content=str(tool_result), tool_call_id=tool_call_id)
        ]
        state_updates["messages"] = new_messages
        state_updates["next_node"] = None
        
    except Exception as e:
        error_message = f"Failed to execute tool '{next_tool_name}' with args {tool_args}: {str(e)}"
        logger.info(f"Error: {error_message}")
        state_updates["tool_results"] = {next_tool_name: {"error": error_message}}
        
        tool_call_id = first_tool_call.get("id") or f"tool_call_error_{next_tool_name}_{os.urandom(4).hex()}"
        new_messages = messages + [
            ToolMessage(content=error_message, tool_call_id=tool_call_id)
        ]
        state_updates["messages"] = new_messages
        state_updates["next_node"] = None
        
    return state_updates