"""Member 3: baseline evidence-only extractor. Extend using RunPod and strict validation."""
import re

def extract_skills(text: str, approved: list[dict]) -> list[dict]:
    results = []
    for skill in approved:
        name = skill['name']
        # Baseline exact-phrase match; conservatively ignores synonym ambiguities.
        found = re.search(r'(?<!\w)' + re.escape(name) + r'(?!\w)', text, flags=re.I)
        if found:
            results.append({'skill_id':skill['id'], 'evidence':found.group(0)})
    return results
