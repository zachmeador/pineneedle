"""Main CLI commands for Pineneedle."""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

import click
from dotenv import load_dotenv

from ..agents import parse_job_posting, generate_resume
from ..models import ModelConfig, ResumeDeps
from ..services import FileSystemService, PDFMetadataService
from ..pdf import PDFGenerator
from ..filename_utils import generate_pdf_filename_from_resume
from .job_commands import add_job_posting_from_editor, add_job_posting_from_file

# Load environment variables
load_dotenv()


@click.group(invoke_without_command=True)
@click.option('--workspace', default='.', help='Workspace directory path')
@click.option('--profile', help='Profile to use')
@click.pass_context
def cli(ctx: click.Context, workspace: str, profile: str | None) -> None:
    """Pineneedle - Intelligent Resume Generation with LLMs."""
    ctx.ensure_object(dict)
    workspace_path = Path(workspace).resolve()
    ctx.obj['workspace'] = workspace_path
    
    # Load config to get current profile
    temp_fs = FileSystemService(workspace_path)
    config = temp_fs.load_config()
    
    # Use provided profile or config default
    current_profile = profile or config.current_profile
    ctx.obj['fs'] = FileSystemService(workspace_path, current_profile)
    ctx.obj['config'] = config
    
    # Update current profile in config if different
    if current_profile != config.current_profile:
        config.current_profile = current_profile
        ctx.obj['fs'].save_config(config)
    
    # Show data directory location for user awareness
    data_dir_env = os.getenv("PINENEEDLE_DATA_DIR")
    if data_dir_env:
        ctx.obj['data_info'] = f"Using data directory from PINENEEDLE_DATA_DIR: {ctx.obj['fs'].data_path}"
    else:
        ctx.obj['data_info'] = f"Using default data directory: {ctx.obj['fs'].data_path}"
    
    # If no subcommand was invoked, start TUI
    if ctx.invoked_subcommand is None:
        from ..tui.main import start_tui
        start_tui(ctx.obj['fs'], ctx.obj['config'])


@cli.command()
@click.pass_context  
def init(ctx: click.Context) -> None:
    """Initialize a new Pineneedle workspace."""
    fs: FileSystemService = ctx.obj['fs']
    workspace_path: Path = ctx.obj['workspace']
    config = ctx.obj['config']
    
    click.echo(f"Initializing Pineneedle workspace in {workspace_path}")
    click.echo(ctx.obj['data_info'])
    
    # Use shared initialization logic
    fs.initialize_workspace(workspace_path, config, click.echo)
    
    click.echo("\n🎉 Workspace initialized successfully!")
    click.echo(f"\nData directory: {fs.data_path}")
    click.echo(f"Profile: {fs.current_profile}")
    click.echo("\nNext steps:")
    click.echo("1. Edit files in data/profiles/{}/background/ with your information".format(fs.current_profile))
    click.echo("2. Run 'pineneedle' to start the interactive interface")


@cli.group()
def job() -> None:
    """Manage job postings."""
    pass


@job.command("add")
@click.argument('content', required=False)
@click.option('--file', '-f', help='Read job posting from file')
@click.option('--id', help='Custom ID for the job posting')
@click.option('--stdin', is_flag=True, help='Read job posting from stdin')
@click.pass_context
def job_add(ctx: click.Context, content: str | None, file: str | None, id: str | None, stdin: bool) -> None:
    """Add a new job posting."""
    fs: FileSystemService = ctx.obj['fs']
    config = ctx.obj['config']
    
    if not content and not file and not stdin:
        # Interactive mode - use CLI function
        result = add_job_posting_from_editor(fs, config, id)
        if not result:
            click.echo("No content provided")
            return
        job_id, posting = result
    elif stdin:
        # Explicit stdin mode - for piped input
        content = sys.stdin.read().strip()
        if not content:
            click.echo("No content provided via stdin")
            return
        try:
            posting = asyncio.run(parse_job_posting(content, config.default_model, id))
            job_id = fs.save_job_posting(posting)
        except Exception as e:
            click.echo(f"Error parsing job posting: {e}")
            sys.exit(1)
    elif file:
        # File mode - use CLI function
        result = add_job_posting_from_file(fs, config, file, id)
        if not result:
            return
        job_id, posting = result
    else:
        # Direct content mode
        if not content:
            click.echo("No content provided")
            return
        try:
            posting = asyncio.run(parse_job_posting(content, config.default_model, id))
            job_id = fs.save_job_posting(posting)
        except Exception as e:
            click.echo(f"Error parsing job posting: {e}")
            sys.exit(1)
    
    click.echo(f"✓ Job posting saved with ID: {job_id}")
    click.echo(f"Title: {posting.title}")
    click.echo(f"Company: {posting.company}")
    click.echo(f"Location: {posting.location or 'Not specified'}")


@job.command("list")
@click.pass_context
def job_list(ctx: click.Context) -> None:
    """List all job postings."""
    fs: FileSystemService = ctx.obj['fs']
    
    postings = fs.list_job_postings()
    
    if not postings:
        click.echo("No job postings found.")
        return
    
    click.echo(f"Found {len(postings)} job posting(s):\n")
    
    for posting in postings:
        # Format the created_at datetime for display
        try:
            created_dt = datetime.fromisoformat(posting.created_at.replace('Z', '+00:00'))
            created_str = created_dt.strftime("%Y-%m-%d %H:%M")
        except (ValueError, AttributeError):
            created_str = "Unknown"
        
        click.echo(f"ID: {posting.id}")
        click.echo(f"Title: {posting.title}")
        click.echo(f"Company: {posting.company}")
        click.echo(f"Location: {posting.location or 'Not specified'}")
        click.echo(f"Added: {created_str}")
        click.echo("-" * 40)


@cli.command()
@click.argument('job_id')
@click.option('--tone', help='Tone for the resume (e.g., casual, technical, formal)')
@click.option('--model', help='Model to use (e.g., openai:gpt-4o, anthropic:claude-3-sonnet)')
@click.option('--temperature', type=float, help='Model temperature (0.0-2.0)')
@click.pass_context
def generate(ctx: click.Context, job_id: str, tone: str | None, model: str | None, temperature: float | None) -> None:
    """Generate a resume for a job posting."""
    fs: FileSystemService = ctx.obj['fs']
    config = ctx.obj['config']
    
    # Load job posting
    try:
        job_posting = fs.load_job_posting(job_id)
    except FileNotFoundError:
        click.echo(f"Job posting '{job_id}' not found")
        return
    
    # Load user background
    try:
        user_background = fs.load_user_background()
    except Exception as e:
        click.echo(f"Error loading user background: {e}")
        click.echo("Make sure you have markdown files in the background/ directory")
        return
    
    # Load template
    template = fs.load_template()
    
    # Configure model
    model_config = config.default_model
    if model:
        provider, model_name = model.split(':', 1) if ':' in model else ('openai', model)
        model_config = ModelConfig(provider=provider, model_name=model_name)
    if temperature is not None:
        model_config.temperature = temperature
    
    # Create dependencies
    deps = ResumeDeps(
        job_posting=job_posting,
        user_background=user_background,
        template=template,
        tone=tone,
        user_feedback=None,
    )
    
    click.echo(f"Generating resume for: {job_posting.title} at {job_posting.company}")
    click.echo(f"Using model: {model_config.provider}:{model_config.model_name}")
    
    try:
        resume_content = asyncio.run(generate_resume(deps, model_config))
        
        # Save the resume
        resume_path = fs.save_resume(job_posting.id, resume_content)
        
        click.echo(f"✓ Resume generated and saved to: {resume_path}")
        click.echo("\nResume content:")
        click.echo("=" * 50)
        click.echo(resume_content.resume_markdown)
        
    except Exception as e:
        click.echo(f"Error generating resume: {e}")
        sys.exit(1)





@cli.command()
@click.argument('job_id')
@click.option('--template', '-t', default='professional', help='PDF style template (professional, modern)')
@click.option('--output', '-o', help='Output PDF file path (default: {job_id}_{template}.pdf)')
@click.option('--version', help='Specific resume version timestamp (defaults to latest)')
@click.pass_context
def export(ctx: click.Context, job_id: str, template: str, output: str | None, version: str | None) -> None:
    """Export a resume to PDF."""
    fs: FileSystemService = ctx.obj['fs']
    
    # Load the resume content
    resume_path = fs.get_resume_version(job_id, version)
    
    if not resume_path or not resume_path.exists():
        if version:
            click.echo(f"No resume version '{version}' found for job ID: {job_id}")
        else:
            click.echo(f"No resume found for job ID: {job_id}")
        
        # Show available versions if any exist
        versions = fs.list_resume_versions(job_id)
        if versions:
            click.echo(f"Available versions: {', '.join([v[0] for v in versions])}")
        return
    
    # Create PDF generator
    pdf_gen = PDFGenerator()
    
    # Check if template is valid
    available_templates = pdf_gen.get_available_templates()
    if template not in available_templates:
        click.echo(f"Invalid template '{template}'. Available: {', '.join(available_templates)}")
        return
    
    # Get resume directory and setup metadata tracking
    resume_dir = fs.fs.get_profile_path("resumes", job_id)
    fs.fs.ensure_directory(resume_dir)  # Make sure directory exists
    pdf_metadata = PDFMetadataService(resume_dir)
    
    # Set output path based on the resume markdown filename
    if output is None:
        resume_filename = resume_path.name
        filename = generate_pdf_filename_from_resume(resume_filename, template)
        output_path = resume_dir / filename
        
        # Check if PDF already exists
        existing_pdf = pdf_metadata.get_pdf_path(resume_filename, template)
        if existing_pdf and existing_pdf.exists():
            click.echo(f"PDF already exists: {existing_pdf}")
            if not click.confirm("Do you want to regenerate it?", default=False):
                click.echo(f"✓ Using existing PDF: {existing_pdf}")
                return
    else:
        output_path = Path(output)
    
    try:
        # Read resume content
        resume_content = resume_path.read_text()
        
        # Generate PDF
        click.echo(f"Generating PDF with '{template}' template...")
        pdf_path = pdf_gen.generate(resume_content, output_path, template)
        
        # Record PDF generation in metadata (if using default naming)
        if output is None:
            pdf_metadata.record_pdf_generation(resume_filename, template, pdf_path)
        
        click.echo(f"✓ PDF exported to: {pdf_path}")
        click.echo(f"File size: {pdf_path.stat().st_size:,} bytes")
        
    except Exception as e:
        click.echo(f"Error generating PDF: {e}")
        sys.exit(1)





@cli.group()
def profile() -> None:
    """Manage profiles."""
    pass


@profile.command("list")
@click.pass_context
def profile_list(ctx: click.Context) -> None:
    """List all profiles."""
    from ..profile_service import ProfileService
    
    fs: FileSystemService = ctx.obj['fs']
    config = ctx.obj['config']
    
    profile_service = ProfileService(fs, config)
    profiles = profile_service.list_profiles()
    current_profile = profile_service.get_current_profile()
    
    if not profiles:
        click.echo("No profiles found.")
        return
    
    click.echo(f"Current profile: {current_profile.display_name}\n")
    click.echo(f"Available profiles:")
    
    for profile in profiles:
        marker = " (current)" if profile.name == current_profile.name else ""
        click.echo(f"  • {profile.display_name}{marker}")
        if profile.description:
            click.echo(f"    {profile.description}")


@profile.command("switch")
@click.argument('profile_name')
@click.pass_context
def profile_switch(ctx: click.Context, profile_name: str) -> None:
    """Switch to a different profile."""
    from ..profile_service import ProfileService
    
    fs: FileSystemService = ctx.obj['fs']
    config = ctx.obj['config']
    
    profile_service = ProfileService(fs, config)
    
    if profile_service.switch_profile(profile_name):
        click.echo(f"✓ Switched to profile: {profile_name}")
    else:
        click.echo(f"Profile '{profile_name}' not found")


@profile.command("create")
@click.argument('name')
@click.option('--display-name', help='Display name for the profile')
@click.option('--description', help='Description of the profile')
@click.pass_context
def profile_create(ctx: click.Context, name: str, display_name: str | None, description: str | None) -> None:
    """Create a new profile."""
    from ..profile_service import ProfileService
    
    if ' ' in name or not name.isalnum():
        click.echo("Profile name must be alphanumeric with no spaces")
        return
    
    fs: FileSystemService = ctx.obj['fs']
    config = ctx.obj['config']
    
    profile_service = ProfileService(fs, config)
    
    if profile_service.create_profile(name, display_name or name.title(), description or ""):
        click.echo(f"✓ Created profile: {display_name or name.title()}")
    else:
        click.echo("Failed to create profile (name may already exist)")


@profile.command("delete")
@click.argument('profile_name')
@click.option('--yes', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def profile_delete(ctx: click.Context, profile_name: str, yes: bool) -> None:
    """Delete a profile."""
    from ..profile_service import ProfileService
    
    if profile_name == "default":
        click.echo("Cannot delete default profile")
        return
    
    fs: FileSystemService = ctx.obj['fs']
    config = ctx.obj['config']
    
    profile_service = ProfileService(fs, config)
    profiles = profile_service.list_profiles()
    
    # Find profile by name or display name
    target_profile = None
    for profile in profiles:
        if profile.name == profile_name or profile.display_name == profile_name:
            target_profile = profile
            break
    
    if not target_profile:
        click.echo(f"Profile '{profile_name}' not found")
        return
    
    if not yes:
        if not click.confirm(f"Delete profile '{target_profile.display_name}'? This cannot be undone."):
            return
    
    if profile_service.delete_profile(target_profile.name):
        click.echo(f"✓ Deleted profile: {target_profile.display_name}")
    else:
        click.echo("Failed to delete profile")


def main() -> None:
    """Main CLI entry point."""
    cli()


if __name__ == "__main__":
    main() 