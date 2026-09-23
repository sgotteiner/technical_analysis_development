# Geometry — definitions, ideas and open questions (draft)

The working file for the geometry layers: what each thing means, what is decided, what is still
open, and the measurements behind the numbers. Decisions move to
`docs/DESIGN_DECISIONS_DIARY.md` (the why) and the rules to `docs/SR_LINES_DESIGN.md` (the what).
Marks: **[owner]** = the owner's, **[proposed]** = Claude's suggestion, awaiting his word.

## Layers (owner, 2026-09-23: "separation of concerns")
| Layer | Owns | Ground truth | Status |
|---|---|---|---|
| 1. Turning points | peaks / valleys by magnitude; each point's size | synthetic charts | done, tested |
| 2. **Lines** | every relevant line: horizontal levels searched back through history, trend lines from the recent move; touches, size class, span | the owner's drawn lines | **the work now** |
| 3. Line sets | range, pipe, channel, triangle (incl. shrinking toward its point) | drawn pairs | after lines |
| 4. Events | breakout, retest, fakeout, confluence — defined by a MOVE, not one candle [owner] | drawn boxes | after line sets |
| 5. Strategy | entries, targets up the ladder, stops, backtest | trades | last |

Rules: each layer is its own module with its own tests; it may use the layer below and must not
know the layer above. A line does not know whether it broke. Claude's first detector broke this
(`strong_resistance` required "no close above" and a 15% fall — event logic inside a line finder),
which is why it could not find the owner's flipped 80.3k level.

## What a trader type sets (owner's idea, 2026-09-23)
"Define what kind of a trader I am… interested in trades that take 2 weeks on average. What is the
average 2-week move for bitcoin? That can be the range sizes I'm looking for. Based on that I can
look for peaks and valleys of close sizes, and based on peaks and valleys we find lines."

Measured on BTC daily (2026-09-23):
- 14-day move, close to close: median 6.9% over 2017-2026, 5.4% over 2024-2026, 5.0% last 12 months.
  Ground covered (high-low) inside those 14 days: 18.3% / 13.9% / 12.7%.
- Zigzag legs, last 2 years: 8% -> 4 days, 10% -> 8, **12% -> 12 days (~22 legs/year)**, 13% -> 16, 15% -> 16.
- So a 2-week BTC swing trader today is a **~12% trader**. The owner's drawn levels sit on 10-14%
  swings, which he found without counting anything.
- The same 10% leg lasted 2 days in 2017-2023 and 8 days now: **the size cannot be a constant**, it
  has to be calibrated from recent data (this answers "fixed % magnitudes go blind in calm markets"
  in SR_LINES_DESIGN).
- One size is not enough: the owner's June-August range is 9.6% wide with 5-9% touches, invisible at
  12%; his ladder needs ~12%. [proposed] a setup has a trade size (~12%) and a structure size (~half).

## Definitions so far
**Turning point** [owner]: a peak / valley confirmed after a reversal of magnitude m.
**Size of a point** [proposed]: the smaller of its two legs; points nest (a 20% point is also a 5% one).
**Points and lines** [proposed]: a point is not owned by one line; a line is built from points of
comparable size ("similar shape" made concrete).
**Line** [owner]: straight in log price, any slope, through / near points it touches; has a start
(first touch), an end (it may stop acting before today) and a state (active / broken / flipped).
**Horizontal level** [owner]: found by searching back from a price zone for the last turning point
of similar size at that price. No window, no line count: "I didn't count lines, I looked for the
previous peak/valley of similar magnitude (similar shape)."
**Trend line** [owner]: from the recent trend, not from history: "I look at that differently."
**Flip** [owner]: a broken level keeps working from the other side (80.3k: support 2025, resistance 2026).
**Range** [owner + his friend]: two roughly horizontal lines acting together, each touched 2-3
times, lasting weeks to ~2 months. Size = width. Measured on his drawing: 2026-06-01 -> 08-22,
81 days, 9.6% wide, 3 touches a side.
**Pipe / triangle** [owner]: the same with slope, never widening; a triangle shrinks toward its point.
**Setup** [owner]: at a date, all the relevant lines across sizes, the structures they form, and the
event now. The number of lines is whatever the chart has — "limiting it to 2 pairs is not enough".
**Ladder** [owner]: the levels above are the targets ("current / next / next next resistance"), the
ones below are support; far ones still count.

## Events (layer 4, not now)
Breakout / retest / fakeout / confluence, all defined by a move rather than a single candle [owner].
Measured examples to test against later: the owner's fakeout (May 2026: runs of 2, 4 and 1 closes
above the 80.3k line, at most 3.2% beyond, then back below) and the confluence breakout of
2026-08-19, where one candle closed above both the range top and the falling trend line.

## The line rule, as the owner states it (built 2026-09-23)
"Found recent support and resistance and looked where else it was in the history."
`modules/shapes/recent_levels.py`, in the playground as rule "recent levels + their history":
- every RECENT swing point (last `recent = last N days`) gives a horizontal level **at its own
  price**; history never picks a level, it only counts how often that price acted before;
- recent points within the tolerance of each other are one level;
- levels are ranked by history touches, then by the most recent anchor;
- trend lines are drawn through the recent points only ("for diagonal lines its the recent trend").

Measured at 2026-09-04, size 8%, recent = 120 days: 6 levels, of which **4 match the owner's drawn
lines** — 57,800 (his "support" 56,956), 59,131 ("recent support" 59,865), 64,166 / 67,292
("previous resistance" 65,733 and "recent resistance" 65,622), plus 73,027 and 70,000 that he did
not draw. His 80.3k "current resistance" appears at 6% (81,479) but not at 8%.
Not found by construction: "next resistance" 106k and "next next" 125k — nothing recent touches
them, they are targets ABOVE price and need their own search (still to do).
### Corrected 2026-09-24 after the owner's review
- **Trend lines** (`modules/shapes/trend_lines.py`): a falling line is resistance and runs on the
  peaks; a rising line is support and runs on the valleys. Nothing of its own kind may poke past it
  between its first and last touch, and it must still be touched now — but it may START as far back
  as the trend goes ("it didnt go long enough"). Wrong-side lines are gone: "i dont think up trends
  support (above the graph) or down trends below are helpful… they seem to add noise".
- **History limit** (`max_history`, default 2): a level keeps only its last visits before the recent
  window. "If we think about current range and its size i can see it in the history twice before
  the current maybe one is enough."
- Measured at 2026-09-04, 8%, recent 120 days, min touches 3, history 2: 6 levels (73,027 / 79,500
  / 64,166 / 70,000 / 57,800 / 67,292, each touched 3x) and 3 falling resistance trends, the best
  being **-0.15%/day, 5 touches, 2025-11-04 -> 2026-08-19**, which is the owner's drawn diagonal
  (-0.20%/day, 2025-09-09 -> 2026-08-28) ending at the breakout. At 12.5% the rule returns
  -0.198%/day 2025-10-06 -> 2026-05-06: his line almost exactly.
- Known noise: with min touches 2, two-touch lines spanning years (e.g. 2020-03-13 -> 2026-07-01)
  outrank the real trend, because the ranking rewards a long reach. 3 is the default for that reason.

Rejected rule (kept in the page as "any line, by touch count"): every pair of points ranked by
touches. It draws 2017-to-2026 diagonals through dense point clouds; the owner: "those lines are a
piece of shit they are not remotely related to the recent dots".

## Open questions (the owner's call)
1. Sizes: a fixed set (5 / 10 / 20%), or calibrated from recent data to the trade horizon (~12% for
   2 weeks)? One size, two (trade + structure), or a sweep over many with a ranking?
2. Span: does a line end at its last touch, or keep running to today while price could return?
   (His range ends 08-22; his 80.3k level runs to today.)
3. Can one turning point support several lines at once? (2026-06-02 is the range's start and a touch.)
4. Should the line layer return everything it finds, ranked by relevance, or only what passes a bar?
5. Range vs pipe: one object with a slope, or two different things?
6. How far up and down does the ladder go? (125k is +54% from today; a lower support "may be useful".)

## Seeing it: swing points in the playground (built 2026-09-23)
"I don't know. We have many ideas and I'd like to just see how it looks on the graph."
The playground's **Swing points** panel draws the peaks and valleys on the candles:
- **trade length in days** -> the calibrated size (14 days on BTC at 2026-09-04: **12.5%**, median
  leg 13 days, 35 legs in 2 years; 40 days -> 21%). Calibration uses only the 2 years before "now".
- **or sizes %** typed by hand (e.g. `6, 12`), up to 4 at once, one colour each.
- Points are those confirmed by "now", so stepping back in time removes the later ones.
- Code: `modules/shapes/swing_calibration.py`, `/api/points`, `ui/js/sr_playground/points_controller.js`.
  12 tests. The line layer will be built on the points that look right here.
