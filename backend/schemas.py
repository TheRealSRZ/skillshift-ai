
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

SkillId = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Interest = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
Scenario = Literal["moderate", "rapid"]


class Profile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    education: str = Field(
        default="",
        max_length=160
    )

    skills: list[SkillId] = Field(
        default_factory=list,
        max_length=30
    )

    interests: list[Interest] = Field(
        default_factory=list,
        max_length=12
    )

    @field_validator("skills")
    @classmethod
    def remove_duplicates(cls, skills: list[str]) -> list[str]:
        return list(dict.fromkeys(skills))


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    profile: Profile
    scenario: Scenario = "moderate"


class RoadmapRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_role: str = Field(min_length=1, max_length=100)
    missing_skills: list[SkillId] = Field(
        default_factory=list,
        max_length=30
    )
    scenario: Scenario = "moderate"
