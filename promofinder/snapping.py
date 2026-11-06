from promofinder.models import Episode, Block

def snap_candidate_boundaries(
    episode: Episode,
    raw_start: float,
    raw_end: float,
    lead_in: float = 0.25,
    tail: float = 0.40,
    max_tail_extend: float = 2.0
) -> tuple[float, float]:
    """
    Applies boundary snapping:
    - Start: raw_start - lead_in. If CAMERA block starts within 0.5s before, snap to camera cut.
    - End: raw_end + tail. If CAMERA reaction/close-up or SOUND starts within 0.6s after, include it up to max_tail_extend.
    """
    snapped_start = max(0.0, raw_start - lead_in)

    # Preceding camera check
    cam_blocks = [b for b in episode.blocks if b.kind == "CAMERA"]
    for cb in cam_blocks:
        if 0.0 <= (raw_start - cb.start) <= 0.6:
            snapped_start = min(snapped_start, cb.start)
            break

    snapped_end = min(episode.duration, raw_end + tail)

    # Reaction camera or sound stinger check
    reaction_blocks = [
        b for b in episode.blocks
        if b.kind in ["CAMERA", "SOUND"] and b.start >= raw_end and b.start <= raw_end + 0.8
    ]
    if reaction_blocks:
        # Extend to end of the earliest reaction block up to max_tail_extend
        first_reaction = reaction_blocks[0]
        extended = min(first_reaction.end, raw_end + max_tail_extend)
        snapped_end = max(snapped_end, extended)

    return round(snapped_start, 2), round(snapped_end, 2)
