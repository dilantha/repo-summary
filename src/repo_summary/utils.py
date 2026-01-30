"""Common utilities for repository summary generation."""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from rich.console import Console

console = Console()


def run_command(cmd: List[str], capture_output: bool = True) -> Optional[str]:
    """Run a shell command and return its output.

    Args:
        cmd: Command as a list of strings
        capture_output: Whether to capture and return output

    Returns:
        Command output as string, or None if command failed
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            check=True
        )
        return result.stdout.strip() if capture_output else None
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error running command: {' '.join(cmd)}[/red]")
        console.print(f"[red]{e.stderr}[/red]")
        return None
    except FileNotFoundError:
        console.print(f"[red]Command not found: {cmd[0]}[/red]")
        console.print(f"[yellow]Please ensure {cmd[0]} is installed and in your PATH[/yellow]")
        return None


def parse_json_output(output: Optional[str]) -> Optional[Any]:
    """Parse JSON output from a command.

    Args:
        output: JSON string from command

    Returns:
        Parsed JSON data, or None if parsing failed
    """
    if not output:
        return None

    try:
        return json.loads(output)
    except json.JSONDecodeError as e:
        console.print(f"[red]Error parsing JSON: {e}[/red]")
        return None


def load_config(config_path: Path) -> Optional[Dict]:
    """Load configuration from YAML file.

    Args:
        config_path: Path to configuration file

    Returns:
        Configuration dictionary, or None if loading failed
    """
    if not config_path.exists():
        console.print(f"[yellow]Config file not found: {config_path}[/yellow]")
        return None

    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        console.print(f"[red]Error parsing config file: {e}[/red]")
        return None


def format_date(date_str: Optional[str], format: str = "%Y-%m-%d") -> str:
    """Format an ISO date string to a more readable format.

    Args:
        date_str: ISO format date string
        format: Output date format

    Returns:
        Formatted date string, or empty string if parsing failed
    """
    if not date_str:
        return ""

    try:
        # Try parsing ISO format with timezone
        if 'T' in date_str:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        else:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime(format)
    except (ValueError, AttributeError):
        # Return original if parsing fails
        return date_str


def format_size(size_bytes: Optional[int]) -> str:
    """Format size in bytes to human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Human-readable size string
    """
    if size_bytes is None or size_bytes == 0:
        return "0 B"

    units = ['B', 'KB', 'MB', 'GB', 'TB']
    size = float(size_bytes)
    unit_index = 0

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    return f"{size:.1f} {units[unit_index]}"


def check_cli_available(cli_name: str) -> bool:
    """Check if a CLI tool is available.

    Args:
        cli_name: Name of the CLI tool to check

    Returns:
        True if CLI is available, False otherwise
    """
    try:
        subprocess.run(
            [cli_name, "--version"],
            capture_output=True,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def ensure_output_directory(output_dir: Path) -> bool:
    """Ensure output directory exists.

    Args:
        output_dir: Path to output directory

    Returns:
        True if directory exists or was created, False otherwise
    """
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        return True
    except OSError as e:
        console.print(f"[red]Error creating output directory: {e}[/red]")
        return False
