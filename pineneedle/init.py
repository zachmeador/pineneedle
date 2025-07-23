"""Workspace initialization functionality."""

from pathlib import Path
import shutil


def initialize_workspace(data_dir: Path, force: bool = False) -> bool:
    """Initialize a new Pineneedle workspace with content templates."""
    if data_dir.exists() and not force:
        return False
    
    if force and data_dir.exists():
        shutil.rmtree(data_dir)
    
    # Create directory structure
    content_dir = data_dir / 'content'
    tones_dir = data_dir / 'tones'
    renders_dir = data_dir / 'renders'
    
    content_dir.mkdir(parents=True)
    tones_dir.mkdir(parents=True)
    renders_dir.mkdir(parents=True)
    
    # Create content templates
    create_content_templates(content_dir)
    
    # Create initial tone configurations
    create_initial_tones(tones_dir)
    
    return True


def create_content_templates(content_dir: Path):
    """Create markdown template files for user content."""
    
    # Personal information template
    personal_md = """# Personal Information

## Contact Details
- **Name**: [Your Full Name]
- **Email**: [your.email@example.com]
- **Phone**: [Your Phone Number]
- **Location**: [City, State/Country]
- **LinkedIn**: [linkedin.com/in/yourprofile]
- **GitHub**: [github.com/yourusername]
- **Website**: [yourwebsite.com]

## Professional Summary
[Write a 2-3 sentence summary of your professional background and key strengths. This will be customized by the LLM for each job application.]

## Objective
[Optional: A brief statement about your career goals and what you're looking for in your next role.]
"""

    # Experience template (consolidated with projects)
    experience_md = """# Experience

## Professional Experience

### [Job Title] - [Company Name]
**[Start Date] - [End Date]** | [Location]

#### Responsibilities
- [Key responsibility or achievement]
- [Key responsibility or achievement]
- [Key responsibility or achievement]

#### Technologies Used
- [Technology/Tool 1]
- [Technology/Tool 2]
- [Technology/Tool 3]

#### Key Achievements
- [Quantified achievement with metrics]
- [Impact or improvement you made]

---

### [Previous Job Title] - [Previous Company Name]
**[Start Date] - [End Date]** | [Location]

#### Responsibilities
- [Key responsibility or achievement]
- [Key responsibility or achievement]

#### Technologies Used
- [Technology/Tool 1]
- [Technology/Tool 2]

#### Key Achievements
- [Quantified achievement with metrics]

---

*Add more positions as needed following the same format*

## Personal Projects

### [Project Name]
**[Your Role]** | [Timeframe] | [GitHub/Demo Link]

#### Description
[Brief description of what the project does and why it was built]

#### Technologies Used
- [Technology 1]
- [Technology 2]
- [Technology 3]

#### Key Features
- [Feature 1 with brief explanation]
- [Feature 2 with brief explanation]
- [Feature 3 with brief explanation]

#### Impact/Results
- [Quantified result or impact]
- [What you learned or achieved]

---

### [Another Project Name]
**[Your Role]** | [Timeframe] | [GitHub/Demo Link]

#### Description
[Brief description]

#### Technologies Used
- [Technology 1]
- [Technology 2]

#### Key Features
- [Feature 1]
- [Feature 2]

#### Impact/Results
- [Result or learning]

---

*Add more projects as needed. Focus on projects that demonstrate skills relevant to your target roles.*
"""

    # Education template
    education_md = """# Education

## [Degree] in [Field of Study]
**[University/Institution Name]** | [Graduation Year]
- GPA: [X.X/4.0] *(optional)*
- Relevant Coursework: [Course 1], [Course 2], [Course 3]
- Honors/Awards: [Any academic honors]

## Certifications
- **[Certification Name]** - [Issuing Organization] ([Year])
- **[Certification Name]** - [Issuing Organization] ([Year])

## Additional Education
- **[Course/Bootcamp Name]** - [Institution] ([Year])
- **[Online Course]** - [Platform] ([Year])

*Add more education entries as needed*
"""

    # Skills template
    skills_md = """# Skills

## Technical Skills

### Programming Languages
- [Language 1] - [Proficiency Level: Beginner/Intermediate/Advanced/Expert]
- [Language 2] - [Proficiency Level]
- [Language 3] - [Proficiency Level]

### Frameworks & Libraries
- [Framework 1]
- [Framework 2]
- [Library 1]

### Tools & Technologies
- [Tool 1] - [Context of use]
- [Tool 2] - [Context of use]
- [Database Technology]
- [Cloud Platform]

### Development Tools
- [IDE/Editor preferences]
- [Version Control: Git, etc.]
- [CI/CD tools]
- [Testing frameworks]

## Soft Skills
- [Skill 1] - [Brief context or example]
- [Skill 2] - [Brief context or example]
- [Skill 3] - [Brief context or example]
- [Communication/Leadership abilities]

## Languages
- **[Language]** - [Proficiency: Native/Fluent/Conversational/Basic]
- **[Language]** - [Proficiency]

*Organize skills by relevance to your target roles*
"""

    # Write template files
    templates = {
        'personal.md': personal_md,
        'experience.md': experience_md,
        'education.md': education_md,
        'skills.md': skills_md
    }
    
    for filename, content in templates.items():
        (content_dir / filename).write_text(content.strip())


def create_initial_tones(tones_dir: Path):
    """Create initial tone configuration files."""
    
    # Technical/Software Development tone
    technical_toml = """name = "technical_professional"
model_provider = "openai"
model_name = "gpt-4"

description = '''
Write in a professional, technical tone focused on quantified achievements and problem-solving abilities. 

Emphasize:
- Technical skills and methodologies
- System design and architecture experience
- Quantified improvements and metrics
- Code quality and best practices
- Team collaboration and technical leadership
- Problem-solving approach and analytical thinking

Use industry-standard terminology and highlight tools, frameworks, and technologies. 
Focus on the technical impact of your work and your ability to deliver scalable solutions.
'''"""

    # Creative/Marketing tone  
    creative_toml = """name = "creative_engaging"
model_provider = "anthropic"
model_name = "claude-3-sonnet"

description = '''
Write in an engaging, creative tone that showcases personality and innovation.

Emphasize:
- Creative problem-solving and innovative solutions
- Client relationships and stakeholder management
- Brand building and marketing impact
- Collaboration and cross-functional teamwork
- Results-driven creativity with measurable outcomes
- Adaptability and trend awareness

Use dynamic language and storytelling to highlight impact. Show passion for creative work
while maintaining professionalism. Focus on how creativity drives business results.
'''"""

    
    # Write tone files
    tones = {
        'technical_professional.toml': technical_toml,
        'creative_engaging.toml': creative_toml,
        'executive_leadership.toml': executive_toml
    }
    
    for filename, content in tones.items():
        (tones_dir / filename).write_text(content.strip()) 