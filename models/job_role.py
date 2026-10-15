"""
models/job_role.py
-------------------
Pydantic models (data-transfer objects) for job roles.
Used by both the FastAPI routers and the Streamlit frontend.
"""

from pydantic import BaseModel, Field
from typing import Optional


class JobRoleBase(BaseModel):
    title:            str
    category:         Optional[str] = None
    required_skills:  list[str]     = Field(default_factory=list)
    description:      Optional[str] = None
    avg_salary:       Optional[str] = None
    experience_level: Optional[str] = None


class JobRoleCreate(JobRoleBase):
    pass


class JobRole(JobRoleBase):
    id: int

    model_config = {"from_attributes": True}


class JobRecommendation(BaseModel):
    title:             str
    category:          Optional[str] = None
    description:       Optional[str] = None
    avg_salary:        Optional[str] = None
    experience_level:  Optional[str] = None
    required_skills:   list[str]     = Field(default_factory=list)
    match_percentage:  float         = 0.0
    missing_skills:    list[str]     = Field(default_factory=list)


class SkillGapResult(BaseModel):
    job_title:         str
    required_skills:   list[str] = Field(default_factory=list)
    user_skills:       list[str] = Field(default_factory=list)
    matching_skills:   list[str] = Field(default_factory=list)
    missing_skills:    list[str] = Field(default_factory=list)
    match_percentage:  float     = 0.0
    description:       Optional[str] = None
    experience_level:  Optional[str] = None
    learning_roadmap:  Optional[dict] = None
