from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain_ollama  import ChatOllama
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
class ChatState(TypedDict):

    messages: Annotated[list[BaseMessage], add_messages]

# llm = ChatOpenAI()
model=ChatOllama(model="llama3.2")

def chat_node(state: ChatState):

    # take user query from state
    messages = state['messages']

    # send to llm
    response = model.invoke(messages)

    # response store state
    return {'messages': [response]}
checkpointer=MemorySaver()
graph = StateGraph(ChatState)

# add nodes
graph.add_node('chat_node', chat_node)

graph.add_edge(START, 'chat_node')
graph.add_edge('chat_node', END)

chatbot = graph.compile(checkpointer=checkpointer)
# chatbot = graph.compile()
initial_state = {
    'messages': [HumanMessage(content='what is the biggest Natinal Park In India')]
}

# chatbot.invoke(initial_state)['messages'][-1].content
thread_id='1'
while True:
    user_message = input("Type here: ")

    if user_message.strip().lower() in ["exit", "quit", "bye"]:
        print("Goodbye!")
        break

    print("User:", user_message)
    config = {"configurable": {"thread_id": thread_id}}

    response = chatbot.invoke(
        {"messages": [HumanMessage(content=user_message)]}, config=config)

    print("AI:", response["messages"][-1].content)