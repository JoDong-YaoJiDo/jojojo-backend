from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas import ChatRequest, ChatResponse

from .service import chat


api = APIRouter(
    prefix="/api",
    tags=["chat"],
)


@api.post(
    "/chat",
    response_model=ChatResponse,
    summary="챗봇 응답 생성",
)
def chat_api(
    req: ChatRequest,
    db: Session = Depends(get_db),
):

    answer = chat(
        req.message,
        db
    )

    return ChatResponse(
        answer=answer
    )