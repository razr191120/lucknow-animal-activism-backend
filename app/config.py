from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/lucknow_bowls"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    NOMINATIM_BASE_URL: str = "https://nominatim.openstreetmap.org/search"
    NOMINATIM_USER_AGENT: str = "lucknow-water-bowl-project/1.0"

    AZURE_STORAGE_CONNECTION_STRING: str = ""
    AZURE_STORAGE_CONTAINER_NAME: str = "uploads"


settings = Settings()
