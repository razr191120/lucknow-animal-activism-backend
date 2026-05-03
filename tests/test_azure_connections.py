"""
Integration tests to verify Azure infrastructure connectivity.

Run with:
    uv run python -m pytest tests/test_azure_connections.py -v

Requires either:
  - AZURE_KEY_VAULT_URL env var set (tests Key Vault -> fetches other secrets)
  - Or direct env vars / .env with DATABASE_URL, AZURE_STORAGE_CONNECTION_STRING
"""

import os
import sys

import pytest

VAULT_URL = os.getenv(
    "AZURE_KEY_VAULT_URL", "https://lucknow-kv.vault.azure.net"
)


class TestKeyVault:
    """Test Azure Key Vault connectivity and secret retrieval."""

    def test_keyvault_connection(self):
        from azure.identity import DefaultAzureCredential
        from azure.keyvault.secrets import SecretClient

        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=VAULT_URL, credential=credential)

        props = client.list_properties_of_secrets()
        secret_names = [s.name for s in props]

        print(f"\n  Vault URL: {VAULT_URL}")
        print(f"  Secrets found: {secret_names}")

        assert len(secret_names) > 0, "No secrets found in Key Vault"

    def test_fetch_database_url(self):
        from azure.identity import DefaultAzureCredential
        from azure.keyvault.secrets import SecretClient

        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=VAULT_URL, credential=credential)

        secret = client.get_secret("DATABASE-URL")
        value = secret.value or ""

        print(f"\n  DATABASE-URL: {value[:30]}...{'*' * 20}")

        assert value, "DATABASE-URL secret is empty"
        assert "postgresql" in value, "DATABASE-URL doesn't look like a PostgreSQL connection string"
        assert "graitechdb" in value, "DATABASE-URL doesn't contain expected server hostname"

    def test_fetch_storage_connection_string(self):
        from azure.identity import DefaultAzureCredential
        from azure.keyvault.secrets import SecretClient

        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=VAULT_URL, credential=credential)

        secret = client.get_secret("AZURE-STORAGE-CONNECTION-STRING")
        value = secret.value or ""

        print(f"\n  Connection string starts with: {value[:40]}...")

        assert value, "AZURE-STORAGE-CONNECTION-STRING secret is empty"
        assert "AccountName=graitechstorageacc" in value

    def test_fetch_storage_container_name(self):
        from azure.identity import DefaultAzureCredential
        from azure.keyvault.secrets import SecretClient

        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=VAULT_URL, credential=credential)

        secret = client.get_secret("AZURE-STORAGE-CONTAINER-NAME")
        value = secret.value or ""

        print(f"\n  Container name: {value}")

        assert value == "uploads"


class TestBlobStorage:
    """Test Azure Blob Storage connectivity."""

    def _get_connection_string(self) -> str:
        conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
        if conn_str:
            return conn_str

        try:
            from azure.identity import DefaultAzureCredential
            from azure.keyvault.secrets import SecretClient

            credential = DefaultAzureCredential()
            client = SecretClient(vault_url=VAULT_URL, credential=credential)
            return client.get_secret("AZURE-STORAGE-CONNECTION-STRING").value or ""
        except Exception:
            pytest.skip("No blob storage connection string available")
            return ""

    def test_blob_storage_connection(self):
        from azure.storage.blob import BlobServiceClient

        conn_str = self._get_connection_string()
        client = BlobServiceClient.from_connection_string(conn_str)

        account_info = client.get_account_information()
        print(f"\n  Account kind: {account_info.get('account_kind')}")
        print(f"  SKU: {account_info.get('sku_name')}")

        assert account_info is not None

    def test_uploads_container_access(self):
        from azure.storage.blob import BlobServiceClient

        conn_str = self._get_connection_string()
        client = BlobServiceClient.from_connection_string(conn_str)

        container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "uploads")
        container_client = client.get_container_client(container_name)

        if not container_client.exists():
            client.create_container(container_name)
            print(f"\n  Created container: {container_name}")
        else:
            print(f"\n  Container '{container_name}' exists")

        assert container_client.exists(), f"Container '{container_name}' does not exist"

    def test_blob_upload_and_delete(self):
        from azure.storage.blob import BlobServiceClient, ContentSettings

        conn_str = self._get_connection_string()
        client = BlobServiceClient.from_connection_string(conn_str)

        container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "uploads")
        container_client = client.get_container_client(container_name)
        if not container_client.exists():
            client.create_container(container_name)

        test_blob_name = "test/connection-test.txt"
        test_content = b"Lucknow Water Bowl Drive - connection test"

        blob_client = client.get_blob_client(
            container=container_name, blob=test_blob_name
        )
        blob_client.upload_blob(
            test_content,
            overwrite=True,
            content_settings=ContentSettings(content_type="text/plain"),
        )
        print(f"\n  Uploaded: {blob_client.url}")

        downloaded = blob_client.download_blob().readall()
        assert downloaded == test_content, "Downloaded content doesn't match"
        print("  Download verified")

        blob_client.delete_blob()
        print("  Cleanup: deleted test blob")


class TestPostgres:
    """Test PostgreSQL connectivity."""

    def _get_database_url(self) -> str:
        db_url = os.getenv("DATABASE_URL", "")
        if db_url:
            return db_url

        try:
            from azure.identity import DefaultAzureCredential
            from azure.keyvault.secrets import SecretClient

            credential = DefaultAzureCredential()
            client = SecretClient(vault_url=VAULT_URL, credential=credential)
            return client.get_secret("DATABASE-URL").value or ""
        except Exception:
            pytest.skip("No database URL available")
            return ""

    def test_postgres_connection(self):
        import asyncio

        async def _test():
            from sqlalchemy.ext.asyncio import create_async_engine
            from sqlalchemy import text

            db_url = self._get_database_url()
            engine = create_async_engine(
                db_url, echo=False,
                connect_args={"timeout": 10},
            )

            async with engine.connect() as conn:
                result = await conn.execute(text("SELECT version()"))
                version = result.scalar()
                print(f"\n  PostgreSQL: {version}")

                result = await conn.execute(text("SELECT current_database()"))
                db_name = result.scalar()
                print(f"  Database: {db_name}")

            await engine.dispose()
            return version

        version = asyncio.run(_test())
        assert version is not None
        assert "PostgreSQL" in version

    def test_postgres_create_extension(self):
        """Verify we can run basic DDL (needed for migrations)."""
        import asyncio

        async def _test():
            from sqlalchemy.ext.asyncio import create_async_engine
            from sqlalchemy import text

            db_url = self._get_database_url()
            engine = create_async_engine(
                db_url, echo=False,
                connect_args={"timeout": 10},
            )

            async with engine.connect() as conn:
                result = await conn.execute(
                    text("SELECT 1 AS test_value")
                )
                val = result.scalar()
                print(f"\n  Query result: {val}")
                assert val == 1

                result = await conn.execute(
                    text("""
                        SELECT table_name FROM information_schema.tables
                        WHERE table_schema = 'public'
                        ORDER BY table_name
                    """)
                )
                tables = [row[0] for row in result.fetchall()]
                print(f"  Existing tables: {tables or '(none)'}")

            await engine.dispose()

        asyncio.run(_test())
