"""Service layer for file operations and utilities."""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from .file_operations import FileOperations
from .filename_utils import generate_job_posting_filename, generate_resume_filename, parse_timestamp_from_resume_filename
from .models import (
    JobPosting,
    PineneedleConfig,
    ProfileConfig,
    ProfileInfo,
    ResumeContent,
    UserBackground,
)
from .pdf import PDFGenerator


class FileSystemService:
    """Handles all file operations for Pineneedle."""
    
    def __init__(self, workspace_path: Path, profile_name: str = "default"):
        self.fs = FileOperations(workspace_path, profile_name)
        self.workspace_path = workspace_path
        self.current_profile = profile_name
        self.data_path = self.fs.data_path
        self.profile_path = self.fs.profile_path
        
        self._ensure_workspace_structure()
    
    def _ensure_workspace_structure(self) -> None:
        """Create necessary directories if they don't exist."""
        # Create main data directory
        self.fs.ensure_directory(self.data_path)
        
        # Create profiles directory
        self.fs.ensure_directory(self.data_path / "profiles")
        
        # Create current profile directory
        self.fs.ensure_directory(self.profile_path)
        
        # Create profile-specific directories
        directories = [
            "background",
            "templates", 
            "job_postings",
            "resumes",
        ]
        
        for dir_name in directories:
            self.fs.ensure_directory(self.profile_path / dir_name)
        
        # Ensure profile config exists
        self._ensure_profile_config()
    
    def _ensure_profile_config(self) -> None:
        """Ensure the current profile has a config.json file."""
        config_path = self.profile_path / "config.json"
        if not config_path.exists():
            # Create default profile config
            profile_config = ProfileConfig.create_default(
                display_name=self.current_profile.title() + " Profile",
                description="Profile configuration"
            )
            self.save_profile_config(profile_config)
    
    def load_profile_config(self) -> ProfileConfig:
        """Load the current profile's configuration."""
        config_path = self.fs.get_profile_path("config.json")
        data = self.fs.read_json(config_path)
        if data:
            return ProfileConfig.model_validate(data)
        else:
            # Return default if not found
            return ProfileConfig.create_default(
                display_name=self.current_profile.title() + " Profile"
            )
    
    def save_profile_config(self, config: ProfileConfig) -> None:
        """Save the current profile's configuration."""
        config_path = self.fs.get_profile_path("config.json")
        data = config.model_dump()
        self.fs.write_json(config_path, data)
    
    def switch_profile(self, profile_name: str) -> None:
        """Switch to a different profile."""
        self.current_profile = profile_name
        self.fs.switch_profile(profile_name)
        self.profile_path = self.fs.profile_path
        self._ensure_workspace_structure()
    
    def create_profile(self, name: str, display_name: str, description: str = "") -> ProfileInfo:
        """Create a new profile."""
        profile_info = ProfileInfo(
            name=name,
            display_name=display_name,
            created_at=datetime.now().isoformat(),
            description=description
        )
        
        # Create profile directory
        profile_dir = self.data_path / "profiles" / name
        profile_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        directories = ["background", "templates", "job_postings", "resumes"]
        for dir_name in directories:
            (profile_dir / dir_name).mkdir(exist_ok=True)
        
        # Copy example data to background if it doesn't exist
        background_path = profile_dir / "background"
        example_data_path = self.workspace_path / "example_data"
        
        if example_data_path.exists():
            for file_name in ["contact.md", "education.md", "experience.md", "reference.md"]:
                example_file = example_data_path / file_name
                background_file = background_path / file_name
                
                if example_file.exists() and not background_file.exists():
                    background_file.write_text(example_file.read_text())
        
        # Create profile config
        profile_config = ProfileConfig.create_default(display_name, description)
        config_path = profile_dir / "config.json"
        config_path.write_text(profile_config.model_dump_json(indent=2), encoding="utf-8")
        
        return profile_info
    
    def list_profiles(self) -> list[ProfileInfo]:
        """List all available profiles."""
        config = self.load_config()
        return list(config.profiles.values())
    
    def delete_profile(self, profile_name: str) -> bool:
        """Delete a profile and all its data."""
        if profile_name == "default":
            return False  # Cannot delete default profile
        
        profile_dir = self.data_path / "profiles" / profile_name
        if profile_dir.exists():
            shutil.rmtree(profile_dir)
            return True
        return False
    
    def is_initialized(self) -> bool:
        """Check if the workspace is properly initialized."""
        return (
            self.data_path.exists() and
            (self.data_path / "config.json").exists() and
            self.profile_path.exists() and
            (self.profile_path / "background").exists() and
            (self.profile_path / "config.json").exists()
        )
    
    def get_profile_status(self) -> dict[str, Any]:
        """Get status information about the current profile."""
        if not self.is_initialized():
            return {
                "initialized": False,
                "profile": self.current_profile,
                "job_count": 0,
                "resume_count": 0,
                "has_background": False
            }
        
        job_count = len(self.list_job_postings())
        
        # Count resumes across all jobs
        resume_count = 0
        resumes_path = self.profile_path / "resumes"
        if resumes_path.exists():
            for job_dir in resumes_path.iterdir():
                if job_dir.is_dir():
                    resume_count += len(self.list_resume_versions(job_dir.name))
        
        # Check if user has background information
        background = self.load_user_background()
        has_background = any([
            background.experience_md.strip(),
            background.education_md.strip(),
            background.contact_md.strip(),
            background.reference_md.strip()
        ])
        
        return {
            "initialized": True,
            "profile": self.current_profile,
            "job_count": job_count,
            "resume_count": resume_count,
            "has_background": has_background
        }
    
    def load_user_background(self) -> UserBackground:
        """Load user background markdown files."""
        background_path = self.profile_path / "background"
        
        experience_md = self._read_file_safe(background_path / "experience.md")
        education_md = self._read_file_safe(background_path / "education.md")
        contact_md = self._read_file_safe(background_path / "contact.md")
        reference_md = self._read_file_safe(background_path / "reference.md")
        
        return UserBackground(
            experience_md=experience_md,
            education_md=education_md,
            contact_md=contact_md,
            reference_md=reference_md,
        )
    
    def _read_file_safe(self, path: Path) -> str:
        """Read file content or return empty string if file doesn't exist."""
        return self.fs.read_text_safe(path)
    
    def load_template(self, template_name: str = "default") -> str:
        """Load resume template."""
        template_path = self.fs.get_profile_path("templates", f"{template_name}.md")
        
        content = self.fs.read_text_safe(template_path)
        if not content:
            # Create default template if it doesn't exist
            default_template = self._get_default_template()
            self.fs.write_text(template_path, default_template)
            return default_template
            
        return content
    
    def _get_default_template(self) -> str:
        """Return the default resume template."""
        return """# {name}
{contact_info}

## Summary
{summary}

## Experience
{experience}

## Education
{education}

## Skills
{skills}
"""
    
    def save_job_posting(self, posting: JobPosting) -> str:
        """Save job posting and return its ID."""
        filename = generate_job_posting_filename(posting)
        posting_path = self.fs.get_profile_path("job_postings", filename)
        content = posting.model_dump_json(indent=2)
        self.fs.write_text(posting_path, content)
        
        return posting.id
    
    def load_job_posting(self, job_id: str) -> JobPosting:
        """Load job posting by ID."""
        job_postings_path = self.fs.get_profile_path("job_postings")
        
        # First try exact filename match (backwards compatibility)
        exact_path = job_postings_path / f"{job_id}.json"
        data = self.fs.read_json(exact_path)
        if data:
            return JobPosting.model_validate(data)
        
        # Search for files that start with the job_id
        matching_files = list(job_postings_path.glob(f"{job_id}_*.json"))
        if not matching_files:
            raise FileNotFoundError(f"Job posting {job_id} not found")
        
        # Use the first match (should be unique)
        posting_path = matching_files[0]
        data = self.fs.read_json(posting_path)
        return JobPosting.model_validate(data)
    
    def list_job_postings(self) -> list[JobPosting]:
        """List all job postings, sorted chronologically (newest first)."""
        job_postings_path = self.fs.get_profile_path("job_postings")
        postings = []
        
        # Get all json files and sort by filename for chronological order
        posting_files = sorted(job_postings_path.glob("*.json"), reverse=True)
        
        for posting_file in posting_files:
            try:
                data = self.fs.read_json(posting_file)
                if not data:
                    continue
                posting = JobPosting.model_validate(data)
                
                # Set created_at from filename if missing (backwards compatibility)
                if not hasattr(posting, 'created_at') or not posting.created_at:
                    # Try to extract timestamp from filename (new format: numericid_company_role_location)
                    filename_parts = posting_file.stem.split('_')
                    if len(filename_parts) >= 1 and filename_parts[0].isdigit():
                        try:
                            # New format: YYYYMMDDHHMMSS
                            if len(filename_parts[0]) == 14:
                                timestamp_str = filename_parts[0]
                                parsed_dt = datetime.strptime(timestamp_str, "%Y%m%d%H%M%S")
                                posting.created_at = parsed_dt.isoformat()
                            # Old format: YYYYMMDD_HHMMSS
                            elif len(filename_parts) >= 2 and filename_parts[0].isdigit() and filename_parts[1].isdigit():
                                timestamp_str = f"{filename_parts[0]}_{filename_parts[1]}"
                                parsed_dt = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                                posting.created_at = parsed_dt.isoformat()
                            else:
                                posting.created_at = datetime.fromtimestamp(posting_file.stat().st_mtime).isoformat()
                        except ValueError:
                            posting.created_at = datetime.fromtimestamp(posting_file.stat().st_mtime).isoformat()
                    else:
                        # Fallback to file modification time
                        posting.created_at = datetime.fromtimestamp(posting_file.stat().st_mtime).isoformat()
                
                postings.append(posting)
            except Exception:
                continue  # Skip corrupted files
                
        return postings
    
    def save_resume(
        self,
        job_posting_id: str,
        resume_content: ResumeContent,
    ) -> Path:
        """Save a generated resume with timestamp."""
        # Create resume directory
        resume_dir = self.fs.get_profile_path("resumes", job_posting_id)
        self.fs.ensure_directory(resume_dir)
        
        # Save resume content with timestamp
        filename = generate_resume_filename()
        content_path = resume_dir / filename
        self.fs.write_text(content_path, resume_content.resume_markdown)
        
        return content_path
    
    def load_config(self) -> PineneedleConfig:
        """Load application configuration."""
        config_path = self.fs.get_data_path("config.json")
        return PineneedleConfig.load(config_path)
    
    def save_config(self, config: PineneedleConfig) -> None:
        """Save application configuration."""
        config_path = self.fs.get_data_path("config.json")
        content = config.model_dump_json(indent=2)
        self.fs.write_text(config_path, content)

    def list_resume_versions(self, job_id: str) -> list[tuple[str, Path]]:
        """List all resume versions for a job posting with timestamps."""
        resume_dir = self.fs.get_profile_path("resumes", job_id)
        
        versions = []
        for resume_file in resume_dir.glob("*_resume.md"):
            timestamp = parse_timestamp_from_resume_filename(resume_file.name)
            versions.append((timestamp, resume_file))
        
        # Sort by timestamp (newest first)
        versions.sort(key=lambda x: x[0], reverse=True)
        return versions
    
    def get_latest_resume_path(self, job_id: str) -> Path | None:
        """Get the path to the latest resume file for a job posting."""
        versions = self.list_resume_versions(job_id)
        if versions:
            timestamp, resume_path = versions[0]  # Most recent
            return resume_path
        
        return None
    
    def get_resume_version(self, job_id: str, timestamp: str | None = None) -> Path | None:
        """Get a specific version of a resume, or latest if timestamp is None."""
        if timestamp is None:
            return self.get_latest_resume_path(job_id)
        
        resume_dir = self.fs.get_profile_path("resumes", job_id)
        filename = generate_resume_filename(datetime.strptime(timestamp, "%Y-%m-%d_%H-%M-%S"))
        version_path = resume_dir / filename
        
        return version_path if version_path.exists() else None
    
    def initialize_workspace(self, workspace_path: Path, config: Any, output_callback=None) -> None:
        """Initialize the pineneedle workspace with example data and configuration.
        
        Args:
            workspace_path: Path to the workspace directory
            config: Application configuration object
            output_callback: Optional function to call for output messages (defaults to print)
        """
        if output_callback is None:
            output_callback = print
        
        # Directory structure is already created by constructor
        output_callback("✓ Created directory structure")
        
        # Copy example data to background if it doesn't exist
        background_path = self.profile_path / "background"
        example_data_path = workspace_path / "example_data"
        
        if example_data_path.exists():
            for file_name in ["contact.md", "education.md", "experience.md", "reference.md"]:
                example_file = example_data_path / file_name
                background_file = background_path / file_name
                
                if example_file.exists() and not background_file.exists():
                    background_file.write_text(example_file.read_text())
                    output_callback(f"✓ Copied {file_name} to background/")
        
        # Create default template
        template_content = self.load_template("default")
        output_callback("✓ Created default resume template")
        
        # Save default config
        self.save_config(config)
        output_callback("✓ Created configuration file")




