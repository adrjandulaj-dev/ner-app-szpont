from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Literal


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    app_name: str = "NER Document Analysis Service"
    app_version: str = "2.0.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = True

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Keycloak
    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "ner-app"
    keycloak_client_id: str = "ner-backend"
    keycloak_client_secret: str = ""
    keycloak_admin_user: str = "admin"
    keycloak_admin_password: str = "admin"

    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket_name: str = "ner-documents"
    minio_secure: bool = False

    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "ner_analysis"
    mongodb_collection_analyses: str = "analyses"
    mongodb_collection_documents: str = "documents"

    # RabbitMQ
    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "guest"
    rabbitmq_password: str = "guest"
    rabbitmq_queue_name: str = "ner_analysis_queue"
    rabbitmq_exchange: str = "ner_exchange"

    # LLM
    llm_provider: Literal["openai", "anthropic", "local"] = "openai"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    llm_model: str = "gpt-4o-mini"

    # NER Model
    ner_model_path: Path = Path("./models/model1/ner_model_2025_07_13.h5")
    ner_word2idx_path: Path = Path("./models/model1/word2idx_2025_07_13.pkl")
    ner_idx2tag_path: Path = Path("./models/model1/idx2tag_2025_07_13.pkl")
    ner_max_len: int = 70

    # Logging
    log_level: str = "INFO"

    # Tag mapping
    human_readable_tags_map: dict = {
        "geo": "geographic locations",
        "gpe": "geopolitical entity",
        "tim": "time",
        "org": "organization",
        "per": "person",
        "art": "artifact",
        "nat": "nationality",
        "eve": "event"
    }

    @property
    def rabbitmq_url(self) -> str:
        return f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}@{self.rabbitmq_host}:{self.rabbitmq_port}/"


settings = Settings()
