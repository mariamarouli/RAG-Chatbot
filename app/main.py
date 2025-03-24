from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.services.unified_agent import unified_agent_with_chat_history
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows all origins
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods
    allow_headers=["*"], # Allows all headers
)

class Question(BaseModel):
    username: str
    question: str

class ResponseText(BaseModel):
    text: str


@app.get("/")
async def root():
    return {"message": "Hello World!"}


@app.post("/zentao-bot/ask")
async def ask_chatbot(query: Question):
    try:
        session_id = query.username
        #config = {"configurable": {"session_id": session_id}}

        response = unified_agent_with_chat_history.invoke(
                {"input": query.question},
                {"configurable": {"session_id": session_id}}
            )
        return ResponseText(text=response["output"])
        
    except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))