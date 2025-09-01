from pydantic import AnyUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class Settings(BaseSettings):
    DATABASE_URL: AnyUrl = "postgresql+psycopg://privet:privet@localhost:5432/privetdb"
    JWT_SECRET: str = "change_me"
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minio"
    S3_SECRET_KEY: str = "minio123"
    S3_BUCKET: str = "privet-bucket"

    # SMTP settings for email sending
    SMTP_HOST: str | None = None
    SMTP_PORT: int | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_TLS: bool = True
    SMTP_FROM: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # ignore unknown env vars like APP_NAME, etc.
    )

    # --- Validators to treat empty strings as None ---
    @field_validator("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD", "SMTP_FROM", mode="before")
    @classmethod
    def _empty_str_to_none(cls, v):  # type: ignore[no-untyped-def]
        if isinstance(v, str) and v.strip() == "":
            return None
        return v

    @field_validator("SMTP_PORT", mode="before")
    @classmethod
    def _parse_smtp_port(cls, v):  # type: ignore[no-untyped-def]
        if v is None:
            return None
        if isinstance(v, str):
            s = v.strip()
            if s == "":
                return None
            try:
                return int(s)
            except ValueError:
                raise
        return v

settings = Settings()
