"""Settings management TUI for Pineneedle."""

import click
import questionary
from questionary import Style


# Custom style with pine tree cursor
pine_style = Style([
    ('pointer', '#00aa00 bold'),  # Green pine tree cursor
    ('highlighted', '#00aa00 bold'),  # Green highlight for selected item
    ('answer', '#00aa00 bold'),  # Green for selected answer
    ('question', 'bold'),
])


class SettingsManager:
    """Handles application settings management."""
    
    def __init__(self, fs, config):
        self.fs = fs
        self.config = config
    
    
    def interactive_manager(self) -> None:
        """Interactive settings management interface."""
        while True:
            click.echo("\nSettings")
            click.echo(f"Current profile: {self.config.current_profile}")
            click.echo(f"Default model: {self.config.default_model.provider}:{self.config.default_model.model_name}")
            click.echo(f"Temperature: {self.config.default_model.temperature}")
            
            action = questionary.select(
                "What would you like to change?",
                choices=[
                    "Default model",
                    "Model temperature",
                ],
                style=pine_style,
                pointer="🌲"
            ).ask()
            
            if not action:  # User pressed ESC
                break
            
            if action.startswith("Default"):
                self._change_default_model()
            elif action.startswith("Model"):
                self._change_temperature()
    
    def _change_default_model(self) -> None:
        """Handle default model changes."""
        provider = questionary.select(
            "Choose provider:",
            choices=["openai", "anthropic"],
            default=self.config.default_model.provider,
            style=pine_style,
            pointer="🌲"
        ).ask()
        
        if provider:
            if provider == "openai":
                models = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]
            elif provider == "anthropic":
                models = ["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"]
            else:
                models = [self.config.default_model.model_name]
            
            model_name = questionary.select(
                "Choose model:",
                choices=models,
                default=self.config.default_model.model_name if self.config.default_model.model_name in models else models[0],
                style=pine_style,
                pointer="🌲"
            ).ask()
            
            if model_name:
                self.config.default_model.provider = provider
                self.config.default_model.model_name = model_name
                self.fs.save_config(self.config)
                click.echo("Default model updated")
    
    def _change_temperature(self) -> None:
        """Handle temperature changes."""
        temp = questionary.text(
            "Temperature (0.0-2.0):",
            default=str(self.config.default_model.temperature),
            validate=lambda x: x.replace('.', '').isdigit() and 0.0 <= float(x) <= 2.0
        ).ask()
        
        if temp:
            self.config.default_model.temperature = float(temp)
            self.fs.save_config(self.config)
            click.echo("Temperature updated") 