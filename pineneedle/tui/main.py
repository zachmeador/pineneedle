"""Main TUI interface for Pineneedle."""

import asyncio
import sys

import click
import questionary

from ..agents import generate_resume
from ..models import ResumeDeps


def start_tui(fs, config):
    """Start the interactive TUI."""
    controller = TUIController(fs, config)
    controller.main_menu()


class TUIController:
    """Handles TUI workflows."""
    
    def __init__(self, fs, config):
        self.fs = fs
        self.config = config
    
    def main_menu(self) -> None:
        """Main interactive interface."""
        # Check if initialized
        if not self.fs.is_initialized():
            self._show_uninitialized_interface()
            return
        
        # Get status
        status = self.fs.get_profile_status()
        
        # Show welcome with context
        click.echo("▗▄▄▖▗▄▄▄▖▗▖  ▗▖▗▄▄▄▖▗▖  ▗▖▗▄▄▄▖▗▄▄▄▖▗▄▄▄ ▗▖   ▗▄▄▄▖")
        click.echo("▐▌ ▐▌ █  ▐▛▚▖▐▌▐▌   ▐▛▚▖▐▌▐▌   ▐▌   ▐▌  █▐▌   ▐▌   ")
        click.echo("▐▛▀▘  █  ▐▌ ▝▜▌▐▛▀▀▘▐▌ ▝▜▌▐▛▀▀▘▐▛▀▀▘▐▌  █▐▌   ▐▛▀▀▘")
        click.echo("▐▌  ▗▄█▄▖▐▌  ▐▌▐▙▄▄▖▐▌  ▐▌▐▙▄▄▖▐▙▄▄▖▐▙▄▄▀▐▙▄▄▖▐▙▄▄▖")
        click.echo()
        click.echo(f"Profile: {status['profile']}")
        
        if status['job_count'] > 0 or status['resume_count'] > 0:
            click.echo(f"\nCurrent status:")
            if status['job_count'] > 0:
                postings = self.fs.list_job_postings()
                latest = postings[0]
                click.echo(f"• {status['job_count']} job posting(s) (newest: \"{latest.title}\" at {latest.company})")
            if status['resume_count'] > 0:
                click.echo(f"• {status['resume_count']} resume(s) generated")
            if not status['has_background']:
                click.echo("🌲 No background information found - add your details in the background files")
            click.echo()
        
        # Build menu options
        choices = []
        if status['job_count'] > 0:
            choices.append(f"🌲 Generate resume for latest job (\"{postings[0].title}\")")
        
        choices.extend([
            "🌱 Add new job posting",
            "🌳 Manage job postings",
            "🍃 Manage resumes",
            "🌿 Export resume to PDF",
            "🌳 Manage profiles",
            "🌲 Settings",
            "🌿 Help",
            "🍂 Quit",
        ])
        
        # Show menu
        choice = questionary.select(
            "What would you like to do?",
            choices=choices,
        ).ask()
        
        if not choice:  # User pressed Ctrl+C
            click.echo("Goodbye! 🍂")
            sys.exit(0)
        
        # Handle choices
        if choice.startswith("🌲 Generate resume for latest"):
            self.quick_generate(postings[0].id)
        elif choice.startswith("🌱 Add new"):
            self.add_job_interactive()
        elif choice.startswith("🌳 Manage job"):
            self.manage_jobs_interactive()
        elif choice.startswith("🍃 Manage resumes"):
            self.show_saved_resumes()
            self.main_menu()
        elif choice.startswith("🌿 Export resume"):
            self.export_interactive()
        elif choice.startswith("🌳 Manage profiles"):
            from .profile import ProfileManagerTUI
            ProfileManagerTUI(self.fs, self.config).interactive_manager()
            self.main_menu()
        elif choice.startswith("🌲 Settings"):
            from .settings import SettingsManager
            SettingsManager(self.fs, self.config).interactive_manager()
            self.main_menu()
        elif choice.startswith("🌿 Help"):
            click.echo("\nPineneedle Help")
            click.echo("=" * 50)
            click.echo("Use 'pineneedle --help' for command-line usage")
            click.echo("This interactive mode guides you through common tasks")
            input("\nPress Enter to continue...")
            self.main_menu()
        elif choice.startswith("🍂 Quit"):
            click.echo("Goodbye! 🍂")
            sys.exit(0)
    
    def _show_uninitialized_interface(self) -> None:
        """Show interface for uninitialized workspace."""
        click.echo("🌲 Pineneedle - AI Resume Generator")
        click.echo("\n🌲 Workspace not initialized")
        click.echo("Let's set up your workspace first!")
        
        if questionary.confirm("Initialize workspace now?", default=True).ask():
            self.initialize_workspace()
            self.main_menu()
        else:
            click.echo("Run 'pineneedle init' when you're ready to set up.")
            sys.exit(0)
    
    def quick_generate(self, job_id: str) -> None:
        """Quick resume generation flow."""
        try:
            job_posting = self.fs.load_job_posting(job_id)
            click.echo(f"🌲 Generating resume for: {job_posting.title} at {job_posting.company}")
            
            # Load dependencies
            user_background = self.fs.load_user_background()
            template = self.fs.load_template()
            
            deps = ResumeDeps(
                job_posting=job_posting,
                user_background=user_background,
                template=template,
                tone=None,
                user_feedback=None,
            )
            
            # Generate resume
            click.echo("🌲 Analyzing job requirements...")
            resume_content = asyncio.run(generate_resume(deps, self.config.default_model))
            
            # Save resume
            resume_path = self.fs.save_resume(job_posting.id, resume_content)
            
            click.echo(f"🌲 Resume generated and saved!")
            
            # Show options
            next_action = questionary.select(
                "What's next?",
                choices=[
                    "👀 Preview resume",
                    "🌿 Export to PDF", 
                    "🌳 Back to main menu",
                ]
            ).ask()
            
            if not next_action:
                self.main_menu()
                return
            
            if next_action.startswith("🍃 Preview"):
                click.echo("\n" + "=" * 50)
                click.echo(resume_content.resume_markdown)
                click.echo("=" * 50)
                input("\nPress Enter to continue...")
            elif next_action.startswith("🌿 Export"):
                self.export_interactive(job_id)
            
            # Return to main menu
            self.main_menu()
            
        except Exception as e:
            click.echo(f"🍂 Error: {e}")
            input("\nPress Enter to continue...")
            self.main_menu()
    
    def select_job_and_generate(self) -> None:
        """Show job selection interface for resume generation."""
        postings = self.fs.list_job_postings()
        
        if not postings:
            click.echo("No job postings found.")
            input("Press Enter to continue...")
            self.main_menu()
            return
        
        # Create choices for job selection
        choices = []
        for posting in postings[:10]:  # Show max 10
            choices.append(f"{posting.title} at {posting.company}")
        choices.append("🌳 Back to main menu")
        
        choice = questionary.select(
            "Select a job posting to generate resume for:",
            choices=choices
        ).ask()
        
        if not choice or choice.startswith("🌳"):
            self.main_menu()
            return
        
        # Find selected posting
        for posting in postings:
            if choice == f"{posting.title} at {posting.company}":
                self.quick_generate(posting.id)
                return
    
    def manage_jobs_interactive(self) -> None:
        """Interactive job posting management."""
        postings = self.fs.list_job_postings()
        
        if not postings:
            click.echo("No job postings found.")
            input("Press Enter to continue...")
            self.main_menu()
            return
        
        # Create choices for job selection
        choices = []
        for posting in postings[:10]:  # Show max 10
            choices.append(f"{posting.title} at {posting.company}")
        choices.append("🌳 Back to main menu")
        
        choice = questionary.select(
            "Select a job posting to manage:",
            choices=choices
        ).ask()
        
        if not choice or choice.startswith("🌳"):
            self.main_menu()
            return
        
        # Find selected posting
        selected_posting = None
        for posting in postings:
            if choice == f"{posting.title} at {posting.company}":
                selected_posting = posting
                break
        
        if selected_posting:
            self._show_job_actions(selected_posting)
    
    def _show_job_actions(self, posting) -> None:
        """Show available actions for a selected job posting."""
        click.echo(f"\n🍃 {posting.title} at {posting.company}")
        
        action = questionary.select(
            "What would you like to do?",
            choices=[
                "🍃 View details",
                "🌲 Generate resume",
                "🍂 Delete posting",
                "🌳 Back to job list",
            ]
        ).ask()
        
        if not action or action.startswith("🌳"):
            self.manage_jobs_interactive()
            return
        
        if action.startswith("🍃 View"):
            self._show_job_details(posting)
        elif action.startswith("🌲 Generate"):
            self.quick_generate(posting.id)
        elif action.startswith("🍂 Delete"):
            self._delete_job_posting(posting)
    
    def _show_job_details(self, posting) -> None:
        """Show detailed information about a job posting."""
        click.echo(f"\n" + "=" * 50)
        click.echo(f"Job Posting Details")
        click.echo("=" * 50)
        click.echo(f"Title: {posting.title}")
        click.echo(f"Company: {posting.company}")
        click.echo(f"Location: {posting.location or 'Not specified'}")
        click.echo(f"ID: {posting.id}")
        click.echo(f"Added: {posting.created_at}")
        
        if posting.pay:
            click.echo(f"Pay: {posting.pay}")
        if posting.industry:
            click.echo(f"Industry: {posting.industry}")
        
        click.echo(f"\nRequirements ({len(posting.requirements)}):")
        for req in posting.requirements:  # Show all requirements
            click.echo(f"  • {req}")
        
        click.echo(f"\nResponsibilities ({len(posting.responsibilities)}):")
        for resp in posting.responsibilities:  # Show all responsibilities
            click.echo(f"  • {resp}")
        
        if posting.keywords:
            click.echo(f"\nKeywords ({len(posting.keywords)}):")
            click.echo(f"  {', '.join(posting.keywords)}")
        
        if posting.practical_description:
            click.echo(f"\nWhat you'd actually be doing:")
            click.echo(f"  {posting.practical_description}")
        
        if posting.tone_reasoning:
            click.echo(f"\nCommunication style analysis:")
            click.echo(f"  {posting.tone_reasoning}")
        
        # Show model info for debugging
        if hasattr(posting, 'model_provider') and posting.model_provider != "unknown":
            click.echo(f"\nParsed using: {posting.model_provider}:{posting.model_name}")
        
        input("\nPress Enter to continue...")
        self._show_job_actions(posting)
    
    def _delete_job_posting(self, posting) -> None:
        """Delete a job posting."""
        if questionary.confirm(f"Delete job posting '{posting.title}' at {posting.company}? This cannot be undone.").ask():
            # Delete the posting file
            import os
            job_postings_path = self.fs.profile_path / "job_postings"
            
            # Find and delete the posting file
            for file_path in job_postings_path.glob(f"{posting.id}_*.json"):
                os.remove(file_path)
                click.echo(f"🌲 Deleted job posting: {posting.title}")
                break
            else:
                # Fallback: try exact match
                exact_path = job_postings_path / f"{posting.id}.json"
                if exact_path.exists():
                    os.remove(exact_path)
                    click.echo(f"🌲 Deleted job posting: {posting.title}")
                else:
                    click.echo("🍂 Failed to delete job posting")
        
        self.manage_jobs_interactive()
    
    def add_job_interactive(self) -> None:
        """Interactive job posting addition."""
        click.echo("🍃 Add New Job Posting")
        
        method = questionary.select(
            "How would you like to add the job posting?",
            choices=[
                "🍃 Paste content (recommended)",
                "🌳 From file",
                "🌳 Cancel",
            ]
        ).ask()
        
        if not method or method.startswith("🌳"):
            self.main_menu()
            return
        
        if method.startswith("🍃 Paste"):
            self.add_job_from_editor()
        elif method.startswith("🌳 From file"):
            file_path = questionary.text("File path:").ask()
            if file_path:
                self.add_job_from_file(file_path)
        
        self.main_menu()
    
    def export_interactive(self, job_id: str = None) -> None:
        """Interactive PDF export."""
        if not job_id:
            # Let user select job
            postings = self.fs.list_job_postings()
            if not postings:
                click.echo("No job postings with resumes found.")
                input("Press Enter to continue...")
                self.main_menu()
                return
            
            # Filter to only postings with resumes
            postings_with_resumes = []
            for posting in postings:
                if self.fs.get_latest_resume_path(posting.id):
                    postings_with_resumes.append(posting)
            
            if not postings_with_resumes:
                click.echo("No resumes found to export.")
                input("Press Enter to continue...")
                self.main_menu()
                return
            
            choices = []
            for posting in postings_with_resumes:
                choices.append(f"{posting.title} at {posting.company}")
            choices.append("🌳 Back to main menu")
            
            choice = questionary.select(
                "Select resume to export:",
                choices=choices
            ).ask()
            
            if not choice or choice.startswith("🌳"):
                self.main_menu()
                return
            
            # Find selected posting
            for posting in postings_with_resumes:
                if choice == f"{posting.title} at {posting.company}":
                    job_id = posting.id
                    break
        
        # Get templates
        from ..pdf import PDFGenerator
        pdf_gen = PDFGenerator()
        templates = pdf_gen.get_available_templates()
        
        template = questionary.select(
            "Choose PDF template:",
            choices=templates,
            default="professional"
        ).ask()
        
        if not template:
            self.main_menu()
            return
        
        # Export to PDF
        output = f"{job_id}_{template}.pdf"
        self._export_resume_to_pdf(job_id, template, output)
        
        input("\nPress Enter to continue...")
        self.main_menu()
    
    def initialize_workspace(self) -> None:
        """Initialize the pineneedle workspace."""
        click.echo(f"Initializing Pineneedle workspace in {self.fs.workspace_path}")
        click.echo(f"Using data directory: {self.fs.data_path}")
        
        # Use shared initialization logic
        self.fs.initialize_workspace(self.fs.workspace_path, self.config, click.echo)
        
        click.echo("\n🌲 Workspace initialized successfully!")
        click.echo(f"\nData directory: {self.fs.data_path}")
        click.echo(f"Profile: {self.fs.current_profile}")
        click.echo("\nNext steps:")
        click.echo("1. Edit files in data/profiles/{}/background/ with your information".format(self.fs.current_profile))
        click.echo("2. Use this interface to add job postings and generate resumes")
        
        input("\nPress Enter to continue...")
    
    def add_job_from_editor(self) -> None:
        """Add job posting using text editor."""
        import questionary
        import asyncio
        from ..agents import parse_job_posting
        
        # Get content from user
        content = questionary.text("Paste job posting content (or press Enter to cancel):").ask()
        
        if not content or not content.strip():
            click.echo("No content provided")
            input("\nPress Enter to continue...")
            return
        
        content = content.strip()
        
        try:
            click.echo("Parsing job posting...")
            posting = asyncio.run(parse_job_posting(content, self.config.default_model))
            job_id = self.fs.save_job_posting(posting)
            
            click.echo(f"🌲 Job posting saved with ID: {job_id}")
            click.echo(f"Title: {posting.title}")
            click.echo(f"Company: {posting.company}")
            click.echo(f"Location: {posting.location or 'Not specified'}")
        except Exception as e:
            click.echo(f"Error parsing job posting: {e}")
        
        input("\nPress Enter to continue...")
    
    def add_job_from_file(self, file_path: str) -> None:
        """Add job posting from a file."""
        import asyncio
        from pathlib import Path
        from ..agents import parse_job_posting
        
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            click.echo(f"File not found: {file_path}")
            input("\nPress Enter to continue...")
            return
        
        try:
            content = file_path_obj.read_text().strip()
            if not content:
                click.echo("File is empty")
                input("\nPress Enter to continue...")
                return
            
            click.echo("Parsing job posting...")
            posting = asyncio.run(parse_job_posting(content, self.config.default_model))
            job_id = self.fs.save_job_posting(posting)
            
            click.echo(f"🌲 Job posting saved with ID: {job_id}")
            click.echo(f"Title: {posting.title}")
            click.echo(f"Company: {posting.company}")
            click.echo(f"Location: {posting.location or 'Not specified'}")
        except Exception as e:
            click.echo(f"Error processing file: {e}")
        
        input("\nPress Enter to continue...")
    

    

    
    def _export_resume_to_pdf(self, job_id: str, template: str, output: str) -> None:
        """Export a resume to PDF."""
        from pathlib import Path
        from ..pdf import PDFGenerator
        
        # Load the resume content
        resume_path = self.fs.get_resume_version(job_id)
        
        if not resume_path or not resume_path.exists():
            click.echo(f"No resume found for job ID: {job_id}")
            return
        
        # Create PDF generator
        pdf_gen = PDFGenerator()
        
        # Check if template is valid
        available_templates = pdf_gen.get_available_templates()
        if template not in available_templates:
            click.echo(f"Invalid template '{template}'. Available: {', '.join(available_templates)}")
            return
        
        output_path = Path(output)
        
        try:
            # Read resume content
            resume_content = resume_path.read_text()
            
            # Generate PDF
            click.echo(f"Generating PDF with '{template}' template...")
            pdf_path = pdf_gen.generate(resume_content, output_path, template)
            
            click.echo(f"🌲 PDF exported to: {pdf_path}")
            click.echo(f"File size: {pdf_path.stat().st_size:,} bytes")
            
        except Exception as e:
            click.echo(f"Error generating PDF: {e}")
    
    def show_saved_resumes(self) -> None:
        """Show all saved resumes."""
        resumes_path = self.fs.profile_path / "resumes"
        
        if not resumes_path.exists():
            click.echo("No saved resumes found")
            input("\nPress Enter to continue...")
            return
        
        resume_dirs = [d for d in resumes_path.iterdir() if d.is_dir()]
        if not resume_dirs:
            click.echo("No saved resumes found")
            input("\nPress Enter to continue...")
            return
        
        click.echo(f"\n🍃 Saved Resumes")
        click.echo(f"Found resumes for {len(resume_dirs)} job(s):\n")
        
        for resume_dir in resume_dirs:
            job_id = resume_dir.name
            versions = self.fs.list_resume_versions(job_id)
            
            if versions:
                # Get job title from posting if available
                try:
                    job_posting = self.fs.load_job_posting(job_id)
                    title = job_posting.title
                    company = job_posting.company
                except:
                    title = "Unknown Job"
                    company = "Unknown Company"
                
                click.echo(f"Job ID: {job_id}")
                click.echo(f"Title: {title}")
                click.echo(f"Company: {company}")
                click.echo(f"Resume versions: {len(versions)}")
                if versions:
                    latest_timestamp = versions[0][0]
                    click.echo(f"Latest: {latest_timestamp}")
                    if len(versions) > 1:
                        click.echo(f"Other versions: {', '.join([v[0] for v in versions[1:]])}")
                click.echo("-" * 40)
        
        input("\nPress Enter to continue...") 