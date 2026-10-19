SKILL_EXTRACTION_PROMPT = """
Given an evidence excerpt and the allowed skill IDs, return JSON mapping only
explicit skill mentions to approved IDs. Include short verbatim evidence spans.
Never infer skills not stated. Never invent source URLs or demand figures.
""".strip()

ROADMAP_PROMPT = """
Only use validated course IDs, titles and estimated hours supplied in the input.
Return an ordered plan with reason per step. Do not invent new courses.
Clearly label hours as estimates. Role match is not employment probability.
""".strip()
