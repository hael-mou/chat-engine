
import pika
import json
import threading

from django.conf import settings
from enum import Enum

# **************************************************************************** #
#   * UserStatus Enum:                                                         #
# **************************************************************************** #
class UserStatus(Enum):
    """Enum for user connection status."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"


# **************************************************************************** #
#   * RabbitMQHandler class:                                                   #
# **************************************************************************** #
class RabbitMQHandler:
    """Handles connections to RabbitMQ."""

    #=== cls Variable : ===================================================
    _count = 0
    _connection = None
    _lock = threading.Lock()


    #=== init : ===========================================================
    def __init__(self) -> None:
        """Initializes the RabbitMQ connection handler."""
        self._channel = None
        RabbitMQHandler._count += 1


    #=== del : ============================================================
    def __del__(self) -> None:
        """Closes the RabbitMQ connection."""
        self.close_channel()
        RabbitMQHandler._count -= 1
        if not RabbitMQHandler._count and self.is_connected():
            RabbitMQHandler._connection.close()

    #=== Connect : ========================================================
    def connect(self) -> bool:
        """Connects to RabbitMQ and opens a channel."""
        with RabbitMQHandler._lock:
            try:
                if self.is_connected() is False:
                   self._channel = None
                   RabbitMQHandler._connection = pika.BlockingConnection(
                        pika.ConnectionParameters(
                           host=settings.RABBITMQ_HOST or 'localhost'
                        )
                   )

                if self._channel is None:
                   self._channel = RabbitMQHandler._connection.channel()
                return True

            except Exception:
                print("Error: Message queue connection failed.")
                return False


    #=== close_channel : ==================================================
    def close_channel(self) -> None:
        """Closes the RabbitMQ channel."""
        if self._channel is not None:
            try:
                self._channel.close()
                del self._channel
            except Exception:
                pass

        self._channel = None


    #=== is_connected : ===================================================
    def is_connected(self) -> bool:
        """Check if the connection is open and active."""
        connection = RabbitMQHandler._connection

        if connection is None or connection.is_closed:
            return False

        try:
            connection.process_data_events()
            return connection.is_open
        except Exception:
            return False


    #=== publish_user_status : ============================================
    def publish_user_status(self, user_id: str, status: UserStatus) -> None:
        """Publishes user status to the connections queue."""
        self._channel.queue_declare(queue='--user-state', durable=True)
        message = {
            'ID': f'{user_id}',
            'STATUS' : f'{status.value}',
            'SERVER_INFO': settings.SERVER_INFO
        }

        try:
            self._channel.basic_publish(
                        exchange='',
                        routing_key='--user-state',
                        body=json.dumps(message),
                        properties=pika.BasicProperties(
                            delivery_mode=pika.DeliveryMode.Persistent
                        ),
            )
        except Exception:
            return None
