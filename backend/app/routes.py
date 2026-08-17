from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agent import ask_agent

router = APIRouter()


class ChatTurn(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    history: list[ChatTurn] = Field(default_factory=list)


class ChartData(BaseModel):
    title: str
    labels: list[str]
    values: list[float]


class ChatResponse(BaseModel):
    response: str
    chart: ChartData | None = None


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        result = ask_agent(
            request.message,
            history=[turn.model_dump() for turn in request.history],
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return ChatResponse(response=result["text"], chart=result["chart"])
