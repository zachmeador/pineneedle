"""Manager classes for handling specific TUI domains."""

import asyncio
import click
import os
from pathlib import Path
from typing import Optional

from .base import MenuController, ListSelector, select_with_back, BACK_SIGNAL
from ..agents import parse_job_posting, generate_resume
from ..models import ResumeDeps


class JobManager(MenuController):
    """Handles job posting related operations."""
    
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
        
        if not method or method == BACK_SIGNAL:
            return
        
        if method.startswith("Paste"):
            self.add_job_from_paste()
        elif method.startswith("From file"):
            file_path = input("File path: ")
            if file_path:
                self.add_job_from_file(file_path)
    
    def manage_jobs_interactive(self) -> None:
        """Interactive job posting management."""
        postings = self.fs.list_job_postings()
        
        if not postings:
            click.echo("No job postings found.")
            self.wait_for_user()
            return
        
        # Select a job posting
        selected_posting = ListSelector.select_from_list(
            postings[:10],  # Show max 10
            "Select a job posting to manage:",
            lambda p: f"{p.title} at {p.company}"
        )
        
        if not selected_posting or selected_posting == BACK_SIGNAL:
            return
        
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
        
        if not action or action == BACK_SIGNAL:
            self.manage_jobs_interactive()
            return
        
        if action.startswith("View"):
            self._show_job_details(posting)
        elif action.startswith("Generate"):
            self._quick_generate(posting.id)
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
        for req in posting.requirements:
            click.echo(f"  • {req}")
        
        click.echo(f"\nResponsibilities ({len(posting.responsibilities)}):")
        for resp in posting.responsibilities:
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
        
        self.wait_for_user()
        self._show_job_actions(posting)
    
    def _delete_job_posting(self, posting) -> None:
        """Delete a job posting."""
        if self.confirm_action(f"Delete job posting '{posting.title}' at {posting.company}? This cannot be undone."):
            # Delete the posting file
            job_postings_path = self.fs.profile_path / "job_postings"
            
            # Find and delete the posting file
            for file_path in job_postings_path.glob(f"{posting.id}_*.json"):
                os.remove(file_path)
                self.show_success(f"Deleted job posting: {posting.title}")
                break
            else:
                # Fallback: try exact match
                exact_path = job_postings_path / f"{posting.id}.json"
                if exact_path.exists():
                    os.remove(exact_path)
                    self.show_success(f"Deleted job posting: {posting.title}")
                else:
                    self.show_error("Failed to delete job posting")
        
        self.manage_jobs_interactive()
    
    def _quick_generate(self, job_id: str) -> None:
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
            self.fs.save_resume(job_posting.id, resume_content)
            self.show_success("Resume generated and saved!")
            
            # Show options
            next_action = select_with_back(
                "What's next?",
                choices=[
                    "Preview resume",
                    "Export to PDF", 
                ]
            )
            
            if not next_action or next_action == BACK_SIGNAL:
                return
            
            if next_action.startswith("Preview"):
                click.echo("\n" + "=" * 50)
                click.echo(resume_content.resume_markdown)
                click.echo("=" * 50)
                self.wait_for_user()
            elif next_action.startswith("Export"):
                # Create export manager inline to avoid circular import
                export_manager = ExportManager(self.fs, self.config)
                export_manager.export_interactive(job_id)
            
        except Exception as e:
            self.show_error(str(e))
    
    def add_job_from_paste(self) -> None:
        """Add job posting using multiline paste input."""
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
                    self.wait_for_user()
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
                self.wait_for_user()
                return
        
        # Join all lines and clean up
        content = '\n'.join(lines).strip()
        
        if not content:
            click.echo("No content provided")
            self.wait_for_user()
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
                if self.confirm_action("\nDoes this look correct? Save this job posting?", default=True):
                    job_id = self.fs.save_job_posting(posting)
                    click.echo(f"\nJob posting saved with ID: {job_id}")
                    self.show_success("Ready to generate resume!")
                else:
                    click.echo("\nJob posting not saved")
            except Exception as confirm_error:
                click.echo(f"Error during confirmation: {confirm_error}")
                # Fallback - save without confirmation
                job_id = self.fs.save_job_posting(posting)
                click.echo(f"\nJob posting saved with ID: {job_id} (auto-saved due to error)")
                
        except Exception as e:
            self.show_error(f"Error parsing job posting: {e}")
            import traceback
            traceback.print_exc()  # Debug output
        
        self.wait_for_user()
    
    def add_job_from_file(self, file_path: str) -> None:
        """Add job posting from a file."""
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            self.show_error(f"File not found: {file_path}")
            return
        
        try:
            content = file_path_obj.read_text().strip()
            if not content:
                self.show_error("File is empty")
                return
            
            click.echo("Parsing job posting...")
            posting = asyncio.run(parse_job_posting(content, self.config.default_model))
            
            # Show parsed details for confirmation
            self._show_parsed_job_summary(posting)
            
            # Ask for confirmation
            if self.confirm_action("\nDoes this look correct? Save this job posting?", default=True):
                job_id = self.fs.save_job_posting(posting)
                click.echo(f"\nJob posting saved with ID: {job_id}")
                self.show_success("Ready to generate resume!")
            else:
                click.echo("\nJob posting not saved")
                
        except Exception as e:
            self.show_error(f"Error processing file: {e}")
        
        self.wait_for_user()
    
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


class ResumeManager(MenuController):
    """Handles resume related operations."""
    
    def delete_resume_interactive(self) -> None:
        """Interactive resume deletion."""
        resumes_path = self.fs.profile_path / "resumes"
        
        if not resumes_path.exists():
            click.echo("No saved resumes found")
            self.wait_for_user()
            return
        
        resume_dirs = [d for d in resumes_path.iterdir() if d.is_dir()]
        if not resume_dirs:
            click.echo("No saved resumes found")
            self.wait_for_user()
            return
        
        # Create list of available resumes
        resume_options = []
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
                
                resume_options.append({
                    'job_id': job_id,
                    'title': title,
                    'company': company,
                    'versions': versions,
                    'display': f"{title} at {company} ({len(versions)} version{'s' if len(versions) != 1 else ''})"
                })
        
        if not resume_options:
            click.echo("No resumes with versions found")
            self.wait_for_user()
            return
        
        # Select which resume to delete
        selected_resume = ListSelector.select_from_list(
            resume_options,
            "Select a resume to delete:",
            lambda r: r['display']
        )
        
        if not selected_resume or selected_resume == BACK_SIGNAL:
            return
        
        # If multiple versions, let user choose specific version or all
        if len(selected_resume['versions']) > 1:
            version_choices = []
            for timestamp, filename in selected_resume['versions']:
                version_choices.append(f"{timestamp} ({filename})")
            version_choices.append("Delete ALL versions")
            
            version_choice = select_with_back(
                f"Which version of '{selected_resume['title']}' resume?",
                version_choices
            )
            
            if not version_choice or version_choice == BACK_SIGNAL:
                return
            
            if version_choice == "Delete ALL versions":
                self._delete_all_resume_versions(selected_resume)
            else:
                # Find specific version to delete
                for timestamp, filename in selected_resume['versions']:
                    if version_choice.startswith(timestamp):
                        self._delete_specific_resume_version(selected_resume, timestamp, filename)
                        break
        else:
            # Only one version, delete it
            timestamp, filename = selected_resume['versions'][0]
            self._delete_specific_resume_version(selected_resume, timestamp, filename)
    
    def _delete_specific_resume_version(self, resume_info, timestamp: str, filename: str) -> None:
        """Delete a specific resume version."""
        confirm_msg = f"Delete resume version '{timestamp}' for {resume_info['title']}? This cannot be undone."
        
        if self.confirm_action(confirm_msg):
            try:
                resume_dir = self.fs.profile_path / "resumes" / resume_info['job_id']
                resume_file = resume_dir / filename
                
                if resume_file.exists():
                    os.remove(resume_file)
                    self.show_success(f"Deleted resume version: {timestamp}")
                    
                    # Also delete any associated PDFs
                    pdf_files = list(resume_dir.glob(f"{filename.rsplit('.', 1)[0]}*.pdf"))
                    for pdf_file in pdf_files:
                        os.remove(pdf_file)
                        click.echo(f"Also deleted PDF: {pdf_file.name}")
                    
                    # If this was the last version, remove the directory
                    remaining_files = [f for f in resume_dir.iterdir() if f.is_file() and f.suffix == '.md']
                    if not remaining_files:
                        import shutil
                        shutil.rmtree(resume_dir)
                        click.echo(f"Removed empty resume directory for {resume_info['title']}")
                else:
                    self.show_error("Resume file not found")
            except Exception as e:
                self.show_error(f"Failed to delete resume: {e}")
    
    def _delete_all_resume_versions(self, resume_info) -> None:
        """Delete all versions of a resume."""
        confirm_msg = f"Delete ALL resume versions for {resume_info['title']}? This cannot be undone."
        
        if self.confirm_action(confirm_msg):
            try:
                import shutil
                resume_dir = self.fs.profile_path / "resumes" / resume_info['job_id']
                
                if resume_dir.exists():
                    shutil.rmtree(resume_dir)
                    self.show_success(f"Deleted all resume versions for: {resume_info['title']}")
                else:
                    self.show_error("Resume directory not found")
            except Exception as e:
                self.show_error(f"Failed to delete resumes: {e}")
    
    def show_saved_resumes(self) -> None:
        """Show all saved resumes (read-only display)."""
        resumes_path = self.fs.profile_path / "resumes"
        
        if not resumes_path.exists():
            click.echo("No saved resumes found")
            self.wait_for_user()
            return
        
        resume_dirs = [d for d in resumes_path.iterdir() if d.is_dir()]
        if not resume_dirs:
            click.echo("No saved resumes found")
            self.wait_for_user()
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
        
        self.wait_for_user()


class ExportManager(MenuController):
    """Handles PDF export operations."""
    
    def export_interactive(self, job_id: Optional[str] = None) -> None:
        """Interactive PDF export."""
        if not job_id:
            # Let user select job
            postings = self.fs.list_job_postings()
            if not postings:
                click.echo("No job postings with resumes found.")
                self.wait_for_user()
                return
            
            # Filter to only postings with resumes
            postings_with_resumes = []
            for posting in postings:
                if self.fs.get_latest_resume_path(posting.id):
                    postings_with_resumes.append(posting)
            
            if not postings_with_resumes:
                click.echo("No resumes found to export.")
                self.wait_for_user()
                return
            
            selected_posting = ListSelector.select_from_list(
                postings_with_resumes,
                "Select resume to export:",
                lambda p: f"{p.title} at {p.company}"
            )
            
            if not selected_posting or selected_posting == BACK_SIGNAL:
                return
            
            job_id = selected_posting.id
        
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
            return
        
        # Export to PDF with filename matching resume markdown
        resume_path = self.fs.get_resume_version(job_id)
        if not resume_path or not resume_path.exists():
            self.show_error(f"No resume found for job ID: {job_id}")
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
            if not self.confirm_action("Do you want to regenerate it?", default=False):
                click.echo(f"✓ Using existing PDF: {existing_pdf}")
                self.wait_for_user()
                return
        
        self._export_resume_to_pdf(job_id, template, str(output_path), pdf_metadata, resume_filename)
        self.wait_for_user()
    
    def _export_resume_to_pdf(self, job_id: str, template: str, output: str, pdf_metadata=None, resume_filename: str = None) -> None:
        """Export a resume to PDF."""
        from pathlib import Path
        from ..pdf import PDFGenerator
        
        # Load the resume content
        resume_path = self.fs.get_resume_version(job_id)
        
        if not resume_path or not resume_path.exists():
            self.show_error(f"No resume found for job ID: {job_id}")
            return
        
        # Create PDF generator
        pdf_gen = PDFGenerator()
        
        # Check if template is valid
        available_templates = pdf_gen.get_available_templates()
        if template not in available_templates:
            self.show_error(f"Invalid template '{template}'. Available: {', '.join(available_templates)}")
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
            self.show_error(f"Error generating PDF: {e}")