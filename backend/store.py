import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / 'data'

def load_json(filename: str):
    # File names must come from internal code, not untrusted user input.
    with (DATA_DIR / filename).open(encoding='utf-8') as f:
        return json.load(f)
