from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.routers import get_db  # 의존성 문제 추후 db.session으로 get_db 이동하여 개선 필요
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