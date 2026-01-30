.PHONY: help clean gitlab github all install check

help:
	@echo "Repository Summary Generator - Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  make clean         - Remove all generated output files"
	@echo "  make gitlab        - Clean and generate GitLab summary"
	@echo "  make github        - Clean and generate GitHub summary"
	@echo "  make all           - Clean and generate all platform summaries"
	@echo "  make install       - Install dependencies using uv"
	@echo "  make check         - Check CLI tools and authentication"
	@echo ""
	@echo "Examples:"
	@echo "  make gitlab        - Generate only GitLab reports"
	@echo "  make github        - Generate only GitHub reports"
	@echo "  make all           - Generate reports for all platforms"

clean:
	@echo "Cleaning output directory..."
	@rm -rf outputs/*.md outputs/*.json outputs/*.csv outputs/*.html
	@echo "✓ Output directory cleaned"

gitlab: clean
	@echo "Generating GitLab repository summary..."
	@uv run repo-summary generate --platform gitlab --format markdown --format json

github: clean
	@echo "Generating GitHub repository summary..."
	@uv run repo-summary generate --platform github --format markdown --format json

all: clean
	@echo "Generating repository summaries for all platforms..."
	@uv run repo-summary generate --format markdown --format json

install:
	@echo "Installing dependencies with uv..."
	@uv sync
	@echo "✓ Dependencies installed"

check:
	@echo "Checking CLI tools and authentication..."
	@uv run repo-summary check
