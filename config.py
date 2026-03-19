"""Configuration loader for HAL agent."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Loads configuration from environment variables."""

    AZURE_CLIENT_ID: str = os.getenv("AZURE_CLIENT_ID", "")
    AZURE_TENANT_ID: str = os.getenv("AZURE_TENANT_ID", "")

    # Optional pre-configured resource IDs
    TEAMS_TEAM_ID: str = os.getenv("TEAMS_TEAM_ID", "")
    TEAMS_CHANNEL_ID: str = os.getenv("TEAMS_CHANNEL_ID", "")
    PLANNER_PLAN_ID: str = os.getenv("PLANNER_PLAN_ID", "")
    PLANNER_BUCKET_ID: str = os.getenv("PLANNER_BUCKET_ID", "")
    SHAREPOINT_SITE_ID: str = os.getenv("SHAREPOINT_SITE_ID", "")

    # Microsoft Graph scopes needed for all services
    SCOPES: list[str] = [
        "User.Read",
        "Mail.Send",
        "ChannelMessage.Send",
        "Team.ReadBasic.All",
        "Channel.ReadBasic.All",
        "Tasks.ReadWrite",
        "Group.ReadWrite.All",
        "Sites.Read.All",
        "Files.Read.All",
    ]

    @classmethod
    def validate(cls) -> list[str]:
        """Return list of missing required config values."""
        missing = []
        if not cls.AZURE_CLIENT_ID:
            missing.append("AZURE_CLIENT_ID")
        if not cls.AZURE_TENANT_ID:
            missing.append("AZURE_TENANT_ID")
        return missing
