def parse_timestamp(time_str: str) -> float:
    """Parses (MM:SS.cc) or MM:SS.cc to seconds."""
    s = time_str.strip().strip("()")
    parts = s.split(":")
    if len(parts) == 2:
        minutes = int(parts[0])
        secs = float(parts[1])
        return round(minutes * 60 + secs, 2)
    elif len(parts) == 3:
        hours = int(parts[0])
        minutes = int(parts[1])
        secs = float(parts[2])
        return round(hours * 3600 + minutes * 60 + secs, 2)
    return float(s)

def format_timestamp(seconds: float) -> str:
    """Formats seconds to MM:SS.cc format."""
    mins = int(seconds // 60)
    remainder = seconds - (mins * 60)
    secs = int(remainder)
    centis = int(round((remainder - secs) * 100))
    if centis >= 100:
        secs += 1
        centis = 0
    return f"{mins:02d}:{secs:02d}.{centis:02d}"
