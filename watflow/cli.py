"""
CLI for WATFlow framework.

Provides commands for creating, listing, validating, and running workflows.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

import click
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from watflow.config import ConfigError, load_config, validate_config
from watflow.validation import validate_workflow

console = Console()


def find_repo_root() -> Path:
    """Find the root of the wf-automation repository."""
    current = Path.cwd()

    # Walk up looking for workflows/ directory
    while current != current.parent:
        if (current / "workflows").is_dir():
            return current
        current = current.parent

    # Fall back to cwd
    return Path.cwd()


def get_workflows_dir() -> Path:
    """Get the workflows directory."""
    return find_repo_root() / "workflows"


def get_template_dir() -> Path:
    """Get the template directory from the watflow package."""
    # Template is bundled with the watflow package
    return Path(__file__).parent.parent / "template"


def load_registry() -> dict:
    """Load the workflow registry."""
    registry_path = get_workflows_dir() / "registry.yaml"

    if not registry_path.exists():
        return {"version": 1, "workflows": []}

    with open(registry_path, "r") as f:
        return yaml.safe_load(f) or {"version": 1, "workflows": []}


def save_registry(registry: dict) -> None:
    """Save the workflow registry."""
    registry_path = get_workflows_dir() / "registry.yaml"

    with open(registry_path, "w") as f:
        yaml.dump(registry, f, default_flow_style=False, sort_keys=False)


def find_workflow(name: str) -> Optional[Path]:
    """Find a workflow by name, searching in category directories."""
    workflows_dir = get_workflows_dir()

    # Check if name includes category (e.g., "data-collection/saas-hunter")
    if "/" in name:
        workflow_path = workflows_dir / name
        if workflow_path.is_dir():
            return workflow_path
        return None

    # Search in all category directories
    for category_dir in workflows_dir.iterdir():
        if category_dir.is_dir() and not category_dir.name.startswith((".", "_")):
            workflow_path = category_dir / name
            if workflow_path.is_dir():
                return workflow_path

    # Check at root level of workflows/
    workflow_path = workflows_dir / name
    if workflow_path.is_dir():
        return workflow_path

    return None


@click.group()
@click.version_option(version="0.1.0", prog_name="watflow")
def main():
    """WATFlow - AI-powered workflow automation framework."""
    pass


@main.command()
@click.argument("name")
@click.option(
    "--category",
    "-c",
    default="automation",
    help="Category for the workflow (e.g., data-collection, reporting)",
)
@click.option(
    "--description",
    "-d",
    default="",
    help="Description of the workflow",
)
def new(name: str, category: str, description: str):
    """Create a new workflow from template.

    NAME is the name of the new workflow (e.g., my-workflow).
    """
    template_dir = get_template_dir()
    workflows_dir = get_workflows_dir()

    # Check if template exists
    if not template_dir.exists():
        console.print(
            Panel(
                f"Template directory not found:\n{template_dir}",
                title="[red]Error[/red]",
                border_style="red",
            )
        )
        raise SystemExit(1)

    # Create category directory if needed
    category_dir = workflows_dir / category
    category_dir.mkdir(parents=True, exist_ok=True)

    # Check if workflow already exists
    workflow_dir = category_dir / name
    if workflow_dir.exists():
        console.print(
            Panel(
                f"Workflow already exists:\n{workflow_dir}",
                title="[red]Error[/red]",
                border_style="red",
            )
        )
        raise SystemExit(1)

    # Copy template
    shutil.copytree(template_dir, workflow_dir)

    # Update config.yaml with workflow name
    config_path = workflow_dir / "config.yaml"
    if config_path.exists():
        with open(config_path, "r") as f:
            config = yaml.safe_load(f) or {}

        config.setdefault("workflow", {})
        config["workflow"]["name"] = name.replace("-", " ").title()
        config["workflow"]["description"] = description

        with open(config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    # Add to registry
    registry = load_registry()
    registry["workflows"].append(
        {
            "name": name,
            "category": category,
            "description": description,
            "author": os.environ.get("USER", "unknown"),
            "tags": [],
        }
    )
    save_registry(registry)

    # Show success
    console.print()
    console.print(
        Panel(
            f"Created [bold cyan]{name}[/bold cyan]\n"
            f"Category: [green]{category}[/green]\n"
            f"Location: {workflow_dir}",
            title="[green]Workflow Created[/green]",
            border_style="green",
        )
    )

    console.print("\n[bold]Next steps:[/bold]")
    console.print(f"  [dim]1.[/dim] cd {workflow_dir}")
    console.print("  [dim]2.[/dim] Edit config.yaml")
    console.print("  [dim]3.[/dim] Create workflows/*.md files")
    console.print("  [dim]4.[/dim] Create tools/*.py scripts")
    console.print(f"  [dim]5.[/dim] Test with: [cyan]wat run {name}[/cyan]")


@main.command(name="list")
@click.option(
    "--category",
    "-c",
    default=None,
    help="Filter by category",
)
def list_workflows(category: Optional[str]):
    """List all available workflows."""
    registry = load_registry()
    workflows = registry.get("workflows", [])

    if not workflows:
        console.print(
            Panel(
                "No workflows found.\nCreate one with: [cyan]wat new my-workflow[/cyan]",
                title="[yellow]Empty[/yellow]",
                border_style="yellow",
            )
        )
        return

    # Filter by category if specified
    if category:
        workflows = [w for w in workflows if w.get("category") == category]
        if not workflows:
            console.print(
                Panel(
                    f"No workflows found in category: [bold]{category}[/bold]",
                    title="[yellow]Empty[/yellow]",
                    border_style="yellow",
                )
            )
            return

    # Create table
    table = Table(
        title="[bold]Available Workflows[/bold]",
        show_header=True,
        header_style="bold",
        border_style="dim",
    )
    table.add_column("Name", style="cyan")
    table.add_column("Category", style="green")
    table.add_column("Description", style="dim")
    table.add_column("Author", style="dim")

    for wf in workflows:
        desc = wf.get("description", "")
        table.add_row(
            wf.get("name", ""),
            wf.get("category", ""),
            desc[:40] + ("..." if len(desc) > 40 else ""),
            wf.get("author", ""),
        )

    console.print()
    console.print(table)
    console.print(f"\n[dim]Total: {len(workflows)} workflow(s)[/dim]")


@main.command()
@click.argument("name")
def validate(name: str):
    """Validate a workflow's structure and configuration.

    NAME is the workflow name (e.g., saas-hunter or data-collection/saas-hunter).
    """
    workflow_path = find_workflow(name)

    if not workflow_path:
        console.print(
            Panel(
                f"Workflow not found: [bold]{name}[/bold]",
                title="[red]Error[/red]",
                border_style="red",
            )
        )
        raise SystemExit(1)

    console.print()
    console.print(
        Panel(
            f"[bold]{workflow_path.name}[/bold]\n{workflow_path}",
            title="[blue]Validating[/blue]",
            border_style="blue",
        )
    )

    errors = []
    warnings = []

    # Check required files
    console.print("\n[bold]Files:[/bold]")
    required_files = ["config.yaml", "main.py", "README.md", ".env.example"]
    for filename in required_files:
        filepath = workflow_path / filename
        if filepath.exists():
            console.print(f"  [green]OK[/green] {filename}")
        else:
            errors.append(f"Missing: {filename}")
            console.print(f"  [red]MISSING[/red] {filename}")

    # Check required directories
    console.print("\n[bold]Directories:[/bold]")
    required_dirs = ["workflows", "tools"]
    for dirname in required_dirs:
        dirpath = workflow_path / dirname
        if dirpath.is_dir():
            console.print(f"  [green]OK[/green] {dirname}/")
        else:
            errors.append(f"Missing: {dirname}/")
            console.print(f"  [red]MISSING[/red] {dirname}/")

    # Validate config.yaml
    console.print("\n[bold]Config:[/bold]")
    config_path = workflow_path / "config.yaml"
    if config_path.exists():
        try:
            # Temporarily change to workflow directory for config loading
            original_cwd = Path.cwd()
            os.chdir(workflow_path)
            try:
                config = load_config(use_cache=False)
                validate_config(config)
                console.print("  [green]OK[/green] config.yaml is valid")
            finally:
                os.chdir(original_cwd)
        except ConfigError as e:
            errors.append(f"Invalid config: {e}")
            console.print(f"  [red]INVALID[/red] {e}")

    # Check for workflows
    console.print("\n[bold]Content:[/bold]")
    workflows_dir = workflow_path / "workflows"
    if workflows_dir.is_dir():
        workflow_files = list(workflows_dir.glob("*.md"))
        if workflow_files:
            console.print(f"  [green]OK[/green] {len(workflow_files)} workflow file(s)")
        else:
            warnings.append("No .md files in workflows/")
            console.print("  [yellow]WARN[/yellow] No .md files in workflows/")

    # Check for tools
    tools_dir = workflow_path / "tools"
    if tools_dir.is_dir():
        tool_files = list(tools_dir.glob("*.py"))
        if tool_files:
            console.print(f"  [green]OK[/green] {len(tool_files)} tool(s)")
        else:
            warnings.append("No .py files in tools/")
            console.print("  [yellow]WARN[/yellow] No .py files in tools/")

    # Check requirements (env vars, files) from config
    console.print("\n[bold]Requirements:[/bold]")
    if config_path.exists():
        try:
            original_cwd = Path.cwd()
            os.chdir(workflow_path)
            try:
                config = load_config(use_cache=False)
                req_result = validate_workflow(config, workflow_path)

                requirements = config.get("requirements", {})
                env_vars = requirements.get("env", [])
                req_files = requirements.get("files", [])

                if not env_vars and not req_files:
                    console.print("  [dim]No requirements defined in config.yaml[/dim]")
                else:
                    # Check env vars
                    for var in env_vars:
                        if var in req_result.missing_env:
                            errors.append(f"Missing env: {var}")
                            console.print(f"  [red]MISSING[/red] ${var}")
                        else:
                            console.print(f"  [green]OK[/green] ${var}")

                    # Check files
                    for filepath in req_files:
                        if filepath in req_result.missing_files:
                            errors.append(f"Missing file: {filepath}")
                            console.print(f"  [red]MISSING[/red] {filepath}")
                        else:
                            console.print(f"  [green]OK[/green] {filepath}")
            finally:
                os.chdir(original_cwd)
        except ConfigError:
            console.print("  [dim]Could not check (config invalid)[/dim]")
    else:
        console.print("  [dim]Could not check (no config.yaml)[/dim]")

    # Summary
    console.print()
    if errors:
        console.print(
            Panel(
                f"[bold red]Failed[/bold red] with {len(errors)} error(s)",
                border_style="red",
            )
        )
        for error in errors:
            console.print(f"  [red]-[/red] {error}")
        raise SystemExit(1)
    elif warnings:
        console.print(
            Panel(
                f"[bold yellow]Passed[/bold yellow] with {len(warnings)} warning(s)",
                border_style="yellow",
            )
        )
    else:
        console.print(
            Panel(
                "[bold green]Validation Passed[/bold green]",
                border_style="green",
            )
        )


@main.command()
@click.argument("name")
@click.option("--no-parallel", is_flag=True, help="Disable parallel execution")
def run(name: str, no_parallel: bool):
    """Run a workflow.

    NAME is the workflow name (e.g., saas-hunter or data-collection/saas-hunter).
    """
    workflow_path = find_workflow(name)

    if not workflow_path:
        console.print(
            Panel(
                f"Workflow not found: [bold]{name}[/bold]",
                title="[red]Error[/red]",
                border_style="red",
            )
        )
        raise SystemExit(1)

    main_py = workflow_path / "main.py"
    if not main_py.exists():
        console.print(
            Panel(
                f"No main.py found in workflow:\n{workflow_path}",
                title="[red]Error[/red]",
                border_style="red",
            )
        )
        raise SystemExit(1)

    console.print()
    console.print(
        Panel(
            f"[bold]{workflow_path.name}[/bold]\n{workflow_path}",
            title="[blue]Running Workflow[/blue]",
            border_style="blue",
        )
    )
    console.print()

    # Build command
    cmd = [sys.executable, str(main_py)]

    # Run the workflow
    env = os.environ.copy()
    if no_parallel:
        env["WATFLOW_NO_PARALLEL"] = "1"

    try:
        result = subprocess.run(
            cmd,
            cwd=workflow_path,
            env=env,
        )
        raise SystemExit(result.returncode)
    except KeyboardInterrupt:
        console.print("\n[yellow]Workflow cancelled by user.[/yellow]")
        raise SystemExit(1)


def check_modal_installed() -> bool:
    """Check if Modal CLI is installed."""
    return shutil.which("modal") is not None


def check_modal_authenticated() -> bool:
    """Check if Modal CLI is authenticated."""
    result = subprocess.run(
        ["modal", "profile", "current"],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def ensure_modal_ready() -> bool:
    """Ensure Modal is installed and authenticated. Returns True if ready."""
    # Check if Modal CLI is installed
    if not check_modal_installed():
        console.print(
            Panel(
                "[red]Modal CLI not installed[/red]\n\n"
                "Install with: [cyan]pip install modal[/cyan]",
                title="[red]Setup Required[/red]",
                border_style="red",
            )
        )
        return False

    # Check if Modal is authenticated
    if not check_modal_authenticated():
        console.print(
            Panel(
                "[yellow]Modal CLI not authenticated[/yellow]\n\n"
                "Run: [cyan]modal setup[/cyan]\n\n"
                "This will open your browser to authenticate with Modal.",
                title="[yellow]Setup Required[/yellow]",
                border_style="yellow",
            )
        )

        # Ask if user wants to run modal setup now
        if click.confirm("Run 'modal setup' now?", default=True):
            subprocess.run(["modal", "setup"])
            # Re-check after setup
            if not check_modal_authenticated():
                console.print("[red]Authentication failed. Please try again.[/red]")
                return False
        else:
            return False

    return True


def schedule_to_cron(config: dict) -> Optional[str]:
    """Convert human-readable schedule to cron expression.

    Config format:
        schedule: daily|weekly|monthly
        schedule_day: monday-sunday (for weekly)
        schedule_time: "HH:MM" in UTC
    """
    deployment = config.get("deployment", {})
    schedule = deployment.get("schedule")

    if not schedule:
        return None

    # Parse time (default to 08:00)
    time_str = deployment.get("schedule_time", "08:00")
    try:
        hour, minute = time_str.split(":")
        hour = int(hour)
        minute = int(minute)
    except (ValueError, AttributeError):
        hour, minute = 8, 0

    # Map day names to cron numbers (0=Sunday, 6=Saturday)
    day_map = {
        "sunday": 0,
        "monday": 1,
        "tuesday": 2,
        "wednesday": 3,
        "thursday": 4,
        "friday": 5,
        "saturday": 6,
    }

    if schedule == "daily":
        return f"{minute} {hour} * * *"
    elif schedule == "weekly":
        day_name = deployment.get("schedule_day", "sunday").lower()
        day_num = day_map.get(day_name, 0)
        return f"{minute} {hour} * * {day_num}"
    elif schedule == "monthly":
        day_of_month = deployment.get("schedule_day_of_month", 1)
        return f"{minute} {hour} {day_of_month} * *"
    else:
        return None


def generate_modal_app(workflow_path: Path, config: dict) -> Path:
    """Generate modal_app.py for the workflow."""
    workflow_name = workflow_path.name
    output_path = workflow_path / "modal_app.py"

    # Get deployment settings
    deployment = config.get("deployment", {})
    timeout = deployment.get("timeout", 1800)  # 30 min default
    python_version = deployment.get("python_version", "3.11")

    # Get cron schedule
    cron_expr = schedule_to_cron(config)

    # Build schedule decorator if needed
    if cron_expr:
        schedule_decorator = f'    schedule=modal.Cron("{cron_expr}"),'
        scheduled_function = f'''

@app.function(
    image=image,
    secrets=[modal.Secret.from_name("{workflow_name}-env")],
{schedule_decorator}
    timeout={timeout},
)
def run_scheduled():
    """Scheduled workflow execution."""
    return run_workflow.local()
'''
    else:
        scheduled_function = ""

    modal_template = f'''"""
Modal deployment for {workflow_name} workflow.

Generated by: wat deploy {workflow_name}
Deploy with: modal deploy modal_app.py
Run once: modal run modal_app.py::run_workflow
"""

import os
import subprocess
import modal

app = modal.App("{workflow_name}")

# Build image with dependencies and workflow files
image = (
    modal.Image.debian_slim(python_version="{python_version}")
    .pip_install_from_requirements("requirements.txt")
    .add_local_dir(".", remote_path="/root/{workflow_name}")
)


@app.function(
    image=image,
    secrets=[modal.Secret.from_name("{workflow_name}-env")],
    timeout={timeout},
)
def run_workflow():
    """Run the workflow."""
    os.chdir("/root/{workflow_name}")
    result = subprocess.run(
        ["python", "main.py"],
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        raise Exception(f"Workflow failed with code {{result.returncode}}")
    return result.stdout
{scheduled_function}

if __name__ == "__main__":
    # For local testing
    with app.run():
        run_workflow.remote()
'''

    with open(output_path, "w") as f:
        f.write(modal_template)

    return output_path


def create_modal_secret(workflow_path: Path) -> bool:
    """Create Modal secret from .env file."""
    workflow_name = workflow_path.name
    secret_name = f"{workflow_name}-env"

    # Load .env file
    env_path = workflow_path / ".env"
    env_vars = {}

    if env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    # Remove quotes if present
                    value = value.strip()
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    env_vars[key.strip()] = value

    if not env_vars:
        console.print("[yellow]Warning: No environment variables found in .env[/yellow]")
        return True

    # Build modal secret create command
    # Use --force to update if exists
    cmd = ["modal", "secret", "create", "--force", secret_name]
    for key, value in env_vars.items():
        cmd.append(f"{key}={value}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        console.print(f"[red]Failed to create secret: {result.stderr}[/red]")
        return False

    return True


@main.command()
@click.argument("name")
@click.option("--dry-run", is_flag=True, help="Generate modal_app.py but don't deploy")
def deploy(name: str, dry_run: bool):
    """Deploy workflow to Modal (one-click deployment).

    NAME is the workflow name (e.g., saas-hunter or data-collection/saas-hunter).

    This command:
    1. Generates modal_app.py
    2. Creates Modal secret from .env file
    3. Deploys to Modal

    Prerequisite: Run the workflow locally first to set up credentials.
    """
    workflow_path = find_workflow(name)

    if not workflow_path:
        console.print(
            Panel(
                f"Workflow not found: [bold]{name}[/bold]",
                title="[red]Error[/red]",
                border_style="red",
            )
        )
        raise SystemExit(1)

    workflow_name = workflow_path.name

    console.print()
    console.print(
        Panel(
            f"[bold]{workflow_name}[/bold]\n{workflow_path}",
            title="[blue]Deploying to Modal[/blue]",
            border_style="blue",
        )
    )
    console.print()

    # Check Modal is ready (unless dry-run)
    if not dry_run and not ensure_modal_ready():
        raise SystemExit(1)

    # Load workflow config
    original_cwd = Path.cwd()
    os.chdir(workflow_path)
    try:
        config = load_config(use_cache=False)
    finally:
        os.chdir(original_cwd)

    # Step 1: Generate modal_app.py
    console.print("[blue]Generating modal_app.py...[/blue]")
    output_path = generate_modal_app(workflow_path, config)
    console.print(f"  [green]✓[/green] Generated {output_path.name}")

    if dry_run:
        console.print()
        console.print(
            Panel(
                f"[yellow]Dry run complete[/yellow]\n\n"
                f"Generated: [cyan]{output_path}[/cyan]\n\n"
                f"To deploy, run: [cyan]wat deploy {name}[/cyan]",
                title="[yellow]Dry Run[/yellow]",
                border_style="yellow",
            )
        )
        return

    # Step 2: Create Modal secret from .env
    console.print("[blue]Creating Modal secret from .env...[/blue]")
    if not create_modal_secret(workflow_path):
        raise SystemExit(1)
    console.print(f"  [green]✓[/green] Created secret: {workflow_name}-env")

    # Step 3: Deploy to Modal
    console.print("[blue]Deploying to Modal...[/blue]")
    result = subprocess.run(
        ["modal", "deploy", "modal_app.py"],
        cwd=workflow_path,
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        # Check if scheduled
        cron_expr = schedule_to_cron(config)
        schedule_info = ""
        if cron_expr:
            deployment = config.get("deployment", {})
            schedule = deployment.get("schedule", "")
            schedule_day = deployment.get("schedule_day", "")
            schedule_time = deployment.get("schedule_time", "08:00")
            schedule_info = f"\nSchedule: {schedule}"
            if schedule_day:
                schedule_info += f" ({schedule_day})"
            schedule_info += f" at {schedule_time} UTC"

        console.print()
        console.print(
            Panel(
                f"[green]Deployed successfully![/green]\n\n"
                f"Dashboard: [cyan]https://modal.com/apps/{workflow_name}[/cyan]\n"
                f"Run now: [cyan]modal run modal_app.py::run_workflow[/cyan]"
                f"{schedule_info}",
                title="[green]Success[/green]",
                border_style="green",
            )
        )
    else:
        console.print()
        console.print(
            Panel(
                f"[red]Deployment failed[/red]\n\n{result.stderr}",
                title="[red]Error[/red]",
                border_style="red",
            )
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
