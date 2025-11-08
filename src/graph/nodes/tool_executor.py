# src/graph/nodes/tool_executor.py
import os
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# from langchain_core.output_parsers import JsonOutputParser # 不再需要
from langchain_core.messages import AIMessage, ToolMessage, BaseMessage
from langchain_qwq import ChatQwen
from typing import Dict, Any, List
from dotenv import load_dotenv

from ..state import GraphState
from ..tools import ALL_TOOLS # 导入所有工具

load_dotenv()

# 不再需要 chat_with_tools，因为这里只执行工具
# chat = ChatQwen(...) # 实际上这个 chat 变量在这里可能也不需要了，因为不进行LLM调用

def tool_executor_node(state: GraphState) -> Dict[str, Any]:
    state_updates = GraphState()
    
    messages: List[BaseMessage] = state.get("messages", [])
    
    last_ai_message: Optional[AIMessage] = None
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.tool_calls:
            last_ai_message = msg
            break

    if not last_ai_message:
        print("Error: tool_executor_node called without a preceding AIMessage containing tool_calls.")
        state_updates["tool_results"] = {"error": "No tool calls found in previous AI message."}
        state_updates["next_node"] = "summarizer"
        return state_updates

    tool_calls = last_ai_message.tool_calls
    
    if not tool_calls:
        print("Error: AIMessage found but no tool_calls. Forcing summarizer.")
        state_updates["tool_results"] = {"error": "AI message has no tool_calls."}
        state_updates["next_node"] = "summarizer"
        return state_updates

    first_tool_call = tool_calls[0]
    
    # 修正这里：直接从 tool_call 字典中获取 'name' 和 'args'
    next_tool_name = first_tool_call.get("name") # 直接获取 'name' 键
    tool_args = first_tool_call.get("args", {}) # 直接获取 'args' 键
    
    if not next_tool_name:
        print(f"Error: Invalid tool call received: {first_tool_call}. No 'name' key. Forcing summarizer.")
        state_updates["tool_results"] = {"error": "Invalid tool call format: missing 'name'."}
        state_updates["next_node"] = "summarizer"
        return state_updates

    tool_to_execute = None
    for t in ALL_TOOLS:
        if t.name == next_tool_name:
            tool_to_execute = t
            break

    if not tool_to_execute:
        print(f"Error: Tool '{next_tool_name}' not found in ALL_TOOLS. Forcing summarizer.")
        state_updates["tool_results"] = {"error": f"Tool '{next_tool_name}' not found."}
        state_updates["next_node"] = "summarizer"
        return state_updates
    
    print(f"tool_executor_node: Executing tool '{next_tool_name}' with args: {tool_args}")

    try:
        tool_result = tool_to_execute.invoke(tool_args)
        print(f"tool_executor_node: Tool '{next_tool_name}' executed. Result: {tool_result}")

        state_updates["tool_results"] = {next_tool_name: tool_result}
        
        tool_call_id = first_tool_call.get("id")
        if not tool_call_id:
            tool_call_id = f"tool_call_{next_tool_name}_{os.urandom(4).hex()}" # 生成一个随机ID
            print(f"Warning: Tool call ID not found in AI message, using '{tool_call_id}'.")


        new_messages = messages + [
            # AIMessage(content=f"思考：决定调用工具 {next_tool_name}，参数为 {tool_args}"), # 这个思考可以省略或在prompt中让LLM自行表达
            ToolMessage(content=str(tool_result), tool_call_id=tool_call_id)
        ]
        state_updates["messages"] = new_messages
        state_updates["next_node"] = None
        
    except Exception as e:
        error_message = f"Failed to execute tool '{next_tool_name}' with args {tool_args}: {str(e)}"
        print(f"Error: {error_message}")
        state_updates["tool_results"] = {next_tool_name: {"error": error_message}}
        
        tool_call_id = first_tool_call.get("id") or f"tool_call_error_{next_tool_name}_{os.urandom(4).hex()}"
        new_messages = messages + [
            ToolMessage(content=error_message, tool_call_id=tool_call_id)
        ]
        state_updates["messages"] = new_messages
        state_updates["next_node"] = None
        
    return state_updates