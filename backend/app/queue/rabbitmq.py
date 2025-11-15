import aio_pika
from aio_pika import connect_robust, Message, DeliveryMode, ExchangeType
from aio_pika.abc import AbstractRobustConnection, AbstractChannel, AbstractQueue, AbstractExchange
from typing import Optional, Callable
import logging
import json

from ..config import settings

logger = logging.getLogger(__name__)


class RabbitMQClient:
    """RabbitMQ client for async task queue"""

    def __init__(self):
        self.connection: Optional[AbstractRobustConnection] = None
        self.channel: Optional[AbstractChannel] = None
        self.queue: Optional[AbstractQueue] = None
        self.exchange: Optional[AbstractExchange] = None

    async def connect(self):
        """Connect to RabbitMQ"""
        try:
            self.connection = await connect_robust(settings.rabbitmq_url)
            self.channel = await self.connection.channel()

            # Set QoS - process one message at a time
            await self.channel.set_qos(prefetch_count=1)

            # Declare exchange
            self.exchange = await self.channel.declare_exchange(
                settings.rabbitmq_exchange,
                ExchangeType.DIRECT,
                durable=True
            )

            # Declare queue
            self.queue = await self.channel.declare_queue(
                settings.rabbitmq_queue_name,
                durable=True
            )

            # Bind queue to exchange
            await self.queue.bind(
                self.exchange,
                routing_key=settings.rabbitmq_queue_name
            )

            logger.info("Connected to RabbitMQ")

        except Exception as e:
            logger.error(f"Error connecting to RabbitMQ: {e}")
            raise

    async def disconnect(self):
        """Disconnect from RabbitMQ"""
        if self.connection:
            await self.connection.close()
            logger.info("Disconnected from RabbitMQ")

    async def publish_task(self, task_data: dict):
        """
        Publish task to queue

        Args:
            task_data: Task data dictionary
        """
        try:
            message_body = json.dumps(task_data).encode()

            message = Message(
                body=message_body,
                delivery_mode=DeliveryMode.PERSISTENT,
                content_type="application/json"
            )

            await self.exchange.publish(
                message,
                routing_key=settings.rabbitmq_queue_name
            )

            logger.info(f"Published task to queue: {task_data.get('task_type')}")

        except Exception as e:
            logger.error(f"Error publishing task: {e}")
            raise

    async def consume_tasks(self, callback: Callable):
        """
        Start consuming tasks from queue

        Args:
            callback: Async function to handle messages
        """
        try:
            await self.queue.consume(callback)
            logger.info("Started consuming tasks from queue")

        except Exception as e:
            logger.error(f"Error consuming tasks: {e}")
            raise


# Global instance
rabbitmq_client = RabbitMQClient()
