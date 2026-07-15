from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Place(BaseModel):
    id: int
    content_id: str
    region: str
    content_type: str
    content_type_id: int
    title: str
    addr1: str
    addr2: str
    tel: str
    zipcode: str
    firstimage: str
    firstimage2: str
    mapx: Optional[float] = None
    mapy: Optional[float] = None
    createdtime: str
    modifiedtime: str

    model_config = {"from_attributes": True}


class PlaceSummary(BaseModel):
    id: int
    content_id: str
    region: str
    content_type: str
    title: str
    firstimage: str
    mapx: Optional[float] = None
    mapy: Optional[float] = None

    model_config = {"from_attributes": True}


class PostCreate(BaseModel):
    place_id: int
    title: str
    content: str
    nickname: str
    password: str
    tags: list[str] = Field(default_factory=list)


class PostUpdate(BaseModel):
    password: str
    place_id: Optional[int] = None
    title: Optional[str] = None
    content: Optional[str] = None
    nickname: Optional[str] = None
    tags: Optional[list[str]] = None


class PostListItem(BaseModel):
    id: int
    place_id: int
    place: PlaceSummary
    title: str
    nickname: str
    view_count: int
    like_count: int
    bookmark_count: int
    created_at: datetime
    updated_at: datetime
    tags: list[str]
    image_count: int

    model_config = {"from_attributes": True}


class CommentCreate(BaseModel):
    nickname: str
    content: str
    parent_id: Optional[int] = None


class CommentOut(BaseModel):
    id: int
    post_id: int
    parent_id: Optional[int]
    nickname: str
    content: str
    created_at: datetime
    updated_at: datetime
    replies: list["CommentOut"] = Field(default_factory=list)

    model_config = {"from_attributes": True}


CommentOut.model_rebuild()


class ChatRequest(BaseModel):
    message: str
    client_id: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str