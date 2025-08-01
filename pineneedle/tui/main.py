"""Main TUI interface for Pineneedle."""

import asyncio
import sys

import click
import questionary
from questionary import Style

from ..agents import generate_resume
from ..models import ResumeDeps


# Custom style with pine tree cursor
pine_style = Style([
    ('pointer', '#00aa00 bold'),  # Green pine tree cursor
    ('highlighted', '#00aa00 bold'),  # Green highlight for selected item
    ('answer', '#00aa00 bold'),  # Green for selected answer
    ('question', 'bold'),
])

# Navigation constants
BACK_SIGNAL = '__PINENEEDLE_BACK__'

def select_with_back(prompt, choices, default=None, show_back=True):
    """Helper function for questionary select with back navigation."""
    # Add "← Back" option to choices if requested and not at root level
    enhanced_choices = choices.copy() if show_back else choices
    if show_back:
        enhanced_choices.append("← Back")
    
    try:
        choice = questionary.select(
            prompt,
            choices=enhanced_choices,
            style=pine_style,
            pointer="🌲",
            default=default
        ).ask()
        
        # Handle back selection
        if choice == "← Back":
            return BACK_SIGNAL
        
        return choice
        
    except KeyboardInterrupt:
        return BACK_SIGNAL


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
                click.echo("No background information found - add your details in the background files")
            click.echo()
        
        # Build menu options
        choices = []
        if status['job_count'] > 0:
            choices.append(f"Generate resume for latest job (\"{postings[0].title}\")")
        
        choices.extend([
            "Add new job posting",
            "Manage job postings",
            "Manage resumes",
            "Export resume to PDF",
            "Manage profiles",
            "Settings",
            "Help",
        ])
        
        # Show menu (no back option at root level)
        choice = select_with_back("What would you like to do?", choices, show_back=False)
        
        if not choice or choice == BACK_SIGNAL:  # User pressed ESC or back - quit at root level
            click.echo("\nGoodbye!")
            sys.exit(0)
        
        # Handle choices
        if choice.startswith("Generate resume for latest"):
            self.quick_generate(postings[0].id)
        elif choice.startswith("Add new"):
            self.add_job_interactive()
        elif choice.startswith("Manage job"):
            self.manage_jobs_interactive()
        elif choice.startswith("Manage resumes"):
            self.show_saved_resumes()
            self.main_menu()
        elif choice.startswith("Export resume"):
            self.export_interactive()
        elif choice.startswith("Manage profiles"):
            from .profile import ProfileManagerTUI
            ProfileManagerTUI(self.fs, self.config).interactive_manager()
            self.main_menu()
        elif choice.startswith("Settings"):
            from .settings import SettingsManager
            SettingsManager(self.fs, self.config).interactive_manager()
            self.main_menu()
        elif choice.startswith("Help"):
            click.echo("\nPineneedle Help")
            click.echo("=" * 50)
            click.echo("Use 'pineneedle --help' for command-line usage")
            click.echo("This interactive mode guides you through common tasks")
            input("\nPress Enter to continue...")
            self.main_menu()
    
    def _show_uninitialized_interface(self) -> None:
        """Show interface for uninitialized workspace."""
        click.echo("Pineneedle - AI Resume Generator")
        click.echo("\nWorkspace not initialized")
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
            click.echo(f"Generating resume for: {job_posting.title} at {job_posting.company}")
            
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
            click.echo("Generating resume...")
            resume_content = asyncio.run(generate_resume(deps, self.config.default_model))
            
            # Save resume
            resume_path = self.fs.save_resume(job_posting.id, resume_content)
            
            click.echo(f"Resume generated and saved!")
            
            # Show options
            next_action = select_with_back(
                "What's next?",
                choices=[
                    "Preview resume",
                    "Export to PDF", 
                ]
            )
            
            if not next_action or next_action == BACK_SIGNAL:  # User pressed ESC or back
                self.main_menu()
                return
            
            if next_action.startswith("Preview"):
                click.echo("\n" + "=" * 50)
                click.echo(resume_content.resume_markdown)
                click.echo("=" * 50)
                input("\nPress Enter to continue...")
            elif next_action.startswith("Export"):
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
        
        choice = select_with_back(
            "Select a job posting to generate resume for:",
            choices
        )
        
        if not choice or choice == BACK_SIGNAL:  # User pressed ESC or back
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
        
        choice = select_with_back(
            "Select a job posting to manage:",
            choices
        )
        
        if not choice or choice == BACK_SIGNAL:  # User pressed ESC or back
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
        click.echo(f"\n{posting.title} at {posting.company}")
        
        action = select_with_back(
            "What would you like to do?",
            choices=[
                "View details",
                "Generate resume",
                "Delete posting",
            ]
        )
        
        if not action or action == BACK_SIGNAL:  # User pressed ESC or back
            self.manage_jobs_interactive()
            return
        
        if action.startswith("View"):
            self._show_job_details(posting)
        elif action.startswith("Generate"):
            self.quick_generate(posting.id)
        elif action.startswith("Delete"):
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
        
        
        # Show model info for debugging
        if hasattr(posting, 'model_provider') and posting.model_provider != "unknown":
            click.echo(f"\nParsed using: {posting.model_provider}:{posting.model_name}")
        
        input("\nPress Enter to continue...")
        self._show_job_actions(posting)
    
    def _show_parsed_job_summary(self, posting) -> None:
        """Show a summary of the parsed job posting for user confirmation."""
        click.echo("\n" + "=" * 60)
        click.echo("PARSED JOB POSTING - Please Review")
        click.echo("=" * 60)
        click.echo(f"Title: {posting.title}")
        click.echo(f"Company: {posting.company}")
        click.echo(f"Location: {posting.location or 'Not specified'}")
        
        if posting.pay:
            click.echo(f"Pay: {posting.pay}")
        if posting.industry:
            click.echo(f"Industry: {posting.industry}")
        
        # Show key requirements (first 5)
        if posting.requirements:
            click.echo(f"\nKey Requirements ({len(posting.requirements)} total):")
            for req in posting.requirements[:5]:
                click.echo(f"  • {req}")
            if len(posting.requirements) > 5:
                click.echo(f"  ... and {len(posting.requirements) - 5} more")
        
        # Show key responsibilities (first 5)
        if posting.responsibilities:
            click.echo(f"\nKey Responsibilities ({len(posting.responsibilities)} total):")
            for resp in posting.responsibilities[:5]:
                click.echo(f"  • {resp}")
            if len(posting.responsibilities) > 5:
                click.echo(f"  ... and {len(posting.responsibilities) - 5} more")
        
        # Show keywords if parsed
        if posting.keywords:
            keywords_preview = posting.keywords[:8]  # Show first 8 keywords
            click.echo(f"\nKeywords: {', '.join(keywords_preview)}")
            if len(posting.keywords) > 8:
                click.echo(f"   ... and {len(posting.keywords) - 8} more")
        
        click.echo("=" * 60)
    
    def _delete_job_posting(self, posting) -> None:
        """Delete a job posting."""
        if questionary.confirm(f"Delete job posting '{posting.title}' at {posting.company}? This cannot be undone.").ask():
            # Delete the posting file
            import os
            job_postings_path = self.fs.profile_path / "job_postings"
            
            # Find and delete the posting file
            for file_path in job_postings_path.glob(f"{posting.id}_*.json"):
                os.remove(file_path)
                click.echo(f"Deleted job posting: {posting.title}")
                break
            else:
                # Fallback: try exact match
                exact_path = job_postings_path / f"{posting.id}.json"
                if exact_path.exists():
                    os.remove(exact_path)
                    click.echo(f"Deleted job posting: {posting.title}")
                else:
                    click.echo("Failed to delete job posting")
        
        self.manage_jobs_interactive()
    
    def add_job_interactive(self) -> None:
        """Interactive job posting addition."""
        click.echo("Add New Job Posting")
        
        method = select_with_back(
            "How would you like to add the job posting?",
            choices=[
                "Paste content directly (recommended)",
                "From file",
            ]
        )
        
        if not method or method == BACK_SIGNAL:  # User pressed ESC or back
            self.main_menu()
            return
        
        if method.startswith("Paste"):
            self.add_job_from_paste()
        elif method.startswith("From file"):
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
            
            choice = select_with_back(
                "Select resume to export:",
                choices
            )
            
            if not choice or choice == BACK_SIGNAL:  # User pressed ESC or back
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
        
        template = select_with_back(
            "Choose PDF template:",
            templates,
            default="professional"
        )
        
        if not template or template == BACK_SIGNAL:
            self.main_menu()
            return
        
        # Export to PDF with filename matching resume markdown
        resume_path = self.fs.get_resume_version(job_id)
        if not resume_path or not resume_path.exists():
            click.echo(f"No resume found for job ID: {job_id}")
            input("\nPress Enter to continue...")
            self.main_menu()
            return
            
        # Get resume directory and setup metadata tracking
        from ..filename_utils import generate_pdf_filename_from_resume
        from ..services import PDFMetadataService
        resume_dir = self.fs.fs.get_profile_path("resumes", job_id)
        self.fs.fs.ensure_directory(resume_dir)  # Make sure directory exists
        pdf_metadata = PDFMetadataService(resume_dir)
        
        # Generate filename based on resume markdown name
        resume_filename = resume_path.name
        filename = generate_pdf_filename_from_resume(resume_filename, template)
        output_path = resume_dir / filename
        
        # Check if PDF already exists
        existing_pdf = pdf_metadata.get_pdf_path(resume_filename, template)
        if existing_pdf and existing_pdf.exists():
            click.echo(f"PDF already exists: {existing_pdf}")
            if not questionary.confirm("Do you want to regenerate it?", default=False).ask():
                click.echo(f"✓ Using existing PDF: {existing_pdf}")
                input("\nPress Enter to continue...")
                self.main_menu()
                return
        
        self._export_resume_to_pdf(job_id, template, str(output_path), pdf_metadata, resume_filename)
        
        input("\nPress Enter to continue...")
        self.main_menu()
    
    def initialize_workspace(self) -> None:
        """Initialize the pineneedle workspace."""
        click.echo(f"Initializing Pineneedle workspace in {self.fs.workspace_path}")
        
        # Use shared initialization logic
        self.fs.initialize_workspace(self.fs.workspace_path, self.config, click.echo)
        
        click.echo("\nWorkspace initialized successfully!")
        click.echo(f"Profile: {self.fs.current_profile}")
        click.echo("\nNext steps:")
        click.echo("1. Edit files in data/profiles/{}/background/ with your information".format(self.fs.current_profile))
        click.echo("2. Use this interface to add job postings and generate resumes")
        
        input("\nPress Enter to continue...")
    
    def add_job_from_paste(self) -> None:
        """Add job posting using multiline paste input."""
        import asyncio
        from ..agents import parse_job_posting
        
        # Show helpful instructions
        click.echo("\nPaste Job Posting Content")
        click.echo("=" * 50)
        click.echo("Instructions:")
        click.echo("• Paste your job posting text below")
        click.echo("• You can paste multiple lines at once")
        click.echo("• Press Enter twice (on empty line) when finished")
        click.echo("• Type 'cancel' to abort")
        click.echo("=" * 50)
        click.echo("\nPaste job posting content:")
        
        # Collect multiline input
        lines = []
        empty_line_count = 0
        
        while True:
            try:
                line = input()
                
                # Allow user to cancel
                if line.strip().lower() == 'cancel':
                    click.echo("Cancelled.")
                    input("\nPress Enter to continue...")
                    return
                
                # Check for double empty line (end of input)
                if line.strip() == "":
                    empty_line_count += 1
                    if empty_line_count >= 2:
                        break
                    lines.append(line)
                else:
                    empty_line_count = 0
                    lines.append(line)
                    
            except (EOFError, KeyboardInterrupt):
                click.echo("\nCancelled.")
                input("\nPress Enter to continue...")
                return
        
        # Join all lines and clean up
        content = '\n'.join(lines).strip()
        
        if not content:
            click.echo("No content provided")
            input("\nPress Enter to continue...")
            return
        
        try:
            click.echo("\nParsing job posting...")
            posting = asyncio.run(parse_job_posting(content, self.config.default_model))
            click.echo("✓ Parsing complete!")
            
            # Show parsed details for confirmation
            try:
                self._show_parsed_job_summary(posting)
            except Exception as summary_error:
                click.echo(f"Error displaying summary: {summary_error}")
                click.echo("Proceeding without summary...")
            
            # Ask for confirmation
            try:
                confirmed = questionary.confirm("\nDoes this look correct? Save this job posting?", default=True).ask()
                if confirmed is None:  # User pressed Ctrl+C
                    click.echo("\nCancelled by user")
                    return
                elif confirmed:
                    job_id = self.fs.save_job_posting(posting)
                    click.echo(f"\nJob posting saved with ID: {job_id}")
                    click.echo("✓ Ready to generate resume!")
                else:
                    click.echo("\nJob posting not saved")
            except Exception as confirm_error:
                click.echo(f"Error during confirmation: {confirm_error}")
                # Fallback - save without confirmation
                job_id = self.fs.save_job_posting(posting)
                click.echo(f"\nJob posting saved with ID: {job_id} (auto-saved due to error)")
                
        except Exception as e:
            click.echo(f"Error parsing job posting: {e}")
            import traceback
            traceback.print_exc()  # Debug output
        
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
            
            # Show parsed details for confirmation
            self._show_parsed_job_summary(posting)
            
            # Ask for confirmation
            if questionary.confirm("\nDoes this look correct? Save this job posting?", default=True).ask():
                job_id = self.fs.save_job_posting(posting)
                click.echo(f"\nJob posting saved with ID: {job_id}")
                click.echo("✓ Ready to generate resume!")
            else:
                click.echo("\nJob posting not saved")
                
        except Exception as e:
            click.echo(f"Error processing file: {e}")
        
        input("\nPress Enter to continue...")
    

    

    
    def _export_resume_to_pdf(self, job_id: str, template: str, output: str, pdf_metadata=None, resume_filename: str = None) -> None:
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
            
            # Record PDF generation in metadata if provided
            if pdf_metadata and resume_filename:
                pdf_metadata.record_pdf_generation(resume_filename, template, pdf_path)
            
            click.echo(f"PDF exported to: {pdf_path}")
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
        
        click.echo(f"\nSaved Resumes")
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