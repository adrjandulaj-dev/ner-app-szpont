from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from pythonjsonlogger import jsonlogger

from .config import settings
from .api.v1 import api_router
from .storage.mongodb import mongodb_client
from .queue.rabbitmq import rabbitmq_client
from .queue.tasks import task_processor

# Configure logging
def setup_logging():
    """Setup JSON logging"""
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.log_level.upper()))

    # Console handler
    console_handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    logger.info("Starting NER Document Analysis Service...")

    try:
        # Connect to MongoDB
        logger.info("Connecting to MongoDB...")
        await mongodb_client.connect()

        # Connect to RabbitMQ
        logger.info("Connecting to RabbitMQ...")
        await rabbitmq_client.connect()

        # Start consuming tasks in background
        logger.info("Starting RabbitMQ consumer...")
        import asyncio
        asyncio.create_task(
            rabbitmq_client.consume_tasks(task_processor.handle_message)
        )

        logger.info("Service started successfully")

    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down NER Document Analysis Service...")

    try:
        # Disconnect from MongoDB
        await mongodb_client.disconnect()

        # Disconnect from RabbitMQ
        await rabbitmq_client.disconnect()

        logger.info("Service shut down successfully")

    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    NER Document Analysis Service with LLM preprocessing

    This API provides:
    - Document upload (PDF, images, text)
    - Automatic text extraction using LLM for PDFs and images
    - Named Entity Recognition (NER) analysis
    - Asynchronous processing with RabbitMQ
    - Keycloak authentication
    - MinIO storage for documents
    - MongoDB storage for analysis results
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
