"""Email service via Microsoft Graph."""

from datetime import datetime, timezone

from msgraph import GraphServiceClient
from msgraph.generated.models.message import Message
from msgraph.generated.models.item_body import ItemBody
from msgraph.generated.models.body_type import BodyType
from msgraph.generated.models.recipient import Recipient
from msgraph.generated.models.email_address import EmailAddress
from msgraph.generated.users.item.send_mail.send_mail_post_request_body import (
    SendMailPostRequestBody,
)
from rich.console import Console

console = Console()


class MailService:
    """Send and read emails via Outlook/Graph."""

    def __init__(self, client: GraphServiceClient):
        self.client = client

    async def send_email(
        self, to: list[str], subject: str, body: str, content_type: str = "Text"
    ) -> None:
        """Send an email to one or more recipients."""
        recipients = [
            Recipient(email_address=EmailAddress(address=addr)) for addr in to
        ]
        ct = BodyType.Text if content_type == "Text" else BodyType.Html
        message = Message(
            subject=subject,
            body=ItemBody(content=body, content_type=ct),
            to_recipients=recipients,
        )
        request_body = SendMailPostRequestBody(
            message=message, save_to_sent_items=True
        )
        await self.client.me.send_mail.post(request_body)

    async def list_inbox(self, top: int = 10) -> list[dict]:
        """List recent inbox messages."""
        from msgraph.generated.users.item.mail_folders.item.messages.messages_request_builder import (
            MessagesRequestBuilder,
        )

        query = MessagesRequestBuilder.MessagesRequestBuilderGetQueryParameters(
            top=top,
            select=["subject", "from", "receivedDateTime", "isRead"],
            orderby=["receivedDateTime DESC"],
        )
        config = MessagesRequestBuilder.MessagesRequestBuilderGetRequestConfiguration(
            query_parameters=query
        )
        result = await self.client.me.mail_folders.by_mail_folder_id("inbox").messages.get(
            request_configuration=config
        )
        messages = []
        if result and result.value:
            for msg in result.value:
                from_addr = ""
                if msg.from_ and msg.from_.email_address:
                    from_addr = msg.from_.email_address.address
                messages.append({
                    "subject": msg.subject,
                    "from": from_addr,
                    "received": str(msg.received_date_time),
                    "read": msg.is_read,
                })
        return messages

    async def scan_todays_emails(self) -> dict:
        """Scan today's inbox and classify emails needing a reply.

        Returns a dict with 'all' (all today's emails) and
        'needs_reply' (unread emails where user is in TO, not just CC).
        """
        from msgraph.generated.users.item.mail_folders.item.messages.messages_request_builder import (
            MessagesRequestBuilder,
        )

        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        ).isoformat()

        query = MessagesRequestBuilder.MessagesRequestBuilderGetQueryParameters(
            top=50,
            select=[
                "subject", "from", "receivedDateTime", "isRead",
                "toRecipients", "ccRecipients", "flag", "importance",
                "hasAttachments", "bodyPreview",
            ],
            filter=f"receivedDateTime ge {today_start}",
            orderby=["receivedDateTime DESC"],
        )
        config = MessagesRequestBuilder.MessagesRequestBuilderGetRequestConfiguration(
            query_parameters=query
        )
        result = await self.client.me.mail_folders.by_mail_folder_id(
            "inbox"
        ).messages.get(request_configuration=config)

        # Get current user email for TO vs CC detection
        me = await self.client.me.get()
        my_email = (me.mail or me.user_principal_name or "").lower()

        all_emails = []
        needs_reply = []

        if result and result.value:
            for msg in result.value:
                from_name = ""
                from_addr = ""
                if msg.from_ and msg.from_.email_address:
                    from_name = msg.from_.email_address.name or ""
                    from_addr = msg.from_.email_address.address or ""

                # Check if user is a direct TO recipient (not just CC)
                is_direct = False
                if msg.to_recipients:
                    for r in msg.to_recipients:
                        if r.email_address and r.email_address.address:
                            if r.email_address.address.lower() == my_email:
                                is_direct = True
                                break

                is_flagged = False
                if msg.flag and msg.flag.flag_status:
                    is_flagged = str(msg.flag.flag_status).lower() == "flagged"

                email_data = {
                    "subject": msg.subject or "(no subject)",
                    "from_name": from_name,
                    "from_addr": from_addr,
                    "received": str(msg.received_date_time),
                    "read": msg.is_read or False,
                    "is_direct": is_direct,
                    "is_flagged": is_flagged,
                    "importance": str(msg.importance or "normal"),
                    "has_attachments": msg.has_attachments or False,
                    "preview": (msg.body_preview or "")[:120],
                }
                all_emails.append(email_data)

                # Needs reply: unread + user is in TO (not just CC'd)
                if not email_data["read"] and is_direct:
                    needs_reply.append(email_data)

        return {"all": all_emails, "needs_reply": needs_reply}
