import json
import csv
from pathlib import Path
from promofinder.models import ScoredCandidate
from promofinder.util_time import format_timestamp

def write_reports(
    promos: list[ScoredCandidate],
    out_dir: Path,
    total_candidates_evaluated: int = 0
):
    out_dir.mkdir(parents=True, exist_ok=True)
    debug_dir = out_dir / "debug"
    debug_dir.mkdir(exist_ok=True)

    # 1. promos.json
    promos_json_data = []
    for rank, sc in enumerate(promos, start=1):
        seg = sc.candidate.segments[0]
        promos_json_data.append({
            "rank": rank,
            "tier": sc.tier,
            "id": sc.candidate.id,
            "type": sc.candidate.type,
            "duration_sec": sc.candidate.duration,
            "segments": [{
                "episode": seg.episode,
                "start": format_timestamp(seg.start),
                "end": format_timestamp(seg.end),
                "start_sec": seg.start,
                "end_sec": seg.end
            }],
            "hook": sc.hook_line,
            "cliffhanger": sc.cliffhanger_line,
            "why_it_works": sc.why_it_works,
            "scores": {
                "hook": sc.features.hook,
                "cliffhanger": sc.features.cliffhanger,
                "clarity": sc.features.clarity,
                "intensity": sc.features.intensity,
                "spoiler_risk": sc.features.spoiler_risk,
                "final": sc.final_score
            },
            "evidence": sc.features.evidence
        })

    with open(out_dir / "promos.json", "w", encoding="utf-8") as f:
        json.dump(promos_json_data, f, indent=2)

    # 2. promos.csv
    with open(out_dir / "promos.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Rank", "Tier", "Episode", "Start", "End", "Duration (s)",
            "Final Score", "Hook Score", "Cliffhanger Score", "Clarity", "Hook", "Cliffhanger", "Why It Works"
        ])
        for p in promos_json_data:
            s0 = p["segments"][0]
            writer.writerow([
                p["rank"], p["tier"], s0["episode"], s0["start"], s0["end"], p["duration_sec"],
                p["scores"]["final"], p["scores"]["hook"], p["scores"]["cliffhanger"], p["scores"]["clarity"],
                p["hook"], p["cliffhanger"], p["why_it_works"]
            ])

    # 3. report.md
    with open(out_dir / "report.md", "w", encoding="utf-8") as f:
        f.write("# Top Ranked Microdrama Promo Clips\n\n")
        f.write(f"Total candidates evaluated: {total_candidates_evaluated}\n\n")
        f.write("| Rank | Tier | Ep | Timestamps | Dur | Final | Hook | Cliff | Reason |\n")
        f.write("|---|---|---|---|---|---|---|---|---|\n")
        for p in promos_json_data:
            s0 = p["segments"][0]
            f.write(f"| {p['rank']} | **{p['tier']}** | Ep {s0['episode']} | `{s0['start']}` - `{s0['end']}` | {p['duration_sec']}s | {p['scores']['final']:.2f} | {p['scores']['hook']:.2f} | {p['scores']['cliffhanger']:.2f} | {p['why_it_works']} |\n")

        f.write("\n\n## Detailed Breakdown for Top 5 Promos (POST_FIRST)\n\n")
        for p in promos_json_data[:5]:
            s0 = p["segments"][0]
            f.write(f"### Rank {p['rank']} - Episode {s0['episode']} ({s0['start']} to {s0['end']})\n")
            f.write(f"- **Tier**: {p['tier']}\n")
            f.write(f"- **Duration**: {p['duration_sec']} seconds\n")
            f.write(f"- **Hook**: {p['hook']}\n")
            f.write(f"- **Cliffhanger**: {p['cliffhanger']}\n")
            f.write(f"- **Why It Works**: {p['why_it_works']}\n")
            f.write(f"- **Scores**: Final `{p['scores']['final']}` | Hook `{p['scores']['hook']}` | Cliffhanger `{p['scores']['cliffhanger']}` | Clarity `{p['scores']['clarity']}` | Intensity `{p['scores']['intensity']}`\n\n")
