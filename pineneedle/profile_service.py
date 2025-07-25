"""App-wide profile management service."""

from datetime import datetime
from typing import List

from .models import ProfileInfo


class ProfileService:
    """Handles profile operations for the entire application."""
    
    def __init__(self, fs, config):
        self.fs = fs
        self.config = config
    
    def list_profiles(self) -> List[ProfileInfo]:
        """List all available profiles."""
        return list(self.config.profiles.values())
    
    def get_current_profile(self) -> ProfileInfo:
        """Get the current active profile."""
        return self.config.profiles[self.config.current_profile]
    
    def switch_profile(self, profile_name: str) -> bool:
        """Switch to a different profile."""
        if profile_name not in self.config.profiles:
            return False
        
        self.config.current_profile = profile_name
        self.fs.save_config(self.config)
        self.fs.switch_profile(profile_name)
        return True
    
    def create_profile(self, name: str, display_name: str, description: str = "") -> bool:
        """Create a new profile."""
        if name in self.config.profiles:
            return False
        
        try:
            profile_info = self.fs.create_profile(name, display_name, description)
            self.config.profiles[name] = profile_info
            self.fs.save_config(self.config)
            return True
        except Exception:
            return False
    
    def delete_profile(self, profile_name: str) -> bool:
        """Delete a profile and all its data."""
        if profile_name == "default" or profile_name not in self.config.profiles:
            return False
        
        # If deleting the current profile, switch to default first
        if profile_name == self.config.current_profile:
            if not self.switch_profile("default"):
                return False  # Failed to switch to default
        
        if self.fs.delete_profile(profile_name):
            del self.config.profiles[profile_name]
            self.fs.save_config(self.config)
            return True
        return False
    
    def get_profile_status(self) -> dict:
        """Get status information about the current profile."""
        return self.fs.get_profile_status() 