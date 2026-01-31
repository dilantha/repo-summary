"""Output formatters for repository data."""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from jinja2 import Template

from .utils import console


def format_markdown(data: Dict[str, Dict[str, List[Dict]]], output_file: Path) -> bool:
    """Format repository data as Markdown tables.

    Args:
        data: Repository data grouped by platform and organization
        output_file: Path to output file

    Returns:
        True if formatting succeeded, False otherwise
    """
    try:
        with open(output_file, "w") as f:
            # Write header
            f.write("# Repository Summary\n\n")
            f.write(
                f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
            )

            # Write GitLab repos
            if "gitlab" in data:
                f.write("## GitLab Repositories\n\n")
                for group, repos in sorted(data["gitlab"].items()):
                    f.write(f"### {group}\n\n")
                    f.write(f"`glab repo list --group {group}`\n\n")
                    write_markdown_table(f, repos)
                    f.write("\n")

            # Write GitHub repos
            if "github" in data:
                f.write("## GitHub Repositories\n\n")
                for owner, repos in sorted(data["github"].items()):
                    f.write(f"### {owner}\n\n")
                    f.write(f"`gh repo list {owner}`\n\n")
                    write_markdown_table(f, repos)
                    f.write("\n")

        console.print(f"[green]✓[/green] Markdown report saved to {output_file}")

        # Format the markdown file using prettier if available
        format_markdown_file(output_file)

        return True

    except IOError as e:
        console.print(f"[red]Error writing Markdown file: {e}[/red]")
        return False


def format_markdown_file(file_path: Path) -> bool:
    """Format a Markdown file using prettier if available.

    Args:
        file_path: Path to markdown file to format

    Returns:
        True if formatting succeeded, False otherwise
    """
    import subprocess

    try:
        # Check if prettier is available
        result = subprocess.run(
            ["npx", "prettier", "--version"], capture_output=True, text=True, timeout=5
        )

        if result.returncode != 0:
            # Prettier not available, skip formatting
            return False

        # Format the file
        subprocess.run(
            ["npx", "prettier", "--write", str(file_path)],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )

        console.print(f"[green]✓[/green] Formatted markdown file with prettier")
        return True

    except (
        subprocess.TimeoutExpired,
        subprocess.CalledProcessError,
        FileNotFoundError,
    ):
        # Formatting failed, but that's okay - file is still valid
        return False


def write_markdown_table(f, repos: List[Dict]):
    """Write a Markdown table for repositories.

    Args:
        f: File handle
        repos: List of repository dictionaries
    """
    # Write table header
    f.write("| Project | Description | Last Updated | Archived |\n")
    f.write("|---------|-------------|--------------|----------|\n")

    # Write table rows
    for repo in repos:
        name = repo.get("name", "")
        path = repo.get("path", "")
        desc = repo.get("description", "").replace("|", "\\|").replace("\n", " ")[:100]

        updated = repo.get("updated_at", "")
        archived = "✓" if repo.get("archived", False) else ""

        f.write(f"| {path} | {desc} | {updated} | {archived} |\n")


def format_json(data: Dict[str, Dict[str, List[Dict]]], output_file: Path) -> bool:
    """Format repository data as JSON.

    Args:
        data: Repository data grouped by platform and organization
        output_file: Path to output file

    Returns:
        True if formatting succeeded, False otherwise
    """
    try:
        output_data = {"generated_at": datetime.now().isoformat(), "platforms": data}

        with open(output_file, "w") as f:
            json.dump(output_data, f, indent=2)

        console.print(f"[green]✓[/green] JSON report saved to {output_file}")
        return True

    except IOError as e:
        console.print(f"[red]Error writing JSON file: {e}[/red]")
        return False


def format_csv(data: Dict[str, Dict[str, List[Dict]]], output_file: Path) -> bool:
    """Format repository data as CSV.

    Args:
        data: Repository data grouped by platform and organization
        output_file: Path to output file

    Returns:
        True if formatting succeeded, False otherwise
    """
    try:
        with open(output_file, "w", newline="") as f:
            # Define CSV columns
            fieldnames = [
                "platform",
                "organization",
                "name",
                "path",
                "description",
                "url",
                "primary_language",
                "stars",
                "forks",
                "open_issues",
                "size",
                "size_bytes",
                "visibility",
                "archived",
                "created_at",
                "updated_at",
                "default_branch",
                "license",
                "topics",
            ]

            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()

            # Write rows for each platform
            for platform, orgs in data.items():
                for org, repos in orgs.items():
                    for repo in repos:
                        # Get primary language
                        primary_lang = repo.get("primary_language", "")
                        if not primary_lang and repo.get("languages"):
                            languages = repo.get("languages", {})
                            if languages:
                                primary_lang = max(
                                    languages.items(), key=lambda x: x[1]
                                )[0]

                        row = {
                            "platform": platform,
                            "organization": org,
                            "primary_language": primary_lang,
                            "topics": ", ".join(repo.get("topics", [])),
                            **repo,
                        }
                        writer.writerow(row)

        console.print(f"[green]✓[/green] CSV report saved to {output_file}")
        return True

    except IOError as e:
        console.print(f"[red]Error writing CSV file: {e}[/red]")
        return False


def format_html(data: Dict[str, Dict[str, List[Dict]]], output_file: Path) -> bool:
    """Format repository data as HTML with interactive tables.

    Args:
        data: Repository data grouped by platform and organization
        output_file: Path to output file

    Returns:
        True if formatting succeeded, False otherwise
    """
    try:
        template = Template(HTML_TEMPLATE)
        html = template.render(
            data=data, generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        with open(output_file, "w") as f:
            f.write(html)

        console.print(f"[green]✓[/green] HTML report saved to {output_file}")
        return True

    except IOError as e:
        console.print(f"[red]Error writing HTML file: {e}[/red]")
        return False


# HTML template with sortable tables
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Repository Summary</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; padding: 2rem; background: #f5f5f5; }
        .container { max-width: 1400px; margin: 0 auto; background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        h1 { color: #333; margin-bottom: 0.5rem; }
        .meta { color: #666; margin-bottom: 2rem; font-size: 0.9rem; }
        h2 { color: #444; margin: 2rem 0 1rem; padding-bottom: 0.5rem; border-bottom: 2px solid #007bff; }
        h3 { color: #555; margin: 1.5rem 0 0.5rem; }
        .command { background: #f8f9fa; padding: 0.5rem 1rem; border-radius: 4px; font-family: monospace; font-size: 0.9rem; margin-bottom: 1rem; }
        table { width: 100%; border-collapse: collapse; margin-bottom: 2rem; }
        th { background: #007bff; color: white; padding: 0.75rem; text-align: left; font-weight: 600; cursor: pointer; user-select: none; }
        th:hover { background: #0056b3; }
        td { padding: 0.75rem; border-bottom: 1px solid #dee2e6; }
        tr:hover { background: #f8f9fa; }
        .archived { color: #dc3545; }
        .badge { display: inline-block; padding: 0.25rem 0.5rem; border-radius: 3px; font-size: 0.85rem; font-weight: 500; }
        .badge-language { background: #e7f3ff; color: #0066cc; }
        .badge-archived { background: #ffe7e7; color: #cc0000; }
        .badge-private { background: #fff3cd; color: #856404; }
        a { color: #007bff; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Repository Summary</h1>
        <p class="meta">Generated on {{ generated_at }}</p>

        {% if data.gitlab %}
        <h2>GitLab Repositories</h2>
        {% for group, repos in data.gitlab.items()|sort %}
        <h3>{{ group }}</h3>
        <div class="command">glab repo list --group {{ group }}</div>
        <table>
            <thead>
                <tr>
                    <th onclick="sortTable(this, 0)">Project</th>
                    <th onclick="sortTable(this, 1)">Description</th>
                    <th onclick="sortTable(this, 2)">Last Updated</th>
                </tr>
            </thead>
            <tbody>
                {% for repo in repos %}
                <tr>
                    <td><a href="{{ repo.url }}" target="_blank">{{ repo.path }}</a>
                        {% if repo.archived %}<span class="badge badge-archived">Archived</span>{% endif %}
                    </td>
                    <td>{{ repo.description[:100] }}</td>
                    <td>{{ repo.updated_at }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% endfor %}
        {% endif %}

        {% if data.github %}
        <h2>GitHub Repositories</h2>
        {% for owner, repos in data.github.items()|sort %}
        <h3>{{ owner }}</h3>
        <div class="command">gh repo list {{ owner }}</div>
        <table>
            <thead>
                <tr>
                    <th onclick="sortTable(this, 0)">Project</th>
                    <th onclick="sortTable(this, 1)">Description</th>
                    <th onclick="sortTable(this, 2)">Language</th>
                    <th onclick="sortTable(this, 3)">Size</th>
                    <th onclick="sortTable(this, 4)">Last Updated</th>
                </tr>
            </thead>
            <tbody>
                {% for repo in repos %}
                <tr>
                    <td><a href="{{ repo.url }}" target="_blank">{{ repo.path }}</a>
                        {% if repo.archived %}<span class="badge badge-archived">Archived</span>{% endif %}
                        {% if repo.visibility == 'private' %}<span class="badge badge-private">Private</span>{% endif %}
                    </td>
                    <td>{{ repo.description[:100] }}</td>
                    <td>
                        {% if repo.primary_language %}
                        <span class="badge badge-language">{{ repo.primary_language }}</span>
                        {% endif %}
                    </td>
                    <td>{{ repo.size }}</td>
                    <td>{{ repo.updated_at }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% endfor %}
        {% endif %}
    </div>

    <script>
        function sortTable(header, column) {
            const table = header.parentElement.parentElement.parentElement;
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));

            rows.sort((a, b) => {
                const aVal = a.cells[column].textContent.trim();
                const bVal = b.cells[column].textContent.trim();
                return aVal.localeCompare(bVal);
            });

            rows.forEach(row => tbody.appendChild(row));
        }
    </script>
</body>
</html>
"""
