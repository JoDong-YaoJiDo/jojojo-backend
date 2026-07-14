import json
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session, joinedload
from passlib.context import CryptContext

from app.core.config import settings
from app.models import Comment, Post, PostBookmark, PostImage, PostLike, PostTag, TourismPlace


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(raw: str, hashed: str) -> bool:
    return pwd_context.verify(raw, hashed)


def load_tourism_json(db: Session) -> int:
    path = Path(settings.tourism_json_path)
    if not path.exists():
        return 0
    payload = json.loads(path.read_text(encoding="utf-8"))
    items = payload.get("items", [])
    count = 0
    for item in items:
        content_id = str(item.get("contentid", ""))
        if not content_id:
            continue
        exists = db.query(TourismPlace).filter(TourismPlace.content_id == content_id).first()
        if exists:
            continue
        place = TourismPlace(
            content_id=content_id,
            region=payload.get("region", ""),
            content_type=payload.get("contentType", ""),
            content_type_id=int(payload.get("contentTypeId", 0) or 0),
            title=item.get("title", ""),
            addr1=item.get("addr1", ""),
            addr2=item.get("addr2", ""),
            tel=item.get("tel", ""),
            zipcode=item.get("zipcode", ""),
            firstimage=item.get("firstimage", ""),
            firstimage2=item.get("firstimage2", ""),
            mapx=float(item["mapx"]) if item.get("mapx") else None,
            mapy=float(item["mapy"]) if item.get("mapy") else None,
            createdtime=item.get("createdtime", ""),
            modifiedtime=item.get("modifiedtime", ""),
            raw_json=json.dumps(item, ensure_ascii=False),
        )
        db.add(place)
        count += 1
    db.commit()
    return count


def list_posts(db: Session, sort: str, page: int, size: int):
    order_map = {
        "latest": desc(Post.created_at),
        "views": desc(Post.view_count),
        "likes": desc(Post.like_count),
    }
    posts = (
        db.query(Post)
        .options(joinedload(Post.images), joinedload(Post.tags))
        .order_by(order_map.get(sort, desc(Post.created_at)))
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    total = db.query(func.count(Post.id)).scalar()
    return posts, total


def create_post(db: Session, payload, image_paths: list[str]):
    post = Post(
        title=payload.title,
        content=payload.content,
        nickname=payload.nickname,
        password_hash=hash_password(payload.password),
    )
    db.add(post)
    db.flush()
    for tag in payload.tags:
        db.add(PostTag(post_id=post.id, tag=tag.strip()))
    for path in image_paths[:10]:
        db.add(PostImage(post_id=post.id, image_path=path))
    db.commit()
    db.refresh(post)
    return post


def get_post_or_404(db: Session, post_id: int) -> Post:
    post = db.query(Post).options(joinedload(Post.images), joinedload(Post.tags)).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="post not found")
    return post


def serialize_post(post: Post):
    return {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "nickname": post.nickname,
        "view_count": post.view_count,
        "like_count": post.like_count,
        "bookmark_count": post.bookmark_count,
        "created_at": post.created_at,
        "updated_at": post.updated_at,
        "tags": [t.tag for t in post.tags],
        "images": [{"id": i.id, "image_path": i.image_path} for i in post.images],
    }


def add_view_count(db: Session, post: Post):
    post.view_count += 1
    db.commit()


def update_post(db: Session, post: Post, payload):
    if not verify_password(payload.password, post.password_hash):
        raise HTTPException(status_code=403, detail="invalid password")
    if payload.title is not None:
        post.title = payload.title
    if payload.content is not None:
        post.content = payload.content
    if payload.nickname is not None:
        post.nickname = payload.nickname
    if payload.tags is not None:
        db.query(PostTag).filter(PostTag.post_id == post.id).delete()
        for tag in payload.tags:
            db.add(PostTag(post_id=post.id, tag=tag.strip()))
    db.commit()
    db.refresh(post)
    return post


def delete_post(db: Session, post: Post, password: str):
    if not verify_password(password, post.password_hash):
        raise HTTPException(status_code=403, detail="invalid password")
    db.delete(post)
    db.commit()


def list_comments(db: Session, post_id: int):
    comments = db.query(Comment).filter(Comment.post_id == post_id).order_by(Comment.created_at.asc()).all()
    by_id = {c.id: c for c in comments}
    roots = []
    for c in comments:
        if c.parent_id and c.parent_id in by_id:
            continue
        roots.append(c)
    return roots


def like_post(db: Session, post: Post, client_id: str):
    exists = db.query(PostLike).filter(PostLike.post_id == post.id, PostLike.client_id == client_id).first()
    if exists:
        raise HTTPException(status_code=409, detail="already liked")
    db.add(PostLike(post_id=post.id, client_id=client_id))
    post.like_count += 1
    db.commit()


def bookmark_post(db: Session, post: Post, client_id: str):
    exists = db.query(PostBookmark).filter(PostBookmark.post_id == post.id, PostBookmark.client_id == client_id).first()
    if exists:
        raise HTTPException(status_code=409, detail="already bookmarked")
    db.add(PostBookmark(post_id=post.id, client_id=client_id))
    post.bookmark_count += 1
    db.commit()


def search_posts(db: Session, q: str):
    return (
        db.query(Post)
        .options(joinedload(Post.images), joinedload(Post.tags))
        .filter(or_(Post.title.ilike(f"%{q}%"), Post.content.ilike(f"%{q}%"), Post.nickname.ilike(f"%{q}%")))
        .order_by(desc(Post.created_at))
        .all()
    )
