
import importlib
import threading
import pika
import time

from django.core.management.base import BaseCommand
from sys import exit as sys_exit
from os import path as os_path
from pathlib import Path


class Command(BaseCommand):
    help        = "Runs a RabbitMQ consumer using the specified module"
    app_dir     = Path(__file__).resolve().parent.parent.parent
    app_name    = os_path.basename(app_dir)


    #=== add_argument: ====================================================
    def add_arguments(self, parser):
        parser.add_argument(
            "module_name",
            type=str,
            help="The name of the consumer module (without .py)"
        )


    #=== handle: ==========================================================
    def handle(self, *args, **options):
        """ Run a RabbitMQ consumer using the specified module """
        module_name = f"{self.app_name}.consumers.{options['module_name']}"

        try:
            consumer_module = importlib.import_module(module_name)
            if not hasattr(consumer_module, 'callback'):
                raise Exception("module lacks 'callback' attribute")

            self.callback = consumer_module.callback
            self._consume(consumer_module)

        except KeyboardInterrupt:
            self.stdout.write("Consumer Exiting....")
            sys_exit(0)

        except Exception as e:
            self.stderr.write(f"Error: while setup consumer: {e}")
            sys_exit(1)


    #=== _consume: ========================================================
    def _consume(self, consumer_module):
        """Consumes messages from the specified queue."""
        while True:
            try:
                connection = pika.BlockingConnection(
                    pika.ConnectionParameters(
                        host=consumer_module.RABBITMQ_HOST,
                        port=consumer_module.RABBITMQ_PORT
                    )
                )
                channel = connection.channel()
                channel.queue_declare(queue=consumer_module.QUEUE_NAME)
                channel.basic_consume(
                    queue=consumer_module.QUEUE_NAME,
                    on_message_callback=self._callback,
                    auto_ack=True
                )

                self.stdout.write("Consumer started... Press Ctrl+C to exit.")
                channel.start_consuming()

            except pika.exceptions.AMQPConnectionError:
                self.stdout.write("restart consumer ...")
                time.sleep(5)


    #=== _callback: =======================================================
    def _callback(self, ch, method, properties, body):
        """Callback for when a message is received."""
        print("Received message, spawning a worker thread.")
        threading.Thread(target=self.callback,
                        args=(method, properties, body)).start()
