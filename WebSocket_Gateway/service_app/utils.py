
import json

from enum import Enum

# **************************************************************************** #
#   * UserStatus Enum:                                                         #
# **************************************************************************** #
class UserStatus(Enum):
    """Enum for user connection status."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"


# **************************************************************************** #
#   * message module:                                                          #
# **************************************************************************** #
class Message:
    #=== class variable : ======================================================
    required_keys = {
        "tn": int,
        "type": str,
        "to": str,
        "contentType": str,
        "body": str,
    }

    allowed_values = {
        "type": {"chat", "group"},
    }


    #=== init : ================================================================
    def __init__(self, message_text: str):
        """Initializes a Message object from a user and a JSON message."""

        try:
            self.message = json.loads(message_text)

            for key, expected_type in self.required_keys.items():
                if key not in self.message:
                    raise ValueError(
                        f"Message is missing required key: {key}"
                    )

                if not isinstance(self.message[key], expected_type):
                    raise ValueError(
                        f"Message key {key} has invalid type. "
                        f"Expected {expected_type.__name__}, got "
                        f"{type(self.message[key]).__name__}"
                    )

                if key in self.allowed_values and\
                    self.message[key] not in self.allowed_values[key]:
                    raise ValueError(
                        f"Message key {key} has invalid value. "
                        f"Allowed values are {self.allowed_values[key]}"
                    )

        except json.JSONDecodeError as error:
            raise ValueError("Invalid JSON format") from error


    #=== post: =================================================================
    def post(self) -> dict:
        """Returns the publish arguments for RabbitMQ."""

        publish_args = {
            "message": json.dumps(self.message).encode(),
            "queue_name": "",
            "exchange_name": ""
        }

        if self.message["type"] == "group":
            publish_args["queue_name"] = "--new-message-group"

        if self.message["type"] == "chat":
            publish_args["exchange_name"] = "--new-message"

        return publish_args


    #=== user_from : ===========================================================
    @property
    def user_from(self) -> str:
        """Returns the user ID of the message sender."""
        return self.message["from"]

    @user_from.setter
    def user_from(self, user_id: str) -> None:
        """Sets the user ID of the message sender."""
        self.message["from"] = user_id


    #=== timestamp : ===========================================================
    @property
    def timestamp(self) -> int:
        """Returns the message timestamp."""
        return self.message["ts"]

    @timestamp.setter
    def timestamp(self, timestamp: int) -> None:
        """Sets the message timestamp."""
        self.message["ts"] = timestamp
