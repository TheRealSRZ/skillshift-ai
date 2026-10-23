
"""Member 3: RunPod Serverless AI client."""

import os
import re
import math
import time

import requests
from dotenv import load_dotenv

load_dotenv()


def ask_ai(prompt: str) -> str:
    api_key = os.getenv("RUNPOD_API_KEY")
    endpoint_id = os.getenv("RUNPOD_ENDPOINT_ID")

    if not api_key or not endpoint_id:
        raise RuntimeError("Missing RunPod API configuration")
    # These strings become URL path components / authorization headers.
    # Reject unexpected characters before making any outbound HTTP request.
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,100}', endpoint_id):
        raise ValueError('Invalid RunPod endpoint ID')
    if len(api_key) > 4096 or any(ch.isspace() or ord(ch) < 33 for ch in api_key):
        raise ValueError('Invalid RunPod API key')

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
    if not isinstance(result, dict):
        raise RuntimeError("Invalid RunPod job response")
    job_id = result.get("id")

    if not isinstance(job_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,160}', job_id):
        raise RuntimeError("RunPod returned an invalid job ID")

    # Maximum time to wait for a RunPod job.
    # Default: 30 seconds for a responsive demo.
    timeout_seconds = float(
        os.getenv("RUNPOD_POLL_TIMEOUT", "30")
    )
    if not math.isfinite(timeout_seconds) or not 0 <= timeout_seconds <= 600:
        raise ValueError('Invalid RunPod polling timeout')
    deadline = time.monotonic() + timeout_seconds

    while time.monotonic() < deadline:
        response = requests.get(
            f"{base_url}/status/{job_id}",
            headers=headers,
            timeout=min(10.0, max(0.5, deadline - time.monotonic())),
        )
        response.raise_for_status()

        result = response.json()
        if not isinstance(result, dict):
            raise RuntimeError("Invalid RunPod status response")
        status = result.get("status")

        if status == "COMPLETED":
            output = result.get("output", [])

            if not output:
                raise RuntimeError("RunPod returned no output")

            if not isinstance(output, list) or not isinstance(output[0], dict):
                raise RuntimeError("Invalid RunPod output structure")
            choices = output[0].get("choices", [])

            if not choices:
                raise RuntimeError("RunPod returned no choices")

            if not isinstance(choices, list) or not isinstance(choices[0], dict):
                raise RuntimeError("Invalid RunPod choice structure")
            text = choices[0].get("text", "")

            if not isinstance(text, str) or not text.strip():
                raise RuntimeError("RunPod returned an empty response")

            return text.strip()

        if status in ("FAILED", "CANCELLED", "TIMED_OUT"):
            raise RuntimeError(f"RunPod job failed: {status}")

        
        # Still waiting: check the job again after a short delay.
        time.sleep(min(3, max(0, deadline - time.monotonic())))

    # This section is OUTSIDE the while loop.
    # It runs only after the polling deadline expires.
    try:
        cancel_response = requests.post(
            f"{base_url}/cancel/{job_id}",
            headers=headers,
            timeout=5,
        )
        cancel_response.raise_for_status()
    except requests.RequestException:
        # Cancellation is best-effort.
        pass

    raise TimeoutError(
        f"RunPod job did not finish within {timeout_seconds:g} seconds"
    )
