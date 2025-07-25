"""Settings management TUI for Pineneedle."""

from pathlib import Path

import click
import questionary


class SettingsManager:
    """Handles application settings management."""
    
    def __init__(self, fs, config):
        self.fs = fs
        self.config = config
    
    def interactive_manager(self) -> None:
        """Interactive settings management interface."""
        while True:
            click.echo("\n🌲 Settings")
            click.echo(f"Data directory: {self.fs.data_path}")
            click.echo(f"Current profile: {self.config.current_profile}")
            click.echo(f"Default model: {self.config.default_model.provider}:{self.config.default_model.model_name}")
            click.echo(f"Temperature: {self.config.default_model.temperature}")
            
            action = questionary.select(
                "What would you like to change?",
                choices=[
                    "🌲 Default model",
                    "🌿 Model temperature",
                    "🌳 Back to main menu",
                ]
            ).ask()
            
            if not action or action.startswith("🌳"):
                break
            
            if action.startswith("🌲 Default"):
                self._change_default_model()
            elif action.startswith("🌿 Model"):
                self._change_temperature()
    
    def _change_default_model(self) -> None:
        """Handle default model changes."""
        provider = questionary.select(
            "Choose provider:",
            choices=["openai", "anthropic"],
            default=self.config.default_model.provider
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
                default=self.config.default_model.model_name if self.config.default_model.model_name in models else models[0]
            ).ask()
            
            if model_name:
                self.config.default_model.provider = provider
                self.config.default_model.model_name = model_name
                self.fs.save_config(self.config)
                click.echo("🌲 Default model updated")
    
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
            click.echo("🌲 Temperature updated") 