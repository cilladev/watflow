# Claude AI Integration

Streaming AI completions with automatic token tracking, error handling, and config-driven model selection.

## Installation

```bash
pip install watflow[claude]
```

## Quick Start

```python
from watflow.integrations import ClaudeClient

# Initialize client (uses ANTHROPIC_API_KEY from .env)
client = ClaudeClient()

# Get a response
response = client.stream(
    prompt="What is 2+2?",
    model="claude-sonnet-4-5-20250929"
)

print(response.text)  # "2+2 equals 4"
print(f"Tokens: {response.usage.input_tokens} in, {response.usage.output_tokens} out")
```

## Setup

###

 1. Get an API Key

1. Sign up at [Anthropic Console](https://console.anthropic.com/)
2. Generate an API key
3. Add to your `.env` file:

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-api03-...
```

### 2. Install Dependencies

```bash
pip install watflow[claude]
```

## Usage

### Basic Completion

```python
from watflow.integrations import ClaudeClient

client = ClaudeClient()

response = client.stream(
    prompt="Explain quantum computing in one sentence",
    model="claude-sonnet-4-5-20250929",
    temperature=0.3,
    max_tokens=1000
)

print(response.text)
```

### With System Prompt

```python
response = client.stream(
    prompt="Analyze this sales data: [data here]",
    system="You are a data analyst. Be concise and focus on actionable insights.",
    model="claude-opus-4-5-20251101",
    max_tokens=5000
)
```

### Real-Time Streaming with Callback

```python
def print_chunk(text: str):
    print(text, end="", flush=True)

response = client.stream(
    prompt="Tell me a short story",
    model="claude-sonnet-4-5-20250929",
    on_chunk=print_chunk  # Prints each chunk as it arrives
)

print("\n\nDone!")
print(f"Total tokens: {response.usage.total_tokens}")
```

### Config-Driven Usage (Recommended for Workflows)

WATFlow workflows use config files to specify model settings:

```yaml
# config.yaml
models:
  analyze_data:
    model: claude-opus-4-5-20251101
    temperature: 0.3
    max_tokens: 50000

  generate_report:
    model: claude-sonnet-4-5-20250929
    temperature: 0.4
    max_tokens: 10000
```

Load and use config:

```python
from watflow.integrations import ClaudeClient
from watflow.config import load_config, get_model_config

# Load config
config = load_config()

# Get model settings for this phase
model_config = get_model_config(config, "analyze_data")

# Use config directly (unpacks model, temperature, max_tokens)
client = ClaudeClient()
response = client.stream(
    prompt="Analyze this dataset...",
    **model_config  # Unpacks all settings
)
```

## API Reference

### ClaudeClient

Main client for streaming completions.

#### Constructor

```python
ClaudeClient(api_key: Optional[str] = None)
```

**Parameters:**
- `api_key` (optional): Anthropic API key. If not provided, reads `ANTHROPIC_API_KEY` from environment.

**Raises:**
- `ClaudeAuthError`: If no API key found

**Example:**
```python
# Recommended: Use environment variable
client = ClaudeClient()

# Or pass explicitly (not recommended for production)
client = ClaudeClient(api_key="sk-ant-...")
```

#### stream()

Stream a completion from Claude.

```python
stream(
    prompt: str,
    model: str = "claude-sonnet-4-5-20250929",
    temperature: float = 0.3,
    max_tokens: int = 8000,
    system: Optional[str] = None,
    on_chunk: Optional[Callable[[str], None]] = None
) -> ClaudeResponse
```

**Parameters:**
- `prompt` (str): User prompt/question
- `model` (str): Claude model to use. Options:
  - `claude-opus-4-5-20251101` - Most capable (expensive)
  - `claude-sonnet-4-5-20250929` - Balanced (recommended)
  - `claude-haiku-4-5-20250910` - Fast and cheap
- `temperature` (float): Sampling temperature (0.0 - 1.0)
  - 0.0 = Deterministic
  - 1.0 = More creative
- `max_tokens` (int): Maximum tokens to generate (up to 200,000)
- `system` (str, optional): System prompt to set behavior
- `on_chunk` (callable, optional): Callback function called for each text chunk

**Returns:** `ClaudeResponse` object

**Raises:**
- `ClaudeAPIError`: General API errors
- `ClaudeRateLimitError`: Rate limit exceeded
- `ClaudeAuthError`: Authentication failed

### ClaudeResponse

Response object from streaming completion (Pydantic model).

**Attributes:**
- `text` (str): Complete response text
- `message` (Message): Full Anthropic Message object
- `usage` (Usage): Token usage statistics
  - `usage.input_tokens` (int): Prompt tokens
  - `usage.output_tokens` (int): Completion tokens
  - `usage.total_tokens` (int): Total tokens
- `model` (str): Model used for completion

**Example:**
```python
response = client.stream(prompt="Hello")

print(response.text)              # "Hello! How can I help you today?"
print(response.usage.input_tokens)  # 5
print(response.usage.output_tokens) # 8
print(response.model)              # "claude-sonnet-4-5-20250929"
```

### Exceptions

All exceptions inherit from `ClaudeError`:

- **ClaudeError**: Base exception
- **ClaudeAPIError**: General API errors
- **ClaudeRateLimitError**: Rate limit exceeded
- **ClaudeAuthError**: Authentication/authorization errors

**Example:**
```python
from watflow.integrations import ClaudeClient, ClaudeRateLimitError, ClaudeAuthError

try:
    client = ClaudeClient()
    response = client.stream(prompt="Hello")
except ClaudeAuthError as e:
    print(f"Authentication failed: {e}")
except ClaudeRateLimitError as e:
    print(f"Rate limit hit: {e}")
    # Wait and retry
except ClaudeAPIError as e:
    print(f"API error: {e}")
```

## Common Use Cases

### 1. Data Analysis

Analyze datasets and extract insights:

```python
from watflow.integrations import ClaudeClient

client = ClaudeClient()

# Analyze sales data
data = """
Q1: $500K revenue, 1000 customers
Q2: $750K revenue, 1500 customers
Q3: $900K revenue, 1800 customers
"""

response = client.stream(
    prompt=f"Analyze this sales data and provide 3 key insights:\n\n{data}",
    system="You are a business analyst. Be concise and actionable.",
    model="claude-opus-4-5-20251101",
    temperature=0.2,  # Low temperature for consistent analysis
    max_tokens=2000
)

print(response.text)
print(f"\nCost: ~{response.usage.input_tokens * 0.000015 + response.usage.output_tokens * 0.000075:.4f} USD")
```

### 2. Content Generation

Generate content with creative control:

```python
response = client.stream(
    prompt="Write a product description for a smart water bottle that tracks hydration",
    system="You are a marketing copywriter. Write compelling, benefit-focused copy.",
    temperature=0.7,  # Higher for creativity
    max_tokens=500
)

print(response.text)
```

### 3. Code Analysis

Analyze code and suggest improvements:

```python
code = """
def process_data(data):
    result = []
    for item in data:
        if item['status'] == 'active':
            result.append(item)
    return result
"""

response = client.stream(
    prompt=f"Review this code and suggest improvements:\n\n```python\n{code}\n```",
    system="You are a senior software engineer. Focus on performance and readability.",
    model="claude-sonnet-4-5-20250929",
    max_tokens=2000
)

print(response.text)
```

### 4. Batch Processing with Progress

Process multiple items with progress tracking:

```python
from watflow.integrations import ClaudeClient

client = ClaudeClient()
items = ["Item 1", "Item 2", "Item 3"]

for i, item in enumerate(items, 1):
    print(f"Processing {i}/{len(items)}...", end=" ")

    response = client.stream(
        prompt=f"Summarize: {item}",
        model="claude-sonnet-4-5-20250929",
        max_tokens=500
    )

    print(f"Done ({response.usage.output_tokens} tokens)")
    print(f"  Summary: {response.text[:100]}...")
```

### 5. Streaming to File

Stream response directly to a file:

```python
output_file = "analysis.txt"

with open(output_file, "w") as f:
    def write_chunk(text: str):
        f.write(text)
        print(text, end="", flush=True)

    response = client.stream(
        prompt="Write a detailed analysis of market trends in AI...",
        model="claude-opus-4-5-20251101",
        max_tokens=10000,
        on_chunk=write_chunk
    )

print(f"\n\nWritten to {output_file}")
print(f"Total tokens: {response.usage.total_tokens}")
```

### 6. Multi-Turn Conversations (Coming Soon)

For multi-turn conversations, currently you need to build the message history manually:

```python
# Current: Manual message building
# Future: ClaudeClient.chat() method for multi-turn

from anthropic import Anthropic

client = Anthropic()

messages = []

# Turn 1
messages.append({"role": "user", "content": "What is 2+2?"})
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=100,
    messages=messages
)
messages.append({"role": "assistant", "content": response.content[0].text})

# Turn 2
messages.append({"role": "user", "content": "And what is that times 3?"})
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=100,
    messages=messages
)
```

**Note:** Multi-turn conversation support will be added in a future version of the integration.

## Migration from Direct Anthropic SDK

If you're currently using the Anthropic SDK directly in your workflows:

### Before (Direct SDK)

```python
import os
from anthropic import Anthropic

api_key = os.getenv('ANTHROPIC_API_KEY')
client = Anthropic(api_key=api_key)

response_text = ""
with client.messages.stream(
    model="claude-opus-4-5-20251101",
    max_tokens=50000,
    temperature=0.3,
    messages=[{"role": "user", "content": prompt}]
) as stream:
    for text in stream.text_stream:
        response_text += text

    final_message = stream.get_final_message()
    usage = final_message.usage
```

### After (WATFlow Integration)

```python
from watflow.integrations import ClaudeClient

client = ClaudeClient()

response = client.stream(
    prompt=prompt,
    model="claude-opus-4-5-20251101",
    temperature=0.3,
    max_tokens=50000
)

response_text = response.text
usage = response.usage
```

**Benefits:**
- 10 lines → 5 lines
- No streaming boilerplate
- Automatic token tracking (no `.get_final_message()` needed)
- Consistent error handling
- Config-compatible (`**model_config` unpacking)

## Performance & Cost

### Model Comparison

| Model | Speed | Cost (Input/Output per MTok) | Best For |
|-------|-------|------------------------------|----------|
| Claude Opus 4.5 | Slow | $15 / $75 | Complex analysis, high accuracy needs |
| Claude Sonnet 4.5 | Medium | $3 / $15 | Balanced performance (recommended) |
| Claude Haiku 4.5 | Fast | $0.80 / $4 | Simple tasks, high volume |

### Token Estimation

Rough estimates:
- 1 token ≈ 0.75 words
- 100 tokens ≈ 75 words
- 1000 tokens ≈ 750 words

Example costs for 1000-word analysis:
- Input: ~1333 tokens
- Output: ~1333 tokens
- **Opus**: ~$0.12
- **Sonnet**: ~$0.024 (recommended)
- **Haiku**: ~$0.006

### Rate Limits

Anthropic API rate limits:
- **Tier 1** (new): 50 requests/min, 50K tokens/min
- **Tier 2**: 1000 requests/min, 100K tokens/min
- **Tier 3**: 2000 requests/min, 200K tokens/min

Handle rate limits:
```python
from watflow.integrations import ClaudeClient, ClaudeRateLimitError
import time

client = ClaudeClient()

for item in items:
    try:
        response = client.stream(prompt=item, model="claude-sonnet-4-5-20250929")
    except ClaudeRateLimitError:
        print("Rate limit hit, waiting 60s...")
        time.sleep(60)
        response = client.stream(prompt=item, model="claude-sonnet-4-5-20250929")
```

## Troubleshooting

### API Key Not Found

**Error:**
```
ClaudeAuthError: ANTHROPIC_API_KEY not found
```

**Solution:**
```bash
# Add to .env file
echo "ANTHROPIC_API_KEY=sk-ant-api03-..." >> .env

# Or export in shell
export ANTHROPIC_API_KEY=sk-ant-api03-...
```

### Import Error

**Error:**
```
ImportError: Claude integration requires extra dependencies
```

**Solution:**
```bash
pip install watflow[claude]
```

### Rate Limit Errors

**Error:**
```
ClaudeRateLimitError: Rate limit exceeded
```

**Solution:** Add delays or implement retry logic (see Performance & Cost section).

### Empty Response

If you get empty responses:
- Check `max_tokens` - may be too low
- Check prompt - may be malformed
- Check system prompt - may be too restrictive

## Advanced Topics

### Custom Error Handling

```python
from watflow.integrations import (
    ClaudeClient,
    ClaudeError,
    ClaudeAPIError,
    ClaudeRateLimitError,
    ClaudeAuthError
)
import time

def robust_stream(client, prompt, max_retries=3):
    """Stream with automatic retry on rate limits."""
    for attempt in range(max_retries):
        try:
            return client.stream(
                prompt=prompt,
                model="claude-sonnet-4-5-20250929"
            )
        except ClaudeRateLimitError:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
        except ClaudeAuthError:
            print("Authentication failed - check API key")
            raise
        except ClaudeAPIError as e:
            print(f"API error: {e}")
            raise

# Usage
client = ClaudeClient()
response = robust_stream(client, "Analyze this data...")
```

### Progress Tracking for Long Completions

```python
import sys

def progress_callback(text: str):
    sys.stdout.write(text)
    sys.stdout.flush()

print("Generating analysis: ", end="")

response = client.stream(
    prompt="Write a 5000-word analysis of AI trends...",
    model="claude-opus-4-5-20251101",
    max_tokens=10000,
    on_chunk=progress_callback
)

print(f"\n\nComplete! {response.usage.total_tokens} tokens")
```

## Resources

- [Anthropic API Documentation](https://docs.anthropic.com/)
- [Claude Models Overview](https://docs.anthropic.com/claude/docs/models-overview)
- [Prompt Engineering Guide](https://docs.anthropic.com/claude/docs/prompt-engineering)
- [API Pricing](https://www.anthropic.com/pricing)

## Support

For issues or questions:
- Open an issue on [GitHub](https://github.com/cilladev/wf-automation/issues)
- Check [existing workflows](../../workflows/) for examples
