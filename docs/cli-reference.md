# CLI Reference

Complete reference for the `wat` command-line interface.

## Global Usage

```bash
wat [OPTIONS] COMMAND [ARGS]...
```

## Commands

### wat new

Create a new workflow from template.

```bash
wat new <name> [OPTIONS]
```

**Arguments:**
- `name` - Name for the new workflow

**Options:**
- `--category`, `-c` - Category subdirectory (e.g., "data-collection", "automation")

**Examples:**

```bash
# Create workflow in workflows/
wat new my-workflow

# Create workflow in workflows/data-collection/
wat new my-workflow --category data-collection

# Short form
wat new my-workflow -c automation
```

**What it creates:**

```
workflows/my-workflow/
├── config.yaml
├── main.py
├── requirements.txt
├── .env.example
├── tools/
│   └── example_tool.py
└── workflows/
    └── main.md
```

---

### wat list

List all available workflows.

```bash
wat list
```

**Output:**

```
Available Workflows:
┌─────────────────┬─────────────────────────────────┬────────────┐
│ Name            │ Description                     │ Category   │
├─────────────────┼─────────────────────────────────┼────────────┤
│ saas-hunter     │ Discover trending SaaS ideas    │ data-coll… │
│ email-digest    │ Weekly email digest generator   │ automation │
└─────────────────┴─────────────────────────────────┴────────────┘
```

---

### wat validate

Validate workflow structure and configuration.

```bash
wat validate <name>
```

**Arguments:**
- `name` - Name of the workflow to validate

**Checks performed:**
- Required files exist (config.yaml, main.py, requirements.txt)
- config.yaml is valid YAML
- Required fields are present
- Tools referenced in config exist
- Environment variables are documented

**Example:**

```bash
wat validate saas-hunter

# Output on success:
# ✓ config.yaml exists and is valid
# ✓ main.py exists
# ✓ requirements.txt exists
# ✓ All tools exist
# ✓ Workflow is valid!

# Output on failure:
# ✗ Missing required file: requirements.txt
# ✗ Tool not found: missing_tool.py
```

---

### wat run

Run a workflow.

```bash
wat run <name> [OPTIONS]
```

**Arguments:**
- `name` - Name of the workflow to run

**Options:**
- `--env`, `-e` - Path to custom .env file

**Examples:**

```bash
# Run workflow
wat run saas-hunter

# Run with custom environment
wat run saas-hunter --env /path/to/.env.production
```

**What it does:**
1. Loads the workflow's `.env` file
2. Validates the workflow
3. Executes `main.py`
4. Displays output and any errors

---

### wat deploy

Deploy workflow to Modal for scheduled execution.

```bash
wat deploy <name> [OPTIONS]
```

**Arguments:**
- `name` - Name of the workflow to deploy

**Options:**
- `--dry-run` - Generate modal_app.py without deploying

**Examples:**

```bash
# Full deployment
wat deploy saas-hunter

# Generate config only (no deploy)
wat deploy saas-hunter --dry-run
```

**Prerequisites:**
- Modal CLI installed (`uv pip install modal`)
- Modal authenticated (`modal setup`)
- Workflow has deployment config in config.yaml

**What it does:**
1. Validates Modal CLI is installed and authenticated
2. Generates `modal_app.py` from workflow config
3. Creates/updates Modal secret from `.env`
4. Deploys to Modal
5. Prints dashboard URL

---

## Workflow Discovery

The CLI searches for workflows in:

1. `./workflows/` - Flat structure
2. `./workflows/<category>/` - Categorized structure

Both structures are supported simultaneously.

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Workflow not found |
| 3 | Validation failed |
| 4 | Deployment failed |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `WATFLOW_WORKFLOWS_DIR` | Custom workflows directory (default: `./workflows`) |
| `WATFLOW_DEBUG` | Enable debug output |
