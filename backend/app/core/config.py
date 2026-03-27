from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MD Strategic Review AI API"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/md_strategic_review"
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    openai_embedding_model: str = "text-embedding-3-large"
    pinecone_api_key: str = ""
    pinecone_index_name: str = "md-strategic-review"
    pinecone_cloud: str = "aws"
    pinecone_region: str = "us-east-1"
    pinecone_namespace: str = "chunks"
    embedding_dimension: int = 3072
    enable_semantic_retrieval: bool = True
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 120
    storage_root: str = "./storage"
    dev_admin_email: str = "admin@example.com"
    dev_admin_password: str = "admin1234"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
