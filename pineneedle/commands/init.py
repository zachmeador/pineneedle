"""Init command to set up pineneedle project structure."""

import click
from pathlib import Path


@click.command()
@click.option('--force', is_flag=True, help='Overwrite existing files')
def init(force):
    """Initialize a new pineneedle project."""
    
    # Create directory structure
    directories = [
        '.data/resumes',
        '.data/job_postings', 
        '.data/templates',
        'content'
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        click.echo(f"Created directory: {dir_path}")
    
    # Create markdown files with templates
    markdown_files = {
        'content/personal.md': _personal_template(),
        'content/experience.md': _experience_template(),
        'content/education.md': _education_template(),
        'content/skills.md': _skills_template(),
        'content/projects.md': _projects_template(),
        'content/tone_samples.md': _tone_samples_template(),
    }
    
    for file_path, content in markdown_files.items():
        path = Path(file_path)
        if path.exists() and not force:
            click.echo(f"Skipped {file_path} (already exists, use --force to overwrite)")
        else:
            path.write_text(content)
            click.echo(f"Created: {file_path}")
    
    click.echo("\n✅ Pineneedle project initialized!")
    click.echo("Edit the markdown files in the content/ directory to add your information.")


def _personal_template():
    return """# Personal Information

## Contact
- **Name**: Your Full Name
- **Email**: your.email@example.com
- **Phone**: (555) 123-4567
- **Location**: City, State
- **LinkedIn**: https://linkedin.com/in/yourprofile
- **GitHub**: https://github.com/yourusername

## Summary
Write a brief professional summary here (2-3 sentences about your background and career focus).
"""


def _experience_template():
    return """# Work Experience

## Senior Software Engineer
**Company Name** | *Jan 2022 - Present* | *Remote*

- Key achievement or responsibility
- Another important accomplishment with metrics
- Technical leadership or project you led

## Software Engineer
**Previous Company** | *Jun 2020 - Dec 2021* | *City, State*

- Major project you worked on
- Technology or process improvements you made
- Collaboration or mentorship activities

## Example Format Guidelines
- Use action verbs (Led, Developed, Implemented, Optimized)
- Include quantifiable results when possible (improved performance by 30%)
- Focus on impact and achievements, not just duties
- Keep bullet points concise and impactful
"""


def _education_template():
    return """# Education

## Bachelor of Science in Computer Science
**University Name** | *Graduated: May 2020* | *City, State*

- **GPA**: 3.8/4.0 (optional)
- **Relevant Coursework**: Data Structures, Algorithms, Software Engineering
- **Activities**: Computer Science Club, Hackathon Winner

## Certifications
- **AWS Certified Solutions Architect** | *Issued: 2023*
- **Google Cloud Professional Developer** | *Issued: 2022*

## Additional Training
- **Machine Learning Specialization** | *Coursera* | *2023*
- **Advanced Python Programming** | *Online Course* | *2022*
"""


def _skills_template():
    return """# Skills

## Programming Languages
- **Proficient**: Python, JavaScript, TypeScript, Java
- **Familiar**: Go, Rust, C++

## Frameworks & Libraries
- **Backend**: Django, FastAPI, Flask, Node.js, Express
- **Frontend**: React, Vue.js, Angular
- **Data**: Pandas, NumPy, TensorFlow, PyTorch

## Tools & Technologies
- **Cloud**: AWS, Google Cloud, Azure
- **Databases**: PostgreSQL, MongoDB, Redis
- **DevOps**: Docker, Kubernetes, CI/CD, GitHub Actions
- **Other**: Git, Linux, REST APIs, GraphQL

## Soft Skills
- Technical leadership and mentoring
- Cross-functional team collaboration
- Agile/Scrum methodology
- Problem-solving and debugging
"""


def _projects_template():
    return """# Notable Projects

## Personal Finance Tracker
**Technologies**: Python, Django, PostgreSQL, React  
**Timeline**: 3 months

- Built full-stack web application for personal budget management
- Implemented automated transaction categorization using machine learning
- Deployed on AWS with 99.9% uptime and handles 1000+ daily users

## Open Source Contribution - Popular Library
**Technologies**: JavaScript, Node.js  
**Timeline**: Ongoing

- Contributing maintainer to XYZ library with 50k+ GitHub stars
- Implemented new feature that improved performance by 40%
- Review pull requests and help with community support

## Hackathon Winner - Data Visualization Tool
**Technologies**: D3.js, Python, Flask  
**Timeline**: 48 hours

- Won first place at City Tech Hackathon
- Created interactive dashboard for COVID-19 data analysis
- Presented to panel of industry judges and 200+ attendees
"""


def _tone_samples_template():
    return """# Tone Samples

This file contains examples of your preferred writing style for different contexts. The LLM will use these samples to match your voice when generating resume content.

## Professional/Corporate Tone
*Use for traditional corporate environments, consulting, finance*

"Spearheaded the development of a comprehensive data analytics platform that revolutionized decision-making processes across multiple departments. Collaborated with cross-functional teams to identify key performance indicators and delivered actionable insights that resulted in a 25% increase in operational efficiency."

## Technical/Engineering Tone  
*Use for software development, technical roles*

"Built and deployed a high-performance microservices architecture using Python and Docker. Implemented automated testing pipelines that reduced deployment time by 60% and improved code quality. Optimized database queries resulting in 3x faster response times."

## Startup/Informal Tone
*Use for startups, creative agencies, tech companies*

"Wore many hats as an early engineer, shipping features fast and iterating based on user feedback. Built the entire authentication system from scratch and helped scale the platform from 100 to 10,000 users. Love solving complex problems with elegant, simple solutions."

## Leadership/Management Tone
*Use for management, senior roles*

"Led a team of 8 engineers through a critical system migration, ensuring zero downtime during the transition. Mentored junior developers and established best practices that improved team productivity by 40%. Fostered a culture of continuous learning and innovation."

## Notes
- Add more examples as you refine your style
- Include specific phrases or terminology you prefer
- Note any words or phrases to avoid
- Consider different tones for different types of roles
""" 