# Pineneedle

A smart Python application that leverages Large Language Models (LLMs) to intelligently manage and customize your resume for different job applications.

## Overview

Pineneedle transforms resume management from a tedious manual process into an intelligent, automated workflow. By maintaining your professional information in structured markdown files, the app can dynamically generate tailored resumes for specific job opportunities using LLM-powered content curation.

## TODOs

- Michael mentioned a good idea about tracking job accomplishments are they are done. Not sure how to integrate. 

## Core Features

### 📝 Markdown-Based Content Management
- **Structured Content**: Organize your professional information in `.data/content/`
  - Personal info (`personal.md`) - Contact details and summary
  - Job experience (`experience.md`) - Work history
  - Education (`education.md`) - Degrees and certifications
  - Skills (`skills.md`) - Technical and soft skills
  - Projects (`projects.md`) - Notable achievements
- **Tone Library**: Reusable tone configurations in `.data/tones/`
- **Version Control**: All data stored in human-readable formats

### 🤖 LLM-Powered Content Updates
- **Experience Updates**: Use natural language to update your base content
  - "Add my recent promotion to Senior Developer at TechCorp"
  - "Update my responsibilities at ABC Company to include team leadership"
- **Smart Content Management**: LLM updates your source markdown files
- **Structure Preservation**: Maintains consistent formatting and organization

### 🎯 Job-Specific Resume Rendering
- **Job Posting Analysis**: Paste any job posting for requirements analysis
- **Content Curation**: Automatically selects relevant experience and skills
- **Tone Application**: Choose from your tone library or create custom tones
- **Smart Rendering**: Combines base content + selected tone + job requirements
- **Keyword Optimization**: Ensures relevant industry keywords are emphasized

### 📄 Professional PDF Export
- **Markdown to PDF Conversion**: Clean, professional PDF generation from markdown
- **Multiple Layout Options**: Choose from various professional resume templates
- **Consistent Formatting**: Ensures all generated resumes maintain professional appearance

### 📊 Render Management
- **Render History**: Track all generated resumes in `.data/renders/`
- **Tone Experiments**: Try different tones with the same base content
- **Job-Specific Archives**: Each render saved with job posting and tone details
- **Comparison Tools**: Compare different renders and tone applications
- **Backup and Recovery**: Never lose a customized resume render

## Future Enhancements

- ATS (Applicant Tracking System) optimization
- Cover letter generation
- Interview preparation based on job requirements
- Analytics on resume performance
