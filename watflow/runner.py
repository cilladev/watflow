"""
Base workflow runner for WATFlow workflows.

Provides a minimal abstract base class with utilities.
The actual execution logic lives in the template's main.py.
"""

import subprocess
import sys
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional

from watflow.config import load_config, get_phases, get_workflow_config, ConfigError
from watflow.env import load_env, check_env
from watflow.validation import validate_workflow, ValidationResult


class BaseWorkflowRunner(ABC):
    """
    Abstract base class for workflow runners.

    Provides minimal utilities:
    - Environment loading and validation
    - Config loading (workflow, phases)
    - Tool subprocess execution

    Subclasses MUST implement:
    - run(): The main workflow execution logic

    Subclasses CAN override:
    - REQUIRED_ENV_VARS: List of required environment variable names
    - OPTIONAL_ENV_VARS: List of optional environment variable names
    """

    # Override in subclass
    REQUIRED_ENV_VARS: list[str] = []
    OPTIONAL_ENV_VARS: list[str] = []

    def __init__(self, tools_dir: Optional[Path] = None):
        """
        Initialize the workflow runner.

        Args:
            tools_dir: Path to tools directory. Defaults to ./tools/
        """
        self.start_time = datetime.now()
        self.tools_dir = tools_dir or Path.cwd() / "tools"

        # Load environment
        load_env()

        # Load configuration
        try:
            self.config = load_config()
            self.phases = get_phases(self.config)
            self.workflow_config = get_workflow_config(self.config)
        except ConfigError as e:
            print(f"ERROR: Config loading failed: {e}", file=sys.stderr)
            raise

    def validate_environment(self) -> bool:
        """
        Validate that required environment variables are set.

        Returns:
            True if all required variables are set.

        Raises:
            EnvError: If required variables are missing.
        """
        if self.REQUIRED_ENV_VARS:
            check_env(self.REQUIRED_ENV_VARS, self.OPTIONAL_ENV_VARS)
        return True

    def validate_requirements(self) -> ValidationResult:
        """
        Validate workflow requirements from config.

        Checks env vars and files defined in config.yaml requirements section.

        Returns:
            ValidationResult with missing env vars and files.
        """
        return validate_workflow(self.config, Path.cwd())

    def get_workflow_name(self) -> str:
        """Return the name of this workflow from config."""
        return self.workflow_config.get("name", "Unnamed Workflow")

    @staticmethod
    def run_tool_subprocess(
        tool_path: Path, timeout: int = 120
    ) -> tuple[bool, str, str, int]:
        """
        Execute a tool script in a subprocess.

        Args:
            tool_path: Path to the tool script.
            timeout: Timeout in seconds.

        Returns:
            Tuple of (success, stdout, stderr, returncode).
        """
        try:
            result = subprocess.run(
                [sys.executable, str(tool_path)],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return (
                result.returncode == 0,
                result.stdout,
                result.stderr,
                result.returncode,
            )
        except subprocess.TimeoutExpired:
            return (False, "", f"Timed out after {timeout}s", -1)
        except Exception as e:
            return (False, "", str(e), -1)

    @abstractmethod
    def run(self) -> int:
        """
        Execute the workflow.

        Must be implemented by subclass with full execution logic.

        Returns:
            Exit code (0 for success, 1 for failure).
        """
        pass
