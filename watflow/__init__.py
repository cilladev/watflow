"""
WATFlow - WAT Framework for AI-powered workflow automations.

The WAT Framework separates AI reasoning from deterministic code execution:
- Workflows: Markdown SOPs defining what to do
- Agents: Claude AI for intelligent orchestration
- Tools: Python scripts for reliable execution
"""

__version__ = "0.1.0"

from watflow.config import (
    load_config,
    validate_config,
    ConfigError,
    get_phases,
    get_phase_by_name,
    get_defaults,
    get_workflow_config,
    get_model_config,
    get_settings,
)
from watflow.env import check_env, load_env, EnvError
from watflow.runner import BaseWorkflowRunner
from watflow.validation import (
    validate_workflow,
    format_validation_error,
    ValidationResult,
    ValidationError,
)

__all__ = [
    "__version__",
    "load_config",
    "validate_config",
    "ConfigError",
    "get_phases",
    "get_phase_by_name",
    "get_defaults",
    "get_workflow_config",
    "get_model_config",
    "get_settings",
    "check_env",
    "load_env",
    "EnvError",
    "BaseWorkflowRunner",
    "validate_workflow",
    "format_validation_error",
    "ValidationResult",
    "ValidationError",
]
