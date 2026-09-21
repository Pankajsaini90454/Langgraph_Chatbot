from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage,HumanMessage
from langchain_openai import ChatOpenAI
from langchain_ollama  import ChatOllama
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.tools import tool
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
import sys
import os
from pathlib import Path

load_dotenv()


# llm = ChatOpenAI()
model=ChatOllama(model="llama3.2")

server_configs = {
    "expense": {
        "transport": "streamable_http",
        "url": "https://splendid-gold-dingo.fastmcp.app/mcp"
    }
}

math_server_path = Path(
    os.getenv(
        "MCP_MATH_SERVER_PATH",
        str(Path.home() / "OneDrive" / "Desktop" / "mcp-math-server" / "main.py"),
    )
)
if math_server_path.is_file():
    server_configs["arith"] = {
        "transport": "stdio",
        "command": sys.executable,
        "args": [str(math_server_path)],
    }

client = MultiServerMCPClient(server_configs)






class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

async def build_grapgh():
    tools=await client.get_tools()
    llm_with_tools = model.bind_tools(tools)

    async def chat_node(state: ChatState):
        messages = state['messages']
        response = await llm_with_tools.ainvoke(messages)
        return {'messages': [response]}

    tool_node = ToolNode(tools)

    graph = StateGraph(ChatState)
    graph.add_node("chat_node", chat_node)
    graph.add_node("tools", tool_node)

    graph.add_edge(START, "chat_node")

    graph.add_conditional_edges("chat_node",tools_condition)
    graph.add_edge('tools', 'chat_node')

    chatbot = graph.compile()


    return chatbot
async def main():
    chabot= await build_grapgh()

    # runnig the graph 
    result=await chabot.ainvoke({"messages":[HumanMessage(content="Find the modulus of 132354 and 23 and give answer. like a cricket commentator.")]})
    print(result['messages'][-1].content)

if __name__=='__main__':
    asyncio.run(main())
