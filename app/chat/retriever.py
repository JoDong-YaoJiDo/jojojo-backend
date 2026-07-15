from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import PlaceItem, Post


def get_place_by_name(db: Session, place_name: str):
    return (
        db.query(PlaceItem)
        .filter(PlaceItem.title.contains(place_name))
        .first()
    )


def search_places(db: Session, keyword: str, limit: int = 5):
    return (
        db.query(PlaceItem)
        .filter(
            or_(
                PlaceItem.title.contains(keyword),
                PlaceItem.region.contains(keyword),
                PlaceItem.content_type.contains(keyword),
            )
        )
        .limit(limit)
        .all()
    )


def get_posts_by_place(db: Session, place_id: int, limit: int = 10):
    return (
        db.query(Post)
        .filter(Post.place_id == place_id)
        .order_by(Post.like_count.desc())
        .limit(limit)
        .all()
    )


def search_posts(db: Session, keyword: str, limit: int = 5):
    return (
        db.query(Post)
        .filter(
            or_(
                Post.title.contains(keyword),
                Post.content.contains(keyword),
            )
        )
        .order_by(Post.like_count.desc())
        .limit(limit)
        .all()
    )


def get_popular_posts(db: Session, limit: int = 5):
    return (
        db.query(Post)
        .order_by(
            Post.like_count.desc(),
            Post.view_count.desc(),
        )
        .limit(limit)
        .all()
    )


def get_recent_posts(db: Session, limit: int = 5):
    return (
        db.query(Post)
        .order_by(Post.created_at.desc())
        .limit(limit)
        .all()
    )