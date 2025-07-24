"""Service layer for file operations and utilities."""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any
import glob

from .models import (
    JobPosting,
    PineneedleConfig,
    ResumeArchive,
    ResumeContent,
    UserBackground,
)


class FileSystemService:
    """Handles all file operations for Pineneedle."""
    
    def __init__(self, workspace_path: Path):
        self.workspace_path = workspace_path
        
        # Use PINENEEDLE_DATA_DIR environment variable if set, otherwise default to workspace/data
        data_dir_env = os.getenv("PINENEEDLE_DATA_DIR")
        if data_dir_env:
            self.data_path = Path(data_dir_env).expanduser().resolve()
        else:
            self.data_path = workspace_path / "data"
            
        self._ensure_workspace_structure()
    
    def _ensure_workspace_structure(self) -> None:
        """Create necessary directories if they don't exist."""
        # Create main data directory
        self.data_path.mkdir(exist_ok=True)
        
        directories = [
            "background",
            "templates", 
            "job_postings",
            "resumes",
        ]
        
        for dir_name in directories:
            (self.data_path / dir_name).mkdir(exist_ok=True)
    
    def load_user_background(self) -> UserBackground:
        """Load user background markdown files."""
        background_path = self.data_path / "background"
        
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
        try:
            return path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return ""
    
    def load_template(self, template_name: str = "default") -> str:
        """Load resume template."""
        template_path = self.data_path / "templates" / f"{template_name}.md"
        
        if not template_path.exists():
            # Create default template if it doesn't exist
            default_template = self._get_default_template()
            template_path.write_text(default_template, encoding="utf-8")
            return default_template
            
        return template_path.read_text(encoding="utf-8")
    
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
        # Generate descriptive filename: numericid_company_role_location
        filename = self._generate_filename(posting)
        posting_path = self.data_path / "job_postings" / filename
        posting_path.write_text(posting.model_dump_json(indent=2), encoding="utf-8")
        
        return posting.id
    
    def _generate_filename(self, posting: JobPosting) -> str:
        """Generate filename in format: numericid_company_role_location.json"""
        def sanitize_for_filename(text: str) -> str:
            """Convert text to filename-safe string."""
            if not text:
                return "unknown"
            # Replace spaces and special chars with underscores, lowercase
            import re
            sanitized = re.sub(r'[^\w\s-]', '', text.lower())
            sanitized = re.sub(r'[\s_-]+', '_', sanitized)
            return sanitized.strip('_')
        
        numeric_id = posting.id
        company = sanitize_for_filename(posting.company)
        title = sanitize_for_filename(posting.title)
        location = sanitize_for_filename(posting.location or "remote")
        
        filename = f"{numeric_id}_{company}_{title}_{location}.json"
        return filename
    
    def load_job_posting(self, job_id: str) -> JobPosting:
        """Load job posting by ID."""
        job_postings_path = self.data_path / "job_postings"
        
        # First try exact filename match (backwards compatibility)
        exact_path = job_postings_path / f"{job_id}.json"
        if exact_path.exists():
            data = json.loads(exact_path.read_text(encoding="utf-8"))
            return JobPosting.model_validate(data)
        
        # Search for files that start with the job_id
        matching_files = list(job_postings_path.glob(f"{job_id}_*.json"))
        if not matching_files:
            raise FileNotFoundError(f"Job posting {job_id} not found")
        
        # Use the first match (should be unique)
        posting_path = matching_files[0]
        data = json.loads(posting_path.read_text(encoding="utf-8"))
        return JobPosting.model_validate(data)
    
    def list_job_postings(self) -> list[JobPosting]:
        """List all job postings, sorted chronologically (newest first)."""
        job_postings_path = self.data_path / "job_postings"
        postings = []
        
        # Get all json files and sort by filename for chronological order
        posting_files = sorted(job_postings_path.glob("*.json"), reverse=True)
        
        for posting_file in posting_files:
            try:
                data = json.loads(posting_file.read_text(encoding="utf-8"))
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
    
    def archive_resume(
        self,
        job_posting: JobPosting,
        resume_content: ResumeContent,
        generation_request: Any,
        model_config: Any,
        iteration_count: int = 1,
    ) -> str:
        """Archive a generated resume with full metadata using timestamped versioning."""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        archive = ResumeArchive(
            job_posting_id=job_posting.id,
            job_posting=job_posting,
            generation_request=generation_request,
            resume_content=resume_content,
            created_at=datetime.now().isoformat(),
            model_used=model_config,
            iteration_count=iteration_count,
        )
        
        # Create resume directory
        resume_dir = self.data_path / "resumes" / job_posting.id
        resume_dir.mkdir(exist_ok=True)
        
        # Save archive metadata with timestamp
        metadata_path = resume_dir / f"{timestamp}_metadata.json"
        metadata_path.write_text(archive.model_dump_json(indent=2), encoding="utf-8")
        
        # Save resume content with timestamp
        content_path = resume_dir / f"{timestamp}_resume.md"
        content_path.write_text(resume_content.resume_markdown, encoding="utf-8")
        
        # Also create/update a "latest" symlink or copy for easy access
        latest_metadata = resume_dir / "latest_metadata.json"
        latest_content = resume_dir / "latest_resume.md"
        
        # Write latest versions (for backwards compatibility)
        latest_metadata.write_text(archive.model_dump_json(indent=2), encoding="utf-8")
        latest_content.write_text(resume_content.resume_markdown, encoding="utf-8")
        
        return str(resume_dir)
    
    def load_config(self) -> PineneedleConfig:
        """Load application configuration."""
        config_path = self.data_path / "config.json"
        return PineneedleConfig.load(config_path)
    
    def save_config(self, config: PineneedleConfig) -> None:
        """Save application configuration."""
        config_path = self.data_path / "config.json"
        config_path.write_text(config.model_dump_json(indent=2), encoding="utf-8")

    def list_resume_versions(self, job_id: str) -> list[tuple[str, Path]]:
        """List all resume versions for a job posting with timestamps."""
        resume_dir = self.data_path / "resumes" / job_id
        if not resume_dir.exists():
            return []
        
        versions = []
        for metadata_file in resume_dir.glob("*_metadata.json"):
            if metadata_file.name.startswith("latest_"):
                continue  # Skip the latest symlinks
            timestamp = metadata_file.name.replace("_metadata.json", "")
            versions.append((timestamp, metadata_file))
        
        # Sort by timestamp (newest first)
        versions.sort(key=lambda x: x[0], reverse=True)
        return versions
    
    def get_latest_resume_path(self, job_id: str) -> Path | None:
        """Get the path to the latest resume file for a job posting."""
        resume_dir = self.data_path / "resumes" / job_id
        latest_resume = resume_dir / "latest_resume.md"
        
        if latest_resume.exists():
            return latest_resume
        
        # Fallback: find the most recent timestamped version
        versions = self.list_resume_versions(job_id)
        if versions:
            timestamp, _ = versions[0]  # Most recent
            return resume_dir / f"{timestamp}_resume.md"
        
        return None
    
    def get_resume_version(self, job_id: str, timestamp: str | None = None) -> Path | None:
        """Get a specific version of a resume, or latest if timestamp is None."""
        if timestamp is None:
            return self.get_latest_resume_path(job_id)
        
        resume_dir = self.data_path / "resumes" / job_id
        version_path = resume_dir / f"{timestamp}_resume.md"
        
        return version_path if version_path.exists() else None


class PDFGenerator:
    """Converts markdown resume to PDF."""
    
    def generate(self, content: str, output_path: Path) -> Path:
        """Generate PDF from markdown content."""
        # For now, just save as markdown - PDF generation can be added later
        # This would use a library like weasyprint or reportlab
        output_path.write_text(content, encoding="utf-8")
        return output_path 