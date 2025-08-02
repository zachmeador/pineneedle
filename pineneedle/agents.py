"""Pydantic-AI agents for Pineneedle."""

import os
from pathlib import Path
from typing import Any

import logfire
from dotenv import load_dotenv
from pydantic_ai import Agent, ModelRetry, RunContext

from .models import (
    JobPosting,
    JobPostingContent,
    ModelConfig,
    ResumeContent,
    ResumeDeps,
    UserBackground,
)

# Load environment variables at module import
load_dotenv()

# Configure logfire for local file logging only
from pathlib import Path
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)
logfire.configure(
    send_to_logfire=False,
    console=False
)
logfire.instrument_pydantic_ai()

def create_model_string(config: ModelConfig) -> str:
    """Create model string for pydantic-ai from config."""
    return f"{config.provider}:{config.model_name}"

def get_default_model_string() -> str:
    """Get default model string from environment variables."""
    provider = os.getenv("PINENEEDLE_DEFAULT_PROVIDER", "openai")
    model_name = os.getenv("PINENEEDLE_DEFAULT_MODEL", "gpt-4o")
    return f"{provider}:{model_name}"

# System prompts
JOB_PARSER_SYSTEM_PROMPT = """You are an expert at parsing job postings and extracting comprehensive structured information for resume optimization.

Your task is to analyze the raw job posting content and extract:

1. **Job title and company name** - Extract exactly as stated
2. **Location** - Include if mentioned, even if remote/hybrid
3. **Comprehensive requirements** - Extract ALL requirements including technical skills, experience, education, certifications
4. **Detailed responsibilities** - Preserve technical depth and specificity
5. **Comprehensive keywords** - Extract technical and business terms
6. **Pay information** - Extract salary/compensation details or null
7. **Industry** - Determine the specific industry/sector this role is in. Be as specific as possible rather than using broad categories. Examples: "Financial Technology (FinTech)", "Enterprise Software", "Healthcare IT", "E-commerce", "Cloud Infrastructure", "Cybersecurity", "Management Consulting", "Investment Banking", "Pharmaceuticals", "Medical Devices", "Automotive Manufacturing", "Renewable Energy", "Real Estate Technology", "Educational Technology", etc.
8. **Practical description** - Provide an honest breakdown of how someone in this role would actually spend their time, rank-ordered by cumulative percentage of time spent. AVOID ALL corporate buzzwords, MBA-speak, and HR jargon. Be specific about the actual activities IN THAT SPECIFIC INDUSTRY. Tailor the activities to the industry context. Examples:
   - For agribusiness data scientist: "30% - Cleaning sensor data from farms (soil, weather, irrigation), 25% - Building crop yield prediction models, 20% - Creating reports for farmers and agronomists, 15% - Field visits to validate predictions, 10% - Meetings with agricultural engineers"
   - For fintech software dev: "45% - Writing code for payment processing systems, 25% - Debugging transaction failures and security issues, 15% - Regulatory compliance meetings and documentation, 10% - Code reviews focused on financial accuracy, 5% - Learning about banking regulations"
   - For healthcare consulting: "35% - Building Excel models of patient flow and costs, 30% - Meetings with hospital administrators, 20% - Analyzing clinical data and outcomes, 10% - Creating PowerPoints for C-suite presentations, 5% - Site visits to medical facilities"

Guidelines:
- Be exhaustive in extraction - don't summarize or condense
- Preserve technical precision and industry-specific language
- Extract implicit requirements from job descriptions
- Consider both hard and soft requirements
- For industry classification, be specific but concise
- For practical description, strip away ALL corporate speak and buzzwords - describe the actual work in plain English as if explaining to a friend what you'd be doing at your desk each day"""

RESUME_GENERATOR_SYSTEM_PROMPT = """You are an expert resume writer who creates tailored resumes for specific job postings.

Your task is to generate a professional resume that:
1. Follows the template structure exactly as defined in the template schema
2. Tailors content specifically to the job posting requirements
3. Uses the user's background information effectively
4. Matches the tone and style appropriate for the role
5. Emphasizes relevant skills and experiences
6. Uses strong action verbs and quantifiable achievements where possible

CRITICAL INSTRUCTIONS:
- Use the get_template_structure tool to understand the exact template format and requirements
- Each required section must be present with the specified format (e.g., "## Summary", "## Experience")
- Ensure each section meets the minimum length requirements defined in the schema
- Follow the placeholder structure exactly as shown in the template content
- Optional sections should only be included if relevant and beneficial

Guidelines:
- Extract and emphasize skills that match the job requirements
- Reorganize experience to highlight the most relevant positions first
- Use keywords from the job posting naturally throughout the resume
- Adapt the language style to match the company's tone
- Keep the resume concise but comprehensive
- Focus on achievements and impact, not just duties

If user feedback is provided, incorporate those specific changes and improvements."""




# Module-level agents - using environment variables for defaults
job_parser_agent = Agent(
    get_default_model_string(),
    output_type=JobPostingContent,
    system_prompt=JOB_PARSER_SYSTEM_PROMPT,
    retries=3
)

# Resume generator with deps and tools
resume_generator = Agent(
    get_default_model_string(),
    deps_type=ResumeDeps,
    output_type=ResumeContent,
    system_prompt=RESUME_GENERATOR_SYSTEM_PROMPT,
    retries=3
)

# Tools for resume generator
@resume_generator.tool
async def load_user_background(ctx: RunContext[ResumeDeps]) -> UserBackground:
    """Load user background information from markdown files."""
    return ctx.deps.user_background


@resume_generator.tool
async def get_job_requirements(ctx: RunContext[ResumeDeps]) -> dict[str, Any]:
    """Get the job posting requirements and details."""
    job = ctx.deps.job_posting
    return {
        "title": job.title,
        "company": job.company,
        "requirements": job.requirements,
        "responsibilities": job.responsibilities,
        "keywords": job.keywords,
        "pay": job.pay,
        "industry": job.industry,
        "practical_description": job.practical_description,
    }

@resume_generator.tool
async def get_tone_guidance(ctx: RunContext[ResumeDeps]) -> str:
    """Get tone and style guidance for the resume."""
    if ctx.deps.tone:
        return f"Use a {ctx.deps.tone} tone throughout the resume."
    
    return "Use a professional, standard tone."

@resume_generator.tool
async def get_feedback_context(ctx: RunContext[ResumeDeps]) -> str:
    """Get any user feedback for revision."""
    if ctx.deps.user_feedback:
        return f"User feedback to incorporate: {ctx.deps.user_feedback}"
    return "No specific feedback provided - create the best possible resume."

@resume_generator.tool
async def get_template_structure(ctx: RunContext[ResumeDeps]) -> dict[str, Any]:
    """Get the template structure, sections, and validation requirements."""
    template = ctx.deps.template
    return {
        "template_name": template.name,
        "template_content": template.content,
        "required_sections": [
            {
                "name": section.name,
                "display_name": section.display_name,
                "format": section.format,
                "description": section.description,
                "min_length": section.min_length,
                "max_length": section.max_length
            }
            for section in template.template_schema.get_required_sections()
        ],
        "optional_sections": [
            {
                "name": section.name,
                "display_name": section.display_name,
                "format": section.format,
                "description": section.description,
                "min_length": section.min_length,
                "max_length": section.max_length
            }
            for section in template.template_schema.get_optional_sections()
        ],
        "placeholders": template.template_schema.placeholders,
        "instructions": f"Generate resume content that exactly matches the template structure. Each required section must be present with the specified format. Template content: {template.content}"
    }

@resume_generator.output_validator
async def validate_resume_completeness(ctx: RunContext[ResumeDeps], content: ResumeContent) -> ResumeContent:
    """Validate that the generated resume follows the template schema requirements."""
    logfire.info("Starting schema-driven resume validation", resume_length=len(content.resume_markdown))
    
    template = ctx.deps.template
    schema = template.template_schema
    
    if len(content.resume_markdown.strip()) < 100:
        logfire.warning("Resume too short", length=len(content.resume_markdown.strip()))
        raise ModelRetry("Resume is too short, please provide more detailed content")
    
    # Extract sections based on schema
    lines = content.resume_markdown.split('\n')
    extracted_sections = {}
    current_section = None
    current_content = []
    
    for line in lines:
        line_stripped = line.strip()
        
        # Check if this line starts a new section
        section_found = None
        for section in schema.sections:
            # Try different format variations for flexibility
            expected_formats = [
                section.format,
                f"#{section.format[1:]}",  # Convert ## to #
                f"##{section.display_name}",
                f"# {section.display_name}"
            ]
            
            for fmt in expected_formats:
                if line_stripped.lower() == fmt.lower():
                    section_found = section.name
                    logfire.info("Found section", section=section.name, line=line_stripped)
                    break
            if section_found:
                break
        
        if section_found:
            # Save previous section if exists
            if current_section and current_content:
                extracted_sections[current_section] = '\n'.join(current_content).strip()
            
            current_section = section_found
            current_content = []
        elif current_section and line_stripped:
            current_content.append(line_stripped)
    
    # Save last section
    if current_section and current_content:
        extracted_sections[current_section] = '\n'.join(current_content).strip()
    
    logfire.info("Extracted sections", sections=list(extracted_sections.keys()))
    
    # Validate required sections
    missing_sections = []
    for section in schema.get_required_sections():
        if section.name not in extracted_sections:
            missing_sections.append(section.display_name)
        else:
            content_text = extracted_sections[section.name]
            if len(content_text) < section.min_length:
                logfire.warning("Section too short", 
                    section=section.name, 
                    length=len(content_text), 
                    min_required=section.min_length,
                    content=content_text[:100]
                )
                raise ModelRetry(f"Section '{section.display_name}' is too brief (minimum {section.min_length} characters). Please provide more detailed content for this section.")
    
    if missing_sections:
        logfire.warning("Missing required sections", missing=missing_sections)
        raise ModelRetry(f"Missing required sections: {', '.join(missing_sections)}. Please include all required sections with the correct format.")
    
    # Store extracted sections in content object
    content.sections = extracted_sections
    
    logfire.info("Resume validation passed", sections_found=len(extracted_sections))
    return content



# Simplified API functions
async def parse_job_posting(raw_content: str, model_config: ModelConfig, job_id: str | None = None) -> JobPosting:
    """Parse raw job posting content into structured data."""
    # Check API key availability
    if model_config.provider == "openai" and not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY environment variable is required for OpenAI models.")
    elif model_config.provider == "anthropic" and not os.getenv("ANTHROPIC_API_KEY"):
        raise ValueError("ANTHROPIC_API_KEY environment variable is required for Anthropic models.")
    
    model_str = create_model_string(model_config)
    
    result = await job_parser_agent.run(
        f"Parse this job posting:\n\n{raw_content}",
        model=model_str,
        model_settings={"temperature": model_config.temperature}
    )
    
    # System creates the full JobPosting with metadata
    from datetime import datetime
    posting_id = job_id or datetime.now().strftime("%Y%m%d%H%M%S")
    created_at = datetime.now().isoformat()
    
    return JobPosting.from_content(
        result.output, 
        posting_id, 
        created_at, 
        model_config.provider, 
        model_config.model_name,
        raw_content  # Pass original raw content directly
    )


async def generate_resume(deps: ResumeDeps, model_config: ModelConfig) -> ResumeContent:
    """Generate a tailored resume."""
    # Check API key availability
    if model_config.provider == "openai" and not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY environment variable is required for OpenAI models.")
    elif model_config.provider == "anthropic" and not os.getenv("ANTHROPIC_API_KEY"):
        raise ValueError("ANTHROPIC_API_KEY environment variable is required for Anthropic models.")
    
    model_str = create_model_string(model_config)
    
    result = await resume_generator.run(
        "Generate a tailored resume for this job posting using the user's background and template.",
        deps=deps,
        model=model_str,
        model_settings={"temperature": model_config.temperature}
    )
    
    return result.output


 