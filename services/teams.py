"""Teams messaging service via Microsoft Graph."""

from msgraph import GraphServiceClient
from msgraph.generated.models.chat_message import ChatMessage
from msgraph.generated.models.item_body import ItemBody
from msgraph.generated.models.body_type import BodyType
from rich.console import Console

console = Console()


class TeamsService:
    """Send messages to Teams channels and chats."""

    def __init__(self, client: GraphServiceClient):
        self.client = client

    async def list_joined_teams(self) -> list[dict]:
        """List teams the authenticated user has joined."""
        result = await self.client.me.joined_teams.get()
        teams = []
        if result and result.value:
            for team in result.value:
                teams.append({"id": team.id, "name": team.display_name})
        return teams

    async def list_channels(self, team_id: str) -> list[dict]:
        """List channels in a team."""
        result = await self.client.teams.by_team_id(team_id).channels.get()
        channels = []
        if result and result.value:
            for ch in result.value:
                channels.append({"id": ch.id, "name": ch.display_name})
        return channels

    async def send_channel_message(
        self, team_id: str, channel_id: str, message: str
    ) -> str:
        """Send a message to a Teams channel. Returns the message ID."""
        body = ChatMessage(
            body=ItemBody(content=message, content_type=BodyType.Text)
        )
        result = await (
            self.client.teams.by_team_id(team_id)
            .channels.by_channel_id(channel_id)
            .messages.post(body)
        )
        return result.id if result else "unknown"

    async def send_chat_message(self, chat_id: str, message: str) -> str:
        """Send a message to an existing 1:1 or group chat."""
        body = ChatMessage(
            body=ItemBody(content=message, content_type=BodyType.Text)
        )
        result = await self.client.chats.by_chat_id(chat_id).messages.post(body)
        return result.id if result else "unknown"
