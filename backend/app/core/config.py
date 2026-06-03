from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    # Database Configuration
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    
    # Redis Configuration
    REDIS_PASSWORD: str
    
    # MinIO Configuration
    MINIO_ROOT_USER: str
    MINIO_ROOT_PASSWORD: str
    MINIO_SECURE: bool = False
    
    # Qdrant Configuration
    QDRANT_API_KEY: str
    
    # === LLM providers ===
    # Anthropic (primary)
    ANTHROPIC_API_KEY: str | None = None
    
    # OpenAI (first fallback)
    OPENAI_API_KEY: str | None = None
    
    # DeepSeek official (cheap & strong)
    DEEPSEEK_API_KEY: str | None = None
    DEEPSEEK_API_BASE: str = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    
    # OpenRouter (gateway for Qwen + DeepSeek redundancy)
    OPENROUTER_API_KEY: str | None = None
    OPENROUTER_BASE: str = "https://openrouter.ai/api/v1"
    OPENROUTER_DEEPSEEK_MODEL: str = "deepseek/deepseek-chat"
    OPENROUTER_QWEN_MODEL: str = "qwen/qwen3-max"
    
    # Failover behavior
    LLM_PROVIDER_ORDER: str = "anthropic,openai,deepseek,deepseek_or,qwen"
    LLM_TIMEOUT_SECONDS: int = 20
    LLM_MAX_RETRIES_PER_PROVIDER: int = 2
    LLM_COOLDOWN_RATE_LIMIT_MIN: int = 5
    LLM_COOLDOWN_AUTH_ERROR_MIN: int = 1
    
    # Security
    JWT_SECRET: str
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@postgres:5432/{self.POSTGRES_DB}"
        
    @property
    def database_url_local(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@localhost:5432/{self.POSTGRES_DB}"
        
    @property
    def redis_url(self) -> str:
        host = "redis" if os.getenv("DOCKER_ENV") else "localhost"
        port = 6379 if os.getenv("DOCKER_ENV") else 6380
        return f"redis://:{self.REDIS_PASSWORD}@{host}:{port}/0"

    @property
    def minio_url(self) -> str:
        host = "minio" if os.getenv("DOCKER_ENV") else "localhost"
        return f"{host}:9000"

    @property
    def qdrant_url(self) -> str:
        host = "qdrant" if os.getenv("DOCKER_ENV") else "localhost"
        return f"http://{host}:6333"

settings = Settings()
