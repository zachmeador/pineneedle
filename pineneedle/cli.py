"""Main CLI interface for pineneedle."""

import click
from pineneedle.commands.init import init


@click.group()
@click.version_option(version="0.1.0")
def main():
    """Pineneedle - Smart LLM-powered resume management."""
    pass


# Register commands
main.add_command(init)


if __name__ == "__main__":
    main() 