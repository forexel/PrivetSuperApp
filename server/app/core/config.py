from pydantic import AnyUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: AnyUrl = "postgresql+psycopg://privet:privet@localhost:5432/privetdb"
    JWT_SECRET: str = "change_me"
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minio"
    S3_SECRET_KEY: str = "minio123"
    S3_BUCKET: str = "privet-bucket"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
