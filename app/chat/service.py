from openai import OpenAI
import json

from app.core.config import settings
from .tools import build_context


def extract_keyword(client, message):

    response = client.responses.create(
        model=settings.openai_model,
        input=f"""
사용자의 관광 관련 질문에서 검색에 사용할 핵심 장소명 또는 키워드만 추출해라.

규칙
- 반드시 JSON만 출력
- 형식은 {{"keyword":"..."}}

질문:
{message}
"""
    )

    try:
        result = json.loads(response.output_text)
        return result["keyword"]
    except Exception:
        return message


def chat(message, db):

    client = OpenAI(
        api_key=settings.openai_api_key
    )

    # 검색 키워드 추출
    keyword = extract_keyword(
        client,
        message,
    )

    # DB 검색
    context = build_context(
        keyword,
        db,
    )

    prompt = f"""
너는 대한민국 여행 전문 챗봇이다.

다음 Context를 참고하여 답변해라.

{context}

사용자 질문
{message}
"""

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
        or "오류가 발생했습니다."
    )