# Pineneedle Integration Tests

This directory contains integration tests that test Pineneedle's core functionality with real LLM endpoints.

## Prerequisites

### 1. API Keys Required

The integration tests require API keys for LLM providers. Set these environment variables:

**For OpenAI tests:**
```bash
export OPENAI_API_KEY="your-openai-api-key"
```

**For Anthropic tests:**
```bash
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

### 2. Install Dependencies

Make sure you have the testing dependencies installed:

```bash
uv pip install -e .
```

Or install test dependencies specifically:
```bash
uv pip install pytest pytest-asyncio
```

## Running Tests

### Quick Start with Test Runner Script
```bash
# Run the convenient test runner script
python run_tests.py

# Or with specific filter
python run_tests.py openai
```

### Run All Integration Tests
```bash
pytest tests/test_integration.py -v
```

### Run Specific Test Classes
```bash
# Test job posting parsing only
pytest tests/test_integration.py::TestJobPostingParsing -v

# Test resume generation only  
pytest tests/test_integration.py::TestResumeGeneration -v

# Test end-to-end workflow
pytest tests/test_integration.py::TestEndToEndFlow -v
```

### Run Tests with Specific Provider
```bash
# OpenAI tests only (requires OPENAI_API_KEY)
pytest tests/test_integration.py -k "openai" -v

# Anthropic tests only (requires ANTHROPIC_API_KEY)  
pytest tests/test_integration.py -k "anthropic" -v
```

## Test Coverage

### 1. Job Posting Parsing (`TestJobPostingParsing`)
- **`test_parse_job_posting_openai`**: Tests parsing job posting text into structured data using OpenAI
- **`test_parse_job_posting_anthropic`**: Tests parsing job posting text using Anthropic

Validates:
- Proper extraction of job title, company, location
- Requirements and responsibilities parsing
- Keywords and tone indicators detection
- Raw content preservation

### 2. Resume Generation (`TestResumeGeneration`)
- **`test_generate_resume_openai`**: Tests generating tailored resume from job posting and background
- **`test_generate_resume_with_feedback`**: Tests incorporating user feedback into resume generation

Validates:
- Resume follows template structure
- Contains relevant user background information
- Tailors content to job requirements
- Incorporates user feedback when provided
- Generates meaningful summary section

### 3. End-to-End Workflow (`TestEndToEndFlow`)
- **`test_complete_workflow`**: Tests full pipeline from raw job posting to archived resume

Validates:
- Job posting parsing and storage
- Background data loading
- Resume generation
- Archive system functionality
- File system operations

## Test Data

The tests use realistic sample data:

- **Job Posting**: Senior ML Engineer position with comprehensive requirements
- **User Background**: Experienced software engineer with ML background
- **Template**: Standard resume structure with placeholders

## Notes

- Tests use temporary workspaces to avoid interfering with real data
- Tests are skipped automatically if required API keys are not set
- Tests use cost-efficient models (gpt-4o-mini, claude-3-haiku) to minimize API costs
- Each test is independent and can be run separately

## Troubleshooting

### "OPENAI_API_KEY not set" / "ANTHROPIC_API_KEY not set"
Set the appropriate environment variables or create a `.env` file in the project root:

```
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
```

### Test timeouts
LLM API calls can be slow. If tests timeout, increase pytest's timeout:
```bash
pytest tests/test_integration.py --timeout=300 -v
```

### Rate limiting
If you hit API rate limits, add delays between tests or run tests sequentially:
```bash
pytest tests/test_integration.py -v --maxfail=1
``` 