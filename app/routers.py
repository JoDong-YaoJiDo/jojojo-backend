import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, FastAPI, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud import (
    add_view_count,
    bookmark_post,
    create_post,
    delete_post,
    get_post_or_404,
    like_post,
    list_comments,
    list_posts,
    load_tourism_json,
    search_posts,
    serialize_post,
    update_post,
)
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.models import Comment, Post, TourismPlace
from app.schemas import ChatRequest, ChatResponse, CommentCreate, PostCreate, PostUpdate, TourismPlaceOut


api = APIRouter(prefix="/api", tags=["api"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@api.on_event("startup")
def on_startup():
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    init_db()
    db = SessionLocal()
    try:
        load_tourism_json(db)
    finally:
        db.close()


@api.get("/tourism", response_model=list[TourismPlaceOut], summary="관광지 목록 조회")
def tourism_list(region: Optional[str] = None, q: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(TourismPlace)
    if region:
        query = query.filter(TourismPlace.region == region)
    if q:
        query = query.filter(TourismPlace.title.ilike(f"%{q}%"))
    return query.order_by(TourismPlace.id.desc()).all()


@api.get("/tourism/{place_id}/location", summary="관광지 좌표 조회")
def tourism_location(place_id: int, db: Session = Depends(get_db)):
    place = db.query(TourismPlace).filter(TourismPlace.id == place_id).first()
    if not place:
        raise HTTPException(status_code=404, detail="tourism place not found")
    return {"id": place.id, "title": place.title, "mapx": place.mapx, "mapy": place.mapy}


@api.get("/posts", summary="게시글 목록 조회")
def posts(sort: str = "latest", page: int = 1, size: int = 20, db: Session = Depends(get_db)):
    items, total = list_posts(db, sort, page, size)
    return {
        "page": page,
        "size": size,
        "total": total,
        "items": [
            {
                "id": p.id,
                "title": p.title,
                "nickname": p.nickname,
                "view_count": p.view_count,
                "like_count": p.like_count,
                "bookmark_count": p.bookmark_count,
                "created_at": p.created_at,
                "updated_at": p.updated_at,
                "tags": [t.tag for t in p.tags],
                "image_count": len(p.images),
            }
            for p in items
        ],
    }


@api.get("/posts/search", summary="게시글 검색")
def posts_search(q: str, db: Session = Depends(get_db)):
    items = search_posts(db, q)
    return {"items": [serialize_post(p) for p in items]}


@api.post("/posts", summary="게시글 생성")
def posts_create(
    title: str = Form(...),
    content: str = Form(...),
    nickname: str = Form(...),
    password: str = Form(...),
    tags: str = Form(""),
    images: list[UploadFile] | None = File(default=None),
    db: Session = Depends(get_db),
):
    images = images or []
    if len(images) > 10:
        raise HTTPException(status_code=400, detail="image limit is 10")
    image_paths = []
    for img in images:
        original_name = img.filename or "image"
        filename = f"{os.urandom(8).hex()}_{original_name}"
        target = Path(settings.upload_dir) / filename
        file_bytes = img.file.read()
        if file_bytes:
            target.write_bytes(file_bytes)
        image_paths.append(str(target))
    try:
        payload = PostCreate(
            title=title,
            content=content,
            nickname=nickname,
            password=password,
            tags=[t.strip() for t in tags.split(",") if t.strip()],
        )
        post = create_post(db, payload, image_paths)
        return {"id": post.id}
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"failed to create post: {exc}")


@api.get("/posts/{post_id}", summary="게시글 상세 조회")
def posts_detail(post_id: int, db: Session = Depends(get_db)):
    post = get_post_or_404(db, post_id)
    add_view_count(db, post)
    return serialize_post(post) | {"comments": [comment_to_tree(c) for c in list_comments(db, post_id)]}


@api.put("/posts/{post_id}", summary="게시글 수정")
def posts_update(post_id: int, payload: PostUpdate, db: Session = Depends(get_db)):
    post = get_post_or_404(db, post_id)
    return serialize_post(update_post(db, post, payload))


@api.delete("/posts/{post_id}", summary="게시글 삭제")
def posts_delete(post_id: int, password: str, db: Session = Depends(get_db)):
    post = get_post_or_404(db, post_id)
    delete_post(db, post, password)
    return {"ok": True}


@api.post("/posts/{post_id}/comments", summary="댓글/답글 생성")
def comments_create(post_id: int, payload: CommentCreate, db: Session = Depends(get_db)):
    post = get_post_or_404(db, post_id)
    comment = Comment(post_id=post.id, parent_id=payload.parent_id, nickname=payload.nickname, content=payload.content)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return {"id": comment.id}


@api.post("/posts/{post_id}/like", summary="좋아요 등록")
def posts_like(post_id: int, client_id: str, db: Session = Depends(get_db)):
    post = get_post_or_404(db, post_id)
    like_post(db, post, client_id)
    return {"ok": True}


@api.post("/posts/{post_id}/bookmark", summary="북마크 등록")
def posts_bookmark(post_id: int, client_id: str, db: Session = Depends(get_db)):
    post = get_post_or_404(db, post_id)
    bookmark_post(db, post, client_id)
    return {"ok": True}


@api.post("/chat", response_model=ChatResponse, summary="챗봇 응답 생성")
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        context = {
            "tourism": [p.title for p in db.query(TourismPlace).limit(20).all()],
            "posts": [p.title for p in db.query(Post).limit(20).all()],
        }
        prompt = f"지역 관광 정보와 커뮤니티를 바탕으로 질문에 답하세요. context={context}\nuser={req.message}"
        resp = client.responses.create(model=settings.openai_model, input=prompt)
        text = getattr(resp, "output_text", None) or "오류가 발생했습니다"
        return ChatResponse(answer=text)
    except Exception:
        return ChatResponse(answer="오류가 발생했습니다")


def comment_to_tree(comment: Comment):
    return {
        "id": comment.id,
        "post_id": comment.post_id,
        "parent_id": comment.parent_id,
        "nickname": comment.nickname,
        "content": comment.content,
        "created_at": comment.created_at,
        "updated_at": comment.updated_at,
        "replies": [comment_to_tree(reply) for reply in comment.replies],
    }


app = FastAPI(
    title="Local Community Backend",
    version="1.0.0",
    description="관광지 조회, 익명 커뮤니티, 댓글/좋아요/북마크, 챗봇을 포함한 지역 정보 공유 백엔드",
)
app.include_router(api)
