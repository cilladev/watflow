"""
WATFlow integrations - common integrations for workflows.

Available integrations:
- gmail: Send & read emails via Gmail API (pip install watflow[gmail])
- claude: AI streaming completions (pip install watflow[claude])

Coming soon:
- google_sheets: Google Sheets read/write (pip install watflow[sheets])
- google_drive: Google Drive upload/download (pip install watflow[drive])
- slack: Slack notifications (pip install watflow[slack])

Install all: pip install watflow[all]

Examples:
    from watflow.integrations import GmailClient, ClaudeClient

    # Gmail
    gmail = GmailClient()
    gmail.send(to="user@example.com", subject="Hi", body="Hello!")

    # Claude AI
    claude = ClaudeClient()
    response = claude.stream(prompt="What is 2+2?", model="claude-sonnet-4-5-20250929")
    print(response.text)
"""

# =============================================================================
# Integration exports - define once, use everywhere
# =============================================================================

_GMAIL_EXPORTS = {
    "GmailClient",
    "GmailMessage",
    "GmailError",
    "GmailAuthError",
    "GmailSendError",
    "GmailReadError",
}

_CLAUDE_EXPORTS = {
    "ClaudeClient",
    "ClaudeResponse",
    "ClaudeError",
    "ClaudeAPIError",
    "ClaudeRateLimitError",
    "ClaudeAuthError",
}

# Future integrations:
# _SLACK_EXPORTS = {"SlackClient", "SlackError"}
# _SHEETS_EXPORTS = {"SheetsClient", "SheetsError"}

__all__ = list(_GMAIL_EXPORTS | _CLAUDE_EXPORTS)


def __getattr__(name: str):
    """
    Lazy import integrations - dependencies only needed when used.

    This allows core watflow to work without integration dependencies.
    Each integration has its own optional dependency group.
    """
    # Gmail integration
    if name in _GMAIL_EXPORTS:
        try:
            from watflow.integrations import gmail as _gmail
        except ImportError as e:
            raise ImportError(
                "Gmail integration requires extra dependencies. "
                "Install with: pip install watflow[gmail]"
            ) from e
        return getattr(_gmail, name)

    # Claude integration
    if name in _CLAUDE_EXPORTS:
        try:
            from watflow.integrations import claude as _claude
        except ImportError as e:
            raise ImportError(
                "Claude integration requires extra dependencies. "
                "Install with: pip install watflow[claude]"
            ) from e
        return getattr(_claude, name)

    # Future: Slack integration
    # if name in _SLACK_EXPORTS:
    #     try:
    #         from watflow.integrations import slack as _slack
    #     except ImportError as e:
    #         raise ImportError(
    #             "Slack integration requires extra dependencies. "
    #             "Install with: pip install watflow[slack]"
    #         ) from e
    #     return getattr(_slack, name)

    raise AttributeError(f"module 'watflow.integrations' has no attribute {name!r}")
