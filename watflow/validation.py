"""Validation for workflow requirements."""

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ValidationResult:
    """Result of validating requirements."""

    valid: bool = True
    missing_env: list[str] = field(default_factory=list)
    missing_files: list[str] = field(default_factory=list)


class ValidationError(Exception):
    """Raised when validation fails."""

    pass


def validate_workflow(config: dict, workflow_dir: Path) -> ValidationResult:
    """Validate workflow-level requirements from config."""
    result = ValidationResult()

    requirements = config.get("requirements", {})

    # Check environment variables
    for var in requirements.get("env", []):
        if not os.getenv(var):
            result.missing_env.append(var)
            result.valid = False

    # Check required files
    for filepath in requirements.get("files", []):
        if not (workflow_dir / filepath).exists():
            result.missing_files.append(filepath)
            result.valid = False

    return result


def format_validation_error(result: ValidationResult) -> str:
    """Format a simple error message."""
    lines = []

    if result.missing_env:
        lines.append("Missing environment variables:")
        for var in result.missing_env:
            lines.append(f"  - {var}")
        lines.append("\nAdd these to your .env file\n")

    if result.missing_files:
        lines.append("Missing required files:")
        for f in result.missing_files:
            lines.append(f"  - {f}")

    return "\n".join(lines)
