from pydantic import BaseModel
import os

class Settings(BaseModel):
    api_base_path: str = os.getenv("API_BASE_PATH", "/v1")
    allowed_origins: str = os.getenv("ALLOWED_ORIGINS", "*")

    # IntelliOptics
    io_token: str | None = os.getenv("INTELLIOPTICS_API_TOKEN") or os.getenv("INTELLOPTICS_API_TOKEN")
    io_endpoint: str | None = os.getenv("INTELLIOPTICS_ENDPOINT") or os.getenv("INTELLOPTICS_API_BASE")

    # Service Bus
    sb_namespace: str | None = os.getenv("AZ_SB_NAMESPACE")
    sb_conn_str: str | None = os.getenv("AZ_SB_CONN_STR") or os.getenv("SERVICE_BUS_CONN")
    sb_image_queue: str = os.getenv("SB_QUEUE_LISTEN", "image-queries")
    sb_results_queue: str = os.getenv("SB_QUEUE_SEND", "inference-results")
    sb_feedback_queue: str = os.getenv("SB_QUEUE_FEEDBACK", "feedback")

    # Storage
    blob_account: str = os.getenv("AZ_BLOB_ACCOUNT", "")
    blob_container: str = os.getenv("AZ_BLOB_CONTAINER", "images")
    blob_conn_str: str | None = os.getenv("AZ_BLOB_CONN_STR")

    # Postgres
    pg_dsn: str | None = os.getenv("POSTGRES_DSN")
    pg_host: str = os.getenv("PG_HOST", "localhost")
    pg_db: str = os.getenv("PG_DB", "intellioptics")
    pg_user: str = os.getenv("PG_USER", "postgres")
    pg_password: str = os.getenv("PG_PASSWORD", "")
    pg_sslmode: str = os.getenv("PG_SSLMODE", "require")

settings = Settings()
