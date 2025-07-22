# Pineneedle

A smart Python application that leverages Large Language Models (LLMs) to intelligently manage and customize your resume for different job applications.

Alert: This is vibe-coded slop that'll reduce your IQ by at least 30pts. 

## Overview

Pineneedle transforms resume management from a tedious manual process into an intelligent, automated workflow. By maintaining your professional information in structured markdown files, the app can dynamically generate tailored resumes for specific job opportunities using LLM-powered content curation.

## Core Features

### 📝 Markdown-Based Resume Management
- **Structured Content**: Organize your professional information across separate markdown files
  - Job experience (`experience.md`)
  - Education history (`education.md`)
  - Skills and certifications (`skills.md`)
  - Projects and achievements (`projects.md`)
  - Tone samples (`tone_samples.md`) - Examples of your preferred writing style
- **Layout Templates**: Configure custom resume layouts using markdown templates
- **Version Control**: All resume data stored in human-readable markdown format

### 🤖 LLM-Powered Content Updates
- **Experience Updates**: Use natural language to update past job experiences
  - "Add my recent promotion to Senior Developer at TechCorp"
  - "Update my responsibilities at ABC Company to include team leadership"
- **Tone-Aware Writing**: LLM matches your personal writing style using your tone sample library
- **Intelligent Content Generation**: LLM processes your updates and maintains consistent formatting
- **Context-Aware Editing**: Preserves existing structure while incorporating new information

### 🎯 Job-Specific Resume Curation
- **Job Posting Analysis**: Paste any job posting and let the LLM analyze requirements
- **Tailored Content Selection**: Automatically curates relevant experience and skills
- **Keyword Optimization**: Ensures your resume includes relevant industry keywords
- **Custom Highlighting**: Emphasizes experiences most relevant to the target role

### 📄 Professional PDF Export
- **Markdown to PDF Conversion**: Clean, professional PDF generation from markdown
- **Multiple Layout Options**: Choose from various professional resume templates
- **Consistent Formatting**: Ensures all generated resumes maintain professional appearance

### 📊 Resume Version Tracking
- **Version History**: Track all generated resume variations in `.data/` directory
- **Job-Specific Archives**: Each tailored resume saved with job posting details
- **Comparison Tools**: Compare different resume versions
- **Backup and Recovery**: Never lose a customized resume version

## Workflow Examples

### Updating Experience
```bash
uv run pineneedle update experience "I got promoted to Lead Engineer at XYZ Corp in March 2024. My new responsibilities include managing a team of 5 developers and overseeing the migration to microservices architecture."
```

### Creating Job-Specific Resume
```bash
uv run pineneedle generate --job-posting "job_posting.txt" --output "resume_senior_python_dev.pdf"
```

Or interactively:
```bash
uv run pineneedle generate --interactive
# Paste job posting when prompted
# Review suggested customizations
# Generate final PDF
```

## Project Structure

```
pineneedle/
├── .data/                      # Resume versions and app state
│   ├── resumes/               # Generated resume versions
│   ├── job_postings/          # Analyzed job postings
│   └── templates/             # Custom layout templates
├── content/                   # Source markdown files
│   ├── experience.md          # Job experience history
│   ├── education.md           # Education background
│   ├── skills.md              # Skills and certifications
│   ├── projects.md            # Notable projects
│   ├── personal.md            # Personal information
│   └── tone_samples.md        # Examples of preferred writing style
├── templates/                 # Default layout templates
├── pineneedle/               # Main application code
├── pyproject.toml            # uv project configuration
└── uv.lock                   # Dependency lock file
```

## Key Benefits

- **Time Saving**: Generate tailored resumes in minutes, not hours
- **Consistency**: Maintain accurate, up-to-date professional information
- **Optimization**: Each resume optimized for specific job requirements
- **Organization**: Never lose track of different resume versions
- **Intelligence**: LLM understands context and maintains professional tone

## Getting Started

1. **Installation**: `uv sync` - Install dependencies and create virtual environment
2. **Initialize**: `uv run pineneedle init` - Set up initial content files
3. **Configure**: Edit markdown files in `content/` directory
4. **Generate**: Start creating job-specific resumes!

## Technology Stack

- **Python 3.12+**: Core application framework
- **uv**: Ultra-fast Python package management and virtual environments
- **LLM Integration**: OpenAI API for intelligent content processing
- **Markdown Processing**: Python-markdown for content parsing
- **CLI Interface**: Click for intuitive command-line interaction

## Future Enhancements

- ATS (Applicant Tracking System) optimization
- Cover letter generation
- Interview preparation based on job requirements
- Analytics on resume performance
