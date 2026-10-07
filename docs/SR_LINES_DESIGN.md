# S/R Lines & Pipes — current design (the WHAT)

> [!warning] Superseded as the description of the line layer by "The line layer as it stands
> (2026-10-07)" in `docs/GEOMETRY_DEFINITIONS.md`. Below is the 2026-09-22 pipe design (4 lines,
> 400/100-day windows, fixed 10%/20% sizes), which still drives the page's separate "pipes" layer.
> What still holds from it as his rule: a line can touch peaks and valleys; a small overshoot does
> not move a line; pipes never widen and are neither too wide nor too narrow.

Why each rule exists: `docs/DESIGN_DECISIONS_DIARY.md` (F4–F5). Claude's own choices and known
problems: `docs/DIARY_FLAGS.md`. This file is edited freely to match the code.

## Why this matters (owner)
Geometry is the core of technical analysis: S/R lines (horizontal or diagonal), the **pipes** they
form, and the **breakouts** out of pipes (with candle patterns, tests, fakeouts). Indicators only
help. Breakout / retest / fakeout detection depends on getting the lines right first.

## Current definition (code: `modules/shapes/sr_turning_points.py`, `sr_lines.py`, `sr_pipes.py`)
Every value below is a setting in `modules/shapes/sr_settings.py` (plus min touches per line,
default 2), except the structural rules: lines through peaks AND valleys, significance against the
line, levels independent. The defaults are the values in this table.

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
- Tests: 98 S/R tests, all pass. The 39 original tests (turning points 6, lines 10, pipes 23) are
  unchanged and still pass on the default settings. 59 are new for the playground: settings 11,
  ranked 27, service 4, ground-truth store 9, API 8. Deliberate code breaks: 13/13 in the
  original code; 18/18 in the new code (the first run caught 14/18; the 3 real gaps got tests).
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

## The playground / annotator (built 2026-09-22)
Run `python scripts/sr_playground.py` -> http://127.0.0.1:8765 (a local server computes the lines
live, no precompute).
- **Settings, live:** levels (any number: window + magnitude, show/hide, add/remove), pipes per
  level (0-10), single lines per level (0-30), and every rule above, each tagged with whose it is.
  Each change recomputes at "now": 0.1-0.4 s at the defaults, ~1.5 s at 6% over 400 days.
  Settings are remembered in the browser; "Reset to the built rules" restores the defaults.
- **Replay:** step "now" by 1 / 7 days (arrow keys) or pick a date; lines use candles up to now.
- **Ranked results:** pipe 1 = the current pipe; pipes 2, 3... are the next best pipes whose lines
  were not used yet. Single lines are ranked by touches, then last touch, then first touch.
- **Drawing = ground truth:** Line / Box tools (keys L / B, Esc = pan): click two points. The label
  field suggests support, resistance, pipe, trendline, range, triangle, flag, pennant, breakout,
  retest, fakeout; any text is accepted. Each drawing is saved with its label, note, two
  (time, price) points, the chart (`btc_1d`) and the "now" it was drawn at, in
  `data/ground_truth/sr_annotations.json` (tracked by git). Label, note and delete are in the side list.
- **Pipe search:** pairs are checked in buckets of equal total touches, best first. Same answer as
  checking all pairs (brute-force tests) for a fraction of the work. It stops after 50M pairs per
  level, and the page then says the search is incomplete and down to which total it checked.
- Code, one thing per file (split 2026-10-03): the pipe view in
  `business_logic_services/sr_pipe_view.py`; the structure at one "now" in `swing_frame.py`,
  drawn by `swing_view.py`; the line rules picked in `line_rules.py`; the setup explained in
  `setup_view.py` + `setup_story.py` + `precedents.py`. Routes split by what they do:
  `routes/sr_view_routes.py` computes, `routes/sr_ground_truth_routes.py` records. One JSON
  file in `repositories/json_doc.py`, with `sr_drawings_repo.py`, `sr_setups_repo.py` and
  `sr_verdicts_repo.py` over it. Schemas likewise: `schemas/sr_view_schema.py` (what the page
  asks for) and `schemas/sr_ground_truth_schema.py` (what he records). Page:
  `ui/sr_playground.html`, `ui/js/sr_playground/`.

Seen in the first run (around 2021-06-01): pipes 2-3 are often near-copies of pipe 1 (same support
start, slopes within 0.05 %/day). With 3 pipes and 4 lines per level the chart gets busy, and
single lines can't be told apart on the chart yet.

### Original request (owner, 2026-09-21/22)
The owner wants a tool to **experiment and to show what he wants**:
- change the settings (windows, magnitudes, width rules...) and immediately see the lines;
- show more than 2 pairs, or single lines;
- **draw lines** himself on the chart (and boxes around patterns: flags, S/R, etc.), so his
  drawings become ground truth for the shape blocks;
- it is for shapes / S/R, to improve the shape blocks.
Ground truth plan: synthetic charts (known answer), brute-force checks of the definition,
properties (rotation, overshoot, scale, no lookahead), and the owner's drawings for real charts.
