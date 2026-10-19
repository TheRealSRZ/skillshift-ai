from typing import Literal
from pydantic import BaseModel, Field

SkillId = str
Scenario = Literal['moderate', 'rapid']

class Profile(BaseModel):
    education: str = ''
    skills: list[SkillId] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)

class AnalyzeRequest(BaseModel):
    profile: Profile
    scenario: Scenario = 'moderate'

class RoadmapRequest(BaseModel):
    target_role: str
    missing_skills: list[SkillId]
    scenario: Scenario = 'moderate'
