

RABBITMQ_HOST="localhost"
RABBITMQ_PORT=5672
QUEUE_NAME="connections"


def callback(method, properties, body):
    print(body)
