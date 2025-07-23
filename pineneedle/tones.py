"""Tone configuration management."""

import tomllib
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ToneConfiguration:
    """Represents a tone configuration loaded from a TOML file."""
    name: str
    description: str
    model_provider: str
    model_name: str
    file_path: str
    
    @classmethod
    def from_toml_file(cls, file_path: Path) -> 'ToneConfiguration':
        """Load a tone configuration from a TOML file."""
        with open(file_path, 'rb') as f:
            data = tomllib.load(f)
        
        return cls(
            name=data['name'],
            description=data['description'],
            model_provider=data['model_provider'],
            model_name=data['model_name'],
            file_path=str(file_path)
        )


class ToneLibrary:
    """Manages a collection of tone configurations."""
    
    def __init__(self, tones_dir: Path):
        self.tones_dir = tones_dir
        self._tones: List[ToneConfiguration] = []
        self.load_tones()
    
    def load_tones(self) -> List[ToneConfiguration]:
        """Load all tone configurations from the tones directory."""
        self._tones = []
        
        if not self.tones_dir.exists():
            return self._tones
        
        for toml_file in self.tones_dir.glob('*.toml'):
            try:
                tone = ToneConfiguration.from_toml_file(toml_file)
                self._tones.append(tone)
            except Exception as e:
                print(f"Warning: Could not load tone from {toml_file}: {e}")
        
        return self._tones
    
    def list_tones(self) -> List[ToneConfiguration]:
        """Get all available tone configurations."""
        return self._tones.copy()
    
    def get_tone(self, name: str) -> Optional[ToneConfiguration]:
        """Get a specific tone by name."""
        for tone in self._tones:
            if tone.name == name:
                return tone
        return None
    
    def get_tone_names(self) -> List[str]:
        """Get list of all tone names."""
        return [tone.name for tone in self._tones] 