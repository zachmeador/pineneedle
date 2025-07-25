"""Filename utilities for safe file naming."""

import re
from datetime import datetime

from .models import JobPosting


def sanitize_for_filename(text: str) -> str:
    """Convert text to filename-safe string."""
    if not text:
        return "unknown"
    # Replace spaces and special chars with underscores, lowercase
    sanitized = re.sub(r'[^\w\s-]', '', text.lower())
    sanitized = re.sub(r'[\s_-]+', '_', sanitized)
    return sanitized.strip('_')


def generate_job_posting_filename(posting: JobPosting) -> str:
    """Generate filename in format: numericid_company_role_location.json"""
    numeric_id = posting.id
    company = sanitize_for_filename(posting.company)
    title = sanitize_for_filename(posting.title)
    location = sanitize_for_filename(posting.location or "remote")
    
    filename = f"{numeric_id}_{company}_{title}_{location}.json"
    return filename


def generate_resume_filename(timestamp: datetime | None = None) -> str:
    """Generate resume filename with timestamp."""
    if timestamp is None:
        timestamp = datetime.now()
    
    timestamp_str = timestamp.strftime("%Y-%m-%d_%H-%M-%S")
    return f"{timestamp_str}_resume.md"


def parse_timestamp_from_resume_filename(filename: str) -> str:
    """Extract timestamp from resume filename."""
    return filename.replace("_resume.md", "") 