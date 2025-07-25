"""Basic file operations helper."""

import json
import os
from pathlib import Path
from typing import Any


class FileOperations:
    """Handles basic file system operations."""
    
    def __init__(self, workspace_path: Path, profile_name: str = "default"):
        self.workspace_path = workspace_path
        self.current_profile = profile_name
        
        # Use PINENEEDLE_DATA_DIR environment variable if set, otherwise default to workspace/data
        data_dir_env = os.getenv("PINENEEDLE_DATA_DIR")
        if data_dir_env:
            self.data_path = Path(data_dir_env).expanduser().resolve()
        else:
            self.data_path = workspace_path / "data"
            
        # Profile-specific data path
        self.profile_path = self.data_path / "profiles" / self.current_profile
    
    def ensure_directory(self, path: Path) -> None:
        """Create directory if it doesn't exist."""
        path.mkdir(parents=True, exist_ok=True)
    
    def read_text_safe(self, path: Path, encoding: str = "utf-8") -> str:
        """Read text file content or return empty string if file doesn't exist."""
        try:
            return path.read_text(encoding=encoding)
        except FileNotFoundError:
            return ""
    
    def write_text(self, path: Path, content: str, encoding: str = "utf-8") -> None:
        """Write text content to file, creating directories if needed."""
        self.ensure_directory(path.parent)
        path.write_text(content, encoding=encoding)
    
    def read_json(self, path: Path) -> dict[str, Any]:
        """Read JSON file content."""
        content = self.read_text_safe(path)
        if not content:
            return {}
        return json.loads(content)
    
    def write_json(self, path: Path, data: dict[str, Any], indent: int = 2) -> None:
        """Write data to JSON file."""
        content = json.dumps(data, indent=indent)
        self.write_text(path, content)
    
    def get_profile_path(self, *parts: str) -> Path:
        """Get path relative to current profile directory."""
        return self.profile_path.joinpath(*parts)
    
    def get_data_path(self, *parts: str) -> Path:
        """Get path relative to data directory."""
        return self.data_path.joinpath(*parts)
    
    def switch_profile(self, profile_name: str) -> None:
        """Switch to a different profile."""
        self.current_profile = profile_name
        self.profile_path = self.data_path / "profiles" / profile_name 