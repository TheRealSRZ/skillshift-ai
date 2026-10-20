
"""Member 3: RunPod Serverless AI client."""

import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()


def ask_ai(prompt: str) -> str:
    api_key = os.getenv("RUNPOD_API_KEY")
    endpoint_id = os.getenv("RUNPOD_ENDPOINT_ID")

    if not api_key or not endpoint_id:
        raise RuntimeError("Missing RunPod API configuration")

    base_url = f"https://api.runpod.ai/v2/{endpoint_id}"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "input": {
            "prompt": prompt,
            "sampling_params": {
                "max_tokens": 200,
                "temperature": 0.2,
            },
        }
    }

    # Submit a job to RunPod.
    response = requests.post(
        f"{base_url}/run",
        headers=headers,
        json=payload,
        timeout=30,
    )
    response.raise_for_status()

    result = response.json()
    job_id = result.get("id")

    if not job_id:
        raise RuntimeError("RunPod did not return a job ID")

    # Wait for the job to complete (maximum 90 seconds).
    deadline = time.monotonic() + 90

    while time.monotonic() < deadline:
        response = requests.get(
            f"{base_url}/status/{job_id}",
            headers=headers,
            timeout=20,
        )
        response.raise_for_status()

        result = response.json()
        status = result.get("status")

        if status == "COMPLETED":
            output = result.get("output", [])

            if not output:
                raise RuntimeError("RunPod returned no output")

            choices = output[0].get("choices", [])

            if not choices:
                raise RuntimeError("RunPod returned no choices")

            text = choices[0].get("text", "")

            if not text.strip():
                raise RuntimeError("RunPod returned an empty response")

            return text.strip()

        if status in ("FAILED", "CANCELLED", "TIMED_OUT"):
            raise RuntimeError(f"RunPod job failed: {status}")

        time.sleep(3)

    raise TimeoutError("RunPod job did not finish within 90 seconds")
