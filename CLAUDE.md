# WATFlow Project Instructions

You're working with **WATFlow**, a framework for building AI-powered workflow automations using the WAT architecture (Workflows, Agents, Tools).

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      WAT Framework                          │
├─────────────────────────────────────────────────────────────┤
│  Workflows    │  Markdown SOPs defining what to do          │
│  (Layer 1)    │  Human-readable instructions                │
├───────────────┼─────────────────────────────────────────────┤
│  Agents       │  AI for intelligent orchestration           │
│  (Layer 2)    │  Decision-making and coordination           │
├───────────────┼─────────────────────────────────────────────┤
│  Tools        │  Python scripts for execution               │
│  (Layer 3)    │  Deterministic, testable, reliable          │
└───────────────┴─────────────────────────────────────────────┘
```

**Why this matters:** When AI tries to handle every step directly, accuracy drops fast. If each step is 90% accurate, you're down to 59% success after just five steps. By offloading execution to deterministic scripts, AI stays focused on orchestration where it excels.

---

## Documentation

| Topic | Description |
|-------|-------------|
| [Getting Started](docs/getting-started.md) | Installation and first workflow |
| [Workflow Structure](docs/workflow-structure.md) | Anatomy of a workflow |
| [Configuration](docs/configuration.md) | config.yaml reference |
| [CLI Reference](docs/cli-reference.md) | All `wat` commands |
| [Deployment](docs/deployment.md) | Modal serverless deployment |
| [Integrations](docs/integrations.md) | Claude, Gmail, Modal |

### Integration Guides

| Integration | Guide |
|-------------|-------|
| Claude AI | [docs/integrations/CLAUDE.md](docs/integrations/CLAUDE.md) |
| Gmail | [docs/integrations/GMAIL.md](docs/integrations/GMAIL.md) |

---

## Project Structure

```
watflow/
├── watflow/              # Core library
│   ├── cli.py            # CLI commands
│   ├── config.py         # Configuration loading
│   ├── runner.py         # Workflow execution
│   └── validator.py      # Workflow validation
├── template/             # Template for new workflows
├── docs/                 # Documentation
└── pyproject.toml        # Poetry configuration
```

## CLI Reference

| Command | Description |
|---------|-------------|
| `wat new <name>` | Create new workflow |
| `wat list` | List workflows |
| `wat validate <name>` | Validate workflow |
| `wat run <name>` | Run workflow |
| `wat deploy <name>` | Deploy to Modal |
