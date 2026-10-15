"""
models/resume.py
-----------------
Pydantic models for resume and interview data transfer.
"""

from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


# ── Resume models ─────────────────────────────────────────────────────────────

class ContactInfo(BaseModel):
    name:     Optional[str] = None
    email:    Optional[str] = None
    phone:    Optional[str] = None
    linkedin: Optional[str] = None
    github:   Optional[str] = None


class EducationEntry(BaseModel):
    degree:      Optional[str] = None
    institution: Optional[str] = None
    year:        Optional[str] = None


class ExperienceEntry(BaseModel):
    title:       Optional[str] = None
    description: Optional[str] = None


class ProjectEntry(BaseModel):
    name:        Optional[str] = None
    description: Optional[str] = None


class ResumeOut(BaseModel):
    id:              int
    filename:        str
    upload_date:     Optional[datetime] = None
    skills:          list[str]               = Field(default_factory=list)
    education:       list[EducationEntry]     = Field(default_factory=list)
    experience:      list[ExperienceEntry]    = Field(default_factory=list)
    projects:        list[ProjectEntry]       = Field(default_factory=list)
    certifications:  list[str]               = Field(default_factory=list)
    contact_info:    Optional[ContactInfo]   = None

    model_config = {"from_attributes": True}


# ── Interview models ───────────────────────────────────────────────────────────

class InterviewQuestion(BaseModel):
    type: str   # "technical" | "hr"
    text: str


class AnswerEvaluation(BaseModel):
    relevance_score:     float = 0.0
    clarity_score:       float = 0.0
    technical_score:     float = 0.0
    communication_score: float = 0.0
    overall_score:       float = 0.0
    feedback:            str   = ""
    improvement_tips:    list[str] = Field(default_factory=list)


class InterviewSessionOut(BaseModel):
    id:            int
    job_role:      str
    status:        str
    overall_score: Optional[float] = None
    started_at:    Optional[datetime] = None
    completed_at:  Optional[datetime] = None
    questions:     list[InterviewQuestion] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class InterviewAnswerOut(BaseModel):
    id:                int
    session_id:        int
    question:          str
    answer:            Optional[str] = None
    score:             Optional[float] = None
    feedback:          Optional[str]  = None
    relevance_score:   Optional[float] = None
    clarity_score:     Optional[float] = None
    technical_score:   Optional[float] = None
    answered_at:       Optional[datetime] = None

    model_config = {"from_attributes": True}
