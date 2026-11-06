import re
from typing import Literal
from pydantic import BaseModel, Field

class Block(BaseModel):
    kind: Literal["CAMERA", "ACTION", "DIALOGUE", "SOUND"]
    start: float
    end: float
    text: str
    speaker: str | None = None
    speaker_id: str | None = None
    emotion_tags: list[str] = Field(default_factory=list)
    is_offscreen: bool = False
    shot_type: str | None = None

class Scene(BaseModel):
    number: int
    heading: str
    start: float
    end: float

class Episode(BaseModel):
    number: int
    logline: str = ""
    continuity_notes: str = ""
    duration: float = 0.0
    scenes: list[Scene] = Field(default_factory=list)
    blocks: list[Block] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

class Segment(BaseModel):
    episode: int
    start: float
    end: float

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)

class Candidate(BaseModel):
    id: str
    type: Literal["SINGLE", "EP_END", "STITCH"]
    segments: list[Segment]
    duration: float

class FeatureScores(BaseModel):
    hook: float = 0.0
    cliffhanger: float = 0.0
    clarity: float = 0.0
    intensity: float = 0.0
    spoiler_risk: float = 0.0
    duration_fit: float = 0.0
    evidence: dict[str, list[str]] = Field(default_factory=dict)

class JudgeResult(BaseModel):
    hook: float
    cliffhanger: float
    clarity: float
    spoiler_risk: float
    hook_line: str
    cliffhanger_line: str
    why: str
    model: str = "heuristic"
    prompt_version: str = "v1"

class ScoredCandidate(BaseModel):
    candidate: Candidate
    features: FeatureScores
    rule_score: float
    judge: JudgeResult | None = None
    final_score: float
    tier: Literal["POST_FIRST", "STRONG", "BACKUP"] | None = None
    hook_line: str = ""
    cliffhanger_line: str = ""
    why_it_works: str = ""
