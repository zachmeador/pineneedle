"""CLI interface for Pineneedle."""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import click
from dotenv import load_dotenv

from .agents import parse_job_posting, generate_resume, process_feedback
from .models import GenerationRequest, ModelConfig, ResumeDeps
from .services import FileSystemService

# Load environment variables
load_dotenv()


@click.group()
@click.option('--workspace', default='.', help='Workspace directory path')
@click.pass_context
def cli(ctx: click.Context, workspace: str) -> None:
    """Pineneedle - Intelligent Resume Generation with LLMs."""
    ctx.ensure_object(dict)
    workspace_path = Path(workspace).resolve()
    ctx.obj['workspace'] = workspace_path
    ctx.obj['fs'] = FileSystemService(workspace_path)
    ctx.obj['config'] = ctx.obj['fs'].load_config()
    
    # Show data directory location for user awareness
    data_dir_env = os.getenv("PINENEEDLE_DATA_DIR")
    if data_dir_env:
        ctx.obj['data_info'] = f"Using data directory from PINENEEDLE_DATA_DIR: {ctx.obj['fs'].data_path}"
    else:
        ctx.obj['data_info'] = f"Using default data directory: {ctx.obj['fs'].data_path}"
    # No need for AgentService anymore - agents are module-level


@cli.command()
@click.pass_context  
def init(ctx: click.Context) -> None:
    """Initialize a new Pineneedle workspace."""
    fs: FileSystemService = ctx.obj['fs']
    workspace_path: Path = ctx.obj['workspace']
    
    click.echo(f"Initializing Pineneedle workspace in {workspace_path}")
    click.echo(ctx.obj['data_info'])
    
    # Create workspace structure (already done by FileSystemService)
    click.echo("✓ Created directory structure")
    
    # Copy example data to background if it doesn't exist
    background_path = fs.data_path / "background"
    example_data_path = workspace_path / "example_data"
    
    if example_data_path.exists():
        for file_name in ["contact.md", "education.md", "experience.md", "reference.md"]:
            example_file = example_data_path / file_name
            background_file = background_path / file_name
            
            if example_file.exists() and not background_file.exists():
                background_file.write_text(example_file.read_text())
                click.echo(f"✓ Copied {file_name} to background/")
    
    # Create default template
    template_content = fs.load_template("default")
    click.echo("✓ Created default resume template")
    
    # Save default config
    config = ctx.obj['config']
    fs.save_config(config)
    click.echo("✓ Created configuration file")
    
    click.echo("\n🎉 Workspace initialized successfully!")
    click.echo(f"\nData directory: {fs.data_path}")
    click.echo("\nNext steps:")
    click.echo("1. Edit files in data/background/ with your information")
    click.echo("2. Add a job posting:")
    click.echo("   • Interactive mode: pineneedle job add")
    click.echo("   • From file: pineneedle job add --file job.txt")
    click.echo("   • From stdin: pineneedle job add --stdin")
    click.echo("3. Generate resume: pineneedle generate <job_id>")


@cli.group()
def job() -> None:
    """Manage job postings.
    
    Tips for adding job postings:
    • Use interactive mode for pasting from browser: 'pineneedle job add'
    • Save to file first for complex content: 'pineneedle job add --file job.txt'
    • Pipe content: 'cat job.txt | pineneedle job add --stdin'
    """
    pass


@job.command("add")
@click.argument('content', required=False)
@click.option('--file', '-f', help='Read job posting from file')
@click.option('--id', help='Custom ID for the job posting')
@click.option('--stdin', is_flag=True, help='Read job posting from stdin')
@click.pass_context
def job_add(ctx: click.Context, content: str | None, file: str | None, id: str | None, stdin: bool) -> None:
    """Add a new job posting.
    
    Examples:
        # Direct argument (quote carefully)
        pineneedle job add "job posting text here"
        
        # From file (recommended for complex content)
        pineneedle job add --file job.txt
        
        # From stdin (great for pasting)
        pineneedle job add --stdin
        # or pipe content:
        echo "job content" | pineneedle job add --stdin
        
        # Interactive mode (no arguments)
        pineneedle job add
    """
    if not content and not file and not stdin:
        # Interactive mode - use Click's built-in editor
        click.echo("Opening editor for job posting content...")
        content = click.edit("# Paste your job posting content here\n# Lines starting with # will be ignored\n\n")
        if not content:
            click.echo("No content provided")
            return
        # Remove comment lines
        content = '\n'.join(line for line in content.split('\n') if not line.strip().startswith('#')).strip()
    elif stdin:
        # Explicit stdin mode - for piped input
        content = sys.stdin.read().strip()
        if not content:
            click.echo("No content provided via stdin")
            return
    elif file:
        file_path = Path(file)
        if not file_path.exists():
            click.echo(f"File not found: {file}")
            return
        content = file_path.read_text()
    
    if not content:
        click.echo("No content provided")
        return
    
    fs: FileSystemService = ctx.obj['fs']
    config = ctx.obj['config']
    
    click.echo("Parsing job posting...")
    
    try:
        posting = asyncio.run(parse_job_posting(content, config.default_model, id))
        job_id = fs.save_job_posting(posting)
        
        click.echo(f"✓ Job posting saved with ID: {job_id}")
        click.echo(f"Title: {posting.title}")
        click.echo(f"Company: {posting.company}")
        click.echo(f"Location: {posting.location or 'Not specified'}")
        
    except Exception as e:
        click.echo(f"Error parsing job posting: {e}")
        sys.exit(1)


@job.command("list")
@click.pass_context
def job_list(ctx: click.Context) -> None:
    """List all job postings."""
    fs: FileSystemService = ctx.obj['fs']
    
    postings = fs.list_job_postings()
    
    if not postings:
        click.echo("No job postings found. Add one with: pineneedle job add 'content'")
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
        click.echo("Make sure you have markdown files in the data/background/ directory")
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
    
    # Create generation request
    request = GenerationRequest(
        job_posting_id=job_id,
        tone=tone,
        llm_config=model_config,
    )
    
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
        
        # Archive the resume
        archive_path = fs.archive_resume(
            job_posting, resume_content, request, model_config
        )
        
        click.echo(f"✓ Resume generated and saved to: {archive_path}")
        click.echo("\nResume content:")
        click.echo("=" * 50)
        click.echo(resume_content.resume_markdown)
        
    except Exception as e:
        click.echo(f"Error generating resume: {e}")
        sys.exit(1)


@cli.command()
@click.argument('job_id')
@click.pass_context
def iterate(ctx: click.Context, job_id: str) -> None:
    """Iteratively improve a resume with feedback."""
    fs: FileSystemService = ctx.obj['fs']
    config = ctx.obj['config']
    
    # Load job posting
    try:
        job_posting = fs.load_job_posting(job_id)
    except FileNotFoundError:
        click.echo(f"Job posting '{job_id}' not found")
        return
    
    # Load user background and template
    user_background = fs.load_user_background()
    template = fs.load_template()
    
    iteration_count = 1
    user_feedback = None
    
    click.echo(f"Starting interactive resume iteration for: {job_posting.title}")
    click.echo("Type 'done' when satisfied, or provide feedback to improve the resume.\n")
    
    while True:
        # Create dependencies
        deps = ResumeDeps(
            job_posting=job_posting,
            user_background=user_background,
            template=template,
            tone=None,
            user_feedback=user_feedback,
        )
        
        try:
            # Generate resume
            click.echo(f"Generating resume (iteration {iteration_count})...")
            resume_content = asyncio.run(generate_resume(deps, config.default_model))
            
            # Show resume
            click.echo("\n" + "=" * 50)
            click.echo("GENERATED RESUME:")
            click.echo("=" * 50)
            click.echo(resume_content.resume_markdown)
            click.echo("=" * 50 + "\n")
            
            # Get user feedback
            feedback = click.prompt("Feedback (or 'done' to finish)", default="done")
            
            if feedback.lower() == 'done':
                # Save final resume
                request = GenerationRequest(job_posting_id=job_id)
                archive_path = fs.archive_resume(
                    job_posting, resume_content, request, config.default_model, iteration_count
                )
                click.echo(f"✓ Final resume saved to: {archive_path}")
                break
            
            # Process feedback
            feedback_result = asyncio.run(process_feedback(feedback, config.default_model))
            user_feedback = feedback_result.revised_prompt
            iteration_count += 1
            
            click.echo(f"\nProcessed feedback: {feedback_result.specific_changes}")
            
        except Exception as e:
            click.echo(f"Error during iteration: {e}")
            break


@cli.group()
def archive() -> None:
    """Manage resume archives."""
    pass


@archive.command("list")
@click.pass_context
def archive_list(ctx: click.Context) -> None:
    """List all archived resumes with version counts."""
    fs: FileSystemService = ctx.obj['fs']
    workspace_path: Path = ctx.obj['workspace']
    resumes_path = workspace_path / "data" / "resumes"
    
    if not resumes_path.exists():
        click.echo("No archived resumes found")
        return
    
    archives = list(resumes_path.iterdir())
    if not archives:
        click.echo("No archived resumes found")
        return
    
    click.echo(f"Found {len(archives)} job(s) with archived resumes:\n")
    
    for archive_dir in archives:
        if archive_dir.is_dir():
            job_id = archive_dir.name
            versions = fs.list_resume_versions(job_id)
            
            if versions:
                # Get latest version metadata
                latest_timestamp, latest_metadata_path = versions[0]
                try:
                    import json
                    metadata = json.loads(latest_metadata_path.read_text())
                    click.echo(f"Job ID: {job_id}")
                    click.echo(f"Title: {metadata['job_posting']['title']}")
                    click.echo(f"Company: {metadata['job_posting']['company'] or 'Not specified'}")
                    click.echo(f"Versions: {len(versions)}")
                    click.echo(f"Latest: {latest_timestamp}")
                    if len(versions) > 1:
                        click.echo(f"Older versions: {', '.join([v[0] for v in versions[1:]])}")
                    click.echo("-" * 40)
                except Exception:
                    click.echo(f"Job ID: {job_id} ({len(versions)} versions, metadata corrupted)")
                    click.echo("-" * 40)


@archive.command("show")
@click.argument('job_id')
@click.option('--version', help='Specific version timestamp (YYYY-MM-DD_HH-MM-SS), defaults to latest')
@click.pass_context
def archive_show(ctx: click.Context, job_id: str, version: str | None) -> None:
    """Show an archived resume (latest version by default)."""
    fs: FileSystemService = ctx.obj['fs']
    
    resume_path = fs.get_resume_version(job_id, version)
    
    if not resume_path or not resume_path.exists():
        if version:
            click.echo(f"No resume version '{version}' found for job ID: {job_id}")
        else:
            click.echo(f"No archived resume found for job ID: {job_id}")
        
        # Show available versions if any exist
        versions = fs.list_resume_versions(job_id)
        if versions:
            click.echo(f"\nAvailable versions: {', '.join([v[0] for v in versions])}")
        return
    
    # Show which version we're displaying
    if version:
        click.echo(f"Resume for job ID: {job_id} (version: {version})")
    else:
        click.echo(f"Resume for job ID: {job_id} (latest version)")
    
    click.echo("=" * 50)
    click.echo(resume_path.read_text())


@archive.command("versions")
@click.argument('job_id')
@click.pass_context
def archive_versions(ctx: click.Context, job_id: str) -> None:
    """List all resume versions for a specific job posting."""
    fs: FileSystemService = ctx.obj['fs']
    
    versions = fs.list_resume_versions(job_id)
    
    if not versions:
        click.echo(f"No resume versions found for job ID: {job_id}")
        return
    
    click.echo(f"Resume versions for job ID: {job_id}\n")
    
    for i, (timestamp, metadata_path) in enumerate(versions):
        marker = " (latest)" if i == 0 else ""
        
        try:
            import json
            metadata = json.loads(metadata_path.read_text())
            iterations = metadata.get('iteration_count', 1)
            model = metadata.get('model_used', {})
            model_name = f"{model.get('provider', 'unknown')}:{model.get('model_name', 'unknown')}"
            
            click.echo(f"{timestamp}{marker}")
            click.echo(f"  Model: {model_name}")
            click.echo(f"  Iterations: {iterations}")
            click.echo(f"  Created: {metadata.get('created_at', 'unknown')}")
            
            # Show tone if specified
            request = metadata.get('generation_request', {})
            if request.get('tone'):
                click.echo(f"  Tone: {request['tone']}")
            
            click.echo()
            
        except Exception:
            click.echo(f"{timestamp}{marker} (metadata corrupted)")
            click.echo()


def main() -> None:
    """Main CLI entry point."""
    cli()


if __name__ == "__main__":
    main() 