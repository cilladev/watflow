# Workflow Structure

Every WATFlow workflow follows a consistent structure that makes it self-contained and portable.

## Directory Layout

```
my-workflow/
├── config.yaml          # Workflow configuration (required)
├── main.py              # Entry point (required)
├── README.md            # Documentation (required)
├── requirements.txt     # Python dependencies (required)
├── .env                 # Environment variables (gitignored)
├── .env.example         # Template for required env vars
├── tools/               # Python scripts for execution
│   ├── __init__.py
│   ├── fetch_data.py
│   └── process_data.py
└── workflows/           # Markdown SOPs
    ├── collect.md
    └── analyze.md
```

## Required Files

### config.yaml

The workflow configuration file. See [Configuration Reference](configuration.md) for full details.

```yaml
# Requirements - fail fast if missing
requirements:
  env:
    - ANTHROPIC_API_KEY
  files: []

# Metadata
workflow:
  name: "My Workflow"
  description: "What this workflow does"
  version: "0.1.0"

# Default phase settings
defaults:
  parallel: false
  max_workers: 4
  timeout: 120

# Execution phases
phases:
  - name: collect
    parallel: true
    tools:
      - fetch_data.py

  - name: process
    tools:
      - transform_data.py

# AI models
models:
  default:
    model: claude-sonnet-4-20250514
    temperature: 0.3
    max_tokens: 8000

# Custom settings
settings:
  max_results: 100
```

### main.py

The entry point for workflow execution. This runs when you call `wat run` or deploy to Modal.

```python
#!/usr/bin/env python3
"""Main entry point for the workflow."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    """Run the workflow."""
    print("Running workflow...")
    # Your workflow logic here

if __name__ == "__main__":
    main()
```

### requirements.txt

Python dependencies for the workflow. Include WATFlow itself:

```
watflow>=0.1.0
python-dotenv>=1.0.0
requests>=2.31.0
# Add your dependencies here
```

### README.md

Documentation for the workflow. Describe what it does, how to configure it, and how to run it.

## Optional Files

### .env and .env.example

`.env` contains your actual API keys (gitignored). `.env.example` is a template:

```
# .env.example
ANTHROPIC_API_KEY=your-key-here
GITHUB_TOKEN=your-token-here
```

### tools/

Python scripts that perform deterministic execution. Each tool should:
- Do one thing well
- Be independently testable
- Handle errors gracefully
- Return structured data

```python
# tools/fetch_data.py
"""Fetch data from an API."""

import requests

def fetch(url: str) -> dict:
    """Fetch JSON data from URL."""
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    # Allow standalone execution for testing
    import sys
    result = fetch(sys.argv[1])
    print(result)
```

### workflows/

Markdown files that serve as Standard Operating Procedures (SOPs). These are human-readable instructions that AI agents follow.

```markdown
# Data Collection Workflow

## Objective
Collect trending topics from multiple sources.

## Steps
1. Fetch data from GitHub Trending
2. Fetch data from Hacker News
3. Combine and deduplicate results
4. Output to JSON file

## Error Handling
- If GitHub API fails, retry 3 times with exponential backoff
- If HN API fails, continue with partial data
```

## The WAT Pattern

```
┌────────────────┐     ┌────────────────┐     ┌────────────────┐
│   Workflows    │────▶│     Agent      │────▶│     Tools      │
│   (Markdown)   │     │     (AI)       │     │   (Python)     │
│                │     │                │     │                │
│  What to do    │     │  Coordinates   │     │  How to do it  │
│  Instructions  │     │  Decisions     │     │  Execution     │
└────────────────┘     └────────────────┘     └────────────────┘
```

- **Workflows**: Define the objective and steps in plain language
- **Agents**: AI reads workflows, makes decisions, calls tools
- **Tools**: Python scripts that do the actual work reliably

## Portability

Each workflow is completely self-contained. You can:

1. Copy the workflow folder anywhere
2. Run `pip install -r requirements.txt`
3. Configure `.env`
4. Run `python main.py`

No external dependencies on the parent project structure.
