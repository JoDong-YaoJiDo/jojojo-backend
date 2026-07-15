import os
from pathlib import Path
from typing import Optional

from fastapi.middleware.cors import CORSMiddleware

from fastapi import (
    APIRouter,
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud import (
    add_view_count,
    bookmark_post,
    create_post,
    delete_post,
    get_place_or_404,
    get_post_or_404,
    like_post,
    list_comments,
    list_place_content_types,
    list_posts,
    list_posts_by_place,
    load_jsons,
    search_posts,
    serialize_place_summary,
    serialize_post,
    update_post,
)
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.models import Comment, PlaceItem, Post, SimplifiedPlace
from app.schemas import (
    ChatRequest,
    ChatResponse,
    CommentCreate,
    Place,
    PostCreate,
    PostUpdate,
)


api = APIRouter(
    prefix="/api",
    tags=["api"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@api.get(
    "/health",
    summary="서버 상태 확인",
)
def health():
    return {
        "status": "ok",
    }


@api.get(
    "/places",
    response_model=list[Place],
    summary="카테고리별 장소 목록 조회",
)
def places(
    content_type_id: Optional[int] = None,
    region: Optional[str] = None,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(PlaceItem)

    if content_type_id is not None:
        query = query.filter(
            PlaceItem.content_type_id
            == content_type_id
        )

    if region:
        query = query.filter(
            PlaceItem.region == region
        )

    if q:
        query = query.filter(
            PlaceItem.title.ilike(
                f"%{q}%"
            )
        )

    return (
        query.order_by(
            PlaceItem.title.asc(),
            PlaceItem.id.asc(),
        )
        .all()
    )



@api.get(
    "/all-places",
    response_model=list[SimplifiedPlace],
    summary="전체 장소 목록 조회",
)
def places(
    content_type_id: Optional[int] = None,
    region: Optional[str] = None,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(
        PlaceItem.id,
        PlaceItem.title,
        PlaceItem.mapx,
        PlaceItem.mapy,
    )

    if content_type_id is not None:
        query = query.filter(
            PlaceItem.content_type_id
            == content_type_id
        )

    if region:
        query = query.filter(
            PlaceItem.region == region
        )

    if q:
        query = query.filter(
            PlaceItem.title.ilike(
                f"%{q}%"
            )
        )

    return (
        query.order_by(
            PlaceItem.title.asc(),
            PlaceItem.id.asc(),
        )
        .all()
    )







@api.get(
    "/categories",
    summary="장소 카테고리 목록 조회",
)
def categories(
    region: Optional[str] = None,
    db: Session = Depends(get_db),
):
    items = list_place_content_types(
        db=db,
        region=region,
    )

    return {
        "items": items,
    }


@api.get(
    "/details",
    response_model=Place,
    summary="장소 상세 조회",
)
def place_details(
    place_id: int,
    db: Session = Depends(get_db),
):
    return get_place_or_404(
        db=db,
        place_id=place_id,
    )


@api.get(
    "/location",
    summary="장소 좌표 조회",
)
def place_location(
    place_id: int,
    db: Session = Depends(get_db),
):
    place = get_place_or_404(
        db=db,
        place_id=place_id,
    )

    return {
        "id": place.id,
        "content_id": place.content_id,
        "title": place.title,
        "mapx": place.mapx,
        "mapy": place.mapy,
    }


@api.get(
    "/places/{place_id}/posts",
    summary="장소별 게시글 목록 조회",
)
def place_posts(
    place_id: int,
    sort: str = "latest",
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
):
    place, items, total = list_posts_by_place(
        db=db,
        place_id=place_id,
        sort=sort,
        page=page,
        size=size,
    )

    normalized_page = max(
        page,
        1,
    )
    normalized_size = min(
        max(size, 1),
        100,
    )

    return {
        "place": serialize_place_summary(
            place
        ),
        "page": normalized_page,
        "size": normalized_size,
        "total": total,
        "items": [
            serialize_post(post)
            for post in items
        ],
    }


@api.get(
    "/posts",
    summary="게시글 목록 조회",
)
def posts(
    sort: str = "latest",
    page: int = 1,
    size: int = 20,
    place_id: Optional[int] = None,
    region: Optional[str] = None,
    content_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    items, total = list_posts(
        db=db,
        sort=sort,
        page=page,
        size=size,
        place_id=place_id,
        region=region,
        content_type=content_type,
    )

    normalized_page = max(
        page,
        1,
    )
    normalized_size = min(
        max(size, 1),
        100,
    )

    return {
        "page": normalized_page,
        "size": normalized_size,
        "total": total,
        "items": [
            {
                "id": post.id,
                "place_id": post.place_id,
                "place": serialize_place_summary(
                    post.place
                ),
                "title": post.title,
                "nickname": post.nickname,
                "view_count": post.view_count,
                "like_count": post.like_count,
                "bookmark_count": (
                    post.bookmark_count
                ),
                "created_at": post.created_at,
                "updated_at": post.updated_at,
                "tags": [
                    tag.tag
                    for tag in post.tags
                ],
                "image_count": len(
                    post.images
                ),
            }
            for post in items
        ],
    }


@api.get(
    "/posts/search",
    summary="게시글 검색",
)
def posts_search(
    q: str,
    place_id: Optional[int] = None,
    region: Optional[str] = None,
    db: Session = Depends(get_db),
):
    items = search_posts(
        db=db,
        q=q,
        place_id=place_id,
        region=region,
    )

    return {
        "items": [
            serialize_post(post)
            for post in items
        ],
    }


@api.post(
    "/posts",
    summary="게시글 생성",
)
def posts_create(
    place_id: int = Form(...),
    title: str = Form(...),
    content: str = Form(...),
    nickname: str = Form(...),
    password: str = Form(...),
    tags: str = Form(""),
    images: list[UploadFile] = File(
        default=[]
    ),
    db: Session = Depends(get_db),
):
    normalized_images: list[UploadFile] = []

    for image in images or []:
        if image is None:
            continue

        if not image.filename:
            continue

        if getattr(
            image,
            "size",
            None,
        ) == 0:
            continue

        normalized_images.append(
            image
        )

    if len(normalized_images) > 10:
        raise HTTPException(
            status_code=400,
            detail="image limit is 10",
        )

    image_paths: list[str] = []

    try:
        for image in normalized_images:
            original_name = (
                Path(image.filename).name
                if image.filename
                else "image"
            )

            filename = (
                f"{os.urandom(8).hex()}_"
                f"{original_name}"
            )

            target = (
                Path(settings.upload_dir)
                / filename
            )

            file_bytes = image.file.read()

            if not file_bytes:
                continue

            target.write_bytes(
                file_bytes
            )

            image_paths.append(
                str(target)
            )

        payload = PostCreate(
            place_id=place_id,
            title=title,
            content=content,
            nickname=nickname,
            password=password,
            tags=[
                tag.strip()
                for tag in tags.split(",")
                if tag.strip()
            ],
        )

        post = create_post(
            db=db,
            payload=payload,
            image_paths=image_paths,
        )

        return {
            "id": post.id,
            "place_id": post.place_id,
        }

    except HTTPException:
        db.rollback()

        for image_path in image_paths:
            path = Path(image_path)

            if path.exists():
                path.unlink()

        raise

    except Exception as exc:
        db.rollback()

        for image_path in image_paths:
            path = Path(image_path)

            if path.exists():
                path.unlink()

        raise HTTPException(
            status_code=500,
            detail=(
                "failed to create post: "
                f"{exc}"
            ),
        ) from exc


@api.get(
    "/posts/{post_id}",
    summary="게시글 상세 조회",
)
def posts_detail(
    post_id: int,
    db: Session = Depends(get_db),
):
    post = get_post_or_404(
        db=db,
        post_id=post_id,
    )

    add_view_count(
        db=db,
        post=post,
    )

    comments = list_comments(
        db=db,
        post_id=post_id,
    )

    return serialize_post(post) | {
        "comments": [
            comment_to_tree(comment)
            for comment in comments
        ],
    }


@api.put(
    "/posts/{post_id}",
    summary="게시글 수정",
)
def posts_update(
    post_id: int,
    payload: PostUpdate,
    db: Session = Depends(get_db),
):
    post = get_post_or_404(
        db=db,
        post_id=post_id,
    )

    updated_post = update_post(
        db=db,
        post=post,
        payload=payload,
    )

    return serialize_post(
        updated_post
    )


@api.delete(
    "/posts/{post_id}",
    summary="게시글 삭제",
)
def posts_delete(
    post_id: int,
    password: str,
    db: Session = Depends(get_db),
):
    post = get_post_or_404(
        db=db,
        post_id=post_id,
    )

    delete_post(
        db=db,
        post=post,
        password=password,
    )

    return {
        "ok": True,
    }


@api.post(
    "/posts/{post_id}/comments",
    summary="댓글 및 답글 생성",
)
def comments_create(
    post_id: int,
    payload: CommentCreate,
    db: Session = Depends(get_db),
):
    post = get_post_or_404(
        db=db,
        post_id=post_id,
    )

    if payload.parent_id is not None:
        parent = (
            db.query(Comment)
            .filter(
                Comment.id
                == payload.parent_id,
                Comment.post_id
                == post_id,
            )
            .first()
        )

        if not parent:
            raise HTTPException(
                status_code=404,
                detail=(
                    "parent comment "
                    "not found"
                ),
            )

    comment = Comment(
        post_id=post.id,
        parent_id=payload.parent_id,
        nickname=payload.nickname,
        content=payload.content,
    )

    db.add(comment)
    db.commit()
    db.refresh(comment)

    return {
        "id": comment.id,
    }


@api.post(
    "/posts/{post_id}/like",
    summary="좋아요 등록",
)
def posts_like(
    post_id: int,
    client_id: str,
    db: Session = Depends(get_db),
):
    post = get_post_or_404(
        db=db,
        post_id=post_id,
    )

    like_post(
        db=db,
        post=post,
        client_id=client_id,
    )

    return {
        "ok": True,
    }


@api.post(
    "/posts/{post_id}/bookmark",
    summary="북마크 등록",
)
def posts_bookmark(
    post_id: int,
    client_id: str,
    db: Session = Depends(get_db),
):
    post = get_post_or_404(
        db=db,
        post_id=post_id,
    )

    bookmark_post(
        db=db,
        post=post,
        client_id=client_id,
    )

    return {
        "ok": True,
    }


def comment_to_tree(
    comment: Comment,
) -> dict:
    return {
        "id": comment.id,
        "post_id": comment.post_id,
        "parent_id": comment.parent_id,
        "nickname": comment.nickname,
        "content": comment.content,
        "created_at": comment.created_at,
        "updated_at": comment.updated_at,
        "replies": [
            comment_to_tree(reply)
            for reply in comment.replies
        ],
    }


app = FastAPI(
    title="Local Community Backend",
    version="1.0.0",
    description=(
        "장소 조회, 익명 커뮤니티, "
        "댓글, 좋아요, 북마크, 챗봇을 포함한 "
        "지역 정보 공유 백엔드"
    ),
)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    Path(settings.upload_dir).mkdir(
        parents=True,
        exist_ok=True,
    )

    init_db()

    db = SessionLocal()

    try:
        load_jsons(db)
    finally:
        db.close()


app.include_router(api)
