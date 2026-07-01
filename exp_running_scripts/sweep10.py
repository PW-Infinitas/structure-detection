"""Full experiment sweep — production-safe replacement for run_experiments.ipynb sweep cells.

Usage:
    caffeinate -i &          # prevent Mac sleep
    tmux new -s sweep        # create detachable session
    python sweep.py          # run
    Ctrl+B then D            # detach (script keeps running)
    tmux attach -t sweep     # reconnect anytime
"""

import sys
import time

from google import genai
from PIL import Image

from exp_running import PromptVersion, run_experiment

# ---------------------------------------------------------------------------
# EDIT THESE before each run
# ---------------------------------------------------------------------------

BATCH_ID = "slip10"  # must match the batch name you want in the log
N_ITERATIONS = 5



path_batch2: list[str] = [
    "test_images/payslip1.jpeg",
    "test_images/payslip10.jpeg",
    "test_images/payslip2.png",
    "test_images/payslip20.png",
    "test_images/payslip3.png",
    "test_images/payslip30.png",
]

augmented_slips: list[str] = ["test_images/payslip10.jpeg",
   'test_images_augmented/by_technique/payslip10_rotation.jpeg',
 'test_images_augmented/by_technique/payslip10_jpeg_compression.jpeg',
 'test_images_augmented/by_technique/payslip10_gaussian_blur.jpeg',
]

# Set which image paths this run covers
paths: list[str] = augmented_slips

models: list[str] = [
    "gemini-2.5-pro",
    "gemini-3.5-flash",
    "gemini-3.1-pro-preview",
]

temperatures: list[float] = [0.1]

# ---------------------------------------------------------------------------
# Prompt loading
# ---------------------------------------------------------------------------

def _read_prompt(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


prompt_v1 = _read_prompt("prompt-library/V1.txt")
system_prompt_v1 = _read_prompt("prompt-library/V1_system.txt")
task_prompt_v1 = _read_prompt("prompt-library/V1_task.txt")

prompt_v2 = _read_prompt("prompt-library/V2.txt")
system_prompt_v2 = _read_prompt("prompt-library/V2_system.txt")
task_prompt_v2 = _read_prompt("prompt-library/V2_task.txt")

# Uncomment / add versions to expand the sweep
prompt_versions: list[PromptVersion] = [
    # PromptVersion(prompt_id="V1",       mode="combined", content=prompt_v1),
    # PromptVersion(prompt_id="V1_split", mode="split",    system=system_prompt_v1, task=task_prompt_v1),
    PromptVersion(prompt_id="V2",       mode="combined", content=prompt_v2),
    # PromptVersion(prompt_id="V2_split", mode="split", system=system_prompt_v2, task=task_prompt_v2),
]

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    client = genai.Client(
        vertexai=True,
        project="infinitas-ds-ai-poc",
        location="global",
    )

    images = [Image.open(p) for p in paths]
    image_list = list(zip(paths, images))

    combos: list[tuple[str, str, Image.Image, PromptVersion, float]] = [
        (model, image_path, image, pv, temp)
        for model in models
        for image_path, image in image_list
        for pv in prompt_versions
        for temp in temperatures
    ]

    total = len(combos) * N_ITERATIONS

    print(f"{'=' * 60}")
    print(f"Sweep start  |  batch={BATCH_ID}  |  iterations={N_ITERATIONS}")
    print(f"Total calls  : {total}")
    print(f"{'=' * 60}")
    sys.stdout.flush()

    sweep_start = time.perf_counter()
    call_num = 0

    for iteration in range(1, N_ITERATIONS + 1):
        print(f"--- Iteration {iteration}/{N_ITERATIONS} ---")
        sys.stdout.flush()
        for model, image_path, image, pv, temp in combos:
            run_experiment(client, image_path, image, pv, model, temp, BATCH_ID)
            call_num += 1

            elapsed = time.perf_counter() - sweep_start
            avg_s = elapsed / call_num
            eta_h = ((total - call_num) * avg_s) / 3600
            print(f"  [{call_num}/{total}] ETA: {eta_h:.1f}h")
            sys.stdout.flush()

    elapsed_total = (time.perf_counter() - sweep_start) / 3600
    print(f"{'=' * 60}")
    print(f"Sweep complete. {total} calls in {elapsed_total:.1f}h.")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
