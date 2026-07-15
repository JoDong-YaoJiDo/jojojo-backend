from app.routers import app
from app.chat.router import api as chat_api

app.include_router(chat_api)
