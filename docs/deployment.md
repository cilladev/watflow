# Deployment Guide

Deploy WATFlow workflows to Modal for scheduled serverless execution.

## Prerequisites

1. **Modal account** - Sign up at [modal.com](https://modal.com) (free tier available)
2. **Workflow tested locally** - Run `wat run <workflow>` first
3. **API keys configured** - All required keys in your `.env` file

## Quick Start

```bash
# Install Modal (first time only)
uv pip install modal

# Authenticate with Modal (opens browser)
modal setup

# Deploy your workflow
wat deploy my-workflow
```

## What Happens During Deployment

```
wat deploy my-workflow
  │
  ├─ 1. Generates modal_app.py
  │     (Container configuration)
  │
  ├─ 2. Creates Modal secret from .env
  │     (API keys stored securely)
  │
  ├─ 3. Deploys to Modal
  │     (All files copied to container)
  │
  └─ 4. Prints success with dashboard URL
```

## Files Deployed to Modal

```
LOCAL                             MODAL CONTAINER
my-workflow/                      /root/my-workflow/
├── main.py            ────────►  ├── main.py
├── config.yaml        ────────►  ├── config.yaml
├── requirements.txt   ────────►  ├── requirements.txt
├── tools/             ────────►  ├── tools/
├── workflows/         ────────►  ├── workflows/
├── credentials.json   ────────►  ├── credentials.json
├── token.json         ────────►  ├── token.json
│                                 │
└── .env               ──secret──►  (env vars injected at runtime)
```

The `.env` file is NOT copied directly - its contents become a Modal Secret for security.

## Schedule Configuration

Add a `deployment` section to your workflow's `config.yaml`:

```yaml
deployment:
  platform: modal
  schedule: weekly          # daily, weekly, or monthly
  schedule_day: sunday      # For weekly: monday-sunday
  schedule_time: "08:00"    # UTC time (24-hour format)
  timeout: 1800             # Optional: seconds (default 1800)
```

Omit schedule fields for on-demand only (no automatic runs).

## Commands Reference

| Command | Description |
|---------|-------------|
| `wat deploy <name>` | Deploy workflow to Modal |
| `wat deploy <name> --dry-run` | Generate modal_app.py without deploying |
| `modal run modal_app.py::run_workflow` | Run deployed workflow once |
| `modal logs` | View workflow logs |

## After Deployment

- **Dashboard**: https://modal.com/apps/your-workflow-name
- **Run manually**: `modal run modal_app.py::run_workflow`
- **View logs**: Check the Modal dashboard

## Updating a Deployed Workflow

Simply run `wat deploy <name>` again. It will:
- Regenerate modal_app.py
- Update the Modal secret with current .env values
- Redeploy with the latest code

## Troubleshooting

### Modal CLI not installed

```bash
uv pip install modal
```

### Modal CLI not authenticated

```bash
modal setup
```

### Deployment fails

Check the Modal dashboard for error logs. Common issues:
- Missing dependencies in requirements.txt
- Invalid Python syntax in tools
- Missing environment variables

### Secret not found

Ensure your `.env` file exists and contains valid `KEY=value` pairs.

## Cost

Modal pricing is based on compute time. A typical workflow running weekly:
- ~30 seconds of compute time per run
- Well within free tier limits

See [Modal pricing](https://modal.com/pricing) for details.
