"""Azure AD authentication with persistent token cache.

Uses MSAL PublicClientApplication with:
1. Silent token acquisition (cached)
2. Interactive login fallback (browser popup)
3. Local token cache persisted to disk
"""

import os
import json
import logging

from msal import PublicClientApplication, TokenCache
from rich.console import Console

from src.config import Config

console = Console()
logger = logging.getLogger(__name__)

CACHE_PATH = ".local_token_cache.json"


class LocalTokenCache(TokenCache):
    """MSAL token cache that persists to a local JSON file."""

    def __init__(self, cache_location: str):
        super().__init__()
        self._cache_location = cache_location
        self._has_state_changed = False

        if not os.path.exists(self._cache_location):
            with self._lock:
                self._cache = {}
                with open(self._cache_location, "w") as f:
                    json.dump({}, f)
        else:
            with self._lock:
                with open(self._cache_location, "r") as f:
                    self._cache = json.load(f)

    def add(self, event, **kwargs):
        super().add(event, **kwargs)
        self._has_state_changed = True

    def modify(self, credential_type, old_entry, new_key_value_pairs=None):
        super().modify(credential_type, old_entry, new_key_value_pairs)
        self._has_state_changed = True

    def save(self):
        """Write cache to disk if changed."""
        if self._has_state_changed:
            with self._lock:
                if self._has_state_changed:
                    with open(self._cache_location, "w") as f:
                        json.dump(self._cache, f)
                    self._has_state_changed = False


# Shared cache instance
TOKEN_CACHE = LocalTokenCache(CACHE_PATH)

# Graph API scopes needed for Copilot APIs
GRAPH_SCOPES = ["https://graph.microsoft.com/.default"]


def acquire_token(force: bool = False) -> str:
    """Acquire a Graph API access token using MSAL.

    Tries silent acquisition first (from cache), falls back to
    interactive browser login.

    Args:
        force: If True, deletes cached tokens and forces a fresh browser login.

    Returns:
        Access token string.
    """
    if force:
        # Wipe cached tokens to force fresh login
        if os.path.exists(CACHE_PATH):
            os.remove(CACHE_PATH)
            console.print(
                "  [yellow]⚠[/yellow] [bold yellow]Token cache cleared — forcing fresh login[/bold yellow]"
            )
        # Re-init cache
        global TOKEN_CACHE
        TOKEN_CACHE = LocalTokenCache(CACHE_PATH)

    pca = PublicClientApplication(
        client_id=Config.AZURE_CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{Config.AZURE_TENANT_ID}",
        token_cache=TOKEN_CACHE,
    )

    response = None
    retry_interactive = force  # skip silent if forced

    try:
        accounts = pca.get_accounts()
        if accounts:
            response = pca.acquire_token_silent(GRAPH_SCOPES, account=accounts[0])
            if not response or "access_token" not in response:
                retry_interactive = True
        else:
            retry_interactive = True
    except Exception as e:
        retry_interactive = True
        logger.error(f"Silent token acquisition failed: {e}")

    if retry_interactive:
        console.print(
            "[bold yellow]  ▸ Opening browser for Microsoft login...[/bold yellow]"
        )
        response = pca.acquire_token_interactive(scopes=GRAPH_SCOPES)

    # Save cache after any token operation
    TOKEN_CACHE.save()

    if response and "access_token" in response:
        return response["access_token"]

    error = response.get("error_description", "Unknown error") if response else "No response"
    raise RuntimeError(f"Token acquisition failed: {error}")
