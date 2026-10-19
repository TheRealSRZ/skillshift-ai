def normalize_skill_name(value: str) -> str:
    return ' '.join(value.strip().casefold().split())
