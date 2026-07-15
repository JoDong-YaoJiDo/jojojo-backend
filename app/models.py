from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


class PlaceItem(Base):
    __tablename__ = "tourism_places"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(
        String,
        unique=True,
        index=True,
        nullable=False,
    )
    region = Column(
        String,
        index=True,
        nullable=False,
    )
    content_type = Column(
        String,
        nullable=False,
    )
    content_type_id = Column(
        Integer,
        nullable=False,
    )
    title = Column(
        String,
        index=True,
        nullable=False,
    )
    addr1 = Column(
        String,
        default="",
    )
    addr2 = Column(
        String,
        default="",
    )
    tel = Column(
        String,
        default="",
    )
    zipcode = Column(
        String,
        default="",
    )
    firstimage = Column(
        String,
        default="",
    )
    firstimage2 = Column(
        String,
        default="",
    )
    mapx = Column(
        Float,
        nullable=True,
    )
    mapy = Column(
        Float,
        nullable=True,
    )
    raw_json = Column(
        Text,
        nullable=False,
    )
    createdtime = Column(
        String,
        default="",
    )
    modifiedtime = Column(
        String,
        default="",
    )

    posts = relationship(
        "Post",
        back_populates="place",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Post(Base):
    __tablename__ = "posts"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )
    place_id = Column(
        Integer,
        ForeignKey(
            "tourism_places.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )
    title = Column(
        String,
        nullable=False,
        index=True,
    )
    content = Column(
        Text,
        nullable=False,
    )
    nickname = Column(
        String,
        nullable=False,
        index=True,
    )
    password_hash = Column(
        String,
        nullable=False,
    )
    view_count = Column(
        Integer,
        default=0,
        nullable=False,
    )
    like_count = Column(
        Integer,
        default=0,
        nullable=False,
    )
    bookmark_count = Column(
        Integer,
        default=0,
        nullable=False,
    )
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        onupdate=datetime.utcnow,
    )

    place = relationship(
        "PlaceItem",
        back_populates="posts",
    )
    images = relationship(
        "PostImage",
        cascade="all, delete-orphan",
        back_populates="post",
        passive_deletes=True,
    )
    tags = relationship(
        "PostTag",
        cascade="all, delete-orphan",
        back_populates="post",
        passive_deletes=True,
    )
    comments = relationship(
        "Comment",
        cascade="all, delete-orphan",
        back_populates="post",
        passive_deletes=True,
    )
    likes = relationship(
        "PostLike",
        cascade="all, delete-orphan",
        back_populates="post",
        passive_deletes=True,
    )
    bookmarks = relationship(
        "PostBookmark",
        cascade="all, delete-orphan",
        back_populates="post",
        passive_deletes=True,
    )


class PostImage(Base):
    __tablename__ = "post_images"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )
    post_id = Column(
        Integer,
        ForeignKey(
            "posts.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )
    image_path = Column(
        String,
        nullable=False,
    )
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    post = relationship(
        "Post",
        back_populates="images",
    )


class PostTag(Base):
    __tablename__ = "post_tags"

    __table_args__ = (
        UniqueConstraint(
            "post_id",
            "tag",
            name="uq_post_tag",
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
    )
    post_id = Column(
        Integer,
        ForeignKey(
            "posts.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )
    tag = Column(
        String,
        nullable=False,
        index=True,
    )

    post = relationship(
        "Post",
        back_populates="tags",
    )


class Comment(Base):
    __tablename__ = "comments"

    id = Column(
        Integer,
        primary_key=True,
    )
    post_id = Column(
        Integer,
        ForeignKey(
            "posts.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )
    parent_id = Column(
        Integer,
        ForeignKey(
            "comments.id",
            ondelete="CASCADE",
        ),
        nullable=True,
        index=True,
    )
    content = Column(
        Text,
        nullable=False,
    )
    nickname = Column(
        String,
        nullable=False,
    )
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        onupdate=datetime.utcnow,
    )

    post = relationship(
        "Post",
        back_populates="comments",
    )
    parent = relationship(
        "Comment",
        remote_side=[id],
        back_populates="replies",
    )
    replies = relationship(
        "Comment",
        back_populates="parent",
        cascade="all, delete-orphan",
        passive_deletes=True,
        single_parent=True,
    )


class PostLike(Base):
    __tablename__ = "post_likes"

    __table_args__ = (
        UniqueConstraint(
            "post_id",
            "client_id",
            name="uq_post_like",
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
    )
    post_id = Column(
        Integer,
        ForeignKey(
            "posts.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )
    client_id = Column(
        String,
        nullable=False,
        index=True,
    )

    post = relationship(
        "Post",
        back_populates="likes",
    )


class PostBookmark(Base):
    __tablename__ = "post_bookmarks"

    __table_args__ = (
        UniqueConstraint(
            "post_id",
            "client_id",
            name="uq_post_bookmark",
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
    )
    post_id = Column(
        Integer,
        ForeignKey(
            "posts.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )
    client_id = Column(
        String,
        nullable=False,
        index=True,
    )

    post = relationship(
        "Post",
        back_populates="bookmarks",
    )
