"""GitHub repository data extraction using gh CLI."""

from typing import Dict, List, Optional

from rich.progress import Progress, SpinnerColumn, TextColumn

from .utils import console, format_date, format_size, parse_json_output, run_command


def check_github_auth() -> bool:
    """Check if gh is authenticated.

    Returns:
        True if authenticated, False otherwise
    """
    import subprocess
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            check=True
        )
        # gh auth status outputs to stderr, not stdout
        output = result.stderr + result.stdout
        return "Logged in" in output
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_github_repos(owners: List[str], limit: int = 100) -> Dict[str, List[Dict]]:
    """Get repositories for all specified GitHub owners/organizations.

    Args:
        owners: List of GitHub usernames or organization names
        limit: Maximum number of repos to fetch per owner

    Returns:
        Dictionary mapping owner names to repository data
    """
    if not check_github_auth():
        console.print("[red]GitHub authentication required. Run: gh auth login[/red]")
        return {}

    all_repos = {}

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        for owner in owners:
            task = progress.add_task(f"Fetching GitHub repos: {owner}", total=None)
            repos = get_owner_repos(owner, limit)
            if repos:
                all_repos[owner] = repos
                console.print(f"[green]✓[/green] Found {len(repos)} repos for {owner}")
            else:
                console.print(f"[yellow]⚠[/yellow] No repos found for {owner}")
            progress.remove_task(task)

    return all_repos


def get_owner_repos(owner: str, limit: int = 100) -> List[Dict]:
    """Get all repositories for a GitHub owner.

    Args:
        owner: GitHub username or organization name
        limit: Maximum number of repos to fetch

    Returns:
        List of repository data dictionaries
    """
    # Define fields to fetch from GitHub API
    fields = [
        "name",
        "description",
        "owner",
        "url",
        "sshUrl",
        "createdAt",
        "updatedAt",
        "pushedAt",
        "stargazerCount",
        "forkCount",
        "issues",
        "primaryLanguage",
        "languages",
        "isPrivate",
        "isArchived",
        "isFork",
        "isTemplate",
        "visibility",
        "defaultBranchRef",
        "diskUsage",
        "licenseInfo",
        "repositoryTopics",
        "hasIssuesEnabled",
        "hasWikiEnabled",
    ]

    # Fetch repos using gh CLI
    output = run_command([
        "gh", "repo", "list", owner,
        "--json", ",".join(fields),
        "--limit", str(limit)
    ])

    if not output:
        return []

    repos_data = parse_json_output(output)
    if not repos_data:
        return []

    # Process each repository
    return [extract_repo_info(repo) for repo in repos_data]


def extract_repo_info(repo: Dict) -> Dict:
    """Extract and normalize repository information.

    Args:
        repo: Raw repository data from gh

    Returns:
        Normalized repository information
    """
    # Extract primary language
    primary_lang = repo.get('primaryLanguage', {})
    primary_language = primary_lang.get('name', '') if primary_lang else ''

    # Extract languages
    languages_data = repo.get('languages', {})
    languages = {}
    if languages_data and 'nodes' in languages_data:
        total_size = sum(lang.get('size', 0) for lang in languages_data['nodes'])
        if total_size > 0:
            languages = {
                lang['name']: round((lang.get('size', 0) / total_size) * 100, 1)
                for lang in languages_data['nodes']
            }

    # Extract license
    license_info = repo.get('licenseInfo', {})
    license_name = license_info.get('name', '') if license_info else ''

    # Extract topics
    topics_data = repo.get('repositoryTopics', {})
    topics = []
    if topics_data and 'nodes' in topics_data:
        topics = [topic['topic']['name'] for topic in topics_data['nodes']]

    # Extract owner info
    owner_info = repo.get('owner', {})
    owner = owner_info.get('login', '') if owner_info else ''

    # Extract issues count
    issues_data = repo.get('issues', {})
    open_issues = issues_data.get('totalCount', 0) if issues_data else 0

    # Extract default branch
    default_branch_ref = repo.get('defaultBranchRef', {})
    default_branch = default_branch_ref.get('name', 'main') if default_branch_ref else 'main'

    return {
        'name': repo.get('name', ''),
        'path': f"{owner}/{repo.get('name', '')}",
        'description': repo.get('description', ''),
        'url': repo.get('url', ''),
        'ssh_url': repo.get('sshUrl', ''),
        'http_url': repo.get('url', '').replace('https://github.com/', 'https://github.com/') + '.git' if repo.get('url') else '',
        'visibility': 'private' if repo.get('isPrivate', False) else 'public',
        'archived': repo.get('isArchived', False),
        'is_fork': repo.get('isFork', False),
        'is_template': repo.get('isTemplate', False),
        'stars': repo.get('stargazerCount', 0),
        'forks': repo.get('forkCount', 0),
        'open_issues': open_issues,
        'created_at': format_date(repo.get('createdAt')),
        'updated_at': format_date(repo.get('updatedAt')),
        'pushed_at': format_date(repo.get('pushedAt')),
        'default_branch': default_branch,
        'primary_language': primary_language,
        'languages': languages,
        'size': format_size(repo.get('diskUsage', 0) * 1024) if repo.get('diskUsage') else '0 B',  # diskUsage is in KB
        'size_bytes': repo.get('diskUsage', 0) * 1024,
        'license': license_name,
        'topics': topics,
        'has_issues': repo.get('hasIssuesEnabled', False),
        'has_wiki': repo.get('hasWikiEnabled', False),
        'namespace': owner,
    }


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
