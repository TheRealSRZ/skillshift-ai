# AI & RunPod owner — Member 3

- Implement RunPod-compatible client in `ai/runpod_client.py`; confirm endpoint API compatibility first.
- Implement skill extraction in `ai/skill_extractor.py` using evidence snippets; validate against approved skill IDs and verify source text.
- Implement learning explanations in `ai/learning_planner.py` using **verified courses only** and deterministic fallback if model is unavailable.
- Validate model output with Pydantic in `ai/validators.py`.
- Do not return invented sources, job demand statistics, course URLs, or employment probabilities.
- Document model ID, endpoint type, prompt family, data shared, cost and failures in AI declaration.
