import re
from pathlib import Path
from promofinder.models import Episode, Scene, Block
from promofinder.util_time import parse_timestamp

SHOT_TYPES = [
    "extreme close-up", "close-up", "insert", "medium close-up", "medium",
    "wide", "over-the-shoulder", "low-angle", "tracking", "pan", "push-in",
    "cut to black", "pov"
]

def derive_shot_type(text: str) -> str | None:
    text_lower = text.lower()
    for st in SHOT_TYPES:
        if st in text_lower:
            return st
    return "shot"

def parse_episode_file(file_path: Path) -> Episode:
    content = file_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    ep_num = 0
    # Fallback from filename
    m_fn = re.search(r"episode-(\d+)", file_path.name, re.IGNORECASE)
    if m_fn:
        ep_num = int(m_fn.group(1))

    logline = ""
    continuity = ""
    warnings: list[str] = []

    # Read header before SCRIPT START
    script_start_idx = 0
    for idx, line in enumerate(lines):
        line_clean = line.strip()
        if line_clean.startswith("--- SCRIPT START ---"):
            script_start_idx = idx + 1
            break
        if line_clean.startswith("EPISODE NUMBER:"):
            m = re.search(r"Episode\s+(\d+)", line_clean, re.IGNORECASE)
            if m:
                ep_num = int(m.group(1))
        elif line_clean.startswith("EPISODE LOGLINE:"):
            logline = line_clean.replace("EPISODE LOGLINE:", "").strip()
        elif line_clean.startswith("CONTINUITY NOTES:"):
            continuity = line_clean.replace("CONTINUITY NOTES:", "").strip()

    scenes: list[Scene] = []
    blocks: list[Block] = []

    current_scene_num = 1
    current_scene_heading = ""
    current_scene_start = 0.0
    current_scene_end = 0.0

    i = script_start_idx
    total_lines = len(lines)

    time_regex = re.compile(r"Start:\s*(\([^)]+\)|[^\s|]+)\s*\|\s*End:\s*(\([^)]+\)|[^\s|]+)")

    while i < total_lines:
        line = lines[i].strip()

        if not line:
            i += 1
            continue

        # Scene headers
        if line.startswith("SCENE "):
            sm = re.search(r"SCENE\s+(\d+)", line)
            if sm:
                current_scene_num = int(sm.group(1))
            i += 1
            continue
        if line.startswith("Scene heading:"):
            current_scene_heading = line.replace("Scene heading:", "").strip()
            i += 1
            continue
        if line.startswith("Scene start:"):
            ts_str = line.replace("Scene start:", "").strip()
            current_scene_start = parse_timestamp(ts_str)
            i += 1
            continue
        if line.startswith("Scene end:"):
            ts_str = line.replace("Scene end:", "").strip()
            current_scene_end = parse_timestamp(ts_str)
            scenes.append(Scene(
                number=current_scene_num,
                heading=current_scene_heading,
                start=current_scene_start,
                end=current_scene_end
            ))
            i += 1
            continue

        # Block headers: **HEADER:**
        block_match = re.match(r"^\*\*(.+?):\*\*\s*$", line)
        if block_match:
            raw_header = block_match.group(1).strip()
            # Next line must be timestamp
            if i + 1 < total_lines:
                time_line = lines[i + 1].strip()
                tm = time_regex.search(time_line)
                if tm:
                    start_str, end_str = tm.group(1), tm.group(2)
                    start_sec = parse_timestamp(start_str)
                    end_sec = parse_timestamp(end_str)
                    if start_sec > end_sec:
                        warnings.append(f"Swapped timestamps {start_sec} > {end_sec} at line {i+2}")
                        start_sec, end_sec = end_sec, start_sec

                    # Collect block text lines until next blank line or next block/scene
                    i += 2
                    text_lines = []
                    while i < total_lines:
                        l = lines[i].strip()
                        if not l:
                            break
                        if l.startswith("**") or l.startswith("SCENE "):
                            break
                        text_lines.append(l)
                        i += 1
                    
                    block_text = " ".join(text_lines).strip()

                    # Classify block
                    if raw_header == "CAMERA":
                        st = derive_shot_type(block_text)
                        blocks.append(Block(
                            kind="CAMERA",
                            start=start_sec,
                            end=end_sec,
                            text=block_text,
                            shot_type=st
                        ))
                    elif raw_header == "ACTION":
                        blocks.append(Block(
                            kind="ACTION",
                            start=start_sec,
                            end=end_sec,
                            text=block_text
                        ))
                    elif raw_header in ["SOUND", "SOUND FX"]:
                        blocks.append(Block(
                            kind="SOUND",
                            start=start_sec,
                            end=end_sec,
                            text=block_text
                        ))
                    else:
                        # Dialogue block: SPEAKER (Emotion, Tags)
                        # e.g. "MATRIARCH (Cold, Commanding)" or "GERALD (O.S.) (Bitter)"
                        is_os = "(O.S.)" in raw_header
                        clean_hdr = raw_header.replace("(O.S.)", "").strip()

                        dia_m = re.match(r"^(?P<speaker>[^()]+?)(?:\s*\((?P<emotion>[^)]*)\))?$", clean_hdr)
                        if dia_m:
                            speaker = dia_m.group("speaker").strip()
                            raw_emotion = dia_m.group("emotion")
                            emotions = [e.strip() for e in raw_emotion.split(",")] if raw_emotion else []
                        else:
                            speaker = clean_hdr
                            emotions = []

                        # Strip surrounding quotes from dialogue text
                        dialogue_content = block_text.strip().strip('"').strip("'")
                        blocks.append(Block(
                            kind="DIALOGUE",
                            start=start_sec,
                            end=end_sec,
                            text=dialogue_content,
                            speaker=speaker,
                            is_offscreen=is_os,
                            emotion_tags=emotions
                        ))
                    continue
                else:
                    warnings.append(f"Block '{raw_header}' missing valid timestamp at line {i+2}")
            else:
                warnings.append(f"Unexpected end of file at line {i+1}")

        i += 1

    # Sort blocks by start time
    blocks.sort(key=lambda b: (b.start, 0 if b.kind == "CAMERA" else 1))
    max_duration = max((b.end for b in blocks), default=0.0)

    return Episode(
        number=ep_num,
        logline=logline,
        continuity_notes=continuity,
        duration=max_duration,
        scenes=scenes,
        blocks=blocks,
        warnings=warnings
    )

def parse_all_episodes(directory: Path) -> list[Episode]:
    files = sorted(directory.glob("*.txt"), key=lambda f: f.name)
    episodes = [parse_episode_file(f) for f in files]
    episodes.sort(key=lambda ep: ep.number)
    return episodes
