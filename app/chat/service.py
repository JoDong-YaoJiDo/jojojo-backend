from openai import OpenAI

from app.core.config import settings

from .retriever import get_context


def chat(message, db):

    client = OpenAI(
        api_key=settings.openai_api_key
    )

    context = get_context(db)

    prompt = (
        "지역 관광 정보와 커뮤니티 게시글을 "
        "바탕으로 질문에 답하세요.\n"
        f"context={context}\n"
        f"user={message}"
    )

    response = client.responses.create(
        model=settings.openai_model,
        input=prompt,
    )

    return (
        getattr(
            response,
            "output_text",
            None,
        )
        or "오류가 발생했습니다"
    )