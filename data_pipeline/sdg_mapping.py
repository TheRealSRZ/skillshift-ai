def sdgs_for_role(role: dict) -> list[int]:
    return role.get('sdgs', [])


def sdgs_for_skill(skill: dict) -> list[int]:
    """Return project-defined SDG IDs from a skill record."""
    return skill.get("sdgs", [])
