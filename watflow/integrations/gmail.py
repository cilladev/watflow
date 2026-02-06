"""Gmail integration for WATFlow workflows.

Send and read emails via the Gmail API with OAuth 2.0 authentication.

Based on official Gmail API documentation:
- https://developers.google.com/workspace/gmail/api/quickstart/python
- https://developers.google.com/workspace/gmail/api/guides/sending
- https://developers.google.com/workspace/gmail/api/guides/list-messages

Example:
    from watflow.integrations import GmailClient

    gmail = GmailClient()

    # Send email
    gmail.send(to="user@example.com", subject="Hi", body="Hello!")

    # Read emails
    for msg in gmail.get_unread():
        print(msg.subject)
        msg.mark_as_read()
"""

from __future__ import annotations

import base64
import mimetypes
from dataclasses import dataclass, field
from email.message import EmailMessage
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

if TYPE_CHECKING:
    from googleapiclient._apis.gmail.v1 import GmailResource


# =============================================================================
# Exceptions
# =============================================================================


class GmailError(Exception):
    """Base exception for Gmail integration."""

    pass


class GmailAuthError(GmailError):
    """Authentication/authorization error."""

    pass


class GmailSendError(GmailError):
    """Email sending error."""

    pass


class GmailReadError(GmailError):
    """Email reading error."""

    pass


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class GmailMessage:
    """
    Represents a Gmail message with helper methods.

    Based on Gmail API Message resource:
    https://developers.google.com/workspace/gmail/api/v1/reference/users/messages

    Attributes:
        id: The immutable message ID.
        thread_id: The thread this message belongs to.
        subject: Email subject from headers.
        sender: From address.
        to: To address.
        date: Date header value.
        snippet: Short preview of the message.
        body_plain: Plain text body content.
        body_html: HTML body content.
        labels: List of label IDs (e.g., ["INBOX", "UNREAD"]).
        attachments: List of attachment metadata dicts.
    """

    id: str
    thread_id: str
    subject: str
    sender: str
    to: str
    date: str
    snippet: str
    body_plain: str
    body_html: str
    labels: list[str]
    attachments: list[dict] = field(default_factory=list)
    _client: Optional[GmailClient] = field(default=None, repr=False)

    def mark_as_read(self) -> None:
        """Remove UNREAD label from this message."""
        if self._client:
            self._client._modify_labels(self.id, remove=["UNREAD"])

    def mark_as_unread(self) -> None:
        """Add UNREAD label to this message."""
        if self._client:
            self._client._modify_labels(self.id, add=["UNREAD"])

    def star(self) -> None:
        """Star this message."""
        if self._client:
            self._client._modify_labels(self.id, add=["STARRED"])

    def unstar(self) -> None:
        """Remove star from this message."""
        if self._client:
            self._client._modify_labels(self.id, remove=["STARRED"])

    def trash(self) -> None:
        """Move this message to trash."""
        if self._client:
            self._client.service.users().messages().trash(
                userId="me", id=self.id
            ).execute()

    def add_label(self, label: str) -> None:
        """Add a label to this message."""
        if self._client:
            self._client._modify_labels(self.id, add=[label])

    def remove_label(self, label: str) -> None:
        """Remove a label from this message."""
        if self._client:
            self._client._modify_labels(self.id, remove=[label])

    def download_attachments(self, output_dir: str | Path) -> list[Path]:
        """
        Download all attachments to the specified directory.

        Args:
            output_dir: Directory to save attachments to.

        Returns:
            List of paths to downloaded files.
        """
        if not self._client or not self.attachments:
            return []

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        downloaded = []
        for attachment in self.attachments:
            attachment_id = attachment.get("attachment_id")
            filename = attachment.get("filename", "attachment")

            if not attachment_id:
                continue

            # Fetch attachment data
            att = (
                self._client.service.users()
                .messages()
                .attachments()
                .get(userId="me", messageId=self.id, id=attachment_id)
                .execute()
            )

            # Decode and save
            data = base64.urlsafe_b64decode(att["data"])
            file_path = output_path / filename
            file_path.write_bytes(data)
            downloaded.append(file_path)

        return downloaded


# =============================================================================
# Main Client
# =============================================================================


class GmailClient:
    """
    Gmail API client for sending and reading emails.

    Handles OAuth 2.0 authentication with automatic token refresh.
    On first use, opens a browser window for user consent.

    OAuth Scopes:
        SCOPE_SEND: Send emails only
        SCOPE_READ: Read emails only (no modifications)
        SCOPE_MODIFY: Read, send, modify labels, trash (default)
        SCOPE_FULL: Full mailbox access

    Args:
        credentials_file: Path to OAuth credentials.json from Google Cloud Console.
        token_file: Path to store/load cached OAuth token.
        scopes: OAuth scopes to request. Defaults to SCOPE_MODIFY.

    Example:
        gmail = GmailClient()

        # Send
        gmail.send(to="user@example.com", subject="Hi", body="Hello!")

        # Read
        for msg in gmail.get_unread():
            print(msg.subject)
            msg.mark_as_read()

        # Search
        invoices = gmail.search("from:billing@company.com has:attachment")
    """

    # OAuth scopes from Gmail API docs
    SCOPE_SEND = ["https://www.googleapis.com/auth/gmail.send"]
    SCOPE_READ = ["https://www.googleapis.com/auth/gmail.readonly"]
    SCOPE_MODIFY = ["https://www.googleapis.com/auth/gmail.modify"]
    SCOPE_FULL = ["https://mail.google.com"]  # No trailing slash

    def __init__(
        self,
        credentials_file: str | Path = "credentials.json",
        token_file: str | Path = "token.json",
        scopes: Optional[list[str]] = None,
    ):
        self.credentials_file = Path(credentials_file)
        self.token_file = Path(token_file)
        # Default: modify scope (covers send + read + labels)
        self.scopes = scopes or self.SCOPE_MODIFY
        self._service: Optional[GmailResource] = None
        self._creds: Optional[Credentials] = None

    # -------------------------------------------------------------------------
    # Authentication
    # -------------------------------------------------------------------------

    def authenticate(self) -> None:
        """
        Authenticate with Gmail API using OAuth 2.0.

        Opens browser for consent on first run, caches token for subsequent use.
        Based on: https://developers.google.com/workspace/gmail/api/quickstart/python

        Raises:
            GmailAuthError: If credentials.json is not found.
        """
        # Load cached token
        if self.token_file.exists():
            self._creds = Credentials.from_authorized_user_file(
                str(self.token_file), self.scopes
            )

        # Refresh or get new token
        if not self._creds or not self._creds.valid:
            if self._creds and self._creds.expired and self._creds.refresh_token:
                try:
                    self._creds.refresh(Request())
                except Exception as e:
                    # Handle scope mismatch errors
                    error_str = str(e)
                    if "invalid_scope" in error_str or "insufficient" in error_str:
                        raise GmailAuthError(
                            f"OAuth scope mismatch. Delete {self.token_file} and re-authenticate.\n"
                            f"Error: {error_str}"
                        ) from e
                    raise GmailAuthError(f"Token refresh failed: {e}") from e
            else:
                if not self.credentials_file.exists():
                    raise GmailAuthError(
                        f"credentials.json not found at {self.credentials_file}. "
                        "Download from Google Cloud Console: "
                        "https://console.cloud.google.com/apis/credentials"
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_file), self.scopes
                )
                self._creds = flow.run_local_server(port=0)

            # Save token for next run
            self.token_file.write_text(self._creds.to_json())

        self._service = build("gmail", "v1", credentials=self._creds)

    @property
    def service(self) -> GmailResource:
        """Lazy-load authenticated Gmail API service."""
        if self._service is None:
            self.authenticate()
        return self._service  # type: ignore

    # -------------------------------------------------------------------------
    # Sending
    # -------------------------------------------------------------------------

    def send(
        self,
        to: str,
        subject: str,
        body: str,
        html: bool = False,
        attachments: Optional[list[str | Path]] = None,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
    ) -> str:
        """
        Send an email.

        Uses EmailMessage for MIME construction with base64url encoding.
        Based on: https://developers.google.com/workspace/gmail/api/guides/sending

        Args:
            to: Recipient email address.
            subject: Email subject line.
            body: Email body (plain text or HTML).
            html: If True, body is treated as HTML.
            attachments: List of file paths to attach.
            cc: CC recipients (comma-separated).
            bcc: BCC recipients (comma-separated).

        Returns:
            Message ID of the sent email.

        Raises:
            GmailSendError: If sending fails or attachment not found.
        """
        try:
            mime_message = EmailMessage()
            mime_message["To"] = to
            mime_message["Subject"] = subject
            if cc:
                mime_message["Cc"] = cc
            if bcc:
                mime_message["Bcc"] = bcc

            # Set body content
            if html:
                mime_message.set_content(body, subtype="html")
            else:
                mime_message.set_content(body)

            # Add attachments
            if attachments:
                for attachment_path in attachments:
                    path = Path(attachment_path)
                    if not path.exists():
                        raise GmailSendError(f"Attachment not found: {path}")

                    # Guess MIME type
                    type_subtype, _ = mimetypes.guess_type(str(path))
                    if type_subtype is None:
                        type_subtype = "application/octet-stream"
                    maintype, subtype = type_subtype.split("/")

                    with open(path, "rb") as fp:
                        mime_message.add_attachment(
                            fp.read(),
                            maintype=maintype,
                            subtype=subtype,
                            filename=path.name,
                        )

            # Encode and send
            encoded_message = base64.urlsafe_b64encode(
                mime_message.as_bytes()
            ).decode()

            result = (
                self.service.users()
                .messages()
                .send(userId="me", body={"raw": encoded_message})
                .execute()
            )

            return result["id"]

        except HttpError as e:
            raise GmailSendError(f"Failed to send email: {e}") from e

    # -------------------------------------------------------------------------
    # Reading
    # -------------------------------------------------------------------------

    def get_messages(
        self,
        query: str = "",
        max_results: int = 10,
        label_ids: Optional[list[str]] = None,
    ) -> list[GmailMessage]:
        """
        Get messages matching query.

        Uses GET /gmail/v1/users/{userId}/messages then fetches full details.
        Based on: https://developers.google.com/workspace/gmail/api/guides/list-messages

        Args:
            query: Gmail search query (e.g., "is:unread from:boss@company.com").
                   See: https://support.google.com/mail/answer/7190
            max_results: Maximum messages to return (1-500).
            label_ids: Filter by label IDs (e.g., ["INBOX", "UNREAD"]).

        Returns:
            List of GmailMessage objects.

        Raises:
            GmailReadError: If listing or fetching fails.
        """
        try:
            # Step 1: List message IDs
            params: dict = {"userId": "me", "maxResults": min(max_results, 500)}
            if query:
                params["q"] = query
            if label_ids:
                params["labelIds"] = label_ids

            results = self.service.users().messages().list(**params).execute()
            message_refs = results.get("messages", [])

            # Step 2: Fetch full message details for each ID
            messages = []
            for ref in message_refs:
                msg = self.get_message(ref["id"])
                messages.append(msg)

            return messages

        except HttpError as e:
            raise GmailReadError(f"Failed to list messages: {e}") from e

    def get_message(self, message_id: str) -> GmailMessage:
        """
        Get a specific message by ID.

        Uses GET /gmail/v1/users/{userId}/messages/{id} with format=full.

        Args:
            message_id: The message ID to retrieve.

        Returns:
            GmailMessage object with full details.

        Raises:
            GmailReadError: If fetching fails.
        """
        try:
            msg = (
                self.service.users()
                .messages()
                .get(userId="me", id=message_id, format="full")
                .execute()
            )

            return self._parse_message(msg)

        except HttpError as e:
            raise GmailReadError(f"Failed to get message {message_id}: {e}") from e

    def get_unread(self, max_results: int = 10) -> list[GmailMessage]:
        """Get unread inbox messages."""
        return self.get_messages(query="is:unread", max_results=max_results)

    def get_starred(self, max_results: int = 10) -> list[GmailMessage]:
        """Get starred messages."""
        return self.get_messages(query="is:starred", max_results=max_results)

    def search(self, query: str, max_results: int = 10) -> list[GmailMessage]:
        """
        Search messages using Gmail query syntax.

        Args:
            query: Gmail search query (e.g., "from:someone@example.com has:attachment").
            max_results: Maximum messages to return.

        Returns:
            List of matching GmailMessage objects.
        """
        return self.get_messages(query=query, max_results=max_results)

    # -------------------------------------------------------------------------
    # Message Parsing
    # -------------------------------------------------------------------------

    def _parse_message(self, msg: dict) -> GmailMessage:
        """Parse Gmail API message response into GmailMessage."""
        headers = {
            h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])
        }

        # Extract body (handle multipart)
        body_plain, body_html = self._extract_body(msg.get("payload", {}))

        # Extract attachment info
        attachments = self._extract_attachments(msg.get("payload", {}), msg["id"])

        return GmailMessage(
            id=msg["id"],
            thread_id=msg["threadId"],
            subject=headers.get("Subject", ""),
            sender=headers.get("From", ""),
            to=headers.get("To", ""),
            date=headers.get("Date", ""),
            snippet=msg.get("snippet", ""),
            body_plain=body_plain,
            body_html=body_html,
            labels=msg.get("labelIds", []),
            attachments=attachments,
            _client=self,
        )

    def _extract_body(self, payload: dict) -> tuple[str, str]:
        """
        Extract plain text and HTML body from message payload.

        Handles multipart/alternative, multipart/mixed, and simple messages.
        """
        body_plain = ""
        body_html = ""

        def extract_from_part(part: dict) -> None:
            nonlocal body_plain, body_html

            mime_type = part.get("mimeType", "")
            body_data = part.get("body", {}).get("data", "")

            if body_data:
                decoded = base64.urlsafe_b64decode(body_data).decode("utf-8", errors="replace")
                if mime_type == "text/plain" and not body_plain:
                    body_plain = decoded
                elif mime_type == "text/html" and not body_html:
                    body_html = decoded

            # Recurse into parts
            for sub_part in part.get("parts", []):
                extract_from_part(sub_part)

        extract_from_part(payload)
        return body_plain, body_html

    def _extract_attachments(self, payload: dict, message_id: str) -> list[dict]:
        """Extract attachment metadata from message payload."""
        attachments = []

        def extract_from_part(part: dict) -> None:
            filename = part.get("filename", "")
            body = part.get("body", {})
            attachment_id = body.get("attachmentId")

            # If it has a filename and attachment ID, it's an attachment
            if filename and attachment_id:
                attachments.append(
                    {
                        "filename": filename,
                        "mime_type": part.get("mimeType", "application/octet-stream"),
                        "size": body.get("size", 0),
                        "attachment_id": attachment_id,
                    }
                )

            # Recurse into parts
            for sub_part in part.get("parts", []):
                extract_from_part(sub_part)

        extract_from_part(payload)
        return attachments

    # -------------------------------------------------------------------------
    # Labels
    # -------------------------------------------------------------------------

    def list_labels(self) -> list[dict]:
        """
        List all labels in the account.

        Returns:
            List of label dicts with 'id', 'name', 'type' keys.
        """
        results = self.service.users().labels().list(userId="me").execute()
        return results.get("labels", [])

    def _modify_labels(
        self,
        message_id: str,
        add: Optional[list[str]] = None,
        remove: Optional[list[str]] = None,
    ) -> None:
        """
        Modify labels on a message.

        Uses POST /gmail/v1/users/{userId}/messages/{id}/modify.
        Can add/remove up to 100 labels per request.

        Args:
            message_id: The message to modify.
            add: Label IDs to add.
            remove: Label IDs to remove.
        """
        body: dict = {}
        if add:
            body["addLabelIds"] = add
        if remove:
            body["removeLabelIds"] = remove

        if body:
            self.service.users().messages().modify(
                userId="me", id=message_id, body=body
            ).execute()
