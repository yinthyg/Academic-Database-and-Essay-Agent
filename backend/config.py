import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings:
    # Core
    PROJECT_NAME: str = "Local Literature RAG Agent"
    API_V1_PREFIX: str = "/api"

    # Security
    SECRET_KEY: str = os.getenv("APP_SECRET_KEY", "change-this-secret-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "720"))  # 12 hours
    ALGORITHM: str = "HS256"

    # Paths
    DATA_DIR: Path = BASE_DIR / "data"
    UPLOAD_DIR: Path = DATA_DIR / "uploads"
    DB_PATH: Path = DATA_DIR / "app.db"
    CHROMA_DIR: Path = DATA_DIR / "chroma"
    PAPERS_DIR: Path = DATA_DIR / "papers"
    STUDENT_PAPERS_DIR: Path = DATA_DIR / "student_papers"
    
    # Embeddings / RAG
    EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-small-zh-v1.5")
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "300"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "100"))
    TOP_K: int = int(os.getenv("TOP_K", "4"))

    # vLLM 配置 - 指向您刚启动的服务
    # vLLM 配置 - 使用 localhost
    VLLM_API_BASE: str = os.getenv("VLLM_API_BASE", "http://127.0.0.1:8000/v1")
    VLLM_API_KEY: str = os.getenv("VLLM_API_KEY", "dummy-key")
    LLM_MODEL_NAME: str = os.getenv("LLM_MODEL_NAME", "/mnt/d/agent_litkb/r1_model_1.5b_hf")
    # 本地模型配置参数（用于兼容性，实际不会用到）
    MODEL_MAX_LENGTH: int = int(os.getenv("MODEL_MAX_LENGTH", "4096"))
    MODEL_MAX_NEW_TOKENS: int = int(os.getenv("MODEL_MAX_NEW_TOKENS", "2048"))
    MODEL_TEMPERATURE: float = float(os.getenv("MODEL_TEMPERATURE", "0.2"))
    MODEL_USE_FP16: bool = os.getenv("MODEL_USE_FP16", "true").lower() == "true"

    # History
    HISTORY_RETENTION_DAYS: int = int(os.getenv("HISTORY_RETENTION_DAYS", "7"))

    # Default admin
    DEFAULT_ADMIN_USERNAME: str = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
    DEFAULT_ADMIN_PASSWORD: str = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")


settings = Settings()

# 创建必要的目录
for path in [
    settings.DATA_DIR,
    settings.UPLOAD_DIR,
    settings.CHROMA_DIR,
    settings.PAPERS_DIR,
    settings.STUDENT_PAPERS_DIR,
]:
    path.mkdir(parents=True, exist_ok=True)