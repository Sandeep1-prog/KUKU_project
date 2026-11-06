import yaml
from pathlib import Path
from promofinder.models import Episode, Block

class LexiconManager:
    def __init__(self, config_dir: Path | None = None):
        if config_dir is None:
            config_dir = Path("config")
        lex_dir = config_dir / "lexicons"

        with open(lex_dir / "emotion_intensity.yaml", "r", encoding="utf-8") as f:
            self.emotion_weights = yaml.safe_load(f) or {}

        with open(lex_dir / "hook_words.yaml", "r", encoding="utf-8") as f:
            hook_data = yaml.safe_load(f) or {}
            self.hook_words = [w.lower() for w in hook_data.get("hook_words", [])]
            self.action_shock_words = [w.lower() for w in hook_data.get("action_shock_words", [])]

        with open(lex_dir / "cliff_words.yaml", "r", encoding="utf-8") as f:
            cliff_data = yaml.safe_load(f) or {}
            self.cliff_words = [w.lower() for w in cliff_data.get("cliff_words", [])]
            self.resolution_words = [w.lower() for w in cliff_data.get("resolution_words", [])]

        with open(lex_dir / "clarity_spoiler.yaml", "r", encoding="utf-8") as f:
            clarity_data = yaml.safe_load(f) or {}
            self.relationship_words = [w.lower() for w in clarity_data.get("relationship_words", [])]
            self.premise_words = [w.lower() for w in clarity_data.get("premise_words", [])]
            self.spoiler_words = [w.lower() for w in clarity_data.get("spoiler_words", [])]

    def get_emotion_intensity(self, tags: list[str]) -> float:
        if not tags:
            return 0.40
        scores = []
        default_val = self.emotion_weights.get("default", 0.40)
        for t in tags:
            clean_t = t.strip()
            score = self.emotion_weights.get(clean_t, default_val)
            scores.append(score)
        return max(scores) * 0.8 + (sum(scores) / len(scores)) * 0.2

class Enricher:
    def __init__(self, lexicons: LexiconManager):
        self.lex = lexicons

    def enrich_episode(self, episode: Episode) -> dict:
        """Computes line-level features and second-by-second tension curve."""
        dia_blocks = [b for b in episode.blocks if b.kind == "DIALOGUE"]
        cam_blocks = [b for b in episode.blocks if b.kind == "CAMERA"]

        max_sec = int(episode.duration) + 2
        tension_curve = [0.0] * max_sec

        # Line intensity
        line_intensities = {}
        for b in dia_blocks:
            line_intensities[id(b)] = self.lex.get_emotion_intensity(b.emotion_tags)

        # Shot rate & tension per second
        for sec in range(max_sec):
            # Active dialogues within [sec-2, sec+2]
            active_dia = [
                line_intensities[id(b)]
                for b in dia_blocks
                if not (b.end < sec - 2 or b.start > sec + 2)
            ]
            max_intensity = max(active_dia, default=0.2)

            # Camera blocks active in [sec-5, sec+5]
            cam_count = sum(
                1 for b in cam_blocks
                if not (b.end < sec - 5 or b.start > sec + 5)
            )
            norm_shot_rate = min(1.0, cam_count / 8.0)

            # Exclamation / question density in active lines
            punc_score = 0.0
            for b in dia_blocks:
                if not (b.end < sec - 2 or b.start > sec + 2):
                    if "?" in b.text or "!" in b.text:
                        punc_score += 0.3
            punc_score = min(1.0, punc_score)

            raw_tension = 0.5 * max_intensity + 0.3 * norm_shot_rate + 0.2 * punc_score
            tension_curve[sec] = raw_tension

        # 3-second smoothing moving average
        smoothed = [0.0] * max_sec
        for sec in range(max_sec):
            window = tension_curve[max(0, sec - 1): min(max_sec, sec + 2)]
            smoothed[sec] = sum(window) / len(window)

        return {
            "tension_curve": smoothed,
            "line_intensities": line_intensities,
            "duration": episode.duration
        }
