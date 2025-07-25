"""CLI commands for job posting operations."""

import asyncio
from pathlib import Path

import click

from ..agents import parse_job_posting
from ..models import JobPosting


def add_job_posting_from_editor(fs, config, custom_id: str = None) -> tuple[str, JobPosting] | None:
    """
    Open editor for job posting input, parse and save.
    Returns (job_id, posting) on success, None if user cancels/no content.
    """
    click.echo("Opening editor for job posting content...")
    content = click.edit("")  # Clean editor with no example text
    
    if not content or not content.strip():
        return None
    
    content = content.strip()
    
    try:
        click.echo("Parsing job posting...")
        posting = asyncio.run(parse_job_posting(content, config.default_model, custom_id))
        job_id = fs.save_job_posting(posting)
        return job_id, posting
    except Exception as e:
        click.echo(f"Error parsing job posting: {e}")
        return None


def add_job_posting_from_file(fs, config, file_path: str, custom_id: str = None) -> tuple[str, JobPosting] | None:
    """
    Load job posting from file, parse and save.
    Returns (job_id, posting) on success, None on error.
    """
    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        click.echo(f"File not found: {file_path}")
        return None
    
    try:
        content = file_path_obj.read_text().strip()
        if not content:
            click.echo("File is empty")
            return None
        
        click.echo("Parsing job posting...")
        posting = asyncio.run(parse_job_posting(content, config.default_model, custom_id))
        job_id = fs.save_job_posting(posting)
        return job_id, posting
    except Exception as e:
        click.echo(f"Error processing file: {e}")
        return None 