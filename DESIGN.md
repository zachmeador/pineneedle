# Pineneedle Design Document

## Vision
Pineneedle is a CLI application that transforms the tedious process of resume writing into an intelligent, automated workflow. Users provide their background information once and can generate tailored resumes for specific job postings using LLMs.

## Core Philosophy
- **Simplicity First**: Leverage pydantic-ai's clean primitives to keep the codebase minimal and maintainable
- **Type Safety**: Use Pydantic models throughout for robust data validation
- **Agent-Oriented**: Build specialized agents for different domains rather than monolithic functions
- **Local-First**: Store everything in human-readable formats (JSON/Markdown) alongside user's content

## High-Level Architecture

### Core Agents (Pydantic-AI Primitives)

#### 1. Job Posting Parser Agent
**Purpose**: Transform raw job posting HTML/text into structured data
```python
class JobPosting(BaseModel):
    title: str
    company: str
    location: str | None
    requirements: list[str]
    responsibilities: list[str]
    keywords: list[str]
    tone_reasoning: str  # Clinical analysis of language patterns and communication style
    raw_content: str

parser_agent = Agent(
    model='openai:gpt-4o',
    output_type=JobPosting,
    system_prompt="Extract structured information from job postings..."
)
```

#### 2. Resume Generator Agent
**Purpose**: Generate tailored resumes based on job postings and user background
```python
class ResumeContent(BaseModel):
    resume_markdown: str

@dataclass
class ResumeDeps:
    job_posting: JobPosting
    user_background: UserBackground
    template: str  # Example resume structure
    tone: str | None
    user_feedback: str | None  # for iteration

resume_agent = Agent(
    model='openai:gpt-4o', 
    deps_type=ResumeDeps,
    output_type=ResumeContent,
    system_prompt="Generate resume following template structure..."
)
```

#### 3. Feedback Handler Agent  
**Purpose**: Process user feedback and generate improvement instructions
```python
class FeedbackResult(BaseModel):
    revised_prompt: str
    specific_changes: list[str]
    
feedback_agent = Agent(
    model='openai:gpt-4o',
    output_type=FeedbackResult,
    system_prompt="Analyze user feedback and provide specific revision instructions..."
)
```

### Data Models (Pydantic Schemas)

```python
class UserBackground(BaseModel):
    """Raw markdown content from user's background files"""
    experience_md: str
    education_md: str
    contact_md: str
    reference_md: str

class GenerationRequest(BaseModel):
    """Parameters for a resume generation request"""
    job_posting_id: str
    tone: str | None = None
    model_config: ModelConfig | None = None
    user_feedback: str | None = None

class ModelConfig(BaseModel):
    provider: str = "openai"
    model_name: str = "gpt-4o"
    temperature: float = 0.7
```

### Tools (Agent Capabilities)

#### File System Tools
```python
@resume_agent.tool
async def load_user_background(ctx: RunContext[ResumeDeps]) -> UserBackground:
    """Load raw markdown files as-is - let LLM interpret and extract skills/projects"""
    experience_md = read_file("background/experience.md")
    education_md = read_file("background/education.md") 
    contact_md = read_file("background/contact.md")
    reference_md = read_file("background/reference.md")
    
    return UserBackground(
        experience_md=experience_md,
        education_md=education_md,
        contact_md=contact_md,
        reference_md=reference_md
    )

@resume_agent.tool
async def load_template(ctx: RunContext[ResumeDeps]) -> str:
    """Load markdown template that defines resume structure"""
    return read_file("templates/default.md")

@resume_agent.tool  
async def save_resume_archive(ctx: RunContext[ResumeDeps], content: ResumeContent) -> str:
    """Save generated resume to archive with metadata"""
    pass
```

#### PDF Generation Tool
```python
@resume_agent.tool
async def generate_pdf(ctx: RunContext[ResumeDeps], content: ResumeContent) -> str:
    """Convert resume content to PDF using markdown template"""
    pass
```

## Template System

Templates are simple markdown files showing resume structure. The LLM follows this structure when generating content.

### Default Template Example
```markdown
# John Doe
john@email.com | (555) 123-4567 | City, State

## Summary
Brief professional summary...

## Experience
### Job Title - Company (Dates)
- Achievement bullet points

## Education
### Degree - School (Year)

## Skills
- Relevant skills
```

Users can modify the default template or create new ones.

## Directory Structure
```
project_root/
├── data/                     # All user data organized separately
│   ├── background/
│   │   ├── experience.md
│   │   ├── education.md
│   │   ├── contact.md
│   │   └── reference.md
│   ├── templates/
│   │   └── default.md
│   ├── job_postings/
│   │   └── {posting_id}.json
│   ├── resumes/
│   │   └── {posting_id}/
│   │       ├── {timestamp}_metadata.json
│   │       ├── {timestamp}_resume.md
│   │       ├── latest_metadata.json      # Latest version symlink
│   │       └── latest_resume.md          # Latest version symlink
│   ├── config.json
│   └── .env                  # Optional: env file in data dir
├── pineneedle/               # Application code
├── pyproject.toml
├── DESIGN.md
├── THOUGHTS.md
└── .env                      # Environment variables (fallback)
```

## CLI Interface Design

### Commands
```bash
# Initialize workspace
pineneedle init

# Add job posting
pineneedle job add "paste job posting here"
pineneedle job add --file job.html
pineneedle job list

# Generate resume
pineneedle generate <job_id>
pineneedle generate <job_id> --tone casual
pineneedle generate <job_id> --model anthropic:claude-3-sonnet

# Interactive iteration
pineneedle iterate <job_id>  # Opens interactive feedback loop

# Archive management  
pineneedle archive list
pineneedle archive show <job_id>
```

### Interactive Flow
```python
# Example of iteration flow
while True:
    resume = await resume_agent.run(generation_request, deps=deps)
    print_resume(resume)
    
    feedback = input("Feedback (or 'done'): ")
    if feedback.lower() == 'done':
        break
        
    feedback_result = await feedback_agent.run(feedback)
    generation_request.user_feedback = feedback_result.revised_prompt
```

## Configuration Management

```python
class PineneedleConfig(BaseModel):
    """Application configuration"""
    default_model: ModelConfig
    workspace_path: Path
    
    @classmethod
    def load(cls) -> 'PineneedleConfig':
        # Load from config.json with defaults
        pass
```

## Dependencies & Architecture

### Dependency Injection Pattern
```python
@dataclass 
class AppDependencies:
    config: PineneedleConfig
    file_system: FileSystemService
    pdf_generator: PDFGenerator
    llm_provider: LLMProvider

# Agents receive clean, testable dependencies
agents = create_agents(deps=AppDependencies(...))
```

### Service Layer
```python
class FileSystemService:
    """Handles all file operations"""
    def load_background(self, workspace: Path) -> UserBackground: ...
    def save_job_posting(self, posting: JobPosting) -> str: ...
    def archive_resume(self, job_id: str, resume: ResumeContent) -> None: ...

class PDFGenerator:
    """Converts markdown to PDF"""
    def generate(self, content: str, template: str) -> bytes: ...
```

## Error Handling & Retry Strategy

```python
# Built into pydantic-ai agents
parser_agent = Agent(
    model='openai:gpt-4o',
    retries=3,  # Automatic retries for transient failures
    output_type=JobPosting  # Automatic retry if validation fails
)

# Custom validation with helpful errors
@resume_agent.output_validator
async def validate_resume_completeness(ctx: RunContext[ResumeDeps], content: ResumeContent) -> ResumeContent:
    if len(content.summary) < 50:
        raise ModelRetry("Summary too short, please provide more detail")
    return content
```

## Why This Architecture?

### Built on Pydantic-AI Strengths
- **Agent Specialization**: Each agent has a clear, single responsibility
- **Type Safety**: Pydantic models ensure data integrity throughout the pipeline
- **Dependency Injection**: Clean separation of concerns, easy testing
- **Tool Composition**: Reusable tools can be shared across agents
- **Structured Output**: LLM responses are automatically validated and retried

### Simplicity Benefits
- **No Complex Orchestration**: Agents call each other through simple tool functions
- **Local State**: Everything stored in JSON/Markdown, no databases needed
- **Minimal Dependencies**: Lean on pydantic-ai's built-in capabilities
- **Easy Testing**: Mock dependencies and test individual agents

### Extensibility
- **New Models**: Easy to swap LLM providers through configuration
- **New Features**: Add new agents or tools without changing existing code
- **Templates**: Support multiple resume formats through templating
- **Integrations**: Add new tools for LinkedIn parsing, ATS optimization, etc.

## Implementation Phases

### Phase 1: Core MVP
1. Basic agent setup with structured models
2. Job posting parser
3. Simple resume generator
4. File system operations
5. Basic CLI commands

### Phase 2: Polish
1. PDF generation
2. Interactive iteration
3. Archive management
4. Configuration system
5. Error handling improvements

### Phase 3: Enhancement
1. Multiple resume templates
2. Additional LLM providers
3. Performance optimizations
4. Advanced CLI features
5. User experience improvements 