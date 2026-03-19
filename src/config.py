"""Configuration loader for HAL agent."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Loads configuration from environment variables."""

    AZURE_CLIENT_ID: str = os.getenv("AZURE_CLIENT_ID", "")
    AZURE_TENANT_ID: str = os.getenv("AZURE_TENANT_ID", "")

    @classmethod
    def validate(cls) -> list[str]:
        """Return list of missing required config values."""
        missing = []
        if not cls.AZURE_CLIENT_ID:
            missing.append("AZURE_CLIENT_ID")
        if not cls.AZURE_TENANT_ID:
            missing.append("AZURE_TENANT_ID")
        return missing
