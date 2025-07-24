"""
Integration tests for Pineneedle with real LLM endpoints.

These tests require API keys for LLM providers (OpenAI or Anthropic) to be set in environment variables.
"""
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from dotenv import load_dotenv

from pineneedle.agents import parse_job_posting, generate_resume
from pineneedle.models import ModelConfig, ResumeDeps, UserBackground
from pineneedle.services import FileSystemService


# Load environment variables from .env file for testing
load_dotenv()


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = Path(temp_dir)
        yield workspace


@pytest.fixture 
def sample_user_background():
    """Sample user background data for testing."""
    return UserBackground(
        experience_md="""
# Work Experience

## Senior Software Engineer - TechCorp (2021-2024)
- Led development of machine learning platform serving 1M+ users
- Built distributed data pipelines processing 100TB+ daily using Python and Spark
- Designed microservices architecture reducing latency by 40%
- Mentored team of 5 junior engineers

## Software Engineer - StartupXYZ (2019-2021)  
- Developed full-stack web applications using Python/Django and React
- Implemented CI/CD pipelines improving deployment frequency by 300%
- Built RESTful APIs handling 10K+ requests per minute
- Collaborated with data science team on ML model deployment

## Software Development Intern - BigTech Inc (Summer 2018)
- Developed automated testing framework reducing bug detection time by 50%
- Contributed to open source projects used by 50K+ developers
- Worked on performance optimization of legacy systems
        """,
        education_md="""
# Education

## Master of Science in Computer Science 
Stanford University, 2017-2019
- Thesis: "Scalable Machine Learning for Real-time Data Streams"
- Relevant Coursework: Machine Learning, Distributed Systems, Algorithms
- GPA: 3.8/4.0

## Bachelor of Science in Software Engineering
UC Berkeley, 2013-2017
- Magna Cum Laude, Phi Beta Kappa
- Relevant Coursework: Data Structures, Software Architecture, Database Systems
- GPA: 3.9/4.0
        """,
        contact_md="""
# Contact Information

**Jane Smith**
jane.smith@email.com
(555) 123-4567
LinkedIn: linkedin.com/in/janesmith
GitHub: github.com/janesmith
San Francisco, CA
        """,
        reference_md="""
# References

Available upon request.

## Previous Managers
- **John Doe**, Engineering Manager at TechCorp - john.doe@techcorp.com
- **Sarah Johnson**, CTO at StartupXYZ - sarah@startupxyz.com

## Technical References  
- **Dr. Michael Chen**, Stanford University Professor - mchen@stanford.edu
        """
    )


@pytest.fixture
def sample_job_posting_text():
    """Sample job posting text for testing."""
    return """
Senior ML Engineer - AI Platform Team
DataFlow Technologies

Location: San Francisco, CA (Hybrid)

We are seeking a Senior Machine Learning Engineer to join our AI Platform team. You'll be responsible for building and scaling machine learning systems that power our core product serving millions of users.

Requirements:
• 5+ years of software engineering experience
• 3+ years of machine learning experience in production environments
• Strong proficiency in Python and ML frameworks (TensorFlow, PyTorch, scikit-learn)
• Experience with distributed computing (Spark, Dask) and cloud platforms (AWS, GCP)
• Deep understanding of ML algorithms, model evaluation, and optimization techniques
• Experience with MLOps tools and practices (MLflow, Kubeflow, Docker)
• Strong problem-solving skills and attention to detail
• Excellent communication and collaboration skills

Responsibilities:
• Design and implement scalable ML pipelines for training and serving models
• Collaborate with data scientists to productionize research models
• Optimize model performance, latency, and resource utilization
• Build monitoring and alerting systems for ML models in production
• Contribute to ML platform tools and infrastructure
• Mentor junior engineers and promote ML best practices

Nice to Have:
• PhD in Computer Science, Machine Learning, or related field
• Experience with real-time ML systems and streaming data
• Knowledge of deep learning architectures (CNNs, RNNs, Transformers)
• Open source contributions to ML libraries

We offer competitive compensation, equity, comprehensive benefits, and the opportunity to work on cutting-edge AI technology that impacts millions of users.

DataFlow Technologies is committed to diversity and inclusion. We welcome applications from all qualified candidates.
    """


class TestJobPostingParsing:
    """Test job posting parsing with real LLM endpoints."""
    
    @pytest.mark.asyncio
    async def test_parse_job_posting_openai(self, temp_workspace, sample_job_posting_text):
        """Test parsing job posting with OpenAI."""
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not set")
        
        # Setup
        model_config = ModelConfig(provider="openai", model_name="gpt-4o-mini")
        
        # Parse job posting
        job_posting = await parse_job_posting(
            sample_job_posting_text,
            model_config,
            job_id="test-ml-engineer"
        )
        
        # Assertions
        assert job_posting.id == "test-ml-engineer"
        assert "Senior ML Engineer" in job_posting.title or "ML Engineer" in job_posting.title
        assert "DataFlow" in job_posting.company or job_posting.company != ""
        assert job_posting.location is not None
        assert len(job_posting.requirements) > 0
        assert len(job_posting.responsibilities) > 0
        assert len(job_posting.keywords) > 0
        assert len(job_posting.tone_reasoning) > 20  # Should have meaningful tone analysis
        assert job_posting.raw_content.strip() == sample_job_posting_text.strip()
        
        # Check that key requirements are captured
        requirements_text = " ".join(job_posting.requirements).lower()
        assert "python" in requirements_text
        assert "machine learning" in requirements_text or "ml" in requirements_text

    @pytest.mark.asyncio
    async def test_parse_job_posting_anthropic(self, temp_workspace, sample_job_posting_text):
        """Test parsing job posting with Anthropic."""
        if not os.getenv("ANTHROPIC_API_KEY"):
            pytest.skip("ANTHROPIC_API_KEY not set")
        
        # Setup
        model_config = ModelConfig(provider="anthropic", model_name="claude-3-haiku-20240307")
        
        # Parse job posting
        job_posting = await parse_job_posting(
            sample_job_posting_text,
            model_config,
            job_id="test-ml-engineer-anthropic"
        )
        
        # Assertions
        assert job_posting.id == "test-ml-engineer-anthropic"
        assert "ML Engineer" in job_posting.title or "Machine Learning" in job_posting.title
        assert len(job_posting.requirements) > 0
        assert len(job_posting.responsibilities) > 0
        assert len(job_posting.keywords) > 0


class TestResumeGeneration:
    """Test resume generation with real LLM endpoints."""
    
    @pytest.mark.asyncio
    async def test_generate_resume_openai(self, temp_workspace, sample_user_background, sample_job_posting_text):
        """Test resume generation with OpenAI."""
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not set")
        
        # Setup services
        fs_service = FileSystemService(temp_workspace)
        model_config = ModelConfig(provider="openai", model_name="gpt-4o-mini")
        
        # Parse job posting first
        job_posting = await parse_job_posting(
            sample_job_posting_text,
            model_config,
            job_id="test-resume-gen"
        )
        
        # Load template
        template = fs_service.load_template()
        
        # Create resume dependencies
        deps = ResumeDeps(
            job_posting=job_posting,
            user_background=sample_user_background,
            template=template,
            tone="professional",
            user_feedback=None
        )
        
        # Generate resume
        resume = await generate_resume(deps, model_config)
        
        # Assertions
        assert len(resume.resume_markdown) > 100
        assert len(resume.summary) > 30  # Validated by agent
        
        # Check that resume contains key information
        resume_text = resume.resume_markdown.lower()
        assert "jane smith" in resume_text  # Contact info
        assert "stanford" in resume_text or "berkeley" in resume_text  # Education
        assert "techcorp" in resume_text or "senior software engineer" in resume_text  # Experience
        assert "python" in resume_text  # Relevant skill
        assert "machine learning" in resume_text or "ml" in resume_text  # Job-relevant content

    @pytest.mark.asyncio
    async def test_generate_resume_with_feedback(self, temp_workspace, sample_user_background, sample_job_posting_text):
        """Test resume generation with user feedback."""
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not set")
        
        # Setup
        fs_service = FileSystemService(temp_workspace)
        agent_service = AgentService(
            default_model_config=ModelConfig(provider="openai", model_name="gpt-4o-mini"),
            workspace_path=temp_workspace
        )
        
        # Parse job posting
        job_posting = await agent_service.parse_job_posting(
            sample_job_posting_text,
            job_id="test-feedback"
        )
        
        # Generate initial resume
        template = fs_service.load_template()
        deps = ResumeDeps(
            job_posting=job_posting,
            user_background=sample_user_background,
            template=template,
            tone=None,
            user_feedback="Please emphasize distributed systems experience more and make the summary more concise"
        )
        
        # Generate resume with feedback
        resume = await generate_resume(deps, model_config)
        
        # Assertions
        assert len(resume.resume_markdown) > 100
        assert len(resume.summary) > 20
        
        # Check that feedback was incorporated
        resume_text = resume.resume_markdown.lower()
        assert "distributed" in resume_text or "spark" in resume_text


class TestEndToEndFlow:
    """Test complete end-to-end workflow."""
    
    @pytest.mark.asyncio
    async def test_complete_workflow(self, temp_workspace, sample_user_background, sample_job_posting_text):
        """Test complete workflow from job posting to archived resume."""
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not set")
        
        # Setup services
        fs_service = FileSystemService(temp_workspace)
        model_config = ModelConfig(provider="openai", model_name="gpt-4o-mini")
        
        # Step 1: Parse and save job posting
        job_posting = await parse_job_posting(
            sample_job_posting_text,
            model_config,
            job_id="end-to-end-test"
        )
        job_id = fs_service.save_job_posting(job_posting)
        assert job_id == "end-to-end-test"
        
        # Step 2: Load job posting back from storage
        loaded_posting = fs_service.load_job_posting(job_id)
        assert loaded_posting.title == job_posting.title
        assert loaded_posting.company == job_posting.company
        
        # Step 3: Generate resume
        template = fs_service.load_template()
        deps = ResumeDeps(
            job_posting=loaded_posting,
            user_background=sample_user_background,
            template=template,
            tone="professional",
            user_feedback=None
        )
        
        resume = await generate_resume(deps, model_config)
        
        # Step 4: Archive the resume
        from pineneedle.models import GenerationRequest
        generation_request = GenerationRequest(
            job_posting_id=job_id,
            tone="professional"
        )
        
        archive_path = fs_service.archive_resume(
            job_posting=loaded_posting,
            resume_content=resume,
            generation_request=generation_request,
            model_config=agent_service.default_model_config,
            iteration_count=1
        )
        
        # Step 5: Verify archived files exist
        archive_dir = Path(archive_path)
        assert archive_dir.exists()
        assert (archive_dir / "latest_resume.md").exists()
        assert (archive_dir / "latest_metadata.json").exists()
        
        # Step 6: Verify archived content
        latest_resume_path = fs_service.get_latest_resume_path(job_id)
        assert latest_resume_path is not None
        assert latest_resume_path.exists()
        
        archived_content = latest_resume_path.read_text()
        assert len(archived_content) > 100
        assert "jane smith" in archived_content.lower()
        
        # Step 7: List resume versions
        versions = fs_service.list_resume_versions(job_id)
        assert len(versions) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 