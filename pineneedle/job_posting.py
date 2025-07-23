import json
import os
from pathlib import Path
from typing import List

from .models import JobPostingInput, JobPostingAnalysis, StoredJobPosting
from .agents import AgentManager


class JobPostingService:
    """Service for ingesting and storing job postings using Pydantic-AI"""
    
    def __init__(self, data_dir: str = ".data"):
        self.data_dir = Path(data_dir)
        self.job_postings_dir = self.data_dir / "job_postings"
        self.job_postings_dir.mkdir(parents=True, exist_ok=True)
        self.agent_manager = AgentManager()
    
    async def store_job_posting(self, raw_text: str, source: str = "manual") -> StoredJobPosting:
        """Analyze and store a job posting using Pydantic-AI"""
        
        # Validate input
        input_data = JobPostingInput(raw_text=raw_text, source=source)
        
        # Analyze with Pydantic-AI agent
        analysis = await self._analyze_job_posting(input_data.raw_text)
        
        # Create stored job posting
        stored_posting = StoredJobPosting(
            raw_text=input_data.raw_text,
            source=input_data.source,
            analysis=analysis
        )
        
        # Save to file
        self._save_job_posting(stored_posting)
        
        return stored_posting
    
    def store_job_posting_sync(self, raw_text: str, source: str = "manual") -> StoredJobPosting:
        """Synchronous wrapper for store_job_posting"""
        import asyncio
        return asyncio.run(self.store_job_posting(raw_text, source))
    
    async def _analyze_job_posting(self, raw_text: str) -> JobPostingAnalysis:
        """Use Pydantic-AI agent to extract structured data from job posting"""
        try:
            return await self.agent_manager.analyze_job_posting(raw_text)
        except Exception as e:
            # Fallback if agent fails
            print(f"Warning: Job analysis failed with error: {e}")
            return JobPostingAnalysis(
                company="Unknown",
                position="Unknown Position",
                requirements=["Analysis failed - please review manually"],
                keywords=["job", "position"]
            )
    
    def _save_job_posting(self, posting: StoredJobPosting) -> None:
        """Save job posting to file"""
        file_path = self.job_postings_dir / f"{posting.id}.json"
        
        with open(file_path, 'w') as f:
            json.dump(posting.model_dump(), f, indent=2, default=str)
    
    def load_job_posting(self, posting_id: str) -> StoredJobPosting:
        """Load job posting from file"""
        file_path = self.job_postings_dir / f"{posting_id}.json"
        
        if not file_path.exists():
            raise FileNotFoundError(f"Job posting {posting_id} not found")
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        return StoredJobPosting(**data)
    
    def list_job_postings(self) -> List[StoredJobPosting]:
        """List all stored job postings"""
        postings = []
        
        for file_path in self.job_postings_dir.glob("job_posting_*.json"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                postings.append(StoredJobPosting(**data))
            except Exception as e:
                print(f"Warning: Could not load job posting from {file_path}: {e}")
                continue
        
        # Sort by creation date, newest first
        return sorted(postings, key=lambda p: p.created_date, reverse=True) 