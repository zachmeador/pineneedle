# Pineneedle

Claude Code but for your boring career stuff.

## Overview

Pineneedle is a simple LLM powered CLI app that manages your resumes, job postings, experiences, references, etc.

## Configuration

Copy `env_template` to `.env` and configure the following environment variables:

### Required API Keys
- `OPENAI_API_KEY` - Your OpenAI API key (for GPT models)
- `ANTHROPIC_API_KEY` - Your Anthropic API key (for Claude models)

### Optional Settings
- `PINENEEDLE_DEFAULT_PROVIDER` - Default model provider (`openai` or `anthropic`)
- `PINENEEDLE_DEFAULT_MODEL` - Default model name (e.g., `gpt-4o`, `claude-sonnet-4-0`)
- `PINENEEDLE_DATA_DIR` - Custom path for your data directory (defaults to `./data`)

### Data Directory Configuration

By default, Pineneedle stores your data in a `data/` subdirectory of your workspace. You can customize this location by setting the `PINENEEDLE_DATA_DIR` environment variable:

```bash
# Use a custom data directory
PINENEEDLE_DATA_DIR=/path/to/my/resume/data

# Use a directory relative to your home folder
PINENEEDLE_DATA_DIR=~/Documents/pineneedle-data

# Use the default (workspace/data)
# PINENEEDLE_DATA_DIR=./data
```

This is useful if you want to:
- Store your data in a centralized location across multiple projects
- Keep your data in a cloud-synced folder (Dropbox, Google Drive, etc.)
- Separate your data from your workspace for organizational purposes 