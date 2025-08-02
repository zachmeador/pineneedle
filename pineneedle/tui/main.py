"""Main TUI interface for Pineneedle."""

import sys
import click

from .base import select_with_back, BACK_SIGNAL
from .managers import JobManager, ResumeManager, ExportManager


def start_tui(fs, config):
    """Start the interactive TUI."""
    controller = TUIController(fs, config)
    controller.main_menu()


class TUIController:
    """Handles TUI workflows."""
    
    def __init__(self, fs, config):
        self.fs = fs
        self.config = config
        
        # Initialize managers
        self.job_manager = JobManager(fs, config)
        self.resume_manager = ResumeManager(fs, config)
        self.export_manager = ExportManager(fs, config)
    
    
    def main_menu(self) -> None:
        """Main interactive interface."""
        # Get status (initialization is now automatic)
        status = self.fs.get_profile_status()
        
        # Show welcome with context
        click.echo("▗▄▄▖▗▄▄▄▖▗▖  ▗▖▗▄▄▄▖▗▖  ▗▖▗▄▄▄▖▗▄▄▄▖▗▄▄▄ ▗▖   ▗▄▄▄▖")
        click.echo("▐▌ ▐▌ █  ▐▛▚▖▐▌▐▌   ▐▛▚▖▐▌▐▌   ▐▌   ▐▌  █▐▌   ▐▌   ")
        click.echo("▐▛▀▘  █  ▐▌ ▝▜▌▐▛▀▀▘▐▌ ▝▜▌▐▛▀▀▘▐▛▀▀▘▐▌  █▐▌   ▐▛▀▀▘")
        click.echo("▐▌  ▗▄█▄▖▐▌  ▐▌▐▙▄▄▖▐▌  ▐▌▐▙▄▄▖▐▙▄▄▖▐▙▄▄▀▐▙▄▄▖▐▙▄▄▖")
        click.echo()
        click.echo(f"Profile: {status['profile']}")
        
        if status['job_count'] > 0 or status['resume_count'] > 0:
            click.echo(f"\nCurrent status:")
            if status['job_count'] > 0:
                postings = self.fs.list_job_postings()
                latest = postings[0]
                click.echo(f"• {status['job_count']} job posting(s) (newest: \"{latest.title}\" at {latest.company})")
            if status['resume_count'] > 0:
                click.echo(f"• {status['resume_count']} resume(s) generated")
            if not status['has_background']:
                click.echo("No background information found - add your details in the background files")
            click.echo()
        
        # Build menu options
        choices = []
        choices.extend([
            "Add new job posting",
            "Manage job postings",
            "Delete a resume",
            "Export resume to PDF",
            "Manage profiles",
            "Settings",
            "Help",
        ])
        
        # Show menu (no back option at root level)
        choice = select_with_back("What would you like to do?", choices, show_back=False)
        
        if not choice or choice == BACK_SIGNAL:  # User pressed ESC or back - quit at root level
            click.echo("\nGoodbye!")
            sys.exit(0)
        
        # Handle choices
        if choice.startswith("Add new"):
            self.job_manager.add_job_interactive()
            self.main_menu()
        elif choice.startswith("Manage job"):
            self.job_manager.manage_jobs_interactive()
            self.main_menu()
        elif choice.startswith("Delete a resume"):
            self.resume_manager.delete_resume_interactive()
            self.main_menu()
        elif choice.startswith("Export resume"):
            self.export_manager.export_interactive()
            self.main_menu()
        elif choice.startswith("Manage profiles"):
            from .profile import ProfileManagerTUI
            ProfileManagerTUI(self.fs, self.config).interactive_manager()
            self.main_menu()
        elif choice.startswith("Settings"):
            from .settings import SettingsManager
            SettingsManager(self.fs, self.config).interactive_manager()
            self.main_menu()
        elif choice.startswith("Help"):
            click.echo("\nPineneedle Help")
            click.echo("=" * 50)
            click.echo("Use 'pineneedle --help' for command-line usage")
            click.echo("This interactive mode guides you through common tasks")
            input("\nPress Enter to continue...")
            self.main_menu()
    
