from langchain.agents import Tool, create_openai_functions_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain import hub
from langchain_community.chat_message_histories.redis import RedisChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from app.services.sql_agent import agent_executor

agent_prompt = hub.pull("hwchase17/openai-functions-agent")

tools = [
    Tool(
        name="SQLAgent",
        func=lambda query: agent_executor.invoke(
             {"input": query}
        ),
        description="""Useful for answering questions about projects,
        products, bugs and tasks. You query a MySQL Database to get the desired answers. 
        Use the entire prompt as input to the tool. For instance, if the prompt is 
        "How many bugs does the BlueHealthPass project contain?", the input should be 
        "How many bugs does the BlueHealthPass project contain?".
        The question is always a string.
        """,
    ),
]

chat_history_func = lambda session_id: RedisChatMessageHistory(
    session_id, url="redis://zentao-fastapi-redis:6379", ttl=0
)

chat_model = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
)

unified_agent = create_openai_functions_agent(
    llm=chat_model,
    tools=tools,
    prompt=agent_prompt
)


unified_agent_executor = AgentExecutor(
    agent=unified_agent,
    tools=tools,
    return_intermediate_steps=True,
    handle_parsing_errors=True,
    verbose=True,
)

unified_agent_with_chat_history = RunnableWithMessageHistory(
    agent_executor,
    chat_history_func,
    input_messages_key = "input",
    history_messages_key = "chat_history"
)