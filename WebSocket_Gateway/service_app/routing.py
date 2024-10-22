
from django.urls import path
from .consumer import AsyncChatConsumer

websocket_urlpatterns = [
    path('ws/chat', AsyncChatConsumer.as_asgi())
]
