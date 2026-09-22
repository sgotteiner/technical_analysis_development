# S/R Lines & Pipes — current design (the WHAT)

Why each rule exists: `docs/DESIGN_DECISIONS_DIARY.md` (F4–F5). Claude's own choices and known
problems: `docs/DIARY_FLAGS.md`. This file is edited freely to match the code.

## Why this matters (owner)
Geometry is the core of technical analysis: S/R lines (horizontal or diagonal), the **pipes** they
form, and the **breakouts** out of pipes (with candle patterns, tests, fakeouts). Indicators only
help. Breakout / retest / fakeout detection depends on getting the lines right first.

## Current definition (code: `modules/shapes/sr_turning_points.py`, `sr_lines.py`, `sr_pipes.py`)
| Rule | Value | Whose |
|---|---|---|
| 4 lines = 2 levels (higher / lower) x (support, resistance); any slope, "just a line" | — | owner |
| Periods | higher 400 days, lower 100 days | owner |
| Peaks / valleys by **magnitude** (a % zigzag on log price), confirmed only after the reversal | lower 10% | owner (10%) |
| | higher 20% | Claude |
| Candidate turning points | zigzag at magnitude / 2 | Claude |
| A line runs through the **most significant peaks AND valleys**; may split the graph; overshoots ignored (no "can't be crossed" rule) | — | owner |
| "Close to the line" | within 1.5% | Claude |
| Significance measured **against the line** (rotation-invariant) | — | owner |
| A touch is significant if price moved >= magnitude away from the line **on both sides** | — | Claude (closes a steep-line loophole) |
| Pipe never widens (upper slope <= lower slope); channels and triangles allowed | — | owner |
| Pipe not wider than the largest swing (strict) | — | owner |
| Pipe not narrower than the median swing | — | Claude (owner: "no really narrow") |
| Both lines act together (touch periods overlap) | — | Claude |
| Rules also hold at "now" (a triangle past its apex opens up = widening) | — | Claude, from owner's "no widening triangle" |
| Levels independent (no nesting) | — | owner (nesting tried and dropped) |

## Status (2026-09-22, measured)
- Tests: 39 (turning points 6, lines 10, pipes 23), all pass; 13/13 deliberate code breaks caught.
- Viewer: `python scripts/export_sr_lines.py` -> `ui/sr_viewer.html` (replay: step "now" through
  history; lines use only data up to now; ~9 min to build).
- **Coverage problem:** pipes exist on 100% of days in 2020–22 but 16–59% in 2023–26 and only 8%
  in the last 120 days (none since 2026-06-23). Fixed % magnitudes suit wild markets and go blind
  in calm ones. Owner suspects the 400-day window and similar limits may play a part too.

## Open questions (owner's call)
1. Magnitude: lower the %s, or make it follow volatility (N x recent average daily range)?
2. Keep "significant on both sides" or allow one side?
3. The 400 / 100 windows — do they hurt?
4. Minimum touches per line (many have 2)?
5. What a pipe shows after a breakout (currently the next valid pipe).

## Next: the annotator / playground (owner, 2026-09-21/22)
The owner wants a tool to **experiment and to show what he wants**:
- change the settings (windows, magnitudes, width rules...) and immediately see the lines;
- show more than 2 pairs, or single lines;
- **draw lines** himself on the chart (and boxes around patterns: flags, S/R, etc.), so his
  drawings become ground truth for the shape blocks;
- it is for shapes / S/R, to improve the shape blocks.
Ground truth plan: synthetic charts (known answer), brute-force checks of the definition,
properties (rotation, overshoot, scale, no lookahead), and the owner's drawings for real charts.
