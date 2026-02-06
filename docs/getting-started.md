# Getting Started with WATFlow

## Installation

```bash
uv pip install watflow

# With optional integrations
uv pip install watflow[claude]      # Claude AI
uv pip install watflow[gmail]       # Gmail
uv pip install watflow[modal]       # Modal deployment
uv pip install watflow[all]         # All integrations
```

## Create Your First Workflow

```bash
# Create a new workflow
wat new my-first-workflow

# Navigate to the workflow
cd workflows/automation/my-first-workflow
```

This creates a workflow with the following structure:

```
my-first-workflow/
├── config.yaml          # Configuration
├── main.py              # Entry point
├── README.md            # Documentation
├── requirements.txt     # Dependencies
├── .env.example         # Required environment variables
├── tools/               # Python scripts
│   └── example_tool.py
└── workflows/           # Markdown SOPs
    └── main.md
```

## Configure Your Workflow

1. **Copy the environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Add your API keys to `.env`:**
   ```
   ANTHROPIC_API_KEY=your-key-here
   ```

3. **Edit `config.yaml`** to define your workflow phases and tools.

## Run Your Workflow

```bash
# From anywhere
wat run my-first-workflow

# Or directly
cd workflows/automation/my-first-workflow
python main.py
```

## Validate Your Workflow

Check that your workflow has all required files and valid configuration:

```bash
wat validate my-first-workflow
```

## Deploy to Modal

Deploy your workflow to run on a schedule:

```bash
# One-time setup
uv pip install modal
modal setup

# Deploy
wat deploy my-first-workflow
```

## Next Steps

- [Workflow Structure](workflow-structure.md) - Detailed workflow anatomy
- [Configuration](configuration.md) - All config.yaml options
- [CLI Reference](cli-reference.md) - All `wat` commands
- [Deployment](deployment.md) - Modal deployment guide
- [Integrations](integrations.md) - Claude, Gmail, Modal
