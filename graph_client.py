"""Microsoft Graph client factory."""

from msgraph import GraphServiceClient

from auth import get_credential
from config import Config


def create_graph_client() -> GraphServiceClient:
    """Create and return an authenticated Graph client."""
    credential = get_credential()
    client = GraphServiceClient(credentials=credential, scopes=Config.SCOPES)
    return client
