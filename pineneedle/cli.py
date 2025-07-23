"""CLI interface for Pineneedle."""

import click
from pathlib import Path

from .init import initialize_workspace
from .job_posting import JobPostingService


@click.group()
def main():
    """Pineneedle - Intelligent resume management with LLMs."""
    pass


@main.command()
@click.option('--force', '-f', is_flag=True, help='Overwrite existing .data directory')
def init(force):
    """Initialize a new Pineneedle workspace with content templates."""
    data_dir = Path('.data')
    
    if initialize_workspace(data_dir, force):
        click.echo("✅ Pineneedle workspace initialized!")
        click.echo(f"📁 Created {data_dir} with content templates and initial tones")
        click.echo("📝 Next steps:")
        click.echo(f"   1. Edit files in {data_dir / 'content'}/ with your information")
        click.echo(f"      - personal.md, experience.md, education.md, skills.md")
        click.echo(f"   2. Review tone configurations in {data_dir / 'tones'}/")
        click.echo("   3. Run 'pineneedle store-job' to analyze a job posting")
    else:
        click.echo(f"❌ Directory {data_dir} already exists. Use --force to overwrite.")


@main.command()
def store_job():
    """Store and analyze a job posting using Pydantic-AI."""
    click.echo("📋 Job Posting Analyzer")
    click.echo("Paste the job posting text below. Press Ctrl+D (Linux/Mac) or Ctrl+Z+Enter (Windows) when done:")
    
    # Read multiline input
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass
    
    job_text = '\n'.join(lines).strip()
    
    if not job_text:
        click.echo("❌ No job posting text provided.")
        return
    
    if len(job_text) < 10:
        click.echo("❌ Job posting text too short. Please provide a complete job description.")
        return
    
    # Analyze the job posting
    service = JobPostingService()
    
    try:
        with click.progressbar(length=1, label='Analyzing job posting') as bar:
            job_posting = service.store_job_posting_sync(job_text)
            bar.update(1)
        
        click.echo(f"\n✅ Job posting analyzed and stored!")
        click.echo(f"🆔 Job ID: {job_posting.id}")
        click.echo(f"🏢 Company: {job_posting.analysis.company}")
        click.echo(f"💼 Position: {job_posting.analysis.position}")
        
        if job_posting.analysis.location:
            click.echo(f"📍 Location: {job_posting.analysis.location}")
        
        if job_posting.analysis.seniority_level:
            click.echo(f"👔 Level: {job_posting.analysis.seniority_level}")
        
        if job_posting.analysis.requirements:
            click.echo(f"\n📋 Key Requirements ({len(job_posting.analysis.requirements)}):")
            for req in job_posting.analysis.requirements[:5]:  # Show first 5
                click.echo(f"  • {req}")
            if len(job_posting.analysis.requirements) > 5:
                click.echo(f"  ... and {len(job_posting.analysis.requirements) - 5} more")
        
        if job_posting.analysis.keywords:
            click.echo(f"\n🔑 Keywords: {', '.join(job_posting.analysis.keywords[:10])}")
        
        click.echo(f"\n💾 Saved to: .data/job_postings/{job_posting.id}.json")
        
    except Exception as e:
        click.echo(f"❌ Error analyzing job posting: {e}")


@main.command()
def list_jobs():
    """List all stored job postings."""
    service = JobPostingService()
    postings = service.list_job_postings()
    
    if not postings:
        click.echo("No job postings found. Use 'pineneedle store-job' to add one.")
        return
    
    click.echo(f"📋 Found {len(postings)} job posting(s):\n")
    
    for posting in postings:
        click.echo(f"🆔 {posting.id}")
        click.echo(f"   🏢 {posting.analysis.company} - {posting.analysis.position}")
        click.echo(f"   📅 Stored: {posting.created_date.strftime('%Y-%m-%d %H:%M')}")
        if posting.analysis.location:
            click.echo(f"   📍 {posting.analysis.location}")
        click.echo()


if __name__ == '__main__':
    main() 