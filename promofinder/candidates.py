import hashlib
from promofinder.models import Episode, Candidate, Segment
from promofinder.snapping import snap_candidate_boundaries

def make_candidate_id(segments: list[Segment]) -> str:
    s = "_".join(f"{seg.episode}:{seg.start:.2f}-{seg.end:.2f}" for seg in segments)
    return hashlib.sha256(s.encode()).hexdigest()[:12]

def generate_episode_candidates(
    episode: Episode,
    min_sec: float = 20.0,
    max_sec: float = 60.0,
    lead_in: float = 0.25,
    tail: float = 0.40
) -> list[Candidate]:
    candidates: list[Candidate] = []
    
    # Dialogue & Action blocks serve as start anchors
    start_anchors = [b for b in episode.blocks if b.kind in ["DIALOGUE", "ACTION"]]
    # Dialogue blocks serve as end anchors
    dia_blocks = [b for b in episode.blocks if b.kind == "DIALOGUE"]

    if not dia_blocks:
        return []

    last_dia_block = dia_blocks[-1]

    # Generate Type A: SINGLE
    for s_block in start_anchors:
        for e_block in dia_blocks:
            if e_block.end <= s_block.start:
                continue

            raw_duration = e_block.end - s_block.start
            if raw_duration < 18.0 or raw_duration > 62.0:
                continue

            snapped_s, snapped_e = snap_candidate_boundaries(
                episode, s_block.start, e_block.end, lead_in=lead_in, tail=tail
            )
            dur = snapped_e - snapped_s
            if min_sec <= dur <= max_sec:
                seg = Segment(episode=episode.number, start=snapped_s, end=snapped_e)
                cand_type = "EP_END" if e_block is last_dia_block else "SINGLE"
                candidates.append(Candidate(
                    id=make_candidate_id([seg]),
                    type=cand_type,
                    segments=[seg],
                    duration=round(dur, 2)
                ))

    return candidates
