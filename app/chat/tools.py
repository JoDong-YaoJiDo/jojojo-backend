from . import retriever


def popular_posts(db):

    posts = retriever.get_popular_posts(db)

    return [
        {
            "title": p.title,
            "content": p.content[:200],
            "likes": p.like_count,
            "views": p.view_count,
        }
        for p in posts
    ]


def recent_posts(db):

    posts = retriever.get_recent_posts(db)

    return [
        {
            "title": p.title,
            "content": p.content[:200],
            "created_at": str(p.created_at),
        }
        for p in posts
    ]


def search_place(db, keyword):

    places = retriever.search_places(
        db,
        keyword,
    )

    return [
        {
            "title": p.title,
            "region": p.region,
            "content_type": p.content_type,
            "address": p.addr1,
        }
        for p in places
    ]


def search_post(db, keyword):

    posts = retriever.search_posts(
        db,
        keyword,
    )

    return [
        {
            "title": p.title,
            "content": p.content[:200],
            "likes": p.like_count,
        }
        for p in posts
    ]


def summarize_place(db, place_name):

    place = retriever.get_place_by_name(
        db,
        place_name,
    )

    if place is None:
        return None

    posts = retriever.get_posts_by_place(
        db,
        place.id,
    )

    return {
        "place": {
            "title": place.title,
            "region": place.region,
            "content_type": place.content_type,
            "address": place.addr1,
            "tel": place.tel,
        },
        "community": [
            {
                "title": p.title,
                "content": p.content[:200],
                "likes": p.like_count,
            }
            for p in posts
        ],
    }

import json


def build_context(message, db):
    message = message.strip()

    context = {}

    # 인기 게시글
    if "인기" in message:
        context["popular_posts"] = popular_posts(db)

    # 최근 게시글
    if "최근" in message:
        context["recent_posts"] = recent_posts(db)

    # 장소 검색
    places = search_place(db, message)
    if places:
        context["places"] = places

        place_name = places[0]["title"]
        summary = summarize_place(db, place_name)

        if summary:
            context["place_summary"] = summary

    # 게시글 검색
    posts = search_post(db, message)
    if posts:
        context["related_posts"] = posts

    if not context:
        context["notice"] = (
            "데이터베이스에서 관련 정보를 찾지 못했습니다."
        )

    return json.dumps(
        context,
        ensure_ascii=False,
        indent=2,
    )

