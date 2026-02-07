# WATFlow

Build reliable AI automation workflows with WATFlow.


## Installation

```bash
uv pip install watflow

# With optional integrations
uv pip install watflow[claude]      # Claude AI integration
uv pip install watflow[gmail]       # Gmail integration
uv pip install watflow[all]         # All integrations
```

## Quick Start

```bash
# Create a new workflow
wat new my-workflow --category automation

# List available workflows
wat list

# Validate a workflow
wat validate my-workflow

# Run a workflow
wat run my-workflow

# Deploy to Modal (serverless)
wat deploy my-workflow
```

## Example Automations

Find ready-to-use workflow automations at:

**https://github.com/cilladev/watflow-automations**

## What is WAT?

**WAT = Workflows + Agents + Tools**

The WAT Framework separates AI reasoning from deterministic code execution:

- **Workflows**: Markdown SOPs defining what to do
- **Agents**: Claude AI for intelligent orchestration
- **Tools**: Python scripts for reliable execution

## Workflow Structure

Each workflow is a self-contained directory:

```
my-workflow/
├── config.yaml          # Workflow configuration
├── main.py              # Entry point
├── requirements.txt     # Dependencies
├── .env                 # API keys (gitignored)
├── tools/               # Python scripts
│   └── fetch_data.py
└── workflows/           # Markdown SOPs
    └── collect.md
```

## Deployment

Deploy workflows to Modal for scheduled execution:

```bash
# Install Modal
uv pip install modal
modal setup

# Deploy (one-command)
wat deploy my-workflow
```

## Documentation

- [Getting Started](docs/getting-started.md)
- [Configuration](docs/configuration.md)
- [CLI Reference](docs/cli-reference.md)
- [Deployment](docs/deployment.md)
- [Integrations](docs/integrations.md)

## License

MIT
