# PromoFinder Execution Report & Quality Assessment

## 1. Overview of Results
The pipeline processed all **50 microdrama episodes** (3,727 script blocks, 1,487 dialogue lines) in **7.30 seconds** on CPU.
- **Candidates Generated**: 13,568 raw candidate segments
- **Passed Hard Rules**: 9,954 candidates
- **Gated Quality Shortlist**: 1,453 candidates scored above threshold
- **Ranked Top Clips**: 20 deduplicated, diversified promos across 10 distinct episodes.

Output artifacts generated:
- [promos.json](file:///C:/New%20folder/out/promos.json): Structured JSON payload for automated pipelines
- [promos.csv](file:///C:/New%20folder/out/promos.csv): Clean spreadsheet for editorial review
- [report.md](file:///C:/New%20folder/out/report.md): Formatted summary breakdown

---

## 2. Top Promos to Post First (Tiers & Rationale)

### Rank 1 (POST_FIRST) — Episode 1 (`00:35.15` - `01:20.50` | 45.35s)
- **Hook (0-3s)**: `LADY JULIANA: "Why are you holding her hand?" / LADY IN GOLD GOWN: "Because he is marrying me."`
- **Cliffhanger**: `LADY JULIANA: "Father..."`
- **Why It Works**: The ultimate betrayal premise delivered immediately in second 1. The bride discovers her fiancé holding hands with her sister at the altar. Cuts precisely as Juliana turns to her father for help before the familial abandonment is finalized.
- **Scores**: Final `0.61` | Hook `0.77` | Cliffhanger `0.47` | Clarity `0.79` | Intensity `0.72`

### Rank 2 (POST_FIRST) — Episode 34 (`00:37.25` - `01:17.50` | 40.25s)
- **Hook (0-3s)**: `JUDGE: "Prudence. You served beside the accused?" / PRUDENCE: "Yes, Your Honor."`
- **Cliffhanger**: `JUDGE: "And did she speak words you could not understand?"`
- **Why It Works**: Immediate high-stakes courtroom confrontation with formal authority; ends on an unresolved accusation question that demands watching the next beat.
- **Scores**: Final `0.57` | Hook `0.70` | Cliffhanger `0.55` | Clarity `0.79` | Intensity `0.63`

### Rank 3 (POST_FIRST) — Episode 2 (`00:00.00` - `00:34.20` | 34.20s)
- **Hook (0-3s)**: `THE FORMER GROOM: "I cannot marry you, Juliana."`
- **Cliffhanger**: `LADY JULIANA (O.S.): "Father..."`
- **Why It Works**: Zero lag—opens on the breakup confession at second 0.00, keeping tension taut through the humiliation walk.
- **Scores**: Final `0.57` | Hook `0.78` | Cliffhanger `0.54` | Clarity `0.41` | Intensity `0.58`

### Rank 4 (POST_FIRST) — Episode 3 (`00:13.55` - `00:43.30` | 29.75s)
- **Hook (0-3s)**: `LADY IN GOLD GOWN: "I didn't steal what was never truly yours." / LADY JULIANA: "This was my wedding."`
- **Cliffhanger**: `LADY JULIANA: "Leave where?"`
- **Why It Works**: Pure sisterly venom and emotional stakes; cleanly established dynamic with an unresolved question cut.
- **Scores**: Final `0.56` | Hook `0.68` | Cliffhanger `0.48` | Clarity `0.67` | Intensity `0.67`

### Rank 5 (POST_FIRST) — Episode 2 (`00:47.55` - `01:18.40` | 30.85s)
- **Hook (0-3s)**: `LADY IN GOLD GOWN: "Why are you surprised, sister? Look at you."`
- **Cliffhanger**: `LADY JULIANA: "You abandoned a woman who trusted you..."`
- **Why It Works**: Insult hook targeting her bridal gown followed by moral confrontation; cuts mid-accusation.
- **Scores**: Final `0.56` | Hook `0.74` | Cliffhanger `0.46` | Clarity `0.58` | Intensity `0.59`

---

## 3. Quality Evaluation: Where Does the Tool Pick Badly?

1. **Context Dependency on Character Nicknames / Pronouns**:
   - *Issue*: In Rank 2 (Ep 34) and Rank 13 (Ep 20), references like *"Prudence"* or *"the frail thing"* work well acoustically, but occasionally dialogue references a plot device without establishing who the character is to a cold viewer.
   - *Fix*: Expand the clarity penalty when the character introduced in the first 3 lines has not appeared in prior dialogue or has no familial label (e.g., sister, husband).

2. **Soft "Trailing-Off" Traps (`...`)**:
   - *Issue*: Lines ending in ellipses like `"Father......"` or `"I said......"` get rewarded as unresolved cliffhangers by punctuation regex. While emotionally effective in Rank 1, in some scenes trailing-off simply denotes quiet exhaustion rather than suspense.
   - *Fix*: Require a minimum tension derivative or camera close-up/sound stinger when rewarding trailing lines.

3. **Pure Visual Action Hooks**:
   - *Issue*: If a scene opens with an uncaptioned dramatic stare or physical gesture not documented in an `**ACTION:**` block, the rule engine scores the hook lower because it cannot see video frames.
   - *Fix*: The tool accurately extracts screenplay descriptions (like "slap", "shove", "blood"), but video multi-modal alignment will be needed for raw video files.
