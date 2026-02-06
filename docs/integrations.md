# Integrations

WATFlow supports optional integrations for common services.

## Installation

Install individual integrations:

```bash
uv pip install watflow[claude]      # Claude AI
uv pip install watflow[gmail]       # Gmail
uv pip install watflow[modal]       # Modal deployment
uv pip install watflow[all]         # All integrations
```

## Available Integrations

| Integration | Description | Documentation |
|-------------|-------------|---------------|
| Claude AI | Intelligent workflow orchestration | [Full Guide](integrations/CLAUDE.md) |
| Gmail | Send workflow outputs via email | [Full Guide](integrations/GMAIL.md) |
| Modal | Serverless deployment | [Deployment Guide](deployment.md) |

---

## Claude AI Integration

Use Claude for intelligent workflow orchestration.

**Installation:**
```bash
uv pip install watflow[claude]
```

**Quick Setup:**
1. Add `ANTHROPIC_API_KEY=your-key` to `.env`
2. Configure models in `config.yaml`

**[→ Full Claude Integration Guide](integrations/CLAUDE.md)**

---

## Gmail Integration

Send workflow outputs via Gmail.

**Installation:**
```bash
uv pip install watflow[gmail]
```

**Quick Setup:**
1. Create Google Cloud project with Gmail API enabled
2. Download OAuth credentials as `credentials.json`
3. Run workflow once to authenticate (opens browser)

**[→ Full Gmail Integration Guide](integrations/GMAIL.md)**

---

## Modal Integration

Deploy workflows to Modal for serverless execution.

**Installation:**
```bash
uv pip install watflow[modal]
```

**Quick Setup:**
```bash
modal setup  # Opens browser for authentication
wat deploy my-workflow
```

**[→ Full Deployment Guide](deployment.md)**

---

## Future Integrations

Planned integrations (not yet implemented):

- **Google Sheets** - Read/write spreadsheet data
- **Google Drive** - File storage and retrieval
- **Slack** - Send notifications to Slack channels
- **Discord** - Send notifications to Discord
- **Notion** - Read/write Notion pages

---

## Creating Custom Integrations

Add custom integrations in your workflow's `tools/` directory:

```python
# tools/custom_integration.py
"""Custom integration for MyService."""

import os
import requests

def send_to_myservice(data: dict) -> bool:
    """Send data to MyService API."""
    response = requests.post(
        "https://api.myservice.com/data",
        json=data,
        headers={"Authorization": f"Bearer {os.environ['MYSERVICE_API_KEY']}"}
    )
    return response.ok
```

Add the required environment variable to your config:

```yaml
env:
  required:
    - MYSERVICE_API_KEY
```
