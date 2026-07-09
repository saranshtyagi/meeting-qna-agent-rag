from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    # ==========================
    # API Keys
    # ==========================

    GROQ_API_KEY: str

    MISTRAL_API_KEY: str

    # ==========================
    # Models
    # ==========================

    GROQ_WHISPER_MODEL: str = "whisper-large-v3-turbo"

    MISTRAL_MODEL: str = "mistral-small-latest"

    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # ==========================
    # Directories
    # ==========================

    UPLOAD_DIR: str = "uploads"

    VECTOR_DB_DIR: str = "vector_db"

    # ==========================
    # Chroma
    # ==========================

    CHROMA_COLLECTION: str = "meeting_transcripts"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )


settings = Settings()