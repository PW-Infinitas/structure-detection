# Synthetic Thai Government Letter Generator & Validator (IDP Pipeline)

This project aims to build a dual-system Intelligent Document Processing (IDP) pipeline:

- **The Generator:** Generates high-fidelity, realistic synthetic Thai government letters (หนังสือราชการ) based on templates, with support for custom layouts, handwriting simulation (signatures), dynamic data injection, and realistic physical distortions (camera perspective, shadows, folds).
- **The Validator:** Automatically parses, extracts, and validates the structure, keyword order, and logical correctness of these letters to assist in a personal loan approval workflow.

---

## Technical Stack

| Component | Technology |
|---|---|
| Language | Python 3.10+ |
| Templating | HTML5, CSS3, Jinja2 |
| Rendering | Playwright (HTML → high-res PNG) |
| Augmentation | OpenCV, PIL (Pillow), Augraphy |
| VLM (Sweep) | Gemini 2.5 Pro / 2.5 Flash via Vertex AI |

---

## Directory Structure

```
structure-detection/
│
├── overview.md
├── requirements.txt
│
├── assets/
│   ├── fonts/
│   │   ├── THSarabunNew.ttf
│   │   ├── THSarabunNew-Bold.ttf
│   │   └── LayijiHandwriting.ttf
│   └── images/
│       └── garuda_emblem.png
│
├── generator/
│   ├── __init__.py
│   ├── template.html          # Jinja2 HTML template
│   ├── styles.css             # A4 print layout CSS
│   ├── engine.py              # Renders template → high-res PNG (Playwright)
│   └── augmenter.py           # Applies folds, rotation, blur, shadows
│
├── validator/
│   ├── __init__.py
│   ├── rules_parser.py        # OCR-based keyword Y-coordinate checks
│   └── vlm_evaluator.py       # VLM prompt execution & JSON response parsing
│
├── mock_data/
│   ├── positive/              # Valid documents (correct structure)
│   └── negative/              # Invalid documents (intentional structural errors)
│
├── prompt-library/            # VLM prompt versions (to be written for this domain)
│
├── exp_running_scripts/       # Detachable sweep scripts (sweep1.py, sweep2.py, ...)
├── exp_running.py             # Core sweep runner (Gemini Vertex AI)
├── result_logger.py           # Append-only JSONL logger + image_labels.json join
├── image_labels.json          # Ground-truth labels keyed by image path
├── analysis_util.py           # Binary classification metrics (precision/recall/F1)
├── run_experiments.ipynb      # Interactive sweep launcher
├── augmentation_script.ipynb  # Augmentation pipeline notebook
└── analysis.ipynb             # Results analysis notebook
```

> **Note — carry-over files from previous project (payslip tampering):**
> `exp_running.py`, `result_logger.py`, `image_labels.json`, `analysis_util.py`, and
> `exp_running_scripts/` were ported from the payslip project. The sweep infrastructure
> is reusable as-is. The following will need domain adaptation before Phase 3:
> - `result_logger.py` — verdict choices (`tampered`/`authentic`) and signal types
> - `image_labels.json` — clear payslip entries, add Thai gov letter entries
> - `analysis_util.py` — `positive_class`/`negative_class` defaults
> - `prompt-library/` — rewrite entirely for structure validation (not forgery detection)

---

## Pipeline Phases

Work through these **one phase at a time**. Do not move to the next phase until you have reviewed the output of the current phase and are satisfied with the result.

---

### Phase 1 — Generator ✅ In Progress

**Goal:** Render realistic Thai government letters as high-res PNGs and verify they conform to official layout standards.

**Status:** `template.html` and `styles.css` complete. Assets in place. `engine.py` not yet written.

#### 1.1 CSS Layout Specifications

Official Thai government letters (A4 format) follow a strict structural protocol:

- **Dimensions:** Standard A4 (210mm × 297mm) with 2.5cm margins.
- **Header Line:**
  - The Garuda Emblem (ตราครุฑ) is centered at the top.
  - The Reference ID (เลขที่หนังสือ) starting with `ที่` must align to the far-left, on the same vertical baseline as the middle of the Garuda.
  - The Issuing Agency (ส่วนราชการ) must align to the far-right.
- **Date Block:** Located at the center-right of the page below the header, written in Thai Buddhist Era format (e.g., `23 ส.ค. 2569`).
- **Subject & Recipient Block:**
  - เรื่อง (Subject) aligns to the left margin.
  - เรียน (Recipient) aligns to the left margin, exactly below เรื่อง.
- **Body:** Paragraphs with a defined hanging indent (~2.5cm), justified text (`text-align: justify; text-justify: inter-character;`).
- **Signature Block:** Bottom right. Closing statement (ขอแสดงความนับถือ) → handwritten signature → printed name in parentheses → official title.

#### 1.2 Signature Simulation

```css
.signature-handwritten {
    font-family: 'LayijiHandwriting', cursive;
    color: #0d3895; /* Blue ink */
    font-size: 24px;
    transform: rotate(-3deg);
    display: inline-block;
    margin-left: 10px;
}
```

#### 1.3 `engine.py` — What to Build

- Load `template.html` + `styles.css` via Playwright.
- Inject a mock data dict (ref_id, agency, date, subject, recipient, body_paragraphs, signature_name, printed_name, title) using Jinja2.
- Render to a high-res PNG (A4 at 150–200 DPI equivalent).
- Output to `mock_data/positive/` or `mock_data/negative/` depending on the data variant.

#### Phase 1 Gate

Before proceeding to Phase 2: visually inspect at least one rendered PNG and confirm:
- Garuda centered, ref-id far-left, agency far-right on the same horizontal baseline
- Date block right-aligned
- เรื่อง / เรียน left-aligned and in correct vertical order
- Signature block in the lower-right quadrant
- Thai text renders correctly in TH Sarabun New

---

### Phase 2 — Augmentation

**Goal:** Distort the clean PNGs to simulate user-submitted mobile photos of paper documents.

**What to build:** `generator/augmenter.py`

| Effect | Implementation |
|---|---|
| Perspective warp | Slight random rotation (−2° to +2°) + corner-warping |
| Lighting / shadows | Radial or linear gradient overlay |
| Paper folds / creases | Subtle gray lines |
| Noise & blur | Gaussian blur + salt-and-pepper noise |

Output augmented images alongside their originals, clearly named (e.g., `letter_001_blur.png`).

#### Phase 2 Gate

Before proceeding to Phase 3: visually compare a set of augmented images against originals. Confirm the distortions look like realistic phone photos, not over-processed or unreadable.

---

### Phase 3 — VLM Sweep (Gemini via Vertex AI)

**Goal:** Test whether Gemini can reliably detect structural errors in Thai government letters given augmented images and a structured prompt.

**Domain adaptations required before this phase:**
1. Write new prompts in `prompt-library/` for structure validation (replace payslip forgery prompts).
2. Update `image_labels.json` — clear payslip entries, add Thai gov letter entries with labels (`valid` / `invalid`) and structural signal types (e.g., `wrong_keyword_order`, `missing_garuda`, `wrong_font`, `missing_ref_id`, `logic_inconsistency`).
3. Update `result_logger.py` — replace verdict set and `EXPECTED_SIGNAL_TYPES` with structure-detection equivalents.
4. Update `analysis_util.py` — change `positive_class` / `negative_class` defaults to `invalid` / `valid`.

**Sweep infrastructure** (reuse as-is from `exp_running.py`):
- Models: `gemini-2.5-pro`, `gemini-2.5-flash`
- Run via detachable `tmux` session: `caffeinate -i & tmux new -s sweep && python sweep.py`
- Results append to `notebook_results/results_log.jsonl`

#### Phase 3 Gate

Before proceeding to Phase 4: confirm that results are logging correctly and at least one full sweep over the image set has completed.

---

### Phase 4 — Analysis & Potential Iteration

**Goal:** Evaluate sweep results and decide whether the prompt, model choice, or data quality needs to change before committing to a validator.

**What to do:**
1. Load results in `analysis.ipynb` using `result_logger.load_results()`.
2. Compute metrics per model and prompt version using `analysis_util.compute_binary_metrics()`.
3. Check: format compliance rate, accuracy, precision, recall, F1.
4. Identify failure patterns — which error types (negative classes) are the model missing or hallucinating on?

**Likely iteration triggers:**
- Low format compliance → tighten the prompt's output schema instructions
- High false negative rate on a specific negative class (e.g., wrong_font) → add explicit examples or chain-of-thought steps for that signal
- One model clearly outperforms → drop the weaker model from further sweeps
- Results are good enough → proceed to Phase 5 without iteration

This phase may loop back to Phase 3 one or more times before the prompt and model are stable.

#### Phase 4 Gate

Before proceeding to Phase 5: the best-performing (model + prompt) combo must show satisfactory accuracy and recall on all four negative class types. Document the chosen model and final prompt version.

---

### Phase 5 — Validator

**Goal:** Build the production-grade validator that classifies real submitted letters using the model and prompt selected in Phase 4.

**Two modes:**

**Mode A — Rules-Based OCR (Fast)**
1. Feed image to OCR engine (Google Cloud Vision API).
2. Retain bounding box Y-coordinates for: `ที่`, `เรื่อง`, `เรียน`, `ขอแสดงความนับถือ`.
3. Verify: `Y(ที่) < Y(เรื่อง) < Y(เรียน) < Y(ขอแสดงความนับถือ)` and signature block X > 50% width.

**Mode B — Native VLM (Recommended)**
1. Pass image directly to the chosen Gemini model.
2. Use the final prompt version from Phase 4.
3. Parse the JSON response and return a structured verdict.

**What to build:** `validator/rules_parser.py` (Mode A) and `validator/vlm_evaluator.py` (Mode B).

---

## Data Split Strategy

Generate a synthetic dataset with a **50/50 split** of valid and invalid classes:

**Class 1 — Positive (Valid)**
- Correct keyword order
- Correct official fonts (TH Sarabun New)
- Realistic dynamic Thai text with valid loan applicant details

**Class 2 — Negative (Invalid — broken intentionally)**

| Type | Description |
|---|---|
| Type A — Structural Out-of-Order | เรียน placed above เรื่อง, or signature block on the far-left |
| Type B — Missing Elements | No ที่ reference number, or missing the Garuda logo |
| Type C — Font Fraud | Informal Thai font (Prompt or Kanit) instead of TH Sarabun New |
| Type D — Logic Inconsistency | Impossible date (e.g., year 3000 BE), or printed name doesn't match body |

---

## Keyword Order Protocol (for both Generator and Validator)

The correct sequential flow of keywords in a valid letter:

```
ที่ → เรื่อง → เรียน → ขอแสดงความนับถือ → (พิมพ์ชื่อ) → ตำแหน่ง
```
