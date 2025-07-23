# Pineneedle Design Document

## Overview
Pineneedle is an intelligent resume management system that leverages LLMs to create tailored resumes for specific job applications. The system maintains structured content in markdown files and uses AI to analyze job requirements and customize resume content accordingly.

## User Flows

### 1. Initial Setup Flow
```
User starts → Initialize directory → Create base markdown files → User edits content → Ready for resume generation
```

**CLI Example:**
```bash
# Initialize new pineneedle workspace
pineneedle init

# Or initialize with basic content templates
pineneedle init --with-examples
```

**Steps:**
1. **Initialize workspace**: Create `.data/` directory structure with base content markdown files
2. **Generate base content templates**:
   - `personal.md` - Contact info and professional summary template
   - `experience.md` - Work history, achievements, and personal projects template
   - `education.md` - Degrees, certifications, courses template
   - `skills.md` - Technical and soft skills template
3. **Setup tone library**: Create initial tone configurations in `.data/tones/`
4. **User edits content**: User directly edits markdown files to add their actual information

### 2. Job-Specific Resume Generation Flow
```
Job posting input → Store job posting → LLM analyzes content → Generate tailored resume → PDF export → Render storage
```

**CLI Example:**
```bash
# Store job posting from clipboard/paste
pineneedle store-job
# Opens editor where user pastes job posting text
# LLM extracts metadata and stores as job_posting_abc123.json

# Generate resume for stored job posting
pineneedle render job_posting_abc123 --tone technical_professional

# Generate resume with custom tone
pineneedle render job_posting_abc123 --tone "Write in a creative, engaging style"

# List available job postings
pineneedle list-jobs

# List available tones
pineneedle list-tones
```

**Steps:**

#### 1. Job Input & Validation
**Input Methods:**
- **Job posting text**: User pastes full job description from job board. 

**Processing:**
- Validate input is non-empty and contains meaningful content
- Store raw input for archival
- Extract basic metadata if possible (company name, position title)

**Output:** `JobPosting` object with raw_text populated

#### 2. Job Analysis & Requirements Extraction
**LLM Prompt:** "Analyze this job posting and extract structured requirements"

**Analysis Tasks:**
- **Company Context**: Industry, size, culture indicators, tech stack
- **Role Requirements**: 
  - Hard skills (programming languages, tools, certifications)
  - Soft skills (leadership, communication, collaboration)
  - Experience level (years, seniority expectations)
  - Specific responsibilities and duties
- **Keywords Extraction**: Important terms for ATS optimization
- **Priority Ranking**: Categorize requirements as "must-have" vs "nice-to-have"

**Output:** Enriched `JobPosting` object with structured analysis

#### 3. Content Library Loading & Parsing
**File Discovery:**
- Scan `.data/content/` directory for all markdown files
- Load and parse each file into `ContentSection` objects
- Validate markdown structure and extract metadata

**Content Structuring:**
- **Personal Info**: Contact details, professional summary, location preferences
- **Experience Entries**: For each job/project, extract:
  - Company, title, dates, responsibilities, achievements
  - Technologies used, quantifiable results
  - Keywords and industry terms
- **Education**: Degrees, certifications, relevant coursework
- **Skills**: Technical skills, soft skills, proficiency levels

**Output:** List of structured `ContentSection` objects

#### 4. Tone Configuration Selection
**Tone Discovery:**
- User selects from available tones in `.data/tones/` OR
- User provides custom tone instructions

**Tone Loading:**
- Parse selected tone TOML file
- Validate LLM provider and model availability
- Load tone instructions and formatting preferences

**Output:** `ToneConfiguration` object with provider/model settings

#### 5. Content Relevance Scoring & Selection
**LLM Prompt:** "Score each content piece for relevance to this job posting"

**Scoring Process:**
- **Experience Matching**: Score each job/project against requirements
  - Technology overlap (exact matches get highest scores)
  - Responsibility alignment (similar duties and scope)
  - Industry relevance (related domains)
  - Seniority level match
- **Skills Prioritization**: Rank skills by job relevance
  - Direct requirement matches (must-have skills)
  - Transferable skills (adjacent technologies)
  - Soft skills alignment
- **Education Relevance**: Score degrees/certs against job needs

**Selection Criteria:**
- Include all experience entries scoring >70% relevance
- Prioritize most recent and highest-scoring experiences
- Ensure skills section covers all job requirements
- Maintain chronological consistency

**Output:** `SelectedContent` object with scored and filtered content

#### 6. Content Customization & Optimization
**LLM Prompt:** "Rewrite selected content for this specific job using the specified tone"

**Customization Tasks:**
- **Responsibility Tailoring**: Rewrite job descriptions to emphasize relevant duties
- **Achievement Quantification**: Highlight metrics that align with role expectations
- **Keyword Integration**: Naturally incorporate job posting keywords
- **Tone Application**: Apply specified writing style and personality
- **ATS Optimization**: Ensure proper keyword density and formatting

**Quality Checks:**
- Verify all critical job requirements are addressed
- Ensure tone consistency across all sections
- Validate factual accuracy (no fabricated information)
- Check for appropriate length and format

**Output:** Customized content ready for resume assembly

#### 7. Resume Assembly & Generation
**Template Selection:**
- Choose appropriate resume template based on role/industry
- Apply formatting preferences from tone configuration

**Content Assembly:**
- **Header**: Personal info with contact details
- **Professional Summary**: Customized 2-3 sentence overview
- **Experience Section**: Selected and customized work history
- **Skills Section**: Prioritized and categorized skills
- **Education Section**: Relevant degrees and certifications
- **Optional Sections**: Projects, publications, awards (if relevant)

**Final Formatting:**
- Apply consistent styling and spacing
- Ensure ATS-friendly formatting
- Optimize for single-page layout (when possible)

**Output:** Complete resume in markdown format

#### 8. PDF Generation & Export
**Markdown to PDF Conversion:**
- Parse markdown using pandoc or similar tool
- Apply professional styling template
- Ensure proper page breaks and formatting
- Embed fonts for consistent rendering

**Quality Assurance:**
- Verify PDF readability and formatting
- Check for text overflow or layout issues
- Validate file size and compatibility

**Output:** Professional PDF file ready for submission

#### 9. Job Posting Storage & Render Archival
**Job Posting Storage:**
- Generate unique job posting ID if not already stored
- Save job posting to `.data/job_postings/{job_posting_id}.json`
- Include all extracted metadata and analysis results

**Render Directory Creation:**
- Create unique render directory: `.data/renders/render_{counter}_{company}_{position}/`
- Use incremental counter for render IDs to allow multiple renders per job

**File Storage:**
- Store generated markdown as `resume.md`
- Save PDF as `resume.pdf`
- Create `metadata.json` with render details and job posting reference

**Metadata Tracking:**
```json
{
  "id": "unique_render_id",
  "timestamp": "2024-01-15T10:30:00Z",
  "job_posting_id": "job_posting_abc123",
  "tone_used": {
    "name": "technical_professional",
    "provider": "openai",
    "model": "gpt-4"
  },
  "content_selected": {
    "experience_entries": ["job1", "job2", "project1"],
    "skills_included": ["Python", "React", "AWS"],
    "relevance_scores": {...}
  }
}
```

**Output:** Complete archived render with full traceability

#### 10. User Feedback & Iteration
**Review Interface:**
- Display generated resume for user review
- Show relevance scores and selection rationale
- Provide options for regeneration with different tone/settings

**Iteration Options:**
- **Quick fixes**: Minor edits without full regeneration
- **Tone adjustment**: Regenerate with different tone
- **Content modification**: Add/remove specific experiences
- **Format changes**: Different template or styling

**Output:** Final approved resume ready for job application

### 3. Render Management Flow
```
View render history → Compare versions → Manage tone library → Export/share
```

**CLI Example:**
```bash
# View all renders
pineneedle list-renders

# View renders for specific job posting
pineneedle list-renders --job job_posting_abc123

# Show details of a specific render
pineneedle show render_001_techcorp_senior_dev

# Copy render files to current directory
pineneedle export render_001_techcorp_senior_dev

# Delete a render
pineneedle delete render_001_techcorp_senior_dev
```

**Steps:**
1. **Browse renders**: View all generated resumes with metadata
2. **Compare versions**: Side-by-side comparison of different renders
3. **Tone management**: Edit, duplicate, or delete tone configurations
4. **Export options**: Download PDF, share link, or export source markdown

## High-Level Objects

### Core Data Objects

#### `ContentSection`
```python
class ContentSection:
    - file_path: str              # Path to markdown file
    - content_type: ContentType   # personal, experience, education, skills
    - raw_content: str           # Original markdown content
    - structured_data: dict      # Parsed content for programmatic access
    - last_modified: datetime    # Track changes
    - metadata: dict            # Additional properties
```

#### `ExperienceEntry`
```python
class ExperienceEntry:
    - company: str
    - position: str
    - start_date: date
    - end_date: Optional[date]
    - responsibilities: List[str]
    - achievements: List[str]
    - technologies: List[str]
    - keywords: List[str]        # For job matching
```

#### `ToneConfiguration`
```python
class ToneConfiguration:
    - name: str                  # "technical_professional", "creative_engaging", etc.
    - description: str           # Full tone instructions/prompt for LLM
    - model_provider: str        # "openai" or "anthropic"
    - model_name: str           # "gpt-4", "claude-3-sonnet", etc.
    - file_path: str            # Path to the .toml file
    - created_date: datetime    # When loaded/created
    - usage_count: int          # Track popularity
```

### Processing Objects

#### `LLMProvider`
```python
class LLMProvider:
    - provider_type: str        # "openai" or "anthropic"
    - api_key: str             # API credentials
    - base_url: str            # API endpoint
    - available_models: List[str]  # Models supported by this provider
    
    def chat_completion(messages, model) -> str
    def validate_model(model_name) -> bool
    def get_model_info(model_name) -> dict
```

#### `JobPosting`
```python
class JobPosting:
    - raw_text: str             # Original job posting
    - company: str
    - position: str
    - requirements: List[str]    # Extracted requirements
    - preferred_skills: List[str]
    - keywords: List[str]       # Important terms for matching
    - seniority_level: str      # Junior, mid, senior, etc.
    - industry: str             # Tech, finance, healthcare, etc.
    - analysis_metadata: dict   # LLM analysis results
```

#### `StoredJobPosting`
```python
class StoredJobPosting:
    - id: str                   # Unique identifier (e.g., "job_posting_abc123")
    - created_date: datetime    # When job posting was first stored
    - source: str               # "manual", "linkedin", "indeed", etc.
    - raw_text: str             # Original job posting text
    - company: str              # Extracted company name
    - position: str             # Job title
    - location: str             # Job location if available
    - requirements: List[str]    # Extracted requirements
    - preferred_skills: List[str]
    - keywords: List[str]       # Important terms for matching
    - seniority_level: str      # Junior, mid, senior, etc.
    - industry: str             # Tech, finance, healthcare, etc.
    - analysis_metadata: dict   # LLM analysis results
    - render_count: int         # Number of renders created for this posting
    - notes: str                # User-added notes about this opportunity
```

#### `ResumeRenderer`
```python
class ResumeRenderer:
    - content_manager: ContentManager    # Access to all markdown content
    - tone_config: ToneConfiguration
    - job_posting: JobPosting
    - template: ResumeTemplate
    - llm_provider: LLMProvider         # Provider specified by tone config
    
    def generate_tailored_resume() -> str  # LLM does content selection + rendering
    def render_pdf() -> bytes
    def save_render() -> RenderRecord
```

### Management Objects

#### `RenderRecord`
```python
class RenderRecord:
    - id: str                   # Unique identifier
    - created_date: datetime
    - job_posting_id: str       # Reference to StoredJobPosting
    - tone_used: ToneConfiguration
    - selected_content: SelectedContent
    - output_markdown: str
    - output_pdf_path: str
    - user_notes: str          # Manual annotations
```

#### `ContentManager`
```python
class ContentManager:
    - content_sections: List[ContentSection]
    - base_path: str           # .data/content/
    
    def load_all_content() -> List[ContentSection]
    def update_content(section, updates) -> ContentSection
    def validate_structure() -> List[ValidationError]
    def backup_content() -> str
```

#### `ToneLibrary`
```python
class ToneLibrary:
    - tones: List[ToneConfiguration]
    - base_path: str           # .data/tones/
    
    def load_tones() -> List[ToneConfiguration]
    def create_tone(config) -> ToneConfiguration
    def update_tone(id, updates) -> ToneConfiguration
    def suggest_tone(job_posting) -> ToneConfiguration
```

#### `JobPostingLibrary`
```python
class JobPostingLibrary:
    - job_postings: List[StoredJobPosting]
    - base_path: str           # .data/job_postings/
    
    def load_job_postings() -> List[StoredJobPosting]
    def store_job_posting(posting) -> StoredJobPosting
    def get_job_posting(id) -> StoredJobPosting
    def search_job_postings(query) -> List[StoredJobPosting]
    def delete_job_posting(id) -> bool
    def get_renders_for_posting(id) -> List[RenderRecord]
```

#### `LLMProviderManager`
```python
class LLMProviderManager:
    - providers: Dict[str, LLMProvider]  # provider_type -> provider instance
    - config_path: str                   # .env or config file
    
    def get_provider(provider_type) -> LLMProvider
    def validate_credentials() -> Dict[str, bool]
    def get_available_models() -> Dict[str, List[str]]
    def test_connection(provider_type) -> bool
```

## Data Architecture

### File Structure
```
.data/
├── content/
│   ├── personal.md
│   ├── experience.md          # includes both professional experience and personal projects
│   ├── education.md
│   └── skills.md
├── tones/
│   ├── technical_professional.toml    # includes model_provider + model_name + description
│   ├── technical_engaging.toml          # e.g., "anthropic" + "claude-4-sonnet" + tone prompt
├── job_postings/
│   ├── job_posting_abc123.json        # stored job posting with metadata
│   ├── job_posting_def456.json
│   └── job_posting_ghi789.json
└── renders/
    ├── render_001_techcorp_senior_dev/
    │   ├── metadata.json           # references job_posting_id
    │   ├── resume.md
    │   └── resume.pdf
    ├── render_002_techcorp_senior_dev/  # different render for same job posting
    │   ├── metadata.json
    │   ├── resume.md
    │   └── resume.pdf
    └── render_003_startup_fullstack/
        ├── metadata.json
        ├── resume.md
        └── resume.pdf
```

### Environment Configuration
```
.env
├── OPENAI_API_KEY=sk-...
├── ANTHROPIC_API_KEY=sk-ant-...
├── DEFAULT_PROVIDER=openai       # fallback if tone doesn't specify
└── DEFAULT_MODEL=gpt-4           # fallback model
```

### Integration Points

#### LLM Integration
- **Multi-provider support**: Both OpenAI and Anthropic APIs using ChatCompletions format
- **Model selection**: Each tone configuration specifies preferred provider and model
  - OpenAI models: `gpt-4`, `gpt-4-turbo`, `gpt-3.5-turbo`
  - Anthropic models: `claude-3-opus`, `claude-3-sonnet`, `claude-3-haiku`
- **Resume generation**: Job posting + all content files + tone → complete tailored resume
  - Intelligent content selection and prioritization
  - Tone application and style adaptation
  - Keyword optimization and industry-specific language
  - Context-aware customization for role and company
- **Fallback strategy**: Use default provider/model if tone config is incomplete or unavailable

#### PDF Generation
- **Template system**: Multiple professional layouts
- **Markdown processing**: Convert structured markdown to formatted PDF
- **Style management**: Consistent fonts, spacing, and formatting
- **Export options**: Different file formats and quality settings

## Future Considerations

### Model Selection Strategy
- **Creative/Marketing roles**: Claude models often excel at creative, engaging language
- **Technical roles**: GPT-4 may be better for technical precision and industry jargon
- **Executive/Leadership**: Consider model performance on formal, strategic language
- **Cost optimization**: Use cheaper models (GPT-3.5, Claude Haiku) for quick iterations/testing
- **Performance tracking**: Track which models produce better application success rates

### Extensibility
- Plugin architecture for custom content processors
- Template marketplace for resume layouts
- Integration with job boards for automatic posting analysis
- Analytics dashboard for tracking application success rates
- Additional LLM providers (Cohere, local models via Ollama)

### Performance
- Caching of LLM responses for similar job posting + content combinations
- Incremental rendering for large content libraries
- Background processing for time-intensive operations
- Content versioning and rollback capabilities
- Model response caching based on content + job posting similarity
