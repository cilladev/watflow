# Configuration Reference

Complete reference for `config.yaml` options.

## Basic Structure

```yaml
# Requirements - validated before workflow runs
requirements:
  env: []           # Required environment variables
  files: []         # Required files

# Workflow metadata
workflow:
  name: "My Workflow"
  description: "What this workflow does"
  version: "0.1.0"

# Default settings for all phases
defaults:
  parallel: false
  max_workers: 4
  timeout: 120
  critical: true
  min_success: 0

# Phases - executed in order
phases:
  - name: collect
    tools:
      - fetch_data.py

# AI model configuration
models:
  default:
    model: claude-sonnet-4-20250514
    temperature: 0.3
    max_tokens: 8000

# Workflow-specific settings
settings:
  example_setting: "value"

# Deployment (optional)
deployment:
  platform: modal
  schedule: weekly
  schedule_day: sunday
  schedule_time: "08:00"
```

---

## Requirements

Define environment variables and files that must exist before the workflow runs.

```yaml
requirements:
  env:
    - ANTHROPIC_API_KEY
    - GITHUB_TOKEN
  files:
    - credentials.json
    - token.json
```

The workflow fails fast with clear error messages if any requirements are missing.

---

## Workflow Metadata

```yaml
workflow:
  name: "My Workflow"           # Required - display name
  description: "Description"    # What the workflow does
  version: "0.1.0"              # Semantic version
```

---

## Defaults

Default settings applied to all phases. Individual phases can override these.

```yaml
defaults:
  parallel: false       # Run tools sequentially by default
  max_workers: 4        # Max parallel workers when parallel: true
  timeout: 120          # Tool timeout in seconds
  critical: true        # Stop workflow on failure
  min_success: 0        # Minimum tools that must succeed
  retry: 0              # Retry count on failure
```

---

## Phases

Phases are executed in order. Each phase runs a list of tools.

```yaml
phases:
  - name: collect
    parallel: true        # Override: run tools in parallel
    max_workers: 5
    timeout: 300
    critical: false       # Continue if some tools fail
    min_success: 1        # At least 1 tool must succeed
    tools:
      - fetch_github.py
      - fetch_reddit.py
      - fetch_hackernews.py

  - name: process
    parallel: false       # Sequential execution
    timeout: 120
    tools:
      - validate_data.py
      - transform_data.py

  - name: analyze
    timeout: 180
    tools:
      - extract_signals.py

  - name: deliver
    parallel: true
    max_workers: 3
    tools:
      - export_results.py
      - send_email.py
```

### Phase Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `name` | string | required | Phase identifier |
| `tools` | list | required | Python scripts to execute |
| `parallel` | bool | false | Run tools in parallel |
| `max_workers` | int | 4 | Max concurrent tools |
| `timeout` | int | 120 | Timeout per tool (seconds) |
| `critical` | bool | true | Stop workflow on failure |
| `min_success` | int | 0 | Minimum tools that must succeed |
| `retry` | int | 0 | Retry count on failure |

---

## Models

Configure Claude AI models for different stages.

```yaml
models:
  default:
    model: claude-sonnet-4-20250514
    temperature: 0.3
    max_tokens: 8000

  # Override for specific stages
  analyze:
    model: claude-opus-4-5-20251101
    temperature: 0.2
    max_tokens: 16000
```

The framework looks for a stage-specific config first, then falls back to `default`.

---

## Settings

Workflow-specific configuration. Access these in your tools.

```yaml
settings:
  max_results: 100
  output_format: json
  deduplicate: true
  custom_option: "value"
```

---

## Deployment

Configure Modal deployment for scheduled execution.

```yaml
deployment:
  platform: modal              # Currently only 'modal' supported

  # Schedule (optional - omit for on-demand only)
  schedule: weekly             # Options: daily, weekly, monthly
  schedule_day: sunday         # For weekly: monday-sunday
  schedule_time: "08:00"       # Time in UTC (24-hour format)

  # Optional overrides
  timeout: 1800                # Seconds (default: 1800 = 30 minutes)
  python_version: "3.11"       # Python version for container
```

### Schedule Options

| Schedule | Additional Options |
|----------|-------------------|
| `daily` | `schedule_time` |
| `weekly` | `schedule_day`, `schedule_time` |
| `monthly` | `schedule_day_of_month`, `schedule_time` |

### Day Options (for weekly)

`monday`, `tuesday`, `wednesday`, `thursday`, `friday`, `saturday`, `sunday`

---

## Complete Example

```yaml
# Requirements
requirements:
  env:
    - ANTHROPIC_API_KEY
    - GITHUB_TOKEN
    - REDDIT_CLIENT_ID
    - REDDIT_CLIENT_SECRET
  files:
    - credentials.json
    - token.json

# Metadata
workflow:
  name: "SaaS Hunter"
  description: "Discover trending SaaS ideas from multiple sources"
  version: "2.0.0"

# Default phase settings
defaults:
  parallel: false
  max_workers: 4
  timeout: 120
  critical: true

# Execution phases
phases:
  - name: collect
    parallel: true
    max_workers: 5
    timeout: 300
    critical: false
    min_success: 1
    tools:
      - fetch_github_trending.py
      - fetch_hackernews.py
      - fetch_reddit.py
      - fetch_product_hunt.py
      - fetch_google_trends.py

  - name: process
    timeout: 120
    tools:
      - validate_data.py

  - name: analyze
    timeout: 300
    tools:
      - extract_signals.py

  - name: deliver
    parallel: true
    tools:
      - export_results.py
      - send_email.py

# AI models
models:
  default:
    model: claude-sonnet-4-20250514
    temperature: 0.3
    max_tokens: 8000
  analyze:
    model: claude-opus-4-5-20251101
    temperature: 0.2
    max_tokens: 16000

# Custom settings
settings:
  max_results_per_source: 50
  output_format: json
  deduplicate: true

# Deployment
deployment:
  platform: modal
  schedule: weekly
  schedule_day: sunday
  schedule_time: "08:00"
  timeout: 1800
```
