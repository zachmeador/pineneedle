# Pineneedle Design Document

## Vision
Pineneedle is a CLI application that transforms the tedious process of resume writing into an intelligent, automated workflow. Users provide their background information once and can generate tailored resumes for specific job postings using LLMs.

## Core Philosophy
- **Simplicity First**: Leverage pydantic-ai's clean primitives to keep the codebase minimal and maintainable
- **Type Safety**: Use Pydantic models throughout for robust data validation
- **Agent-Oriented**: Build specialized agents for different domains rather than monolithic functions
- **Local-First**: Store everything in human-readable formats (JSON/Markdown) alongside user's content

## High-Level Architecture

### Core Agents (Pydantic-AI)

#### 1. Job Posting Parser Agent
Transforms raw job posting text into structured data with comprehensive analysis including requirements, responsibilities, industry classification, and practical job descriptions.

#### 2. Resume Generator Agent
Generates tailored resumes using user background, job requirements, and resume templates. Includes tools for loading background data, templates, and job context.

#### 3. Feedback Handler Agent  
Processes user feedback and generates specific revision instructions for iterative resume improvement.

### Core Data Models

```python
# User's background information
class UserBackground(BaseModel):
    experience_md: str
    education_md: str
    contact_md: str
    reference_md: str

# Structured job posting data
class JobPosting(BaseModel):
    id: str
    title: str
    company: str
    location: str | None
    requirements: list[str]
    responsibilities: list[str]
    keywords: list[str]
    tone_reasoning: str
    pay: str | None
    industry: str
    practical_description: str
    created_at: str
    raw_content: str
    model_provider: str
    model_name: str

# Generated resume content
class ResumeContent(BaseModel):
    resume_markdown: str
    summary: str

# Profile-specific configuration
class ProfileConfig(BaseModel):
    display_name: str
    description: str
    created_at: str
    preferred_model: ModelConfig | None  # Overrides global defaults
    default_tone: str | None
    default_template: str

# Application configuration
class PineneedleConfig(BaseModel):
    default_model: ModelConfig
    workspace_path: Path
    current_profile: str
    profiles: dict[str, ProfileInfo]
```

### Multi-Profile System

Pineneedle supports multiple profiles for different career paths or specializations:
- Each profile has separate background files, job postings, and resumes
- Each profile has its own `config.json` with profile-specific settings
- Profiles are managed through CLI commands or interactive TUI
- Default profile created automatically on initialization

#### Configuration Hierarchy

**Global Configuration (`data/config.json`)**:
- Default model settings (provider, model name, temperature)
- Current active profile
- Profile metadata registry
- Data directory path
- Workspace path

**Profile Configuration (`data/profiles/{name}/config.json`)**:
- Profile display name and description
- Profile-specific model preferences (overrides global defaults)
- Default tone for resume generation
- Default template name
- Creation timestamp

### Directory Structure
```
project_root/
├── data/                     # All user data
│   ├── config.json          # Global configuration
│   └── profiles/
│       └── {profile_name}/
│           ├── config.json  # Profile-specific configuration
│           ├── background/
│           │   ├── experience.md
│           │   ├── education.md
│           │   ├── contact.md
│           │   └── reference.md
│           ├── templates/
│           │   └── default.md
│           ├── job_postings/
│           │   └── {id}_{company}_{title}_{location}.json
│           └── resumes/
│               └── {job_id}/
│                   ├── {timestamp}_metadata.json
│                   ├── {timestamp}_resume.md
│                   └── latest_*.* (latest versions)
├── pineneedle/               # Application code
├── example_data/             # Example background files
└── pyproject.toml
```

## Interface Design

### CLI Commands
```bash
pineneedle                    # Start interactive TUI
pineneedle init               # Initialize workspace
pineneedle job add            # Add job posting (interactive or file)
pineneedle job list           # List all job postings
pineneedle generate <job_id>  # Generate resume
pineneedle export <job_id>    # Export to PDF

pineneedle profile list       # Manage profiles
```

### Interactive TUI
Terminal user interface providing guided workflows for:
- Adding job postings
- Generating resumes
- Managing profiles
- Exporting PDFs
- Viewing archives

## Service Layer

### FileSystemService
Handles all file operations including:
- Profile management and switching
- Loading/saving job postings and resumes
- Resume versioning with timestamps
- Configuration management
- Background data loading

### PDFGenerator
Converts markdown resumes to formatted PDFs using templates and WeasyPrint.

## Key Features

### Job Analysis
- Comprehensive requirement extraction
- Industry classification
- Practical job description (strips corporate jargon)
- Tone analysis for resume matching

### Resume Generation
- Template-based structure
- Keyword optimization
- Content tailoring to job requirements
- Multiple model support (OpenAI, Anthropic)

### Iterative Improvement
- User feedback processing
- Multiple resume versions
- Timestamp-based versioning

### Export Options
- PDF generation with professional templates
- Multiple output formats

## Dependencies
- **pydantic-ai**: Agent framework and LLM integration
- **click**: CLI interface
- **questionary**: Interactive TUI components
- **weasyprint**: PDF generation
- **openai/anthropic**: LLM providers

## Implementation Status
✅ All core functionality implemented  
✅ Multi-profile system  
✅ Interactive TUI  
✅ PDF export  
✅ Resume versioning  
✅ Comprehensive job analysis 