# Diary Flags & Debt — algo-trading (trading_projects)

Companion to [DESIGN_DECISIONS_DIARY.md](DESIGN_DECISIONS_DIARY.md). Holds what must NOT go
in the diary: decisions Claude made on its own (pending the owner's approval or already
corrected) and known-but-deferred problems. Append-only; mark an item resolved by adding a
dated line under it, never by deleting it.

## Claude-on-its-own decisions

- **2026-09-20 · Lookahead fix landed inside the owner's "Added median" commit (8906f42).**
  The file was saved while the owner committed, so the history doesn't separate the fix from
  the median feature.
- **2026-09-20 · Called the block layer "vaporware".** Only `strategies/` had been read, not
  `modules/`. The owner corrected it: blocks were the design from the start, only the bridge
  from blocks to the backtest was missing.
- **2026-09-20 · Attributed Cryptron's "a weak result is usually the wrong exit" to the owner.**
  He corrected it: not his rule, and it doesn't apply here.
- **2026-09-20 · Built the explainer, intrabar stop, MAE/MFE and equity-curve drawdown** under
  the broad "make your tools good" request (delegated). The shapes of these metrics are Claude's.
- **2026-09-21 · MarketStructureBlock redesign:** 3 states; a break below the last swing low now
  outranks an older bullish structure (the old code only had the bullish side); "not ready"
  is reported as SIDEWAYS. The owner asked to "fix it"; these specifics are Claude's.
- **2026-09-21 · Regime rule thresholds:** straight = efficiency ≥ 0.45, counter-move ≤ 15%,
  ≤ 1 flat step; stairs = ≥ 2 flat steps (21 days within 15%); flat = band ≤ 1.15×;
  range = band 1.25–1.6× with ≥ 4 touches; trends ≥ 30% and end at their extreme. Proposed
  and reported, not explicitly approved.
- **2026-09-21 · Different regimes may never share a day; the same regime may overlap.**
  Proposed and reported, not explicitly approved. This excludes good flats that sit inside
  bigger trends (e.g. Jul–Sep 2025).
- **2026-09-21 · Metric definitions** (efficiency ratio, R², trend/noise, true range, episode
  counts, flat steps, range touches) chosen by Claude in answer to "how are these measured?".
- **2026-09-21 · Classifier pass bars** (trend ≥ 70% agreement and ≤ 10% opposite; sideways
  ≥ 50%; grading starts 20 days in) carried over from Claude's first test. No target has been
  set by the owner yet. Lag and flips are reported, not graded.
- **2026-09-21 · Saved lead-in = 365 days of daily data only** (no 1H) per batch in
  `data/regimes/`.
- **2026-09-21 · Regime viewer is a separate page** (`ui/regime_viewer.html`), although
  GEMINI.md says to export only to `ui/tradingview_chart.html`. Flagged to the owner; no answer yet.
- **2026-09-21 · TrendClassifierBlock design and settings.** The owner asked for a better
  classifier with sub-parts (e.g. separate lookbacks, or indicators); the specifics are Claude's:
  - direction: votes over n/2, n and 2n days;
  - going nowhere: back within 10% of the price n days ago, or n-day efficiency < 0.10;
  - persistence: a new state must hold 5 days;
  - n = 30, the middle of the plateau where n = 20–45 all give 7/12.
  18 variants tried (scratch ledger); 7 of 9 neighbouring settings also give 7/12.
- **2026-09-21 · Replaced a failing synthetic unit test.** It expected a smooth 80-day-cycle
  range to read sideways. It is now two tests: a range with short swings reads sideways, and a
  range with legs longer than the patience window reads as alternating trends. The original
  expectation contradicted the classifier's time scale; the limit is now documented, not hidden.

## Findings (measured, not decided)

- **2026-09-21 · The measurable regime rules accepted examples the owner rejected.** The COVID
  crash (flat + one huge candle) passed as a straight bear, because the efficiency ratio can't
  tell a single jump from a steady trend. The ETF bull was counted as 5 flat steps where the owner
  sees 1. The rules are weaker than the owner's eye.
- **2026-09-21 · MarketStructureBlock (5-day swings)** is causal (0 live-replay mismatches on
  3,306 days) but a poor regime label. It passes 4 of the 12 accepted batches: straight trends
  and one flat, but no stairs and no ranges.
- **2026-09-21 · Strategy experiments (scratch only, not in repo).** Splitting entry (strict)
  from exit (EMA20 < EMA50) beat the current Daily Supertrend in both cycles. A 4H version was
  the best balance (C2 +155%, 29% drawdown). 1H was noise after fees. Search count 75.
- **2026-09-21 · Stairs trends can't be separated from flats/ranges without hindsight.**
  - Over 60 days, stairs have efficiency 0.14–0.17 and flats/ranges 0.04–0.17.
  - Most flats follow a rally (90-day return up to +48%), so a stair step and the start of a flat
    look the same until the next leg does, or doesn't, come.
  - More patience helps stairs slightly (still < 70%) but breaks sideways detection (5/5 at
    20–30 days, 1/5 at 90 days).
  - The stairs pass bar may be unreachable for any causal classifier; this needs the owner's target.
- **2026-09-21 · TrendClassifierBlock (n=30): 7/12 batches.**
  - All straight trends and all sideways batches pass; all 5 stairs fail, mostly by calling steps
    sideways (opposite-trend calls 0–14%).
  - Flips: 43, against 206 for the swing block. Lag: 4–35 days.
  - The 2023 spring flat passes narrowly (53%).

## Known debt (deferred)

- Engine max drawdown is only measured at trade exits: 41% reported vs 62% measured bar by bar.
- Each cycle is cut off from earlier history, so slow indicators are blind at the start of
  each cycle. On Cycle 2 this can make a strategy look like it avoided the 2022 crash.
- After a stop-out the engine re-enters immediately if the regime is still on (a stop-and-re-enter
  loop).
- Stops fill exactly at the stop price even when the market gaps through it (optimistic).
- `explain.py` reports 0% profit concentration whenever total PnL is negative.
- Fees and slippage are parked (owner decision). Results are relative, not real P&L.
- Nothing after 8906f42 is committed yet.

## Owner messages deliberately not turned into diary entries

- 2026-09-21 15:46–15:53Z: greeting, VS Code layout questions, pointing to the Antigravity /
  Click Click Claude history (orientation, no design).
- 2026-09-21 15:58Z, 16:01Z, 17:08Z–17:15Z: questions about the system and requests to run and
  improve strategies. These are experiments delegated to Claude, results under Findings.
  17:08Z "just run a strategy and see its metrics" is feedback on working style (too much
  protocol for a simple ask). That belongs in the owner's global preferences, not here.
- 2026-09-21 18:42Z: "what is bull" / "definition of bull market": questions that led to
  the answer-key entries.
- 2026-09-20 09:27–09:40Z, 11:14–11:18Z, 11:46–11:48Z, 12:05Z, 15:08Z: orientation questions,
  "fix 1 and measure again" (execution), "how can I see what you have done", "i did a good job
  there" (about Cryptron).

## 2026-09-22 — S/R lines and pipes (Claude's choices, pending the owner's review)
- Higher-level magnitude 20% (the owner said 10%); candidate turning points use a magnitude/2 zigzag.
- "Close to the line" = 1.5%.
- A touch counts only if price moved >= magnitude away from the line on BOTH sides. This closes a
  loophole where a steep line got one far neighbour for free, and it also cuts touches.
- Minimum pipe width = the median swing (the owner said "no really narrow" without a number).
- Both lines must act together (touch periods overlap), and all rules are also checked at "now"
  (a triangle past its apex). Both were added after the viewer showed pipes made of lines from
  different times, and lines that had crossed.
- The first extreme of the data is not a turning point (it only anchors the zigzag direction).

## Findings 2026-09-21/22
- "Buy only in bull" on the 4H strategy removed the best trades. Early breakout entries happen
  while the slow block still says "sideways". "Sideways after bear" held the best-quality trades
  in both cycles (50% winners), but the samples are small (8 and 14 trades).
- The old MTF S/R block has lookahead (30 of 1,944 hours differed in live replay), a fake
  resistance (support x 1.05), and no touch counting.
- S/R magnitude definition: pipes on 100% of days in 2020–22 but 8% in the last 120 days.
  Fixed % magnitudes go blind in calm markets.

## Known debt (2026-09-22)
- The S/R viewer takes ~9 min to build; the lines are computed for every day.
- Old shape blocks (flags, triangles, MTF S/R, InstitutionalGeometry) still have lookahead and no tests.
- Nothing from 2026-09-20 onward is committed.
