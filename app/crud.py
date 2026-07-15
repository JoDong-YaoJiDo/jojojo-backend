import json
from pathlib import Path
from typing import Any

from fastapi import HTTPException
from passlib.context import CryptContext
from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session, joinedload

from app.models import (
    Comment,
    PlaceItem,
    Post,
    PostBookmark,
    PostImage,
    PostLike,
    PostTag,
)


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(
    raw: str,
    hashed: str,
) -> bool:
    return pwd_context.verify(raw, hashed)


def to_float(value: Any) -> float | None:
    if value in (None, ""):
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def to_int(
    value: Any,
    default: int = 0,
) -> int:
    if value in (None, ""):
        return default

    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def load_jsons(db: Session) -> int:
    json_dir = Path("./data")

    if not json_dir.exists():
        return 0

    if not json_dir.is_dir():
        return 0

    json_files = sorted(
        json_dir.glob("*.json")
    )

    existing_content_ids = {
        content_id
        for (content_id,) in (
            db.query(PlaceItem.content_id)
            .all()
        )
    }

    inserted_count = 0

    try:
        for json_file in json_files:
            payload = json.loads(
                json_file.read_text(
                    encoding="utf-8"
                )
            )

            region = str(
                payload.get("region", "")
            ).strip()

            content_type = str(
                payload.get(
                    "contentType",
                    "",
                )
            ).strip()

            content_type_id = to_int(
                payload.get("contentTypeId")
            )

            items = payload.get(
                "items",
                [],
            )

            if not region:
                continue

            if not content_type:
                continue

            if not isinstance(items, list):
                continue

            for item in items:
                if not isinstance(item, dict):
                    continue

                content_id = str(
                    item.get(
                        "contentid",
                        "",
                    )
                ).strip()

                title = str(
                    item.get(
                        "title",
                        "",
                    )
                ).strip()

                if not content_id:
                    continue

                if not title:
                    continue

                if (
                    content_id
                    in existing_content_ids
                ):
                    continue

                item_content_type_id = to_int(
                    item.get(
                        "contenttypeid"
                    ),
                    default=content_type_id,
                )

                if item_content_type_id <= 0:
                    continue

                place = PlaceItem(
                    content_id=content_id,
                    region=region,
                    content_type=content_type,
                    content_type_id=(
                        item_content_type_id
                    ),
                    title=title,
                    addr1=str(
                        item.get(
                            "addr1",
                            "",
                        )
                        or ""
                    ).strip(),
                    addr2=str(
                        item.get(
                            "addr2",
                            "",
                        )
                        or ""
                    ).strip(),
                    tel=str(
                        item.get(
                            "tel",
                            "",
                        )
                        or ""
                    ).strip(),
                    zipcode=str(
                        item.get(
                            "zipcode",
                            "",
                        )
                        or ""
                    ).strip(),
                    firstimage=str(
                        item.get(
                            "firstimage",
                            "",
                        )
                        or ""
                    ).strip(),
                    firstimage2=str(
                        item.get(
                            "firstimage2",
                            "",
                        )
                        or ""
                    ).strip(),
                    mapx=to_float(
                        item.get("mapx")
                    ),
                    mapy=to_float(
                        item.get("mapy")
                    ),
                    raw_json=json.dumps(
                        item,
                        ensure_ascii=False,
                    ),
                    createdtime=str(
                        item.get(
                            "createdtime",
                            "",
                        )
                        or ""
                    ).strip(),
                    modifiedtime=str(
                        item.get(
                            "modifiedtime",
                            "",
                        )
                        or ""
                    ).strip(),
                )

                db.add(place)

                existing_content_ids.add(
                    content_id
                )

                inserted_count += 1

        db.commit()

        return inserted_count

    except Exception:
        db.rollback()
        raise


def get_place_or_404(
    db: Session,
    place_id: int,
) -> PlaceItem:
    place = (
        db.query(PlaceItem)
        .filter(
            PlaceItem.id == place_id
        )
        .first()
    )

    if not place:
        raise HTTPException(
            status_code=404,
            detail="tourism place not found",
        )

    return place


def list_place_content_types(
    db: Session,
    region: str | None = None,
) -> list[dict]:
    query = db.query(
        PlaceItem.content_type,
        PlaceItem.content_type_id,
        func.count(
            PlaceItem.id
        ).label("place_count"),
    )

    if region:
        query = query.filter(
            PlaceItem.region == region
        )

    rows = (
        query.group_by(
            PlaceItem.content_type,
            PlaceItem.content_type_id,
        )
        .order_by(
            PlaceItem.content_type_id.asc()
        )
        .all()
    )

    return [
        {
            "content_type": row.content_type,
            "content_type_id": (
                row.content_type_id
            ),
            "place_count": row.place_count,
        }
        for row in rows
    ]


def list_posts(
    db: Session,
    sort: str,
    page: int,
    size: int,
    place_id: int | None = None,
    region: str | None = None,
    content_type: str | None = None,
):
    page = max(page, 1)
    size = min(
        max(size, 1),
        100,
    )

    order_map = {
        "latest": desc(
            Post.created_at
        ),
        "views": desc(
            Post.view_count
        ),
        "likes": desc(
            Post.like_count
        ),
        "bookmarks": desc(
            Post.bookmark_count
        ),
    }

    query = (
        db.query(Post)
        .options(
            joinedload(Post.place),
            joinedload(Post.images),
            joinedload(Post.tags),
        )
    )

    requires_place_join = (
        region is not None
        or content_type is not None
    )

    if requires_place_join:
        query = query.join(
            Post.place
        )

    if place_id is not None:
        query = query.filter(
            Post.place_id == place_id
        )

    if region:
        query = query.filter(
            PlaceItem.region == region
        )

    if content_type:
        query = query.filter(
            PlaceItem.content_type
            == content_type
        )

    total = query.count()

    posts = (
        query.order_by(
            order_map.get(
                sort,
                desc(Post.created_at),
            ),
            desc(Post.id),
        )
        .offset(
            (page - 1) * size
        )
        .limit(size)
        .all()
    )

    return posts, total


def list_posts_by_place(
    db: Session,
    place_id: int,
    sort: str = "latest",
    page: int = 1,
    size: int = 20,
):
    place = get_place_or_404(
        db=db,
        place_id=place_id,
    )

    posts, total = list_posts(
        db=db,
        sort=sort,
        page=page,
        size=size,
        place_id=place_id,
    )

    return place, posts, total


def create_post(
    db: Session,
    payload,
    image_paths: list[str],
):
    place = get_place_or_404(
        db=db,
        place_id=payload.place_id,
    )

    post = Post(
        place_id=place.id,
        title=payload.title,
        content=payload.content,
        nickname=payload.nickname,
        password_hash=hash_password(
            payload.password
        ),
    )

    db.add(post)
    db.flush()

    normalized_tags = {
        tag.strip()
        for tag in payload.tags
        if tag.strip()
    }

    for tag in normalized_tags:
        db.add(
            PostTag(
                post_id=post.id,
                tag=tag,
            )
        )

    for path in image_paths[:10]:
        db.add(
            PostImage(
                post_id=post.id,
                image_path=path,
            )
        )

    db.commit()
    db.refresh(post)

    return get_post_or_404(
        db=db,
        post_id=post.id,
    )


def get_post_or_404(
    db: Session,
    post_id: int,
) -> Post:
    post = (
        db.query(Post)
        .options(
            joinedload(Post.place),
            joinedload(Post.images),
            joinedload(Post.tags),
        )
        .filter(
            Post.id == post_id
        )
        .first()
    )

    if not post:
        raise HTTPException(
            status_code=404,
            detail="post not found",
        )

    return post


def serialize_place_summary(
    place: PlaceItem,
) -> dict:
    return {
        "id": place.id,
        "content_id": place.content_id,
        "region": place.region,
        "content_type": (
            place.content_type
        ),
        "content_type_id": (
            place.content_type_id
        ),
        "title": place.title,
        "firstimage": (
            place.firstimage
        ),
        "mapx": place.mapx,
        "mapy": place.mapy,
    }


def serialize_post(
    post: Post,
) -> dict:
    return {
        "id": post.id,
        "place_id": post.place_id,
        "place": (
            serialize_place_summary(
                post.place
            )
            if post.place
            else None
        ),
        "title": post.title,
        "content": post.content,
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
        "images": [
            {
                "id": image.id,
                "image_path": (
                    image.image_path
                ),
            }
            for image in post.images
        ],
    }


def add_view_count(
    db: Session,
    post: Post,
):
    post.view_count += 1

    db.commit()
    db.refresh(post)


def update_post(
    db: Session,
    post: Post,
    payload,
):
    if not verify_password(
        payload.password,
        post.password_hash,
    ):
        raise HTTPException(
            status_code=403,
            detail="invalid password",
        )

    if payload.place_id is not None:
        place = get_place_or_404(
            db=db,
            place_id=payload.place_id,
        )

        post.place_id = place.id

    if payload.title is not None:
        post.title = payload.title

    if payload.content is not None:
        post.content = (
            payload.content
        )

    if payload.nickname is not None:
        post.nickname = (
            payload.nickname
        )

    if payload.tags is not None:
        (
            db.query(PostTag)
            .filter(
                PostTag.post_id
                == post.id
            )
            .delete(
                synchronize_session=False
            )
        )

        normalized_tags = {
            tag.strip()
            for tag in payload.tags
            if tag.strip()
        }

        for tag in normalized_tags:
            db.add(
                PostTag(
                    post_id=post.id,
                    tag=tag,
                )
            )

    db.commit()

    return get_post_or_404(
        db=db,
        post_id=post.id,
    )


def delete_post(
    db: Session,
    post: Post,
    password: str,
):
    if not verify_password(
        password,
        post.password_hash,
    ):
        raise HTTPException(
            status_code=403,
            detail="invalid password",
        )

    db.delete(post)
    db.commit()


def list_comments(
    db: Session,
    post_id: int,
):
    comments = (
        db.query(Comment)
        .filter(
            Comment.post_id == post_id
        )
        .order_by(
            Comment.created_at.asc()
        )
        .all()
    )

    comment_ids = {
        comment.id
        for comment in comments
    }

    roots = []

    for comment in comments:
        if (
            comment.parent_id
            and comment.parent_id
            in comment_ids
        ):
            continue

        roots.append(comment)

    return roots


def like_post(
    db: Session,
    post: Post,
    client_id: str,
):
    exists = (
        db.query(PostLike)
        .filter(
            PostLike.post_id
            == post.id,
            PostLike.client_id
            == client_id,
        )
        .first()
    )

    if exists:
        raise HTTPException(
            status_code=409,
            detail="already liked",
        )

    db.add(
        PostLike(
            post_id=post.id,
            client_id=client_id,
        )
    )

    post.like_count += 1

    db.commit()


def bookmark_post(
    db: Session,
    post: Post,
    client_id: str,
):
    exists = (
        db.query(PostBookmark)
        .filter(
            PostBookmark.post_id
            == post.id,
            PostBookmark.client_id
            == client_id,
        )
        .first()
    )

    if exists:
        raise HTTPException(
            status_code=409,
            detail="already bookmarked",
        )

    db.add(
        PostBookmark(
            post_id=post.id,
            client_id=client_id,
        )
    )

    post.bookmark_count += 1

    db.commit()


def search_posts(
    db: Session,
    q: str,
    place_id: int | None = None,
    region: str | None = None,
):
    query = (
        db.query(Post)
        .options(
            joinedload(Post.place),
            joinedload(Post.images),
            joinedload(Post.tags),
        )
    )

    if region:
        query = query.join(
            Post.place
        )

    if place_id is not None:
        query = query.filter(
            Post.place_id == place_id
        )

    if region:
        query = query.filter(
            PlaceItem.region == region
        )

    query = query.filter(
        or_(
            Post.title.ilike(
                f"%{q}%"
            ),
            Post.content.ilike(
                f"%{q}%"
            ),
            Post.nickname.ilike(
                f"%{q}%"
            ),
            PlaceItem.title.ilike(
                f"%{q}%"
            )
            if region
            else Post.title.ilike(
                f"%{q}%"
            ),
        )
    )

    return (
        query.order_by(
            desc(Post.created_at)
        )
        .all()
    )