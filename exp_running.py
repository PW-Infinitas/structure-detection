"""Runs one (image, prompt_version, model, temperature) experiment and logs the result."""

import time
from dataclasses import dataclass
from typing import Literal

from google import genai
from google.genai import types
from google.genai.errors import ClientError
from PIL import Image

from result_logger import log_result

# --- Rate limit handling ---
# We don't know our Vertex AI quota tier (RPM/TPM) upfront, and gemini-2.5-pro
# typically has a much lower per-minute limit than gemini-2.5-flash. Rather than
# guessing a fixed delay between every call, we only slow down when we actually
# hit a 429 (rate limit exceeded), then back off exponentially and retry —
# this self-adapts to whatever quota we actually have.
MAX_RATE_LIMIT_RETRIES = 3
INITIAL_BACKOFF_S = 5.0


@dataclass
class PromptVersion:
    """One prompt variant to test.

    mode="combined": `content` is sent as a single string alongside the image.
    mode="split": `system` is sent as the system_instruction, `task` as the user turn.
    """

    prompt_id: str
    mode: Literal["combined", "split"]
    content: str | None = None
    system: str | None = None
    task: str | None = None


def run_experiment(
    client: genai.Client,
    image_path: str,
    image: Image.Image,
    prompt_version: PromptVersion,
    model: str,
    temperature: float,
    batch_id: str,
) -> None:
    """Call the model for one (image, prompt_version, model, temperature) combo and log the result."""
    if prompt_version.mode == "combined":
        contents = [prompt_version.content, image]
        config = types.GenerateContentConfig(temperature=temperature)
    else:
        contents = [prompt_version.task, image]
        config = types.GenerateContentConfig(
            system_instruction=prompt_version.system,
            temperature=temperature,
        )

    backoff_s = INITIAL_BACKOFF_S

    for attempt in range(MAX_RATE_LIMIT_RETRIES + 1):
        start = time.perf_counter()

        try:
            response = client.models.generate_content(model=model, contents=contents, config=config)
        except ClientError as error:
            # 429 = rate limit exceeded: wait and retry with exponential backoff
            # (5s, 10s, 20s, ...), since the limit is per-minute and may clear soon.
            if error.code == 429 and attempt < MAX_RATE_LIMIT_RETRIES:
                print(
                    f"Rate limited ({prompt_version.prompt_id}, {model}, T={temperature}); "
                    f"retrying in {backoff_s:.0f}s (attempt {attempt + 1}/{MAX_RATE_LIMIT_RETRIES})"
                )
                time.sleep(backoff_s)
                backoff_s *= 2
                continue

            # Non-429 client error, or retries exhausted: log as a failed
            # result so the sweep can continue, instead of crashing the loop.
            log_result(
                batch_id=batch_id,
                image_path=image_path,
                prompt_id=prompt_version.prompt_id,
                model=model,
                temperature=temperature,
                raw_response=f"ERROR: {error}",
                latency_s=round(time.perf_counter() - start, 2),
                notes="API call failed",
            )
            return
        except Exception as error:
            # Any other error (server error, network issue, etc.): same
            # fail-and-continue handling as above.
            log_result(
                batch_id=batch_id,
                image_path=image_path,
                prompt_id=prompt_version.prompt_id,
                model=model,
                temperature=temperature,
                raw_response=f"ERROR: {error}",
                latency_s=round(time.perf_counter() - start, 2),
                notes="API call failed",
            )
            return

        latency_s = round(time.perf_counter() - start, 2)
        log_result(
            batch_id=batch_id,
            image_path=image_path,
            prompt_id=prompt_version.prompt_id,
            model=model,
            temperature=temperature,
            raw_response=response.text,
            latency_s=latency_s,
        )
        print(f"{image_path} | {prompt_version.prompt_id} | {model} | T={temperature} -> logged ({latency_s}s)")
        return
