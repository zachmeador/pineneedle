from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
import uuid


class JobPostingInput(BaseModel):
    """Raw job posting text from user input"""
    raw_text: str = Field(..., min_length=10, description="Raw job posting text")
    source: str = Field(default="manual", description="Source of the job posting")


class JobPostingAnalysis(BaseModel):
    """LLM analysis results of job posting"""
    company: str
    position: str
    location: Optional[str] = None
    requirements: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    seniority_level: Optional[str] = None
    industry: Optional[str] = None


class StoredJobPosting(BaseModel):
    """Complete job posting record stored in .data/job_postings/"""
    id: str = Field(default_factory=lambda: f"job_posting_{uuid.uuid4().hex[:8]}")
    created_date: datetime = Field(default_factory=datetime.utcnow)
    raw_text: str
    source: str = "manual"
    analysis: JobPostingAnalysis
    render_count: int = 0
    notes: str = ""

    class Config:
        # Allow datetime serialization
        json_encoders = {
            datetime: lambda v: v.isoformat()
        } 