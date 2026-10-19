"""Member 3: hosted inference client. Never expose RUNPOD_API_KEY to browser."""
import os
from openai import OpenAI

def ask_ai(prompt: str) -> str:
    key = os.getenv('RUNPOD_API_KEY')
    base_url = os.getenv('RUNPOD_BASE_URL')
    model = os.getenv('RUNPOD_MODEL')
    if not all((key, base_url, model)):
        raise RuntimeError('Missing RunPod configuration. Set private environment secrets.')
    client = OpenAI(api_key=key, base_url=base_url, timeout=20.0, max_retries=1)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {'role':'system','content':'Use only provided evidence; do not invent links or statistics.'},
            {'role':'user','content':prompt},
        ],
        temperature=0.2,
        max_tokens=350,
    )
    return response.choices[0].message.content or ''
