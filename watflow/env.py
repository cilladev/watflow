"""
Environment variable validation for WATFlow workflows.

Provides utilities to check and validate required environment variables
before running workflows.
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


class EnvError(Exception):
    """Raised when required environment variables are missing or invalid."""

    pass


def load_env(env_path: Optional[Path] = None) -> bool:
    """
    Load environment variables from a .env file.

    Args:
        env_path: Path to .env file. If None, searches current directory.

    Returns:
        True if .env file was loaded, False if not found.
    """
    if env_path is None:
        env_path = Path.cwd() / ".env"

    if env_path.exists():
        load_dotenv(env_path)
        return True

    return False


def check_env(
    required: list[str],
    optional: Optional[list[str]] = None,
    raise_on_missing: bool = True,
) -> dict[str, bool]:
    """
    Check if required environment variables are set.

    Args:
        required: List of required environment variable names.
        optional: List of optional environment variable names.
        raise_on_missing: Whether to raise EnvError if required vars missing.

    Returns:
        Dictionary mapping variable names to whether they are set.

    Raises:
        EnvError: If required variables are missing and raise_on_missing is True.
    """
    result = {}
    missing = []

    # Check required variables
    for var in required:
        is_set = bool(os.getenv(var))
        result[var] = is_set
        if not is_set:
            missing.append(var)

    # Check optional variables
    if optional:
        for var in optional:
            result[var] = bool(os.getenv(var))

    # Raise error if required vars are missing
    if missing and raise_on_missing:
        raise EnvError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            f"Please set them in your .env file."
        )

    return result


def get_env(var: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    """
    Get an environment variable with optional default.

    Args:
        var: Environment variable name.
        default: Default value if not set.
        required: Whether to raise error if not set and no default.

    Returns:
        The environment variable value or default.

    Raises:
        EnvError: If required and not set with no default.
    """
    value = os.getenv(var, default)

    if value is None and required:
        raise EnvError(f"Required environment variable not set: {var}")

    return value


def parse_env_example(env_example_path: Optional[Path] = None) -> dict[str, list[str]]:
    """
    Parse a .env.example file to get required and optional variables.

    Variables marked with '# required' comment are treated as required.
    All others are treated as optional.

    Args:
        env_example_path: Path to .env.example file.

    Returns:
        Dictionary with 'required' and 'optional' lists.
    """
    if env_example_path is None:
        env_example_path = Path.cwd() / ".env.example"

    if not env_example_path.exists():
        return {"required": [], "optional": []}

    required = []
    optional = []

    with open(env_example_path, "r") as f:
        for line in f:
            line = line.strip()

            # Skip empty lines and pure comments
            if not line or line.startswith("#"):
                continue

            # Check for required marker in comment
            is_required = "# required" in line.lower() or "required" in line.lower()

            # Extract variable name
            if "=" in line:
                var_name = line.split("=")[0].strip()

                if is_required:
                    required.append(var_name)
                else:
                    optional.append(var_name)

    return {"required": required, "optional": optional}


def validate_env_from_example(
    env_example_path: Optional[Path] = None,
    raise_on_missing: bool = True,
) -> dict[str, bool]:
    """
    Validate environment variables based on .env.example file.

    Args:
        env_example_path: Path to .env.example file.
        raise_on_missing: Whether to raise error if required vars missing.

    Returns:
        Dictionary mapping variable names to whether they are set.

    Raises:
        EnvError: If required variables are missing and raise_on_missing is True.
    """
    vars_info = parse_env_example(env_example_path)
    return check_env(
        required=vars_info["required"],
        optional=vars_info["optional"],
        raise_on_missing=raise_on_missing,
    )


def print_env_status(env_status: dict[str, bool]) -> None:
    """Print environment variable status in a readable format."""
    print("\nEnvironment Variables:")
    print("-" * 40)

    for var, is_set in env_status.items():
        status = "✓ SET" if is_set else "✗ MISSING"
        print(f"  {var}: {status}")

    print("-" * 40)


if __name__ == "__main__":
    # Test environment loading
    load_env()

    # Check common required variables
    try:
        status = check_env(
            required=["ANTHROPIC_API_KEY"],
            optional=["GITHUB_TOKEN", "REDDIT_CLIENT_ID"],
            raise_on_missing=False,
        )
        print_env_status(status)
    except EnvError as e:
        print(f"Environment error: {e}")
