"""Command-line interface for repository summary generator."""

from pathlib import Path
from typing import List, Optional

import click

from . import __version__
from .formatters import format_csv, format_html, format_json, format_markdown
from .github import check_github_auth, get_github_repos
from .gitlab import check_gitlab_auth, get_gitlab_groups
from .utils import (
    check_cli_available,
    console,
    ensure_output_directory,
    load_config,
)


@click.group()
@click.version_option(version=__version__)
def main():
    """Repository Summary Generator - Extract and format repository information."""
    pass


@main.command()
@click.option(
    '--platform',
    type=click.Choice(['all', 'gitlab', 'github'], case_sensitive=False),
    default='all',
    help='Platform to fetch repositories from'
)
@click.option(
    '--format',
    'formats',
    multiple=True,
    type=click.Choice(['markdown', 'json', 'csv', 'html'], case_sensitive=False),
    default=['markdown'],
    help='Output format(s) - can specify multiple'
)
@click.option(
    '--output',
    type=click.Path(path_type=Path),
    default=Path('./outputs'),
    help='Output directory for generated reports'
)
@click.option(
    '--config',
    type=click.Path(exists=True, path_type=Path),
    default=Path('./config.yaml'),
    help='Configuration file path'
)
@click.option(
    '--include-languages/--no-languages',
    default=False,
    help='Include detailed language breakdown (slower for GitLab)'
)
@click.option(
    '--gitlab-groups',
    multiple=True,
    help='GitLab groups to fetch (overrides config)'
)
@click.option(
    '--gitlab-mine/--no-gitlab-mine',
    default=False,
    help='Include personal GitLab repositories'
)
@click.option(
    '--github-owners',
    multiple=True,
    help='GitHub owners/orgs to fetch (overrides config)'
)
def generate(
    platform: str,
    formats: tuple,
    output: Path,
    config: Path,
    include_languages: bool,
    gitlab_groups: tuple,
    gitlab_mine: bool,
    github_owners: tuple,
):
    """Generate repository summary reports."""
    console.print(f"[bold]Repository Summary Generator v{__version__}[/bold]\n")

    # Ensure output directory exists
    if not ensure_output_directory(output):
        return

    # Load configuration
    cfg = load_config(config) if config.exists() else {}

    # Get GitLab groups
    gitlab_groups_list = list(gitlab_groups) if gitlab_groups else cfg.get('gitlab', {}).get('groups', [])

    # Check if we should include personal GitLab repos
    gitlab_include_mine = gitlab_mine or cfg.get('gitlab', {}).get('include_mine', False)

    # Get GitHub owners
    github_owners_list = list(github_owners) if github_owners else cfg.get('github', {}).get('owners', [])

    # Validate platform availability and configuration
    should_fetch_gitlab = platform in ['all', 'gitlab'] and (gitlab_groups_list or gitlab_include_mine)
    should_fetch_github = platform in ['all', 'github'] and github_owners_list

    if not should_fetch_gitlab and not should_fetch_github:
        console.print("[red]Error: No platforms configured. Please provide groups/owners via CLI or config file.[/red]")
        return

    # Check CLI tools availability
    if should_fetch_gitlab:
        if not check_cli_available('glab'):
            console.print("[red]Error: glab CLI not found. Please install it: https://gitlab.com/gitlab-org/cli[/red]")
            return
        if not check_gitlab_auth():
            console.print("[red]Error: GitLab authentication required. Run: glab auth login[/red]")
            return

    if should_fetch_github:
        if not check_cli_available('gh'):
            console.print("[red]Error: gh CLI not found. Please install it: https://cli.github.com/[/red]")
            return
        if not check_github_auth():
            console.print("[red]Error: GitHub authentication required. Run: gh auth login[/red]")
            return

    # Fetch repository data
    all_data = {}

    if should_fetch_gitlab:
        console.print("[bold blue]Fetching GitLab repositories...[/bold blue]")
        gitlab_data = get_gitlab_groups(gitlab_groups_list, include_languages, gitlab_include_mine)
        if gitlab_data:
            all_data['gitlab'] = gitlab_data
        console.print()

    if should_fetch_github:
        console.print("[bold blue]Fetching GitHub repositories...[/bold blue]")
        github_limit = cfg.get('github', {}).get('limit', 100)
        github_data = get_github_repos(github_owners_list, limit=github_limit)
        if github_data:
            all_data['github'] = github_data
        console.print()

    if not all_data:
        console.print("[yellow]No repository data collected.[/yellow]")
        return

    # Generate output files
    console.print("[bold blue]Generating reports...[/bold blue]")

    formats_list = list(formats) if formats else ['markdown']

    # Determine platform prefix for output files
    platforms = list(all_data.keys())
    if len(platforms) == 1:
        prefix = platforms[0].capitalize()
    else:
        prefix = "All-Platforms"

    for fmt in formats_list:
        if fmt == 'markdown':
            output_file = output / f'{prefix}-Repository-Summary.md'
            format_markdown(all_data, output_file)
        elif fmt == 'json':
            output_file = output / f'{prefix.lower()}-repository-summary.json'
            format_json(all_data, output_file)
        elif fmt == 'csv':
            output_file = output / f'{prefix.lower()}-repository-summary.csv'
            format_csv(all_data, output_file)
        elif fmt == 'html':
            output_file = output / f'{prefix.lower()}-repository-summary.html'
            format_html(all_data, output_file)

    console.print(f"\n[bold green]✓ Reports generated successfully![/bold green]")


@main.command()
def check():
    """Check CLI tools and authentication status."""
    console.print("[bold]Checking CLI tools and authentication...[/bold]\n")

    # Check glab
    if check_cli_available('glab'):
        console.print("[green]✓[/green] glab CLI is installed")
        if check_gitlab_auth():
            console.print("[green]✓[/green] GitLab authentication is valid")
        else:
            console.print("[yellow]⚠[/yellow] GitLab authentication required. Run: glab auth login")
    else:
        console.print("[red]✗[/red] glab CLI not found. Install from: https://gitlab.com/gitlab-org/cli")

    console.print()

    # Check gh
    if check_cli_available('gh'):
        console.print("[green]✓[/green] gh CLI is installed")
        if check_github_auth():
            console.print("[green]✓[/green] GitHub authentication is valid")
        else:
            console.print("[yellow]⚠[/yellow] GitHub authentication required. Run: gh auth login")
    else:
        console.print("[red]✗[/red] gh CLI not found. Install from: https://cli.github.com/")


@main.command()
@click.argument('config_path', type=click.Path(path_type=Path), default=Path('./config.yaml'))
def init(config_path: Path):
    """Initialize a sample configuration file."""
    if config_path.exists():
        if not click.confirm(f"{config_path} already exists. Overwrite?"):
            return

    sample_config = """# Repository Summary Generator Configuration

gitlab:
  # GitLab groups to fetch
  groups:
    - example-group-1
    - example-group-2
  # Include personal/user repositories
  include_mine: false

github:
  # GitHub owners/organizations to fetch
  owners:
    - your-username
    - your-org-name
  # Maximum repos to fetch per owner (default: 100)
  limit: 100

# Output configuration
output:
  # Output directory for reports
  directory: ./outputs
  # Default output formats
  formats:
    - markdown
    - json

# Options
options:
  # Include detailed language breakdown (slower for GitLab)
  include_languages: false
"""

    try:
        with open(config_path, 'w') as f:
            f.write(sample_config)
        console.print(f"[green]✓[/green] Configuration file created: {config_path}")
        console.print("[yellow]Please edit the file to add your groups and owners.[/yellow]")
    except IOError as e:
        console.print(f"[red]Error creating config file: {e}[/red]")


if __name__ == '__main__':
    main()
