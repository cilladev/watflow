#!/usr/bin/env python3
"""
Workflow Entry Point

This script contains the full workflow execution logic.
Customize it for your workflow's specific needs.

Run with: python main.py
"""

import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from watflow import BaseWorkflowRunner

console = Console()


class WorkflowRunner(BaseWorkflowRunner):
    """
    Main workflow runner with full execution logic.

    Customize:
    - REQUIRED_ENV_VARS: Environment variables that must be set
    - OPTIONAL_ENV_VARS: Environment variables with warnings if missing
    - run(): Main orchestration logic
    - run_phase(): How each phase executes
    """

    # Required environment variables (workflow will fail if missing)
    REQUIRED_ENV_VARS = [
        "ANTHROPIC_API_KEY",
    ]

    # Optional environment variables (warnings if missing)
    OPTIONAL_ENV_VARS = [
        "USER_EMAIL",
    ]

    def __init__(self):
        super().__init__()
        self.results: dict[str, list[dict[str, Any]]] = {}
        self.errors: list[str] = []

    def run(self) -> int:
        """Execute the complete workflow."""
        workflow_name = self.get_workflow_name()

        # Show header
        console.print()
        console.print(
            Panel(
                f"[bold]{workflow_name}[/bold]\n"
                f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Phases: {len(self.phases)}",
                title="[blue]Workflow Start[/blue]",
                border_style="blue",
            )
        )

        try:
            # Validate requirements from config
            console.print("\n[bold]Validating requirements...[/bold]")
            result = self.validate_requirements()
            if not result.valid:
                from watflow.validation import format_validation_error

                console.print(f"[red]{format_validation_error(result)}[/red]")
                return 1
            console.print("  [green]✓ All requirements met[/green]")

            # Validate environment (legacy REQUIRED_ENV_VARS)
            self.validate_environment()

            # Run all phases from config
            for phase_config in self.phases:
                self.run_phase(phase_config)

            # Success!
            return self._finish_success()

        except Exception as e:
            return self._finish_failure(e)

    def run_phase(self, phase_config: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Execute a single phase.

        Args:
            phase_config: Phase configuration from config.yaml

        Returns:
            List of tool results with 'tool' and 'success' keys.
        """
        phase_name = phase_config["name"]
        tools = phase_config.get("tools", [])
        parallel = phase_config.get("parallel", False)
        max_workers = phase_config.get("max_workers", 4)
        timeout = phase_config.get("timeout", 120)
        critical = phase_config.get("critical", True)
        min_success = phase_config.get("min_success", 0)

        # Show phase header
        mode = "[cyan]parallel[/cyan]" if parallel else "[dim]sequential[/dim]"
        console.print(f"\n[bold]Phase:[/bold] {phase_name} ({mode})")

        # Skip empty phases
        if not tools:
            console.print("  [dim]No tools configured - skipping[/dim]")
            self.results[phase_name] = []
            return []

        # Execute tools
        if parallel:
            phase_results = self._run_parallel(tools, max_workers, timeout)
        else:
            phase_results = self._run_sequential(tools, timeout, critical)

        self.results[phase_name] = phase_results

        # Check minimum success threshold
        successful = sum(1 for r in phase_results if r["success"])
        total = len(tools)

        if successful == total:
            console.print(f"  [green]{successful}/{total} tools succeeded[/green]")
        elif successful >= min_success:
            console.print(f"  [yellow]{successful}/{total} tools succeeded[/yellow]")
        else:
            console.print(f"  [red]{successful}/{total} tools succeeded[/red]")
            raise Exception(
                f"Only {successful} tools succeeded in {phase_name}. "
                f"Minimum {min_success} required."
            )

        return phase_results

    def _run_sequential(
        self, tools: list[str], timeout: int, critical: bool
    ) -> list[dict[str, Any]]:
        """Run tools one at a time."""
        results = []

        for tool in tools:
            tool_path = self.tools_dir / tool
            console.print(f"  Running: {tool}...", end=" ")

            success, stdout, stderr, returncode = self.run_tool_subprocess(tool_path, timeout)

            if success:
                console.print("[green]done[/green]")
                if stdout.strip():
                    for line in stdout.strip().split("\n"):
                        console.print(f"    [dim]{line}[/dim]")
            else:
                console.print("[red]failed[/red]")
                error_msg = f"{tool} failed (code {returncode})"
                if stderr.strip():
                    error_msg += f": {stderr.strip()}"
                self.errors.append(error_msg)

                if critical:
                    raise Exception(error_msg)

            results.append({"tool": tool, "success": success})

        return results

    def _run_parallel(
        self, tools: list[str], max_workers: int, timeout: int
    ) -> list[dict[str, Any]]:
        """Run tools simultaneously using ProcessPoolExecutor."""
        results = []
        console.print(f"  Launching {len(tools)} tools...")

        with ProcessPoolExecutor(max_workers=min(len(tools), max_workers)) as executor:
            # Submit all tools
            future_to_tool = {
                executor.submit(self.run_tool_subprocess, self.tools_dir / tool, timeout): tool
                for tool in tools
            }

            # Collect results as they complete
            for future in as_completed(future_to_tool):
                tool = future_to_tool[future]
                try:
                    success, stdout, stderr, returncode = future.result()

                    if success:
                        console.print(f"    [green]{tool}[/green] done")
                    else:
                        console.print(f"    [red]{tool}[/red] failed")
                        error_msg = f"{tool} failed (code {returncode})"
                        if stderr.strip():
                            error_msg += f": {stderr.strip()}"
                        self.errors.append(error_msg)

                    results.append({"tool": tool, "success": success})

                except Exception as e:
                    console.print(f"    [red]{tool}[/red] error: {e}")
                    self.errors.append(f"{tool} error: {e}")
                    results.append({"tool": tool, "success": False})

        return results

    def _finish_success(self) -> int:
        """Handle successful workflow completion."""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        # Build summary table
        table = Table(show_header=True, header_style="bold")
        table.add_column("Phase")
        table.add_column("Result", justify="right")

        for phase_name, phase_results in self.results.items():
            successful = sum(1 for r in phase_results if r["success"])
            total = len(phase_results)
            if total == 0:
                table.add_row(phase_name, "[dim]skipped[/dim]")
            elif successful == total:
                table.add_row(phase_name, f"[green]{successful}/{total}[/green]")
            else:
                table.add_row(phase_name, f"[yellow]{successful}/{total}[/yellow]")

        # Show success panel
        console.print()
        console.print(
            Panel(
                f"[bold green]Completed Successfully[/bold green]\n\n"
                f"Duration: {duration:.1f}s ({duration / 60:.1f}m)\n"
                f"Finished: {end_time.strftime('%Y-%m-%d %H:%M:%S')}",
                title="[green]Workflow Complete[/green]",
                border_style="green",
            )
        )

        console.print(table)

        if self.errors:
            console.print(f"\n[yellow]Warnings ({len(self.errors)}):[/yellow]")
            for error in self.errors:
                console.print(f"  [dim]- {error}[/dim]")

        return 0

    def _finish_failure(self, error: Exception) -> int:
        """Handle workflow failure."""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        console.print()
        console.print(
            Panel(
                f"[bold red]Workflow Failed[/bold red]\n\n"
                f"Error: {error}\n"
                f"Duration: {duration:.1f}s",
                title="[red]Failure[/red]",
                border_style="red",
            )
        )

        if self.results:
            console.print(f"Failed at phase: {list(self.results.keys())[-1]}")

        if self.errors:
            console.print(f"\n[red]Errors ({len(self.errors)}):[/red]")
            for err in self.errors:
                console.print(f"  - {err}")

        console.print("\n[dim]Troubleshooting:[/dim]")
        console.print("  1. Check .env file for missing/invalid API keys")
        console.print("  2. Review error messages above")
        console.print("  3. Check .tmp/ for intermediate data")

        return 1


def main():
    """Main entry point."""
    runner = WorkflowRunner()
    return runner.run()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Workflow cancelled by user.[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Unexpected error:[/red] {e}", highlight=False)
        import traceback

        traceback.print_exc()
        sys.exit(1)
