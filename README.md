# PromoFinder — Microdrama Promo Generation Engine

Automated, deterministic, local-first engine that parses episodic microdrama screenplays and discovers, scores, and ranks 20–60 second viral promo clips (hooks & cliffhangers) for TikTok, Instagram Reels, and YouTube Shorts.

Tested on **50 full screenplay episodes** of *"I Married a Broken Soldier. He was a Duke"*.

---

## 🚀 Quickstart & How to Run

### 1. Prerequisites
- Python 3.10+
- Install dependencies:
```bash
pip install -r requirements.txt
```

### 2. Run PromoFinder CLI
To run the full end-to-end pipeline across all 50 episodes and generate ranked promo moments:
```bash
python -m promofinder.cli --top 20
```

To specify custom input/output directories:
```bash
python -m promofinder.cli --input "I Married a Broken Soldier. He was a Duke-script/I Married a Broken Soldier. He was a Duke" --out out --top 20
```

### 3. Run Automated Tests
```bash
python -m pytest tests
```

---

## 📊 Outputs & Deliverables

Every run produces clean unedited deliverables in the `out/` folder:
- **`out/promos.json`**: Complete structured output with episode numbers, exact `MM:SS.cc` timestamps, duration, scores, matched lexical evidence, and explanations.
- **`out/promos.csv`**: Flat spreadsheet formatted for editorial review and video cutters.
- **`out/report.md`**: Human-readable breakdown of the top promos, ranked by tiers (`POST_FIRST`, `STRONG`, `BACKUP`).
- **`QUALITY_EVALUATION.md`**: Evaluation report detailing failure modes, soft-cliffhanger edge cases, and quality limitations.

---

## 🏆 Top Picks to Post First

| Rank | Tier | Ep | Timestamps | Duration | Opening Hook (0-3s) | Cliffhanger Cut Point |
|:---:|:---:|:---:|:---:|:---:|:---|:---|
| **1** | `POST_FIRST` | **Ep 1** | `00:35.15` - `01:20.50` | 45.35s | *Juliana: "Why are you holding her hand?" / Clarissa: "Because he is marrying me."* | *Juliana: "Father..."* |
| **2** | `POST_FIRST` | **Ep 34** | `00:37.25` - `01:17.50` | 40.25s | *Judge: "Prudence. You served beside the accused?"* | *Judge: "And did she speak words you could not understand?"* |
| **3** | `POST_FIRST` | **Ep 2** | `00:00.00` - `00:34.20` | 34.20s | *Gerald: "I cannot marry you, Juliana."* | *Juliana (O.S.): "Father..."* |
| **4** | `POST_FIRST` | **Ep 3** | `00:13.55` - `00:43.30` | 29.75s | *Clarissa: "I didn't steal what was never truly yours."* | *Juliana: "Leave where?"* |
| **5** | `POST_FIRST` | **Ep 2** | `00:47.55` - `01:18.40` | 30.85s | *Clarissa: "Why are you surprised, sister? Look at you."* | *Juliana: "You abandoned a woman who trusted you..."* |

---

## 🏗 Architecture & Scoring Engine
1. **Parser (`promofinder/parser.py`)**: Robust screenplay parser extracting camera angles, actions, characters, dialogue, and emotions with sub-second timestamps.
2. **Enricher (`promofinder/enrich.py`)**: Tension curves, shot frequencies, and emotion intensity modeling.
3. **Candidate Generator (`promofinder/candidates.py`)**: Sub-minute segment windowing with boundary snapping (`snapping.py`).
4. **Scorer & Filter (`promofinder/scoring.py`, `filters.py`)**: Evaluates hook power, cliffhangers, clarity, and spoiler risks using domain-tuned lexicons.
5. **Ranker & Diversifier (`promofinder/rank.py`)**: Temporal IoU overlap suppression, per-episode caps, and tier assignment.
