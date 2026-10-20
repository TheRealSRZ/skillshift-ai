"""Team-defined AI adoption assumptions, not empirical labour forecasts.

Stable version and descriptions help audit changes and explain results.
Do not silently update these multipliers when new job-market data arrives.
"""

SCENARIO_VERSION = "scenario_assumptions_v1"

SCENARIO_MULTIPLIERS = {
    "moderate": {},
    "rapid": {
        "skill_cloud": 1.20,
        "skill_automation": 1.20,
        "skill_security": 1.15,
        "skill_data_viz": 1.10,
    },
}

SCENARIO_DESCRIPTIONS = {
    "moderate": "Baseline assumption: no additional AI-adoption adjustment beyond the active trend snapshot.",
    "rapid": (
        "Illustrative faster-adoption assumption: cloud and automation weights rise 20%, "
        "security 15%, and data visualization 10%, relative to the same snapshot."
    ),
}

SCENARIO_DISCLAIMER = (
    "Hypothetical team-defined weighting, not a validated workforce prediction."
)


def scenario_metadata(scenario: str) -> dict:
    """Describe exactly which team-authored assumptions were used."""
    if scenario not in SCENARIO_MULTIPLIERS:
        raise ValueError(f"Unsupported scenario: {scenario}")
    return {
        "scenario_version": SCENARIO_VERSION,
        "scenario_description": SCENARIO_DESCRIPTIONS[scenario],
        "scenario_multipliers": dict(SCENARIO_MULTIPLIERS[scenario]),
    }
