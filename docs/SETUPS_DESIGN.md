# Setups — current design (the WHAT)

Why: `docs/DESIGN_DECISIONS_DIARY.md` ("Three stages…", "Buy the breakout of a strong resistance…").
Claude's own choices and known problems: `docs/DIARY_FLAGS.md`. This file is edited freely.

## The three stages (owner, 2026-09-22)
1. **Ground truth:** setups drawn in the playground. A setup is a name, a note on how to trade it,
   and its drawings (S/R lines, pattern boxes, retest / fakeout boxes). Only the owner's count.
2. **Detectors:** code that finds the same setups without drawing, tested against stage 1.
3. **Strategies:** trade the detected setups, backtested.

## Stage 1: setup groups (built 2026-09-22)
- Stored with the drawings in `data/ground_truth/sr_annotations.json` (`setups`: id, name, note,
  members, author). Drawings and setups record `author` = owner | claude.
- Playground: "My setups" (name, trading note, members, the detector's verdict), "+ New setup";
  each drawing's dropdown puts it in a setup (at most one). Deleting a drawing removes it from its setup.
- Setup 1: "BTC flat resistance + bull flag (Sep 2026)": flat resistance at ~$82k (2026-01-09 to
  2026-09-03) and a bull-flag box (2026-08-15 to 2026-09-04), drawn at "now" = 2026-09-04.

## Stage 2: detector "strong resistance + bull flag" (built 2026-09-22)
Code: `modules/shapes/bull_flag.py`, `modules/shapes/strong_resistance.py`,
`modules/setups/resistance_flag.py`; evaluation `business_logic_services/setup_evaluation.py`.
All thresholds are Claude's, read from setup 1. Everything uses only bars up to the day checked.

| Part | Rule |
|---|---|
| Bull flag at `end` | pole top = highest high 3–25 bars back; pole start = last lowest low in the 15 bars before it; pole rise >= 15%; the flag gives back <= 50% of the pole and never trades > 5% above its top |
| Strong resistance | a line through two major peaks (10% zigzag, confirmed, last 400 days, before the pole); no close > 2% above it from its first peak to the pole start; price fell >= 15% (log) after its last peak |
| Setup | the flag's high is within 3% of the line; closest line wins (then more touches, then the most recent peak). `broken` = the close is above the line |
| Found (vs a drawn setup) | on the day it was drawn: the detected line is within 2% of the drawn line there, and the flag span (pole start to now) overlaps the drawn box by >= 50% (time) |

**Measured (2026-09-22):**
- Setup 1 is found: line 0.45% from the owner's, flag overlap 95%. It's detected from 2026-08-24,
  10 days before the owner drew it.
- Over all BTC daily history (2017–2026): 71 episodes (459 days, 14% of days). By the detected
  line's slope: 14 flat (like setup 1), 14 falling, 19 rising, 24 steeply rising (> 0.3%/day,
  mostly in bull runs).
- The playground lists them all ("Detected setups"); ◄ / ► jumps to each one and draws it in purple.
- Tests: 43 (flag 7, resistance 6, setup 7, evaluation 5, store 8, API 3, ground truth 2);
  deliberate breaks 18/18 (first run 12/18; the 6 gaps got tests, and the flag window no longer
  needs 25 bars of history).

## Open (owner's call)
- Is a rising or falling line a "resistance" for this setup, or only flat ones?
- Which of the 71 detections are the setup, and which are not? (Accepted ones become ground truth.)
- Then stage 3: the entry (breakout, maybe a retest) and the exit.
