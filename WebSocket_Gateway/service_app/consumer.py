
from channels.generic.websocket import AsyncWebsocketConsumer
from .utils.rabbitmq import RabbitMQHandler, UserStatus
from asgiref.sync import sync_to_async
from typing import Dict, List

# **************************************************************************** #
#   * Global Variable:                                                         #
# **************************************************************************** #
connection_registry: Dict[int, List[AsyncWebsocketConsumer]] = {}


# **************************************************************************** #
#   * Decorators :                                                             #
# **************************************************************************** #
def require_rabbitmq_connection(func):
    async def wrapper(self, *args, **kwargs):
        if not await sync_to_async(self.message_queue.connect)():
            await self.close()
            return None

        return await func(self, *args, **kwargs)

    return wrapper


# **************************************************************************** #
#   * AsyncChatConsumer Class :                                                #
# **************************************************************************** #
class AsyncChatConsumer(AsyncWebsocketConsumer):
    """Handles WebSocket connections for chat functionality."""

    #=== init : ============================================================
    def __init__(self, *args, **kwargs):
        """Initializes the consumer with a RabbitMQ handler."""
        super().__init__(*args, **kwargs)
        self.message_queue = RabbitMQHandler()

    #=== connect : =========================================================
    @require_rabbitmq_connection
    async def connect(self) -> None:
        """Handles the connection event."""
        self.user_id = "1"
        connection_registry.setdefault(self.user_id, []).append(self)
        await self.accept()
        await self._publish_user_status(UserStatus.CONNECTED)

    #=== disconnect : =====================================================
    async def disconnect(self, code: int) -> None:
        """Handles the disconnect event."""
        self.message_queue.close_channel()
        user_channels = connection_registry.get(self.user_id, [])
        if self in user_channels:
            user_channels.remove(self)
        await self._publish_user_status(UserStatus.DISCONNECTED)

    #=== send_message : ===================================================
    async def send_message(self, recipient_id: str, message: str) -> bool:
        """Sends a message to all recipient ID channels"""
        channels = connection_registry.get(recipient_id, [])
        for channel in channels:
            await channel.send(message)

    #=== _publish_user_status : ===========================================
    @require_rabbitmq_connection
    async def _publish_user_status(self, status: UserStatus) -> None:
        """Publishes user status to the connections queue."""
        await sync_to_async(
            self.message_queue.publish_user_status)(self.user_id, status)
