"""Core Pydantic models for Pineneedle."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel


class UserBackground(BaseModel):
    """Raw markdown content from user's background files."""
    experience_md: str
    education_md: str  
    contact_md: str
    reference_md: str


class JobPostingContent(BaseModel):
    """Content extracted from job posting by LLM - no system metadata."""
    title: str
    company: str
    location: str | None
    requirements: list[str]
    responsibilities: list[str]
    keywords: list[str]
    tone_reasoning: str  # Clinical analysis of language patterns and communication style
    pay: str | None  # Salary information (range or single figure)
    industry: str  # Approximation of what industry this role is in
    practical_description: str  # What the job would actually entail in practice, not HR speak


class JobPosting(BaseModel):
    """Complete job posting with system metadata."""
    id: str  # System-generated numeric timestamp
    title: str
    company: str
    location: str | None
    requirements: list[str]
    responsibilities: list[str]
    keywords: list[str]
    tone_reasoning: str
    pay: str | None
    industry: str  # Approximation of what industry this role is in
    practical_description: str  # What the job would actually entail in practice, not HR speak
    created_at: str  # ISO format datetime when posting was added
    raw_content: str
    model_provider: str = "unknown"  # Provider used to parse this posting (e.g., "openai", "anthropic")
    model_name: str = "unknown"  # Model name used to parse this posting (e.g., "gpt-4o", "claude-3-5-sonnet-20241022")
    
    @classmethod
    def from_content(cls, content: JobPostingContent, id: str, created_at: str, model_provider: str, model_name: str, raw_content: str) -> 'JobPosting':
        """Create JobPosting from LLM content and system metadata."""
        return cls(
            id=id,
            title=content.title,
            company=content.company,
            location=content.location,
            requirements=content.requirements,
            responsibilities=content.responsibilities,
            keywords=content.keywords,
            tone_reasoning=content.tone_reasoning,
            pay=content.pay,
            industry=content.industry,
            practical_description=content.practical_description,
            created_at=created_at,
            raw_content=raw_content,
            model_provider=model_provider,
            model_name=model_name,
        )


class ModelConfig(BaseModel):
    """Configuration for LLM model."""
    provider: str = "openai"
    model_name: str = "gpt-4o"
    temperature: float = 0.7


class GenerationRequest(BaseModel):
    """Parameters for a resume generation request."""
    job_posting_id: str
    tone: str | None = None
    llm_config: ModelConfig | None = None
    user_feedback: str | None = None


class ResumeContent(BaseModel):
    """Generated resume content."""
    resume_markdown: str
    summary: str = ""  # Will be extracted for validation


class FeedbackResult(BaseModel):
    """Result of processing user feedback."""
    revised_prompt: str
    specific_changes: list[str]


class PineneedleConfig(BaseModel):
    """Application configuration."""
    default_model: ModelConfig = ModelConfig()
    workspace_path: Path = Path.cwd()
    
    class Config:
        arbitrary_types_allowed = True
    
    @classmethod
    def load(cls, config_path: Path | None = None) -> 'PineneedleConfig':
        """Load configuration from file with defaults."""
        import os
        
        # Start with defaults, potentially overridden by environment variables
        default_model = ModelConfig(
            provider=os.getenv("PINENEEDLE_DEFAULT_PROVIDER", "openai"),
            model_name=os.getenv("PINENEEDLE_DEFAULT_MODEL", "gpt-4o"),
            temperature=float(os.getenv("PINENEEDLE_DEFAULT_TEMPERATURE", "0.7"))
        )
        
        # If no config_path provided, try to find it in the data directory
        if config_path is None:
            data_dir_env = os.getenv("PINENEEDLE_DATA_DIR")
            if data_dir_env:
                data_path = Path(data_dir_env).expanduser().resolve()
                config_path = data_path / "config.json"
            else:
                config_path = Path.cwd() / "data" / "config.json"
        
        if config_path and config_path.exists():
            import json
            data = json.loads(config_path.read_text())
            # Override with file settings if they exist
            if 'default_model' not in data:
                data['default_model'] = default_model.model_dump()
            return cls.model_validate(data)
        
        return cls(default_model=default_model, workspace_path=Path.cwd())


class ResumeArchive(BaseModel):
    """Archived resume generation with full metadata."""
    job_posting_id: str
    job_posting: JobPosting
    generation_request: GenerationRequest
    resume_content: ResumeContent
    created_at: str
    model_used: ModelConfig
    iteration_count: int = 1


@dataclass
class ResumeDeps:
    """Dependencies for resume generation agent."""
    job_posting: JobPosting
    user_background: UserBackground
    template: str
    tone: str | None
    user_feedback: str | None 