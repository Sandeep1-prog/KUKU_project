from promofinder.models import Episode, Candidate
from promofinder.enrich import LexiconManager

LOW_INFO_STARTS = {"yes", "no", "okay", "ok", "hello", "hi", "well"}

def passes_hard_filters(
    candidate: Candidate,
    episode: Episode,
    lex: LexiconManager,
    max_ep_fraction: float = 0.70,
    total_episodes: int = 50
) -> tuple[bool, str]:
    """
    Checks all non-negotiable hard rules. Returns (is_valid, reject_reason).
    """
    # 1. Duration check
    if not (20.0 <= candidate.duration <= 60.0):
        return False, f"Duration {candidate.duration:.1f}s not in [20, 60]"

    # 2. Spoiler cutoff check
    if episode.number > int(total_episodes * max_ep_fraction):
        return False, f"Episode {episode.number} exceeds spoiler cutoff ({int(total_episodes * max_ep_fraction)})"

    # Blocks inside first segment
    seg = candidate.segments[0]
    blocks_in_win = [
        b for b in episode.blocks
        if not (b.end <= seg.start or b.start >= seg.end)
    ]
    if not blocks_in_win:
        return False, "No blocks in segment window"

    dia_blocks = [b for b in blocks_in_win if b.kind == "DIALOGUE"]
    if not dia_blocks:
        return False, "No dialogue in candidate"

    # 3. Hook gate: Dialogue or action starts within 3.0s of window start
    first_block = blocks_in_win[0]
    first_start_diff = first_block.start - seg.start
    if first_start_diff > 3.0:
        return False, f"No line/action within 3.0s of start ({first_start_diff:.2f}s)"

    # 4. No cold mid-sentence: first line not starting lowercase
    first_line = dia_blocks[0]
    first_text = first_line.text.strip()
    if first_text and first_text[0].islower():
        return False, "First line starts with lowercase (mid-sentence)"

    # 5. Not a dead start: "Yes", "No", "Okay" unless high emotion
    first_word = first_text.split()[0].lower().strip(",.!?") if first_text else ""
    if first_word in LOW_INFO_STARTS:
        intensity = lex.get_emotion_intensity(first_line.emotion_tags)
        if intensity < 0.70:
            return False, f"Dead start on low-info word '{first_word}' with low intensity {intensity:.2f}"

    # 6. Not a resolution ending
    last_line = dia_blocks[-1]
    last_text_lower = last_line.text.lower()
    for rw in lex.resolution_words:
        if rw in last_text_lower:
            return False, f"Ends on resolution phrase '{rw}'"

    return True, "OK"
