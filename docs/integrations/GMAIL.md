# Gmail Integration

Full-featured Gmail client with OAuth2 authentication for sending and reading emails via the Gmail API.

## Installation

```bash
pip install watflow[gmail]
```

Or install with other Google integrations:

```bash
pip install watflow[google]  # All Google integrations
pip install watflow[all]     # All integrations
```

## Setup

### 1. Google Cloud Console Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable the Gmail API:
   - Navigate to **APIs & Services** > **Library**
   - Search for "Gmail API"
   - Click **Enable**
4. Create OAuth 2.0 credentials:
   - Go to **APIs & Services** > **Credentials**
   - Click **Create Credentials** > **OAuth client ID**
   - Select **Desktop app** as application type
   - Name it (e.g., "WATFlow Gmail Client")
   - Click **Create**
5. Download the credentials:
   - Click the download icon next to your OAuth 2.0 Client ID
   - Save as `credentials.json` in your workflow directory
6. Enable scopes
   - Goto  `Data Access` > `Add or remove scopes`
   - Search and enable desired scopes depending on your use case
   - Recommended scopes:
     - `https://www.googleapis.com/auth/gmail.modify` - Full access to your Gmail account
     - `https://www.googleapis.com/auth/gmail.readonly` - Read-only access to your Gmail account
     - `https://www.googleapis.com/auth/gmail.send` - Send-only access to your Gmail account


### 2. First Run Authentication

On first use, a browser window will open for OAuth consent:

```python
from watflow.integrations import GmailClient

gmail = GmailClient()
# Browser opens automatically for authentication
# After consent, token is cached in token.json
```

The token is cached in `token.json` and will auto-refresh. You only need to authenticate once.

### 3. File Structure

```
your-workflow/
├── credentials.json    # OAuth credentials (from Google Cloud Console)
├── token.json          # Cached token (auto-generated, gitignored)
└── main.py             # Your workflow code
```

**Important:** Add `credentials.json` and `token.json` to your `.gitignore`.

## Quick Start

### Sending Emails

**Plain text:**
```python
from watflow.integrations import GmailClient

gmail = GmailClient()
gmail.send(
    to="user@example.com",
    subject="Hello from WATFlow",
    body="This is a plain text email."
)
```

**HTML email:**
```python
gmail.send(
    to="user@example.com",
    subject="Weekly Report",
    body="<h1>Your report is ready</h1><p>See attachment.</p>",
    html=True
)
```

**With attachments:**
```python
gmail.send(
    to="user@example.com",
    subject="Report with PDF",
    body="See attached report.",
    attachments=["report.pdf", "data.csv"]
)
```

**With CC/BCC:**
```python
gmail.send(
    to="primary@example.com",
    cc="cc@example.com",
    bcc="bcc@example.com",
    subject="Team Update",
    body="This goes to multiple recipients."
)
```

### Reading Emails

**Get unread messages:**
```python
# Get 5 most recent unread messages
messages = gmail.get_unread(max_results=5)

for msg in messages:
    print(f"From: {msg.sender}")
    print(f"Subject: {msg.subject}")
    print(f"Body: {msg.body_plain}")
    print("---")
```

**Search with Gmail query syntax:**
```python
# Search for specific emails
invoices = gmail.search("from:billing@company.com has:attachment", max_results=10)

for invoice in invoices:
    print(f"{invoice.subject} - {invoice.date}")
    invoice.download_attachments("./invoices/")
```

**Common Gmail search queries:**
```python
# Unread from specific sender
gmail.search("is:unread from:boss@company.com")

# Emails with attachments
gmail.search("has:attachment")

# Emails in date range
gmail.search("after:2026/01/01 before:2026/01/31")

# Starred messages
gmail.get_starred()

# Multiple criteria
gmail.search("from:github.com subject:security is:unread")
```

See [Gmail search operators](https://support.google.com/mail/answer/7190) for full query syntax.

### Message Operations

**Mark as read/unread:**
```python
msg = gmail.get_unread()[0]
msg.mark_as_read()
msg.mark_as_unread()
```

**Star/unstar:**
```python
msg.star()
msg.unstar()
```

**Move to trash:**
```python
msg.trash()
```

**Labels:**
```python
# Add label
msg.add_label("processed")

# Remove label
msg.remove_label("processed")

# List all labels
labels = gmail.list_labels()
for label in labels:
    print(f"{label['name']} ({label['id']})")
```

**Download attachments:**
```python
msg = gmail.get_message(message_id="abc123")

# Download all attachments to directory
files = msg.download_attachments("./downloads/")
for file in files:
    print(f"Downloaded: {file}")
```

## API Reference

### GmailClient

Main client for Gmail API operations.

#### Constructor

```python
GmailClient(
    credentials_file: str | Path = "credentials.json",
    token_file: str | Path = "token.json",
    scopes: Optional[list[str]] = None
)
```

**Parameters:**
- `credentials_file`: Path to OAuth credentials JSON (default: `credentials.json`)
- `token_file`: Path to cached token file (default: `token.json`)
- `scopes`: OAuth scopes (default: `SCOPE_MODIFY` - send + read + modify labels)

**OAuth Scopes:**
- `GmailClient.SCOPE_SEND` - Send only: `gmail.send`
- `GmailClient.SCOPE_READ` - Read only: `gmail.readonly`
- `GmailClient.SCOPE_MODIFY` - Send + read + labels: `gmail.modify` (default)
- `GmailClient.SCOPE_FULL` - Full access: `mail.google.com`

**Example:**
```python
# Default (modify scope - covers most use cases)
gmail = GmailClient()

# Send-only
gmail = GmailClient(scopes=GmailClient.SCOPE_SEND)

# Read-only
gmail = GmailClient(scopes=GmailClient.SCOPE_READ)

# Custom paths
gmail = GmailClient(
    credentials_file="config/gmail_creds.json",
    token_file="config/gmail_token.json"
)
```

#### Methods

##### send()

Send an email.

```python
send(
    to: str,
    subject: str,
    body: str,
    html: bool = False,
    attachments: Optional[list[str | Path]] = None,
    cc: Optional[str] = None,
    bcc: Optional[str] = None
) -> str
```

**Parameters:**
- `to`: Recipient email address
- `subject`: Email subject
- `body`: Email body (plain text or HTML)
- `html`: If True, body is treated as HTML
- `attachments`: List of file paths to attach
- `cc`: CC recipients (comma-separated)
- `bcc`: BCC recipients (comma-separated)

**Returns:** Message ID string

**Raises:** `GmailSendError` on failure

##### get_messages()

Get messages matching query.

```python
get_messages(
    query: str = "",
    max_results: int = 10,
    label_ids: Optional[list[str]] = None
) -> list[GmailMessage]
```

**Parameters:**
- `query`: Gmail search query (e.g., `"is:unread from:boss@company.com"`)
- `max_results`: Maximum messages to return (1-500)
- `label_ids`: Filter by label IDs (e.g., `["INBOX", "UNREAD"]`)

**Returns:** List of `GmailMessage` objects

##### get_message()

Get a specific message by ID.

```python
get_message(message_id: str) -> GmailMessage
```

**Parameters:**
- `message_id`: Gmail message ID

**Returns:** `GmailMessage` object

##### get_unread()

Get unread inbox messages.

```python
get_unread(max_results: int = 10) -> list[GmailMessage]
```

Shortcut for `get_messages(query="is:unread", max_results=max_results)`.

##### get_starred()

Get starred messages.

```python
get_starred(max_results: int = 10) -> list[GmailMessage]
```

Shortcut for `get_messages(query="is:starred", max_results=max_results)`.

##### search()

Search messages using Gmail query syntax.

```python
search(query: str, max_results: int = 10) -> list[GmailMessage]
```

**Parameters:**
- `query`: Gmail search query
- `max_results`: Maximum messages to return

**Returns:** List of `GmailMessage` objects

##### list_labels()

List all labels in the account.

```python
list_labels() -> list[dict]
```

**Returns:** List of label dictionaries with `id`, `name`, `type`, etc.

### GmailMessage

Represents a Gmail message with helper methods.

**Attributes:**
- `id` (str): Message ID
- `thread_id` (str): Thread ID
- `subject` (str): Email subject
- `sender` (str): From address
- `to` (str): To address
- `date` (str): Date string
- `snippet` (str): Preview snippet
- `body_plain` (str): Plain text body
- `body_html` (str): HTML body
- `labels` (list[str]): Label IDs
- `attachments` (list[dict]): Attachment metadata

**Methods:**
- `mark_as_read()`: Remove UNREAD label
- `mark_as_unread()`: Add UNREAD label
- `star()`: Star the message
- `unstar()`: Unstar the message
- `trash()`: Move to trash
- `add_label(label: str)`: Add a label
- `remove_label(label: str)`: Remove a label
- `download_attachments(output_dir: str | Path) -> list[Path]`: Download all attachments

### Exceptions

- `GmailError`: Base exception
- `GmailAuthError`: Authentication/authorization error
- `GmailSendError`: Email sending error
- `GmailReadError`: Email reading error

**Example:**
```python
from watflow.integrations import GmailClient, GmailSendError

try:
    gmail = GmailClient()
    gmail.send(to="user@example.com", subject="Test", body="Hello")
except GmailSendError as e:
    print(f"Failed to send email: {e}")
```

## Common Use Cases

### 1. Email-Triggered Workflows

Process new emails and take action:

```python
from watflow.integrations import GmailClient

gmail = GmailClient()

# Watch for new contact form submissions
new_leads = gmail.search("is:unread from:contact-form@mysite.com")

for lead in new_leads:
    # Extract contact info from email body
    contact_info = extract_contact_info(lead.body_plain)

    # Save to CRM
    save_to_crm(contact_info)

    # Mark as processed
    lead.mark_as_read()
    lead.add_label("processed")
```

### 2. Automated Reporting

Send weekly reports via email:

```python
from watflow.integrations import GmailClient

gmail = GmailClient()

# Generate report
report_html = generate_weekly_report()
report_pdf = create_pdf_from_html(report_html)

# Send to team
gmail.send(
    to="team@company.com",
    subject="Weekly Analytics Report - Week 5",
    body=report_html,
    html=True,
    attachments=[report_pdf]
)
```

### 3. Invoice Processing

Auto-download and process invoices:

```python
from watflow.integrations import GmailClient

gmail = GmailClient()

# Search for invoices
invoices = gmail.search(
    "from:billing@vendor.com subject:invoice has:attachment is:unread"
)

for invoice_email in invoices:
    # Download attachments
    files = invoice_email.download_attachments("./invoices/")

    # Process each attachment
    for file in files:
        if file.suffix == ".pdf":
            extract_invoice_data(file)

    # Mark as processed
    invoice_email.mark_as_read()
    invoice_email.add_label("invoices-processed")
```

### 4. Email Summarization

Summarize unread emails using AI:

```python
from watflow.integrations import GmailClient

gmail = GmailClient()

# Get unread messages
unread = gmail.get_unread(max_results=20)

# Create summary
summary_parts = []
for msg in unread:
    summary_parts.append(f"From: {msg.sender}")
    summary_parts.append(f"Subject: {msg.subject}")
    summary_parts.append(f"Preview: {msg.snippet}")
    summary_parts.append("---")

summary = "\n".join(summary_parts)

# Send summary to yourself
gmail.send(
    to="me@company.com",
    subject="Daily Email Summary",
    body=summary
)
```

### 5. Support Ticket Creation

Convert emails to support tickets:

```python
from watflow.integrations import GmailClient

gmail = GmailClient()

# Monitor support inbox
support_emails = gmail.search("to:support@company.com is:unread")

for email in support_emails:
    # Create ticket in your system
    ticket_id = create_support_ticket(
        subject=email.subject,
        body=email.body_plain,
        sender=email.sender,
        attachments=email.attachments
    )

    # Reply with ticket number
    gmail.send(
        to=email.sender,
        subject=f"Re: {email.subject}",
        body=f"Thanks for contacting us! Your ticket #{ticket_id} has been created."
    )

    # Mark original as processed
    email.mark_as_read()
    email.add_label(f"ticket-{ticket_id}")
```

## Advanced Usage

### Custom OAuth Scopes

For send-only workflows (no reading):

```python
from watflow.integrations import GmailClient

# Send-only scope
gmail = GmailClient(scopes=GmailClient.SCOPE_SEND)

# Can send, but cannot read
gmail.send(to="user@example.com", subject="Test", body="Hello")
```

For read-only workflows:

```python
# Read-only scope
gmail = GmailClient(scopes=GmailClient.SCOPE_READ)

# Can read, but cannot send or modify
messages = gmail.get_unread()
```

### Batch Processing

Process messages in batches to avoid rate limits:

```python
from watflow.integrations import GmailClient
import time

gmail = GmailClient()

# Get all matching messages
all_messages = gmail.search("is:unread", max_results=100)

# Process in batches
batch_size = 10
for i in range(0, len(all_messages), batch_size):
    batch = all_messages[i:i+batch_size]

    for msg in batch:
        process_message(msg)
        msg.mark_as_read()

    # Rate limit protection
    time.sleep(1)
```

### Error Handling

Handle authentication and API errors:

```python
from watflow.integrations import (
    GmailClient,
    GmailAuthError,
    GmailSendError,
    GmailReadError
)

try:
    gmail = GmailClient()

    # Try to send
    gmail.send(to="user@example.com", subject="Test", body="Hello")

except GmailAuthError as e:
    print(f"Authentication failed: {e}")
    print("Check credentials.json and token.json")

except GmailSendError as e:
    print(f"Failed to send email: {e}")
    # Retry logic here

except GmailReadError as e:
    print(f"Failed to read messages: {e}")
```

### Multiple Accounts

Use different credentials for different accounts:

```python
from watflow.integrations import GmailClient

# Personal account
personal = GmailClient(
    credentials_file="personal_creds.json",
    token_file="personal_token.json"
)

# Work account
work = GmailClient(
    credentials_file="work_creds.json",
    token_file="work_token.json"
)

# Use separately
personal.send(to="friend@example.com", subject="Hi", body="Hey!")
work.send(to="boss@company.com", subject="Report", body="See attached")
```

## Troubleshooting

### credentials.json not found

**Error:**
```
GmailAuthError: credentials.json not found at credentials.json
```

**Solution:** Download OAuth credentials from Google Cloud Console and save as `credentials.json`.

### Invalid scope / Scope mismatch

**Error:**
```
invalid_scope: Bad Request
GmailAuthError: OAuth scope mismatch
```

**Cause:** The cached `token.json` was created with different OAuth scopes than what the code is now requesting. This happens when you change scope configurations between runs.

**Solution:** Delete `token.json` and re-authenticate:
```bash
rm token.json
python main.py  # Opens browser to re-authenticate with new scopes
```

### Rate limits

Gmail API has quotas:
- **250 messages/second** (sending)
- **1 billion quota units/day** (general)

**Solution:** Add delays between batch operations:
```python
import time
for msg in messages:
    process_message(msg)
    time.sleep(0.1)  # 100ms delay
```

### Token expired

Tokens auto-refresh, but if you see auth errors:

**Solution:** Delete `token.json` and re-authenticate:
```bash
rm token.json
python main.py  # Re-authenticates
```

## Security Best Practices

1. **Never commit credentials:**
   ```bash
   # .gitignore
   credentials.json
   token.json
   ```

2. **Use environment variables for sensitive paths:**
   ```python
   import os
   gmail = GmailClient(
       credentials_file=os.getenv("GMAIL_CREDS", "credentials.json"),
       token_file=os.getenv("GMAIL_TOKEN", "token.json")
   )
   ```

3. **Use minimal scopes:**
   - Send-only workflows → `SCOPE_SEND`
   - Read-only workflows → `SCOPE_READ`
   - Only use `SCOPE_FULL` when necessary

4. **Restrict OAuth consent screen:**
   - In Google Cloud Console, set OAuth consent to "Internal" for organization-only access

## Resources

- [Gmail API Documentation](https://developers.google.com/workspace/gmail/api)
- [Gmail Search Operators](https://support.google.com/mail/answer/7190)
- [OAuth 2.0 Setup](https://developers.google.com/workspace/gmail/api/quickstart/python)
- [Gmail API Quotas](https://developers.google.com/workspace/gmail/api/reference/quota)

## Support

For issues or questions:
- Open an issue on [GitHub](https://github.com/cilladev/wf-automation/issues)
- Check [existing workflows](../../workflows/) for examples
