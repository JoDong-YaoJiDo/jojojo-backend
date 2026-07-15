from app.models import PlaceItem, Post


def get_context(db):

    tourism_places = (
        db.query(PlaceItem)
        .order_by(
            PlaceItem.id.desc()
        )
        .limit(20)
        .all()
    )

    posts = (
        db.query(Post)
        .order_by(
            Post.created_at.desc()
        )
        .limit(20)
        .all()
    )

    return {
        "places": [
            {
                "id": place.id,
                "title": place.title,
                "region": place.region,
                "content_type": place.content_type,
                "content_type_id": place.content_type_id,
            }
            for place in tourism_places
        ],
        "posts": [
            {
                "id": post.id,
                "place_id": post.place_id,
                "title": post.title,
            }
            for post in posts
        ],
    }