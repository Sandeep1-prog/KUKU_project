import json
from pathlib import Path
import pytest
from promofinder.parser import parse_episode_file, parse_all_episodes
from promofinder.snapping import snap_candidate_boundaries
from promofinder.enrich import LexiconManager, Enricher
from promofinder.candidates import generate_episode_candidates
from promofinder.filters import passes_hard_filters

DATA_DIR = Path("I Married a Broken Soldier. He was a Duke-script/I Married a Broken Soldier. He was a Duke")

def test_parser_ep001():
    ep1_file = DATA_DIR / "episode-001-Episode 1671703.txt"
    ep = parse_episode_file(ep1_file)
    assert ep.number == 1
    assert len(ep.scenes) == 1
    assert len(ep.blocks) > 80
    assert len(ep.warnings) == 0
    # Dialogue check
    dia = [b for b in ep.blocks if b.kind == "DIALOGUE"]
    assert len(dia) > 20

def test_all_50_episodes_parse():
    eps = parse_all_episodes(DATA_DIR)
    assert len(eps) == 50
    for ep in eps:
        assert ep.duration > 0
        assert len(ep.blocks) > 0

def test_snapping_invariants():
    ep1_file = DATA_DIR / "episode-001-Episode 1671703.txt"
    ep = parse_episode_file(ep1_file)
    s, e = snap_candidate_boundaries(ep, 35.15, 80.0, lead_in=0.25, tail=0.40)
    assert s <= 35.15
    assert e >= 80.0
    assert (e - s) >= 44.0

def test_hard_filters_drop_bad_starts():
    ep1_file = DATA_DIR / "episode-001-Episode 1671703.txt"
    ep = parse_episode_file(ep1_file)
    lex = LexiconManager(Path("config"))
    cands = generate_episode_candidates(ep)
    assert len(cands) > 50
