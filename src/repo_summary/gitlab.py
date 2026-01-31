"""GitLab repository data extraction using glab CLI."""

import urllib.parse
from typing import Dict, List, Optional

from rich.progress import Progress, SpinnerColumn, TextColumn

from .utils import console, format_date, format_size, parse_json_output, run_command


def check_gitlab_auth() -> bool:
    """Check if glab is authenticated.

    Returns:
        True if authenticated, False otherwise
    """
    import subprocess

    try:
        result = subprocess.run(
            ["glab", "auth", "status"], capture_output=True, text=True, check=True
        )
        # glab auth status outputs to stderr, not stdout
        output = result.stderr + result.stdout
        return "Logged in" in output
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_gitlab_groups(
    groups: List[str], include_languages: bool = False, include_mine: bool = False
) -> Dict[str, List[Dict]]:
    """Get repositories for all specified GitLab groups and optionally personal repos.

    Args:
        groups: List of GitLab group names
        include_languages: Whether to fetch language breakdown (slower)
        include_mine: Whether to include personal/user repositories

    Returns:
        Dictionary mapping group names to repository data
    """
    if not check_gitlab_auth():
        console.print("[red]GitLab authentication required. Run: glab auth login[/red]")
        return {}

    all_repos = {}

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Fetch personal repos if requested
        if include_mine:
            task = progress.add_task("Fetching personal GitLab repos", total=None)
            repos = get_user_repos(include_languages)
            if repos:
                all_repos["personal"] = repos
                console.print(f"[green]✓[/green] Found {len(repos)} personal repos")
            else:
                console.print(f"[yellow]⚠[/yellow] No personal repos found")
            progress.remove_task(task)

        # Fetch group repos
        for group in groups:
            task = progress.add_task(f"Fetching GitLab group: {group}", total=None)
            repos = get_group_repos(group, include_languages)
            if repos:
                all_repos[group] = repos
                console.print(f"[green]✓[/green] Found {len(repos)} repos in {group}")
            else:
                console.print(f"[yellow]⚠[/yellow] No repos found in {group}")
            progress.remove_task(task)

    return all_repos


def get_user_repos(include_languages: bool = False) -> List[Dict]:
    """Get personal repositories for the authenticated user (under their username).

    Args:
        include_languages: Whether to fetch language breakdown

    Returns:
        List of repository data dictionaries
    """
    # First get the authenticated username
    username = get_authenticated_username()
    if not username:
        return []

    # Fetch all repos with pagination
    all_repos_data = []
    page = 1
    while True:
        output = run_command(
            [
                "glab",
                "repo",
                "list",
                "--mine",
                "--per-page",
                "100",
                "--page",
                str(page),
                "--output",
                "json",
            ]
        )

        if not output:
            break

        repos_data = parse_json_output(output)
        if not repos_data:
            break

        all_repos_data.extend(repos_data)

        # If we got fewer than per-page items, we've reached the end
        if len(repos_data) < 100:
            break

        page += 1

    # Filter to only repos owned by the user (personal repos)
    repos = []
    for repo in all_repos_data:
        repo_namespace = repo.get("namespace", {}).get("path", "")
        repo_kind = repo.get("namespace", {}).get("kind", "")

        # Only include repos where namespace matches username (personal repos)
        if repo_namespace == username and repo_kind == "user":
            repo_info = extract_repo_info(repo)

            # Optionally fetch language data and statistics
            if include_languages:
                languages = get_repo_languages(repo.get("path_with_namespace", ""))
                if languages:
                    repo_info["languages"] = languages
                    repo_info["primary_language"] = get_primary_language(languages)

                # Also fetch statistics when getting languages (both are expensive)
                project_id = repo.get("id")
                if project_id:
                    stats = get_project_statistics(project_id)
                    if stats:
                        repo_info["size"] = format_size(stats.get("repository_size", 0))
                        repo_info["size_bytes"] = stats.get("repository_size", 0)

            repos.append(repo_info)

    return repos


def get_authenticated_username() -> Optional[str]:
    """Get the authenticated username from GitLab.

    Returns:
        Username string or None if fetch failed
    """
    output = run_command(["glab", "api", "user"])

    if not output:
        return None

    user_data = parse_json_output(output)
    if not user_data:
        return None

    return user_data.get("username")


def get_group_repos(group: str, include_languages: bool = False) -> List[Dict]:
    """Get all repositories for a GitLab group.

    Args:
        group: GitLab group name
        include_languages: Whether to fetch language breakdown

    Returns:
        List of repository data dictionaries
    """
    # Fetch repos using glab CLI
    output = run_command(["glab", "repo", "list", "--group", group, "--output", "json"])

    if not output:
        return []

    repos_data = parse_json_output(output)
    if not repos_data:
        return []

    # Process each repository
    repos = []
    for repo in repos_data:
        repo_info = extract_repo_info(repo)

        # Optionally fetch language data and statistics
        if include_languages:
            languages = get_repo_languages(repo.get("path_with_namespace", ""))
            if languages:
                repo_info["languages"] = languages
                repo_info["primary_language"] = get_primary_language(languages)

            # Also fetch statistics when getting languages (both are expensive)
            project_id = repo.get("id")
            if project_id:
                stats = get_project_statistics(project_id)
                if stats:
                    repo_info["size"] = format_size(stats.get("repository_size", 0))
                    repo_info["size_bytes"] = stats.get("repository_size", 0)

        repos.append(repo_info)

    return repos


def extract_repo_info(repo: Dict) -> Dict:
    """Extract and normalize repository information.

    Args:
        repo: Raw repository data from glab

    Returns:
        Normalized repository information
    """
    size_bytes = 0
    if repo.get("statistics"):
        size_bytes = repo.get("statistics", {}).get("repository_size", 0)

    return {
        "name": repo.get("name", ""),
        "path": repo.get("path_with_namespace", ""),
        "description": repo.get("description", ""),
        "url": repo.get("web_url", ""),
        "ssh_url": repo.get("ssh_url_to_repo", ""),
        "http_url": repo.get("http_url_to_repo", ""),
        "visibility": repo.get("visibility", "unknown"),
        "archived": repo.get("archived", False),
        "stars": repo.get("star_count", 0),
        "forks": repo.get("forks_count", 0),
        "created_at": format_date(repo.get("created_at")),
        "updated_at": format_date(repo.get("last_activity_at")),
        "default_branch": repo.get("default_branch", "main"),
        "topics": repo.get("topics", []),
        "namespace": repo.get("namespace", {}).get("name", ""),
        "size": format_size(size_bytes),
        "size_bytes": size_bytes,
    }


def get_repo_languages(repo_path: str) -> Optional[Dict[str, float]]:
    """Get language breakdown for a repository.

    Args:
        repo_path: Repository path (e.g., 'group/project')

    Returns:
        Dictionary mapping language names to percentages, or None if fetch failed
    """
    # URL-encode the project path
    encoded_path = urllib.parse.quote(repo_path, safe="")

    # Use glab API to fetch languages
    output = run_command(["glab", "api", f"projects/{encoded_path}/languages"])

    if not output:
        return None

    languages_data = parse_json_output(output)
    if not languages_data:
        return None

    # Convert byte counts to percentages
    total_bytes = sum(languages_data.values())
    if total_bytes == 0:
        return None

    return {
        lang: round((bytes_count / total_bytes) * 100, 1)
        for lang, bytes_count in languages_data.items()
    }


def get_project_statistics(project_id: int) -> Optional[Dict]:
    """Get repository statistics for a project.

    Args:
        project_id: GitLab project ID

    Returns:
        Dictionary containing repository statistics, or None if fetch failed
    """
    output = run_command(["glab", "api", f"projects/{project_id}?statistics=true"])

    if not output:
        return None

    data = parse_json_output(output)
    if not data:
        return None

    return data.get("statistics")


def get_primary_language(languages: Optional[Dict[str, float]]) -> str:
    """Get the primary language from language breakdown.

    Args:
        languages: Dictionary of languages and their percentages

    Returns:
        Name of primary language, or empty string if none
    """
    if not languages:
        return ""

    return max(languages.items(), key=lambda x: x[1])[0]
