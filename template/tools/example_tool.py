#!/usr/bin/env python3
"""
Example Tool

This is a template for creating workflow tools.
Each tool should be a standalone script that:
1. Reads input from files or environment
2. Performs a specific action
3. Writes output to files
4. Returns exit code 0 on success, non-zero on failure
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
OUTPUT_DIR = Path(".tmp")


def main():
    """Main entry point."""
    print("Example Tool Starting...")

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Example: Read from environment
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set", file=sys.stderr)
        return 1

    # Example: Do some work
    result = {
        "status": "success",
        "message": "Example tool completed",
        "data": [],
    }

    # Example: Write output
    output_file = OUTPUT_DIR / "example_output.json"
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)

    print(f"Output written to: {output_file}")
    print("Example Tool Completed!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
