"""Profile management TUI interface for Pineneedle."""

import click
import questionary

from .base import pine_style
from ..profile_service import ProfileService


class ProfileManagerTUI:
    """TUI interface for profile management operations."""
    
    def __init__(self, fs, config):
        self.profile_service = ProfileService(fs, config)
    
    
    def interactive_manager(self) -> None:
        """Interactive profile management interface."""
        while True:
            profiles = self.profile_service.list_profiles()
            current_profile = self.profile_service.get_current_profile()
            
            click.echo("\nProfile Management")
            click.echo(f"Current profile: {current_profile.display_name}")
            
            # Show available profiles
            if profiles:
                click.echo("\nAvailable profiles:")
                for profile in profiles:
                    marker = " (current)" if profile.name == current_profile.name else ""
                    click.echo(f"  • {profile.display_name}{marker}")
            
            action = questionary.select(
                "What would you like to do?",
                choices=[
                    "Switch profile",
                    "New profile",
                    "Delete profile",
                ],
                style=pine_style,
                pointer="🌲"
            ).ask()
            
            if not action:  # User pressed ESC
                break
            
            if action.startswith("Switch"):
                self._switch_profile_ui(profiles, current_profile)
            elif action.startswith("New"):
                self._create_profile_ui()
            elif action.startswith("Delete"):
                self._delete_profile_ui(profiles)
    
    def _switch_profile_ui(self, profiles, current_profile) -> None:
        """UI for profile switching."""
        other_profiles = [p for p in profiles if p.name != current_profile.name]
        if not other_profiles:
            click.echo("No other profiles available.")
            return
            
        choices = [p.display_name for p in other_profiles]
        
        choice = questionary.select(
            "Switch to profile:",
            choices=choices,
            style=pine_style,
            pointer="🌲"
        ).ask()
        
        if choice:
            # Find the profile by display name
            for profile in other_profiles:
                if profile.display_name == choice:
                    if self.profile_service.switch_profile(profile.name):
                        click.echo(f"Switched to profile: {profile.display_name}")
                    else:
                        click.echo("Failed to switch profile")
                    break
    
    def _create_profile_ui(self) -> None:
        """UI for profile creation."""
        name = questionary.text("Profile name (no spaces):").ask()
        if not name or ' ' in name or not name.isalnum():
            click.echo("Profile name must be alphanumeric with no spaces")
            return
        
        display_name = questionary.text("Display name:", default=name.title()).ask()
        description = questionary.text("Description (optional):").ask()
        
        if self.profile_service.create_profile(name, display_name or name.title(), description or ""):
            click.echo(f"Created profile: {display_name or name.title()}")
        else:
            click.echo("Failed to create profile (name may already exist)")
    
    def _delete_profile_ui(self, profiles) -> None:
        """UI for profile deletion."""
        deletable_profiles = [p for p in profiles if p.name != "default"]
        if not deletable_profiles:
            click.echo("No profiles available for deletion (cannot delete default).")
            return
        
        choices = [p.display_name for p in deletable_profiles]
        
        choice = questionary.select(
            "Delete which profile?",
            choices=choices,
            style=pine_style,
            pointer="🌲"
        ).ask()
        
        if choice:
            # Find the profile by display name
            for profile in deletable_profiles:
                if profile.display_name == choice:
                    current_profile = self.profile_service.get_current_profile()
                    is_current = profile.name == current_profile.name
                    
                    confirm_msg = f"Delete profile '{profile.display_name}'? This cannot be undone."
                    if is_current:
                        confirm_msg += "\n(This is your current profile - you'll be switched to 'Default Profile' automatically)"
                    
                    if questionary.confirm(confirm_msg).ask():
                        if self.profile_service.delete_profile(profile.name):
                            if is_current:
                                click.echo(f"Deleted profile: {profile.display_name}")
                                click.echo("Switched to Default Profile")
                            else:
                                click.echo(f"Deleted profile: {profile.display_name}")
                        else:
                            click.echo("Failed to delete profile")
                    break 