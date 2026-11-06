# PromoFinder: Automated Promo Selection for Microdrama

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Live App](https://img.shields.io/badge/Live%20Dashboard-GitHub%20Pages-brightgreen)](https://sandeep1-prog.github.io/KUKU_project/)

A deterministic, local-first engine that parses full episodic microdrama screenplays and discovers, snaps, scores, and ranks 20–60 second viral promotional clips (hooks & cliffhangers) for TikTok, Instagram Reels, and YouTube Shorts.

- **Live Web Dashboard:** [https://sandeep1-prog.github.io/KUKU_project/](https://sandeep1-prog.github.io/KUKU_project/)
- **Runtime:** **4.61 seconds** on CPU across 50 full episodes (3,727 blocks) at **$0.00 cost** (no mandatory API calls).
- **Core Principle:** Deterministic rules and boundary snapping first; optional pluggable LLM layer for shortlist judging.

---

## Architecture Overview

```
episodes/*.txt
     │
[1. Parser] ──────────► Dialogue, Camera, and Action objects with sub-second timestamps
     │
[2. Enricher] ────────► Emotional intensity scoring & 1-second rolling tension curves
     │
[3. Candidate Gen] ───► Sliding 20–60s windows anchored on dialogue & action beats
     │
[4. Snapping & Filter]► Boundary snapping (pre-camera cuts, reaction holds) & hard gates
     │
[5. Feature Scorer] ──► Hook (0-3s), Cliffhanger (last 5s), Clarity, and Intensity
     │
[6. Ranker & Filter] ─► Temporal IoU deduplication (<=0.20) & per-episode diversity caps
     │
[7. Deliverables] ────► promos.json, promos.csv, report.md, interactive dashboard
```

---

## 3-Stage Narrative Posting Sequence

To prevent plot spoilers while maximizing viewer retention across social media campaigns, candidate clips are organized into a 3-stage sequence:

| Stage | Episodes | Focus | Key Example |
|---|---|---|---|
| **1. Initial Hook** | Eps 1–16 | Betrayal & Humiliation (0 context needed) | **Ep 1 (00:35–01:20):** *"Why are you holding her hand?"* $\rightarrow$ *"Father..."* |
| **2. Rising Action** | Eps 17–33 | The "broken soldier" husband defends Juliana | **Ep 15 (00:53–01:24):** *"What? You want to fight us, veteran?!"* |
| **3. Pre-Climax** | Eps 34–38 | High-stakes courtroom inquiry cut at the key question | **Ep 34 (00:37–01:17):** *"And did she speak words you could not understand?"* |

*Note: Episodes 39–50 are strictly excluded from promo circulation to protect the series finale resolution.*

---

## Quickstart & Local Execution

### 1. Prerequisites
- Python 3.10+
```bash
pip install -r requirements.txt
```

### 2. Run the Engine CLI
Run the full discovery, scoring, and ranking pipeline across all 50 episodes:
```bash
python -m promofinder.cli --top 20
```

### 3. Launch Local Review App
Run the local Streamlit dashboard:
```bash
python -m streamlit run app.py
```
Or open the static web dashboard (`index.html`) directly in your browser.

### 4. Run Unit Tests
```bash
python -m pytest tests
```

---

## Deliverables & Outputs

Every run produces clean, unedited deliverables in the `out/` directory:
- **`out/promos.json`**: Structured JSON payload containing exact `MM:SS.cc` timestamps, duration, scores, matched lexical evidence, and explanations.
- **`out/promos.csv`**: Flat table formatted for editorial review and video cutters.
- **`out/report.md`**: Human-readable markdown summary report.
- **`SOLUTION_DOCUMENT.md`**: Detailed technical solution document evaluated across all 5 evaluation lenses.
- **`QUALITY_EVALUATION.md`**: Failure mode analysis detailing edge cases and areas where heuristic tools struggle.

---

## Repository Structure

```
├── promofinder/               # Core engine package
│   ├── models.py              # Pydantic data models (Episode, Block, Candidate)
│   ├── parser.py              # Screenplay regex parser
│   ├── snapping.py            # Pre-camera & tail reaction cut snapping
│   ├── enrich.py              # Emotion intensity & rolling tension curves
│   ├── candidates.py          # 20-60s window generator
│   ├── filters.py             # Non-negotiable hard constraint filters
│   ├── scoring.py             # Hook, cliffhanger, clarity, and intensity scorers
│   ├── rank.py                # Temporal IoU deduplication & tiering
│   ├── report.py              # Export generators (JSON, CSV, MD)
│   ├── util_time.py           # Timestamp parser and formatter
│   └── cli.py                 # Command-line interface entry point
├── config/
│   ├── default.yaml           # Pipeline weights and thresholds
│   └── lexicons/              # Domain-tuned emotional and lexical dictionaries
├── tests/
│   └── test_pipeline.py       # Pytest suite verifying invariants and parsing
├── out/                       # Unedited run deliverables
│   ├── promos.json
│   ├── promos.csv
│   └── report.md
├── index.html                 # Minimal, clean standalone web dashboard
├── app.py                     # Streamlit review dashboard
├── requirements.txt           # Python dependencies
├── SOLUTION_DOCUMENT.md       # Complete evaluation document
└── QUALITY_EVALUATION.md      # Honest failure analysis
```

---

## Confidentiality Note
Per assignment guidelines, raw screenplay files are excluded from this repository via `.gitignore`.
