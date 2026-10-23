
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

SkillId = Annotated[str, StringConstraints(strict=True, strip_whitespace=True, min_length=1, max_length=100, pattern=r"^skill_[a-z0-9_]+$")]
RoleId = Annotated[str, StringConstraints(strict=True, strip_whitespace=True, min_length=1, max_length=100, pattern=r"^role_[a-z0-9_]+$")]
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

    @field_validator("education", "interests")
    @classmethod
    def reject_control_characters(cls, value):
        """Reject C0/DEL controls while allowing natural Unicode, tabs and newlines."""
        entries = value if isinstance(value, list) else [value]
        for entry in entries:
            if any((ord(char) < 32 and char not in '\t\n\r') or ord(char) == 127 for char in entry):
                raise ValueError("Unsupported control characters")
        return value

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

    target_role: RoleId
    missing_skills: list[SkillId] = Field(
        default_factory=list,
        max_length=30
    )
    scenario: Scenario = "moderate"


class WhatIfRequest(BaseModel):
    """A hypothetical skill acquisition preview, never an update to the user's profile."""
    model_config = ConfigDict(extra="forbid")

    profile: Profile
    target_role: RoleId
    add_skills: list[SkillId] = Field(min_length=1, max_length=10)
    scenario: Scenario = "moderate"

    @field_validator("add_skills")
    @classmethod
    def unique_added_skills(cls, skills: list[str]) -> list[str]:
        if len(skills) != len(set(skills)):
            raise ValueError("Duplicate skills are not allowed")
        return skills
