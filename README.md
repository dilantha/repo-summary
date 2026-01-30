# Repository Summary Generator

A Python-based tool to extract and summarize repository information from GitLab, GitHub, and other Git hosting services. Generate comprehensive reports in multiple formats (Markdown, JSON, CSV, HTML) for easy tracking and documentation.

## Features

- **Multi-Platform Support**: Extract data from GitLab and GitHub using their official CLIs
- **Rich Metadata**: Capture language stats, activity metrics, size, health indicators, and collaboration data
- **Multiple Output Formats**:
  - Markdown tables (Obsidian-friendly)
  - JSON (structured data for processing)
  - CSV (spreadsheet import)
  - HTML (interactive with sortable tables)
- **CLI Authentication**: Leverages existing `glab` and `gh` CLI authentication
- **Cron-Friendly**: Perfect for automated scheduled reports
- **Extensible**: Easy to add support for additional platforms

## Prerequisites

Before using this tool, you need to install and authenticate with the platform CLIs:

### GitLab CLI (glab)

```bash
# Install glab
# macOS
brew install glab

# Linux
# See: https://gitlab.com/gitlab-org/cli/-/releases

# Authenticate
glab auth login
```

### GitHub CLI (gh)

```bash
# Install gh
# macOS
brew install gh

# Linux/Windows
# See: https://cli.github.com/

# Authenticate
gh auth login
```

## Installation

This project uses `uv` for Python package management. If you don't have it installed:

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then install the project:

```bash
# Clone or navigate to the repo-summary directory
cd repo-summary

# Install dependencies (uv handles this automatically)
uv sync
```

## Configuration

Create a configuration file to specify which groups/organizations to track:

```bash
# Create config from example
cp config.example.yaml config.yaml

# Edit the config file
nano config.yaml
```

Example configuration:

```yaml
gitlab:
  groups:
    - example-group-1
    - example-group-2
    - my-organization
  # Include personal/user repositories
  include_mine: false

github:
  owners:
    - your-username
    - your-org
  limit: 100

output:
  directory: ./outputs
  formats:
    - markdown
    - json

options:
  include_languages: false
```

## Usage

### Quick Start with Makefile

The easiest way to generate reports is using the included Makefile:

```bash
# Generate GitLab summary (cleans old files first)
make gitlab

# Generate GitHub summary (cleans old files first)
make github

# Generate all platform summaries (cleans old files first)
make all

# Clean output directory
make clean

# Check authentication and CLI tools
make check

# Install dependencies
make install
```

### Check CLI Tools and Authentication

Verify that all required tools are installed and authenticated:

```bash
uv run repo-summary check
# or
make check
```

### Generate Reports

Generate reports with default settings (from config.yaml):

```bash
uv run repo-summary generate
```

### Generate with Custom Options

Generate for specific platform:

```bash
# GitLab only
uv run repo-summary generate --platform gitlab

# GitHub only
uv run repo-summary generate --platform github
```

Specify output formats:

```bash
# Single format
uv run repo-summary generate --format markdown

# Multiple formats
uv run repo-summary generate --format markdown --format json --format html
```

Custom output directory:

```bash
# Generate to specific directory (e.g., Obsidian vault)
uv run repo-summary generate --output ~/Documents/Obsidian/Reports/
```

Override configuration with CLI arguments:

```bash
# Specify groups/owners directly
uv run repo-summary generate \
  --gitlab-groups example-group-1 \
  --gitlab-groups example-group-2 \
  --github-owners your-username

# Include personal GitLab repositories
uv run repo-summary generate --gitlab-mine

# Include language breakdown (slower)
uv run repo-summary generate --include-languages
```

### Initialize Configuration

Generate a sample configuration file:

```bash
uv run repo-summary init
# or
uv run repo-summary init custom-config.yaml
```

## Output Examples

### Markdown Format

```markdown
## GitLab Repositories

### my-organization

| Project | Description | Language | Size | Last Updated | Archived |
|---------|-------------|----------|------|--------------|----------|
| my-organization/awesome-project | Awesome project | Python | 1.2 MB | 2025-11-10 | |
| my-organization/documentation | Documentation | Markdown | 500.0 KB | 2025-10-27 | |
```

### JSON Format

```json
{
  "generated_at": "2025-01-30T10:00:00",
  "platforms": {
    "gitlab": {
      "my-organization": [
        {
          "name": "awesome-project",
          "description": "Awesome project",
          "stars": 5,
          "primary_language": "Python",
          ...
        }
      ]
    }
  }
}
```

### HTML Format

Interactive HTML page with:
- Sortable tables (click column headers)
- Clickable repository links
- Visual badges for status (archived, private)
- Clean, modern design

## Automation with Cron

Set up automated daily reports:

```bash
# Edit crontab
crontab -e

# Add entry for daily updates at 2 AM
0 2 * * * cd /path/to/repo-summary && uv run repo-summary generate --output ~/Documents/Obsidian/Reports/
```

Or use a weekly schedule:

```bash
# Every Sunday at 3 AM
0 3 * * 0 cd /path/to/repo-summary && uv run repo-summary generate --output ~/Documents/Obsidian/Reports/
```

## Metadata Collected

The tool extracts comprehensive metadata for each repository:

### Basic Information
- Name and path
- Description
- URL (web, SSH, HTTP)
- Visibility (public/private)
- Archived status

### Activity Metrics
- Stars count
- Forks count
- Open issues (GitHub)
- Created date
- Last updated date
- Last pushed date (GitHub)

### Technical Details
- Primary programming language
- Language breakdown (%) with `--include-languages`
- Repository size
- Default branch
- License information (GitHub)
- Topics/tags

### Additional
- Fork/template status (GitHub)
- Wiki/Issues enabled status (GitHub)

## Extending the Tool

### Adding More Platforms

To add support for additional platforms (Gitea, Bitbucket, etc.):

1. Create a new extractor module (e.g., `src/repo_summary/gitea.py`)
2. Implement data extraction functions following the pattern in `gitlab.py` or `github.py`
3. Update `cli.py` to include the new platform
4. Add configuration options to `config.example.yaml`

### Custom Formatters

Add custom output formats by:

1. Creating a new formatter function in `formatters.py`
2. Adding the format option to `cli.py`

## Troubleshooting

### "Command not found: glab/gh"

Ensure the CLI tools are installed and in your PATH. Run the installation commands above.

### "Authentication required"

Run `glab auth login` or `gh auth login` to authenticate with the respective platform.

### "No repository data collected"

- Check your configuration file has valid groups/owners
- Verify authentication with `uv run repo-summary check`
- Ensure you have access to the specified groups/organizations

### Empty output files

- Verify the groups/owners exist and you have access
- Check CLI tool output with manual commands:
  ```bash
  glab repo list --group <group-name>
  gh repo list <owner>
  ```

## Development

This project uses:
- **uv**: Fast Python package installer and resolver
- **Click**: Command-line interface creation
- **Rich**: Terminal formatting and progress indicators
- **Jinja2**: HTML template rendering
- **PyYAML**: Configuration file parsing

## License

This project is open source and available under the MIT License.

## Contributing

Contributions welcome! Areas for improvement:
- Support for additional platforms (Gitea, Bitbucket, etc.)
- More output formats (XML, YAML, etc.)
- Advanced filtering options
- Contributor statistics
- CI/CD pipeline status integration
- Dependency analysis

## Author

Created for managing multiple repositories across GitLab and GitHub hosting platforms.
