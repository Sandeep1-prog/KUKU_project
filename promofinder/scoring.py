import re
from promofinder.models import Episode, Candidate, FeatureScores, ScoredCandidate
from promofinder.enrich import LexiconManager

PRONOUNS = {"he", "she", "they", "him", "her", "his", "their"}

class RuleScorer:
    def __init__(self, lexicons: LexiconManager, weights: dict | None = None):
        self.lex = lexicons
        self.weights = weights or {
            "hook": 0.30,
            "cliff": 0.30,
            "clarity": 0.15,
            "intensity": 0.10,
            "duration": 0.05,
            "spoiler": 0.10
        }
        # Pre-compile regexes once for massive speedup
        self.hook_regexes = [
            (w, re.compile(rf"\b{re.escape(w)}\b")) for w in self.lex.hook_words
        ]
        self.action_regexes = [
            (w, re.compile(rf"\b{re.escape(w)}\b")) for w in self.lex.action_shock_words
        ]
        self.cliff_regexes = [
            (w, re.compile(rf"\b{re.escape(w)}\b")) for w in self.lex.cliff_words
        ]
        self.rel_regexes = [
            (w, re.compile(rf"\b{re.escape(w)}\b")) for w in self.lex.relationship_words
        ]
        self.prem_regexes = [
            (w, re.compile(rf"\b{re.escape(w)}\b")) for w in self.lex.premise_words
        ]
        self.spoil_regexes = [
            (w, re.compile(rf"\b{re.escape(w)}\b")) for w in self.lex.spoiler_words
        ]

    def score_candidate(self, candidate: Candidate, episode: Episode, enrich_data: dict) -> ScoredCandidate | None:
        seg = candidate.segments[0]
        blocks = [
            b for b in episode.blocks
            if not (b.end <= seg.start or b.start >= seg.end)
        ]
        dia_blocks = [b for b in blocks if b.kind == "DIALOGUE"]
        act_blocks = [b for b in blocks if b.kind == "ACTION"]
        cam_blocks = [b for b in blocks if b.kind == "CAMERA"]

        if not dia_blocks:
            return None

        evidence: dict[str, list[str]] = {
            "hook": [],
            "cliffhanger": [],
            "clarity": [],
            "intensity": []
        }

        # ------------------ HOOK SCORE (0..1) ------------------
        first_dia = dia_blocks[0]
        start_diff = first_dia.start - seg.start
        early_start = 1.0 if start_diff <= 1.0 else (0.5 if start_diff <= 3.0 else 0.0)

        first_text_lower = first_dia.text.lower()
        matched_hook_words = [w for w, rgx in self.hook_regexes if rgx.search(first_text_lower)]
        first_line_power = min(1.0, len(matched_hook_words) * 0.40)
        if matched_hook_words:
            evidence["hook"].extend([f"word:{w}" for w in matched_hook_words])

        first_intensity = self.lex.get_emotion_intensity(first_dia.emotion_tags)
        if first_dia.emotion_tags:
            evidence["hook"].extend([f"tag:{t}" for t in first_dia.emotion_tags])

        action_shock = 0.0
        early_actions = [a for a in act_blocks if a.start - seg.start <= 3.0]
        for a in early_actions:
            a_text = a.text.lower()
            matched_act = [w for w, rgx in self.action_regexes if rgx.search(a_text)]
            if matched_act:
                action_shock = 1.0
                evidence["hook"].extend([f"action:{w}" for w in matched_act])
                break

        word_count = len(first_dia.text.split())
        short_punch = 1.0 if (2 <= word_count <= 8) else 0.4

        first_word = first_text_lower.split()[0].strip(",.!?") if first_text_lower else ""
        pronoun_start = 1.0 if first_word in PRONOUNS else 0.0

        raw_hook = (
            0.25 * early_start +
            0.25 * first_line_power +
            0.20 * first_intensity +
            0.15 * action_shock +
            0.15 * short_punch -
            0.20 * pronoun_start
        )
        hook_score = max(0.0, min(1.0, raw_hook))

        # ------------------ CLIFFHANGER SCORE (0..1) ------------------
        last_dia = dia_blocks[-1]
        last_text = last_dia.text.strip()
        last_text_lower = last_text.lower()

        ends_on_q_or_trailing = 1.0 if (last_text.endswith("?") or last_text.endswith("...") or last_text.endswith("—")) else 0.0
        if ends_on_q_or_trailing:
            evidence["cliffhanger"].append("punctuation:unresolved")

        matched_cliff = [w for w, rgx in self.cliff_regexes if rgx.search(last_text_lower)]
        threat_or_reveal = min(1.0, len(matched_cliff) * 0.50)
        if matched_cliff:
            evidence["cliffhanger"].extend([f"cliff_word:{w}" for w in matched_cliff])

        tension_curve = enrich_data.get("tension_curve", [])
        end_idx = min(len(tension_curve) - 1, int(seg.end))
        tension_at_end = tension_curve[end_idx] if end_idx < len(tension_curve) else 0.5

        late_cam = [c for c in cam_blocks if c.start >= last_dia.end]
        unresolved_reaction = 1.0 if (late_cam and any("close-up" in (c.shot_type or "") or "insert" in (c.shot_type or "") for c in late_cam)) else 0.3

        ep_end_bonus = 1.0 if (candidate.type == "EP_END" and (ends_on_q_or_trailing or threat_or_reveal > 0)) else 0.0

        raw_cliff = (
            0.30 * ends_on_q_or_trailing +
            0.25 * threat_or_reveal +
            0.20 * tension_at_end +
            0.15 * unresolved_reaction +
            0.10 * ep_end_bonus
        )
        cliff_score = max(0.0, min(1.0, raw_cliff))

        # ------------------ EARLY GATING CUT ------------------
        if hook_score < 0.35 or cliff_score < 0.35:
            return None

        # ------------------ CLARITY SCORE (0..1) ------------------
        full_text_lower = " ".join(b.text.lower() for b in dia_blocks)
        distinct_speakers = {b.speaker for b in dia_blocks if b.speaker}

        matched_rel = [w for w, rgx in self.rel_regexes if rgx.search(full_text_lower)]
        rel_score = min(1.0, len(matched_rel) * 0.35)

        few_speakers = 1.0 if (2 <= len(distinct_speakers) <= 3) else (0.6 if len(distinct_speakers) == 4 else 0.3)

        matched_prem = [w for w, rgx in self.prem_regexes if rgx.search(full_text_lower)]
        prem_score = min(1.0, len(matched_prem) * 0.30)

        clarity_score = max(0.0, min(1.0, 0.40 * rel_score + 0.30 * few_speakers + 0.30 * prem_score))

        # ------------------ INTENSITY SCORE (0..1) ------------------
        intensities = [self.lex.get_emotion_intensity(b.emotion_tags) for b in dia_blocks]
        mean_intensity = sum(intensities) / len(intensities) if intensities else 0.4
        close_up_count = sum(1 for c in cam_blocks if "close-up" in (c.shot_type or ""))
        cu_share = min(1.0, close_up_count / max(1, len(cam_blocks)))
        shot_rate = min(1.0, len(cam_blocks) / max(1, (seg.duration / 3.0)))

        intensity_score = max(0.0, min(1.0, 0.50 * mean_intensity + 0.30 * cu_share + 0.20 * shot_rate))

        # ------------------ SPOILER RISK (0..1) ------------------
        ep_ratio = max(0.0, (episode.number - 15) / 35.0)
        matched_spoil = [w for w, rgx in self.spoil_regexes if rgx.search(full_text_lower)]
        spoiler_score = max(0.0, min(1.0, 0.60 * ep_ratio + 0.40 * (1.0 if matched_spoil else 0.0)))

        # ------------------ DURATION FIT (0..1) ------------------
        dur = candidate.duration
        if 30.0 <= dur <= 45.0:
            duration_fit = 1.0
        elif dur < 30.0:
            duration_fit = 0.5 + 0.5 * ((dur - 20.0) / 10.0)
        else:
            duration_fit = 0.5 + 0.5 * ((60.0 - dur) / 15.0)
        duration_fit = max(0.0, min(1.0, duration_fit))

        # ------------------ RULE SCORE COMBINATION ------------------
        w = self.weights
        rule_score = (
            w["hook"] * hook_score +
            w["cliff"] * cliff_score +
            w["clarity"] * clarity_score +
            w["intensity"] * intensity_score +
            w["duration"] * duration_fit -
            w["spoiler"] * spoiler_score
        )
        rule_score = max(0.0, min(1.0, rule_score))

        features = FeatureScores(
            hook=round(hook_score, 2),
            cliffhanger=round(cliff_score, 2),
            clarity=round(clarity_score, 2),
            intensity=round(intensity_score, 2),
            spoiler_risk=round(spoiler_score, 2),
            duration_fit=round(duration_fit, 2),
            evidence=evidence
        )

        h_line = f"{first_dia.speaker}: \"{first_dia.text}\""
        if len(dia_blocks) > 1 and dia_blocks[1].speaker != first_dia.speaker:
            h_line += f" / {dia_blocks[1].speaker}: \"{dia_blocks[1].text}\""

        c_line = f"{last_dia.speaker}: \"{last_dia.text}\""
        why = f"High confrontation hook ({first_intensity:.2f} emotion); cuts on unresolved line '{last_text[:35]}...'."

        return ScoredCandidate(
            candidate=candidate,
            features=features,
            rule_score=round(rule_score, 3),
            final_score=round(rule_score, 3),
            hook_line=h_line,
            cliffhanger_line=c_line,
            why_it_works=why
        )
