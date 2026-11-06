from promofinder.models import ScoredCandidate

def compute_temporal_iou(seg_a, seg_b) -> float:
    if seg_a.episode != seg_b.episode:
        return 0.0
    start_inter = max(seg_a.start, seg_b.start)
    end_inter = min(seg_a.end, seg_b.end)
    inter = max(0.0, end_inter - start_inter)
    if inter == 0.0:
        return 0.0
    min_len = min(seg_a.duration, seg_b.duration)
    return inter / min_len

def rank_and_diversify(
    scored_candidates: list[ScoredCandidate],
    top_k: int = 20,
    per_episode_cap: int = 2,
    overlap_max: float = 0.20
) -> list[ScoredCandidate]:
    """
    Ranks by final_score and applies greedy selection:
    - Time overlap with selected promo in same episode <= overlap_max
    - Per episode cap <= per_episode_cap
    - Mix constraint: at least 3 distinct episodes in top 10
    """
    sorted_cands = sorted(scored_candidates, key=lambda sc: sc.final_score, reverse=True)
    selected: list[ScoredCandidate] = []
    ep_counts: dict[int, int] = {}

    for cand in sorted_cands:
        if len(selected) >= top_k:
            break

        ep = cand.candidate.segments[0].episode
        if ep_counts.get(ep, 0) >= per_episode_cap:
            continue

        # Overlap check
        is_overlapping = False
        seg_c = cand.candidate.segments[0]
        for sel in selected:
            seg_s = sel.candidate.segments[0]
            if compute_temporal_iou(seg_c, seg_s) > overlap_max:
                is_overlapping = True
                break

        if is_overlapping:
            continue

        selected.append(cand)
        ep_counts[ep] = ep_counts.get(ep, 0) + 1

    # Assign tiers
    for idx, sc in enumerate(selected):
        rank = idx + 1
        if rank <= 5:
            sc.tier = "POST_FIRST"
        elif rank <= 15:
            sc.tier = "STRONG"
        else:
            sc.tier = "BACKUP"

    return selected
