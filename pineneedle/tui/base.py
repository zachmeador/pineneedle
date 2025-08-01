"""Base classes and utilities for TUI components."""

import click
import questionary
from questionary import Style
from typing import List, Optional, Any, Callable


# Custom style with pine tree cursor
pine_style = Style([
    ('pointer', '#00aa00 bold'),  # Green pine tree cursor
    ('highlighted', '#00aa00 bold'),  # Green highlight for selected item
    ('answer', '#00aa00 bold'),  # Green for selected answer
    ('question', 'bold'),
])

# Navigation constants
BACK_SIGNAL = '__PINENEEDLE_BACK__'


def select_with_back(prompt: str, choices: List[str], default: Optional[str] = None, show_back: bool = True) -> Optional[str]:
    """Helper function for questionary select with back navigation."""
    # Add "← Back" option to choices if requested and not at root level
    enhanced_choices = choices.copy() if show_back else choices
    if show_back:
        enhanced_choices.append("← Back")
    
    try:
        choice = questionary.select(
            prompt,
            choices=enhanced_choices,
            style=pine_style,
            pointer="🌲",
            default=default
        ).ask()
        
        # Handle back selection
        if choice == "← Back":
            return BACK_SIGNAL
        
        return choice
        
    except KeyboardInterrupt:
        return BACK_SIGNAL


class ListSelector:
    """Utility class for list selection patterns."""
    
    @staticmethod
    def select_from_list(
        items: List[Any], 
        prompt: str,
        display_func: Callable[[Any], str],
        show_back: bool = True
    ) -> Optional[Any]:
        """Select an item from a list with consistent UI patterns."""
        if not items:
            return None
        
        choices = [display_func(item) for item in items]
        choice = select_with_back(prompt, choices, show_back=show_back)
        
        if not choice or choice == BACK_SIGNAL:
            return BACK_SIGNAL
        
        # Find the selected item
        for item in items:
            if display_func(item) == choice:
                return item
        
        return None


class MenuController:
    """Base class for menu controllers with common navigation patterns."""
    
    def __init__(self, fs, config):
        self.fs = fs
        self.config = config
    
    def wait_for_user(self, message: str = "\nPress Enter to continue...") -> None:
        """Wait for user input before continuing."""
        input(message)
    
    def confirm_action(self, message: str, default: bool = False) -> bool:
        """Ask user to confirm an action."""
        try:
            return questionary.confirm(message, default=default).ask()
        except KeyboardInterrupt:
            return False
    
    def show_error(self, message: str) -> None:
        """Display an error message."""
        click.echo(f"🍂 Error: {message}")
        self.wait_for_user()
    
    def show_success(self, message: str) -> None:
        """Display a success message."""
        click.echo(f"✓ {message}")