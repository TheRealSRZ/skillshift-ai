def sdgs_for_role(role: dict) -> list[int]:
    return role.get('sdgs', [])
