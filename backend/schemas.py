
from typing import Literal
from pydantic import BaseModel, Field, field_validator

SkillId = str
Scenario = Literal["moderate", "rapid"]


class Profile(BaseModel):
    education: str = Field(
        default="",
        max_length=160
    )

    skills: list[SkillId] = Field(
        default_factory=list,
        max_length=30
    )

    interests: list[str] = Field(
        default_factory=list,
        max_length=12
    )

    @field_validator("skills")
    @classmethod
    def remove_duplicates(cls, skills: list[str]) -> list[str]:
        return list(dict.fromkeys(skills))


class AnalyzeRequest(BaseModel):
    profile: Profile
    scenario: Scenario = "moderate"


class RoadmapRequest(BaseModel):
    target_role: str = Field(min_length=1, max_length=100)
    missing_skills: list[SkillId] = Field(
        default_factory=list,
        max_length=30
    )
    scenario: Scenario = "moderate"
