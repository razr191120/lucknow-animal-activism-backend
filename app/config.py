import logging

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


def _load_keyvault_secrets(vault_url: str) -> dict[str, str]:
    """Fetch all required secrets from Azure Key Vault.

    Uses DefaultAzureCredential which automatically works with:
    - Managed Identity on Azure VMs (production)
    - Azure CLI login (local development)
    - Service Principal env vars (CI/CD)
    """
    try:
        from azure.identity import DefaultAzureCredential
        from azure.keyvault.secrets import SecretClient

        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=vault_url, credential=credential)

        secret_names = [
            "DATABASE-URL",
            "AZURE-STORAGE-CONNECTION-STRING",
            "AZURE-STORAGE-CONTAINER-NAME",
        ]

        secrets: dict[str, str] = {}
        for name in secret_names:
            try:
                secret = client.get_secret(name)
                env_key = name.replace("-", "_").upper()
                secrets[env_key] = secret.value or ""
            except Exception:
                logger.warning("Could not fetch secret '%s' from Key Vault", name)

        logger.info(
            "Loaded %d/%d secrets from Key Vault", len(secrets), len(secret_names)
        )
        return secrets

    except Exception:
        logger.warning(
            "Key Vault unavailable at %s — falling back to env vars / .env",
            vault_url,
        )
        return {}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    AZURE_KEY_VAULT_URL: str = ""

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/lucknow_bowls"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    NOMINATIM_BASE_URL: str = "https://nominatim.openstreetmap.org/search"
    NOMINATIM_USER_AGENT: str = "lucknow-water-bowl-project/1.0"

    AZURE_STORAGE_CONNECTION_STRING: str = ""
    AZURE_STORAGE_CONTAINER_NAME: str = "uploads"


def _build_settings() -> Settings:
    """Build settings, overlaying Key Vault secrets if vault URL is configured."""
    base = Settings()

    if not base.AZURE_KEY_VAULT_URL:
        logger.info("No AZURE_KEY_VAULT_URL set — using env vars / .env only")
        return base

    kv_secrets = _load_keyvault_secrets(base.AZURE_KEY_VAULT_URL)
    if not kv_secrets:
        return base

    overrides: dict[str, str] = {}
    if "DATABASE_URL" in kv_secrets:
        overrides["DATABASE_URL"] = kv_secrets["DATABASE_URL"]
    if "AZURE_STORAGE_CONNECTION_STRING" in kv_secrets:
        overrides["AZURE_STORAGE_CONNECTION_STRING"] = kv_secrets[
            "AZURE_STORAGE_CONNECTION_STRING"
        ]
    if "AZURE_STORAGE_CONTAINER_NAME" in kv_secrets:
        overrides["AZURE_STORAGE_CONTAINER_NAME"] = kv_secrets[
            "AZURE_STORAGE_CONTAINER_NAME"
        ]

    if overrides:
        return Settings(**overrides)
    return base


settings = _build_settings()
