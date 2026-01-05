"""S3-compatible storage helpers (MinIO)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Optional

import boto3
from botocore.client import BaseClient, Config

from app.core.config import settings
import os


@dataclass
class PresignedPost:
    url: str
    fields: dict[str, str]
    file_key: str


class StorageService:
    def __init__(self) -> None:
        self._bucket = settings.S3_BUCKET
        self._client: Optional[BaseClient] = None
        self._public_client: Optional[BaseClient] = None

    def _client_or_init(self) -> BaseClient:
        if self._client is None:
            self._client = boto3.client(
                "s3",
                endpoint_url=settings.S3_ENDPOINT,
                aws_access_key_id=settings.S3_ACCESS_KEY,
                aws_secret_access_key=settings.S3_SECRET_KEY,
                config=Config(signature_version="s3v4"),
            )
        return self._client

    def _public_client_or_init(self) -> BaseClient:
        if self._public_client is None:
            public_endpoint = os.getenv("S3_PUBLIC_ENDPOINT") or getattr(settings, "S3_PUBLIC_ENDPOINT", None) or settings.S3_ENDPOINT
            self._public_client = boto3.client(
                "s3",
                endpoint_url=public_endpoint,
                aws_access_key_id=settings.S3_ACCESS_KEY,
                aws_secret_access_key=settings.S3_SECRET_KEY,
                config=Config(signature_version="s3v4"),
            )
        return self._public_client

    @property
    def bucket(self) -> str:
        return self._bucket

    def generate_presigned_post(self, *, key_prefix: str, content_type: str | None = None, expires: int = 600) -> PresignedPost:
        file_key = f"{key_prefix.rstrip('/')}/{uuid.uuid4()}"
        conditions = []
        if content_type:
            conditions.append({"Content-Type": content_type})

        presigned = self._client_or_init().generate_presigned_post(
            Bucket=self._bucket,
            Key=file_key,
            Fields={"Content-Type": content_type} if content_type else None,
            Conditions=conditions or None,
            ExpiresIn=expires,
        )
        return PresignedPost(url=presigned["url"], fields=presigned["fields"], file_key=file_key)

    def upload_bytes(self, *, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        self._client_or_init().put_object(Bucket=self._bucket, Key=key, Body=data, ContentType=content_type)
        return key

    def get_public_url(self, key: str) -> str:
        public_endpoint = os.getenv("S3_PUBLIC_ENDPOINT") or getattr(settings, "S3_PUBLIC_ENDPOINT", None) or settings.S3_ENDPOINT
        return f"{public_endpoint.rstrip('/')}/{self._bucket}/{key.lstrip('/')}"

    def generate_presigned_get_url(self, key: str, expires: int = 60 * 60 * 24 * 7) -> str:
        return self._public_client_or_init().generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires,
        )


storage_service = StorageService()
