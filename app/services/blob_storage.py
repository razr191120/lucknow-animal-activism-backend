import logging
import uuid
from datetime import datetime, timezone

from azure.storage.blob import BlobServiceClient, ContentSettings
from fastapi import UploadFile

from app.config import settings

logger = logging.getLogger(__name__)


class BlobStorageService:
    def __init__(self) -> None:
        self._client: BlobServiceClient | None = None

    @property
    def client(self) -> BlobServiceClient:
        if self._client is None:
            self._client = BlobServiceClient.from_connection_string(
                settings.AZURE_STORAGE_CONNECTION_STRING
            )
        return self._client

    @property
    def container_name(self) -> str:
        return settings.AZURE_STORAGE_CONTAINER_NAME

    def _ensure_container(self) -> None:
        try:
            container_client = self.client.get_container_client(
                self.container_name
            )
            if not container_client.exists():
                self.client.create_container(
                    self.container_name, public_access="blob"
                )
        except Exception:
            logger.exception("Failed to ensure blob container exists")

    def _generate_blob_name(self, original_filename: str | None) -> str:
        ext = "jpg"
        if original_filename and "." in original_filename:
            ext = original_filename.rsplit(".", 1)[-1].lower()
        date_prefix = datetime.now(timezone.utc).strftime("%Y/%m/%d")
        return f"{date_prefix}/{uuid.uuid4()}.{ext}"

    async def upload(self, upload: UploadFile) -> tuple[str, str, int]:
        """Upload a file to Azure Blob Storage.

        Returns (blob_name, blob_url, size_bytes).
        """
        self._ensure_container()
        content = await upload.read()
        size_bytes = len(content)
        blob_name = self._generate_blob_name(upload.filename)

        content_type = upload.content_type or "application/octet-stream"

        blob_client = self.client.get_blob_client(
            container=self.container_name, blob=blob_name
        )
        blob_client.upload_blob(
            content,
            overwrite=True,
            content_settings=ContentSettings(content_type=content_type),
        )

        blob_url = blob_client.url
        return blob_name, blob_url, size_bytes

    def delete(self, blob_name: str) -> None:
        try:
            blob_client = self.client.get_blob_client(
                container=self.container_name, blob=blob_name
            )
            blob_client.delete_blob()
        except Exception:
            logger.exception("Failed to delete blob: %s", blob_name)

    def get_url(self, blob_name: str) -> str:
        blob_client = self.client.get_blob_client(
            container=self.container_name, blob=blob_name
        )
        return blob_client.url


blob_storage_service = BlobStorageService()
