"""Azure AD authentication using device code flow."""

from azure.identity import DeviceCodeCredential
from rich.console import Console

from config import Config

console = Console()


def get_credential() -> DeviceCodeCredential:
    """Create a device code credential for interactive CLI login.

    The user will be shown a URL and code to authenticate in a browser.
    """

    def callback(verification_uri: str, user_code: str, expires_on):
        console.print(
            f"\n[bold yellow]🔑 To sign in, open [link={verification_uri}]{verification_uri}[/link] "
            f"and enter code: [bold cyan]{user_code}[/bold cyan][/bold yellow]\n"
        )

    credential = DeviceCodeCredential(
        client_id=Config.AZURE_CLIENT_ID,
        tenant_id=Config.AZURE_TENANT_ID,
        prompt_callback=callback,
    )
    return credential
