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
from promofinder.groq_judge import GroqJudge

app = typer.Typer(help="PromoFinder: Microdrama Promo Clip Generation Pipeline")

@app.command()
def run(
    input_dir: str = typer.Option("I Married a Broken Soldier. He was a Duke-script/I Married a Broken Soldier. He was a Duke", "--input", "-i", help="Directory of episode scripts"),
    out_dir: str = typer.Option("out", "--out", "-o", help="Output directory"),
    config_dir: str = typer.Option("config", "--config", "-c", help="Config directory"),
    top_k: int = typer.Option(20, "--top", "-k", help="Number of top promos to output"),
    judge: str = typer.Option("none", "--judge", "-j", help="Judge provider: 'none' or 'groq'"),
    groq_api_key: str = typer.Option(None, "--groq-key", envvar="GROQ_API_KEY", help="Groq API key"),
    shortlist_size: int = typer.Option(40, "--shortlist", help="Number of candidates to pass to judge"),
):
    start_time = time.time()
    in_path = Path(input_dir)
    out_path = Path(out_dir)
    cfg_path = Path(config_dir)

    typer.echo(f"==> 1. Parsing episodes from {in_path}...")
    episodes = parse_all_episodes(in_path)
    episodes_map = {ep.number: ep for ep in episodes}
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

    # Optional Groq Judge Stage
    if judge.lower() == "groq":
        typer.echo("==> 3b. Invoking Groq Judge on top candidate shortlist...")
        groq_judge = GroqJudge(api_key=groq_api_key)
        if groq_judge.is_available():
            all_scored_candidates.sort(key=lambda sc: sc.final_score, reverse=True)
            shortlist = all_scored_candidates[:shortlist_size]
            remainder = all_scored_candidates[shortlist_size:]
            judged_shortlist = groq_judge.judge_shortlist(shortlist, episodes_map)
            all_scored_candidates = judged_shortlist + remainder
            typer.echo("    Groq judge completed evaluation.")
        else:
            typer.echo("    [WARNING] Groq API key not provided or found in GROQ_API_KEY environment variable. Falling back to rules.")

    typer.echo("==> 4. Ranking and diversifying...")
    ranked_promos = rank_and_diversify(all_scored_candidates, top_k=top_k)
    typer.echo(f"    Selected top {len(ranked_promos)} promos across episodes.")

    typer.echo(f"==> 5. Writing reports to {out_path}...")
    write_reports(ranked_promos, out_path, total_candidates_evaluated=total_raw_cands)

    elapsed = time.time() - start_time
    typer.echo(f"[SUCCESS] PromoFinder run completed in {elapsed:.2f}s! See '{out_path}/report.md'.")

if __name__ == "__main__":
    app()
