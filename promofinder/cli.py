import time
from pathlib import Path
import typer
from promofinder.parser import parse_all_episodes
from promofinder.enrich import LexiconManager, Enricher
from promofinder.candidates import generate_episode_candidates
from promofinder.snapping import snap_candidate_boundaries
from promofinder.filters import passes_hard_filters
from promofinder.scoring import RuleScorer
from promofinder.rank import rank_and_diversify
from promofinder.report import write_reports

app = typer.Typer(help="PromoFinder: Microdrama Promo Clip Generation Pipeline")

@app.command()
def run(
    input_dir: str = typer.Option("I Married a Broken Soldier. He was a Duke-script/I Married a Broken Soldier. He was a Duke", "--input", "-i", help="Directory of episode scripts"),
    out_dir: str = typer.Option("out", "--out", "-o", help="Output directory"),
    config_dir: str = typer.Option("config", "--config", "-c", help="Config directory"),
    top_k: int = typer.Option(20, "--top", "-k", help="Number of top promos to output"),
):
    start_time = time.time()
    in_path = Path(input_dir)
    out_path = Path(out_dir)
    cfg_path = Path(config_dir)

    typer.echo(f"==> 1. Parsing episodes from {in_path}...")
    episodes = parse_all_episodes(in_path)
    typer.echo(f"    Loaded {len(episodes)} episodes.")

    typer.echo("==> 2. Initializing Lexicons & Enricher...")
    lex = LexiconManager(cfg_path)
    enricher = Enricher(lex)
    scorer = RuleScorer(lex)

    all_scored_candidates = []
    total_raw_cands = 0
    total_passed_filters = 0

    typer.echo("==> 3. Generating, filtering and scoring candidates...")
    for ep in episodes:
        enrich_data = enricher.enrich_episode(ep)
        cands = generate_episode_candidates(ep)
        total_raw_cands += len(cands)

        for c in cands:
            passed, reason = passes_hard_filters(c, ep, lex, max_ep_fraction=0.70, total_episodes=len(episodes))
            if not passed:
                continue
            total_passed_filters += 1
            scored = scorer.score_candidate(c, ep, enrich_data)
            if scored:
                all_scored_candidates.append(scored)

    typer.echo(f"    Generated {total_raw_cands} raw candidates -> {total_passed_filters} passed filters -> {len(all_scored_candidates)} scored above gating.")

    typer.echo("==> 4. Ranking and diversifying...")
    ranked_promos = rank_and_diversify(all_scored_candidates, top_k=top_k)
    typer.echo(f"    Selected top {len(ranked_promos)} promos across episodes.")

    typer.echo(f"==> 5. Writing reports to {out_path}...")
    write_reports(ranked_promos, out_path, total_candidates_evaluated=total_raw_cands)

    elapsed = time.time() - start_time
    typer.echo(f"[SUCCESS] PromoFinder run completed in {elapsed:.2f}s! See '{out_path}/report.md'.")

if __name__ == "__main__":
    app()
