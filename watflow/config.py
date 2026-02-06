"""
Configuration loading and validation for WATFlow workflows.

Provides utilities to load config.yaml files with schema validation
and sensible defaults.
"""

from pathlib import Path
from typing import Any, Optional

import yaml


class ConfigError(Exception):
    """Raised when configuration is invalid or missing."""
    pass


# Default phase settings (phases inherit these if not specified)
DEFAULT_PHASE_SETTINGS = {
    "parallel": False,
    "max_workers": 4,
    "timeout": 120,
    "retry": 0,
    "critical": True,
    "min_success": 0,
}

# Default configuration schema
DEFAULT_CONFIG = {
    "workflow": {
        "name": "Unnamed Workflow",
        "description": "",
        "version": "0.1.0",
    },
    "defaults": DEFAULT_PHASE_SETTINGS.copy(),
    "phases": [],
    "models": {
        "default": {
            "model": "claude-sonnet-4-20250514",
            "temperature": 0.3,
            "max_tokens": 8000,
        }
    },
    "settings": {},
}

# Required fields that must be present
REQUIRED_FIELDS = ["workflow", "phases"]


_config_cache: Optional[dict[str, Any]] = None


def load_config(config_path: Optional[Path] = None, use_cache: bool = True) -> dict[str, Any]:
    """
    Load configuration from a YAML file.

    Args:
        config_path: Path to config.yaml. If None, searches current directory.
        use_cache: Whether to use cached config (default True).

    Returns:
        Configuration dictionary with defaults applied.

    Raises:
        ConfigError: If config file not found or invalid.
    """
    global _config_cache

    if use_cache and _config_cache is not None:
        return _config_cache

    # Find config file
    if config_path is None:
        config_path = Path.cwd() / "config.yaml"

    if not config_path.exists():
        raise ConfigError(f"Configuration file not found: {config_path}")

    # Load YAML
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in config file: {e}")

    # Apply defaults
    config = _apply_defaults(config, DEFAULT_CONFIG)

    # Validate
    validate_config(config)

    if use_cache:
        _config_cache = config

    return config


def _apply_defaults(config: dict[str, Any], defaults: dict[str, Any]) -> dict[str, Any]:
    """Recursively apply default values to config."""
    result = defaults.copy()

    for key, value in config.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _apply_defaults(value, result[key])
        else:
            result[key] = value

    return result


def validate_config(config: dict[str, Any]) -> None:
    """
    Validate configuration structure.

    Args:
        config: Configuration dictionary to validate.

    Raises:
        ConfigError: If configuration is invalid.
    """
    # Check required fields
    for field in REQUIRED_FIELDS:
        if field not in config:
            raise ConfigError(f"Missing required configuration field: {field}")

    # Validate workflow section
    workflow = config.get("workflow", {})
    if not isinstance(workflow, dict):
        raise ConfigError("'workflow' must be a dictionary")

    if "name" not in workflow or not workflow["name"]:
        raise ConfigError("'workflow.name' is required")

    # Validate defaults section
    defaults = config.get("defaults", {})
    if not isinstance(defaults, dict):
        raise ConfigError("'defaults' must be a dictionary")

    _validate_phase_settings(defaults, "defaults")

    # Validate phases section
    phases = config.get("phases", [])
    if not isinstance(phases, list):
        raise ConfigError("'phases' must be a list")

    if len(phases) == 0:
        raise ConfigError("'phases' must contain at least one phase")

    phase_names = set()
    for i, phase in enumerate(phases):
        if not isinstance(phase, dict):
            raise ConfigError(f"'phases[{i}]' must be a dictionary")

        if "name" not in phase:
            raise ConfigError(f"'phases[{i}].name' is required")

        phase_name = phase["name"]
        if phase_name in phase_names:
            raise ConfigError(f"Duplicate phase name: '{phase_name}'")
        phase_names.add(phase_name)

        if "tools" not in phase:
            raise ConfigError(f"'phases[{i}].tools' is required for phase '{phase_name}'")

        if not isinstance(phase["tools"], list):
            raise ConfigError(f"'phases[{i}].tools' must be a list")

        _validate_phase_settings(phase, f"phases[{i}] ({phase_name})")

    # Validate models section
    models = config.get("models", {})
    if not isinstance(models, dict):
        raise ConfigError("'models' must be a dictionary")

    for stage_name, model_config in models.items():
        if not isinstance(model_config, dict):
            raise ConfigError(f"'models.{stage_name}' must be a dictionary")

        if "model" not in model_config:
            raise ConfigError(f"'models.{stage_name}.model' is required")


def _validate_phase_settings(settings: dict[str, Any], context: str) -> None:
    """Validate phase-level settings (used for both defaults and individual phases)."""
    if "max_workers" in settings:
        max_workers = settings["max_workers"]
        if not isinstance(max_workers, int) or max_workers < 1:
            raise ConfigError(f"'{context}.max_workers' must be a positive integer")

    if "timeout" in settings:
        timeout = settings["timeout"]
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            raise ConfigError(f"'{context}.timeout' must be a positive number")

    if "parallel" in settings:
        if not isinstance(settings["parallel"], bool):
            raise ConfigError(f"'{context}.parallel' must be a boolean")

    if "critical" in settings:
        if not isinstance(settings["critical"], bool):
            raise ConfigError(f"'{context}.critical' must be a boolean")

    if "min_success" in settings:
        min_success = settings["min_success"]
        if not isinstance(min_success, int) or min_success < 0:
            raise ConfigError(f"'{context}.min_success' must be a non-negative integer")

    if "retry" in settings:
        retry = settings["retry"]
        if not isinstance(retry, int) or retry < 0:
            raise ConfigError(f"'{context}.retry' must be a non-negative integer")


def get_workflow_config(config: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Get the workflow section of config."""
    if config is None:
        config = load_config()
    return config.get("workflow", {})


def get_defaults(config: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Get the defaults section of config."""
    if config is None:
        config = load_config()
    return config.get("defaults", DEFAULT_PHASE_SETTINGS.copy())


def get_phases(config: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
    """
    Get phases with defaults applied.

    Returns a list of phase configs, each with all settings populated
    (using defaults where phase doesn't specify).
    """
    if config is None:
        config = load_config()

    defaults = get_defaults(config)
    phases = config.get("phases", [])

    # Apply defaults to each phase
    resolved_phases = []
    for phase in phases:
        resolved = DEFAULT_PHASE_SETTINGS.copy()
        resolved.update(defaults)
        resolved.update(phase)
        resolved_phases.append(resolved)

    return resolved_phases


def get_phase_by_name(
    name: str, config: Optional[dict[str, Any]] = None
) -> Optional[dict[str, Any]]:
    """Get a specific phase by name with defaults applied."""
    phases = get_phases(config)
    for phase in phases:
        if phase.get("name") == name:
            return phase
    return None


def get_model_config(
    stage: str, config: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    """
    Get model configuration for a specific stage.

    Falls back to 'default' if stage-specific config not found.

    Args:
        stage: The workflow stage name (e.g., 'extract_signals').
        config: Optional config dict (loads from file if not provided).

    Returns:
        Model configuration dictionary with 'model', 'temperature', 'max_tokens'.

    Raises:
        ConfigError: If no model configuration found.
    """
    if config is None:
        config = load_config()

    models = config.get("models", {})

    # Try stage-specific config first
    if stage in models:
        return models[stage]

    # Fall back to default
    if "default" in models:
        return models["default"]

    raise ConfigError(f"No model configuration found for stage: {stage}")


def get_settings(config: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Get the settings section of config (workflow-specific settings)."""
    if config is None:
        config = load_config()
    return config.get("settings", {})


def clear_cache() -> None:
    """Clear the configuration cache."""
    global _config_cache
    _config_cache = None


if __name__ == "__main__":
    # Test configuration loading
    try:
        config = load_config()
        print("Configuration loaded successfully!")
        print(f"Workflow: {config['workflow']['name']}")
        print(f"Version: {config['workflow']['version']}")
    except ConfigError as e:
        print(f"Configuration error: {e}")
