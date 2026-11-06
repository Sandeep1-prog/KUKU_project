import os
import json
import hashlib
import urllib.request
import urllib.error
from pathlib import Path
from promofinder.models import ScoredCandidate, Episode

class GroqJudge:
    """
    Optional AI Shortlist Judge using Groq API.
    Operates ONLY on shortlisted candidates (default: top 40) to:
    1. Score narrative coherence and stand-alone appeal (0.0 to 1.0).
    2. Generate an editorial summary explaining why the clip converts.
    Responses are cached in .cache/ to ensure zero redundant API calls.
    """
    def __init__(
        self,
        api_key: str | None = None,
        model: str = "llama-3.1-8b-instant",
        cache_dir: str = ".cache"
    ):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        self.model = model
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def is_available(self) -> bool:
        return bool(self.api_key)

    def _get_cache_path(self, text: str) -> Path:
        key = hashlib.sha256(f"{self.model}:{text}".encode()).hexdigest()
        return self.cache_dir / f"{key}.json"

    def evaluate_candidate(
        self,
        candidate: ScoredCandidate,
        episode: Episode,
        dialogue_text: str
    ) -> dict | None:
        if not self.is_available():
            return None

        cache_file = self._get_cache_path(dialogue_text)
        if cache_file.exists():
            try:
                return json.loads(cache_file.read_text(encoding="utf-8"))
            except Exception:
                pass

        # Construct concise prompt rubric
        prompt = (
            "You are an expert microdrama promo editor for TikTok and Instagram Reels.\n"
            f"Series Context: {episode.logline}\n\n"
            f"Promo Clip Transcript:\n{dialogue_text}\n\n"
            "Evaluate this 20-60 second promo clip on:\n"
            "1. hook (0-10): does the first line or action shock a scrolling viewer?\n"
            "2. cliffhanger (0-10): does it cut on an unresolved, suspenseful beat?\n"
            "3. clarity (0-10): can a cold viewer understand the conflict without backstory?\n"
            "4. why (max 20 words): why this moment pulls viewers into the app.\n\n"
            "Return JSON ONLY with keys: hook, cliffhanger, clarity, why"
        )

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a professional microdrama editor. Respond strictly in valid JSON."},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.0
        }

        try:
            req = urllib.request.Request(
                "https://api.groq.com/openai/v1/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                content = data["choices"][0]["message"]["content"]
                result = json.loads(content)

                # Cache response
                cache_file.write_text(json.dumps(result, indent=2), encoding="utf-8")
                return result
        except Exception as e:
            # Fall back gracefully to rules if API fails; never break the pipeline
            return None

    def judge_shortlist(
        self,
        shortlist: list[ScoredCandidate],
        episodes_map: dict[int, Episode],
        alpha: float = 0.50
    ) -> list[ScoredCandidate]:
        """
        Re-scores only the shortlist and blends judge score:
        final = (1 - alpha) * rule_score + alpha * judge_score
        """
        if not self.is_available():
            return shortlist

        for sc in shortlist:
            seg = sc.candidate.segments[0]
            ep = episodes_map.get(seg.episode)
            if not ep:
                continue

            dia_lines = [
                f"{b.speaker}: \"{b.text}\""
                for b in ep.blocks
                if b.kind == "DIALOGUE" and not (b.end <= seg.start or b.start >= seg.end)
            ]
            dialogue_text = "\n".join(dia_lines)

            eval_res = self.evaluate_candidate(sc, ep, dialogue_text)
            if eval_res:
                try:
                    j_hook = float(eval_res.get("hook", 5.0)) / 10.0
                    j_cliff = float(eval_res.get("cliffhanger", 5.0)) / 10.0
                    j_clarity = float(eval_res.get("clarity", 5.0)) / 10.0
                    judge_score = round(0.40 * j_hook + 0.40 * j_cliff + 0.20 * j_clarity, 3)

                    # Blend with rule score
                    sc.final_score = round((1 - alpha) * sc.rule_score + alpha * judge_score, 3)
                    if "why" in eval_res and eval_res["why"]:
                        sc.why_it_works = eval_res["why"].strip()
                except Exception:
                    pass

        return shortlist
