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

## What a setup is (owner, 2026-10-03, confirmed: "thats correct")
The answer to one question, asked from where price is now. Not a list of prices.

**The move running now** is the yardstick: its size is what every line is measured against.

**The lines - about five to seven, not twenty:**
- the trend
- current support and current resistance
- next support and next resistance
- maybe one rung beyond that ("maybe a bit more not a lot more")

**Every line says two things:**
1. **what it is** - its role in the trade, not just a price;
2. **how it was found** - the previous time price was at that level, after a move of comparable
   size. Found by walking back from now and STOPPING at the match: "you found something similar
   like i did and described you stop. you dont check the entire history."

**And the trade that falls out of it:** buy the break of the current resistance (maybe on the
retest); the stop is the previous support, the rung below the one price is standing on ("the
previous support obviously its not rocket science"); the targets are the rungs above in order,
which are the previous peaks above ("the next breakout is the previous peak above that point which
was 96 or 108"). With R, because that is what decides whether the trade is worth taking.

**Plus the state** - what the structure is doing: the overall trend, whether the valleys have
turned, whether price is in a pipe that may hold or break.

**What a setup is NOT:** 723 peaks and valleys, nine years of chart, lines with no reason attached,
or a list of prices with no roles. Those are what made it "too messy" to read.

Open, his call: whether "a bit more" means one extra rung each way, or also the structure objects -
the range / pipe as a named thing rather than two lines.

## Events (layer 4, not now)
> [!warning] Built 2026-10-08 - see "The events and patterns as switches" at the end of this file.
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

## Next build: zones, the current price, and targets (agreed 2026-09-24)
The owner's review of the levels at 8% / 9%: likes 57.8k and 67.3k, calls 59.1k / 64.2k / 70k
noise, and the two most important lines are missing — 80.3k (price is standing on it) and 106k.
Measured causes: 57.8k and 59.1k are 2.3% apart (one zone); 64.2k -> 67.3k -> 70k are 4.9% and 4.0%
apart (one congestion area); the 79,500 peak of 2026-08-21 is a turning point at 8% but not at 9%,
so nothing recent anchors 80.3k, though history has 80,600 (2025-11-21) and 81,500 (2025-03-04);
106k has 107,255 (2025-09-01) but nothing recent, because it is above price.
1. **Zones instead of lines.** Band width from the swing size in percent (about half a swing);
   one line per zone, at the strongest price inside it. Strength = **visits**: touches separated
   by price leaving the zone and coming back, with their spread in time and recency - not a raw
   touch count. Same rule cleans the 3 near-copy trend lines.
2. **The current price is always an anchor.** A level is searched at today's price too, not only at
   recent swing points. When price sits on a level it is labelled by the direction it arrived
   from: came up to it = resistance, came down to it = support (owner, 2026-09-24).
3. **Targets:** the nearest zones above and below price from history alone, no recent touch needed.
4. **Shown as:** a translucent band at the zone's price width from its first visit to now, a solid
   line at its strongest price, ticks at each visit, dots coloured by zone, its own checkbox; and a
   panel that answers from the current price first (on / between, then next up and next down).

## The line layer as it stands (2026-09-24, the owner: "wonderful setup... even better than mine")
One mechanism, no special cases:
1. **Dots**: peaks and valleys of a zigzag whose size comes from the trade horizon
   (`modules/shapes/sr_turning_points.py`, `swing_calibration.py`).
2. **Clusters**: dots fall into price bands of `merge_pct` (`modules/shapes/price_zones.py`). A band
   never grows wider than that, so nothing chains across the chart. Strength = **visits**: price has
   to leave the band and come back (three wiggles in a week are one visit).
3. **Which clusters are shown** (`business_logic_services/level_rule.py`): those price has been at
   recently, plus the nearest ones above and below that nothing recent touches - the **targets**,
   searched at a `target_scale` bigger swing, because the ladder is bigger-scale structure.
4. **One last spacing pass over the whole list**: recent lines and targets come from two different
   clusterings, so the final list may never hold two lines closer than the band.
5. **Trends** (`modules/shapes/trend_lines.py`): a falling line runs on peaks (resistance), a rising
   one on valleys (support); nothing may poke past it before its last touch; it must still be
   touched now but may start as far back as the trend goes; touches count as **visits** (the same
   rule as levels - this is what killed the junk line anchored on the 2020 COVID low); near-copies
   merge and at most one per side is drawn.

**Tuned settings** (preset `tuned lines 2026-09-24`, and the defaults): swing **7%**, band
**1.5%**, min **3 visits**, crowded area goes to the **most recently visited** cluster, targets
**2 each way** at **2.5x** the swing, recent = last **120 days**.
Found by search: sizes 5-12%, bands 1.5-4%, four tie-breaks, min visits 2-3, each scored against
the owner's drawn lines AND his stated likes / dislikes. Result at 2026-09-04:
58,000 / 62,510 / 66,956 / 72,799 / 79,500 (price on it) / 108,969 (target) + one falling trend.
His likes (58, 67) are in, his dislikes (59, 64, 70) are out, and 80k / 106k are found.
**The tie-break was the bug**: ranking a crowded area by most visits kept 63,931 over 65,618, which
sat 0.2% from his own line. "Most recent wins" matches his eye.

## Next session (owner, 2026-09-24, end of session)
1. ~~**Stepping "now" looks broken and is really slow.**~~ Done 2026-10-02, see
   [Stepping "now": what the time was actually going on](#stepping-now-what-the-time-was-actually-going-on).
2. **Show the configuration on the chart.** He cannot see the clusters: which dots belong to which
   line, where the band is, where the visits are. The zone bands were rejected as a replacement for
   his lines, but something light (dots coloured by cluster, ticks at visits) is still wanted.
3. **The lines may be lucky.** "I feel like it got lucky finding some lines from the back but you
   saw in my drawings i used closer ones" - the rule prefers long-lived clusters, while his own
   lines come from nearer history. Worth a term for recency / nearness in the search.
4. `scripts/tune_lines.py`: the search generalised over every drawn setup and its own date, so a new
   setup is draw -> run -> read the table (today's search was hand-run on one date).
5. Then events (breakout / retest / fakeout, by a move), then strategies and backtests.
6. A pass over the code and these docs together.

## Stepping "now": what the time was actually going on (profiled 2026-10-02)
The suspects in the note above were wrong. Profiled (cProfile, BTC daily 3,306 bars, the tuned
preset at 7%, `now` = 2026-09-04): **`trend_lines` was 94% of the call** (31.8 s of 33.8 s);
`price_zones` was 1.2 s and the big-swing target search was not on the list.

Why it was slow: every pair of same-kind turning points (284k pairs at 7%) was scored against
every point one pair at a time, and the visit grouping ran for all 140k pairs that survived the
slope filter. Two of the owner's own rules are cheap filters that were being applied last:
- a trend must **still be touched now**, so it must hit one of the few points inside the recent
  window — testing the pair against those alone first carries 8k of the 142k pairs;
- grouping touches into visits only ever **drops** bars, so a pair with fewer raw hits than
  `min_touches` can never pass.
With those first, and the remaining work batched as one matrix per point instead of per pair, the
answer is **unchanged**: verified identical over 90 `price_zones` cases, 90 `trend_lines` cases and
60 whole-answer cases (10 dates x 3 sizes x 2 settings), and the tuned preset still returns
58,000 / 62,510 / 66,956 / 72,799 / 79,500 / 108,969 plus one falling resistance trend.
`price_zones` got the same treatment (one band membership matrix, visits as rising edges).

Measured over real HTTP, pristine server, quiet machine:

| | before | after |
|---|---|---|
| `/api/points` alone, first call after start | 9.0 s | **0.72 s** |
| `/api/points` alone, ten -7d steps | 7.4 s mean (max 10.0) | **0.77 s mean (max 1.4)** |
| in the page, one -7d step | 6.7 s | **0.58 s** |
| in the page, four -7d steps pressed quickly | **113 s**, all four computed | **4.7 s**, three cancelled |

The page now aborts a superseded `/api/points` (`AbortController`) and the panel says
`computing… (the lines below are the previous answer)` with the `points` panel marked busy, so a
stale answer can no longer look like the current one; when the answer lands the panel shows how
long it took. Browser-checked end to end (10 checks: the busy line appears on the click, 3 of 4
requests are cancelled, the kept answer is the one for the date on screen).

### Two findings that are the owner's call
1. **The 94 s cold start is `/api/setup-detections`, not the lines.** On a pristine server the
   setup detector runs over all of 2017-2026 on the page's first load and holds the interpreter for
   16-22 s (measured 16.6 s and 21.6 s on two single loads); `/api/points` is fired at the same
   moment and waits behind it (19-22 s) although its own work is 0.7 s. Reload before the first run
   finishes and two of them overlap: 53 s measured. Nothing in the fix touches that endpoint - it
   could be computed lazily, in a worker, or only when the detections panel is opened.
2. **Cancelling in the browser does not stop the server.** The fetch is aborted, but the request's
   thread keeps computing to the end, so four quick steps still cost 4.7 s instead of 0.6 s: the
   last request shares the CPU with three abandoned ones. Stopping them needs the server to know a
   request is superseded (a request id plus a check between stages) - not built, not asked for.

## Seeing it and talking about it (built 2026-10-03)
The half of the system that is not the algorithm: how he sees what the code did and tells Claude why
it is wrong. Every one of these was asked for by him, and between them they produced six of the
design corrections in this session.

| tool | what it is for |
|---|---|
| ✓ / ✗ on every line, with a note | his verdict on what the code drew, recorded as ground truth instead of living in the chat |
| "draw instead" | the line he would have drawn in its place, linked to the verdict |
| freehand sketch (Ctrl+drag, or the Sketch tool) | explaining something in a picture; several strokes under one note; keep it, or "just showing you" and clear it later |
| swing boxes | each peak and valley as the journey it is - support to resistance to support - bounded to the picture |
| the setup, explained | a card describing the lines the chart draws: what each one is, how it was found, and the dots it is made of |
| click a line | only that line, its dots, and the boxes of those dots - nothing else |
| the sidebar as cards | one card per section, open what you need |
| the build stamp | the page says when its own files changed, so a cached page can never be mistaken for a bug |

## Next session (2026-10-03, end of session)
**The order is decided (owner, end of session): keep improving the LINE algorithm. Events,
strategies and backtests wait** - "we still cant build on that ... we have more tools to do it."
Everything downstream reads the lines, so a line layer that is only "partially good" on a second
date would be measured by a backtest that cannot tell a bad strategy from a bad line. The tools
built this session (his verdicts on each line, notes, "draw instead", sketches, the boxes, one line
at a time, the explanation card) are the means to do it.

His read, in his words: "the setup is correct and shows nicely. i can see it got there using
parameter tuning and not geometrically like me so it may overfit but thats a start because it is
correct... need to see it on other graphs." A quick look at another date: "partially good. not like
this setup. it means its not generic."

1. **Make it generic.** It is tuned, not derived. The knobs that are still Claude's guesses and have
   never been searched: the swing size (the page still defaults to **7%**, though he has twice said
   9% is better and 9% is the only size where his own two numbers agree), the band, the "same move"
   similarity window (0.7-1.45x), and what makes a cluster "good" (currently >= 2 dots, which filters
   almost nothing).
2. **The supports are still the weak side.** The resistance comes from his search; the supports come
   from the nearest good cluster, which lands near his 72,799 and 66,659 but not on 59,906 or 56,932.
3. **Targets:** walking back gives 97,924 (his "96") and then 116,400, where he said 108. His own
   phrasing was "96 or 108", so this may be looser than it looked - but it is unresolved.
4. **At 9% the rule returns no resistance at all** - every line is below price. The size decides
   whether the trade even has a target.
5. Then the structure objects he described but Claude has not built: the range / pipe as a named
   thing, and the valley-direction change that ends a downtrend.
6. Scoring the ✓/✗ verdicts: they are recorded but nothing reads them yet, so false positives are
   still uncounted (`ground_truth_score.py` returns `extra` and ignores the verdicts).

## His rules, stated and NOT in the code (collected 2026-10-04/05)
Ideas he has said out loud that the code either contradicts or has never implemented. Written here
because they were living in the chat only - "all the ideas are documented well?" - and the answer
was no.

| # | his rule, in his words | what the code does |
|---|---|---|
| 1 | **"higher highs up trend, lower lows down trend, same hight horizontal range"** | nothing. Trend is a geometric line fit; the structure of the peaks and valleys is never read. The "valleys turned" state in his own setup definition is also unbuilt. |
| 2 | **"up trend lines are marked by candle lows meaning below them and downtrend by highs meaning above them"** | HALF done. A peak's price is its HIGH and a valley's its LOW (`sr_turning_points.py`), so the touch points are right. But the containment check (`trend_lines.py`) only asks that no *turning point of the same kind* pokes past the line - never that no CANDLE low sits below a rising support. And past its last touch the line is extrapolated with no containment at all, which is how 2025-10-03 draws a "support" at 138,120 with price at 122,232 - above the candles, the wrong side entirely. |
| 3 | **"lines can use both peaks and valleys"** (2026-09-22: "a single line can touch both peaks and valleys and split the graph") | contradicted. `trend_lines` fits falling lines on peaks ONLY and rising on valleys ONLY. His separate rule - that a rising line ABOVE the graph is noise - was merged into this one and the "both kinds" half was lost. |
| 4 | **"its not the time its the shape level and size"** - walk back to the last move at a similar level and size, learn from the important parts of history and only them | built as the EXPLANATION only (`precedents.py` writes "how it was found"). The lines themselves are still chosen by clustering plus a most-recent tie-break, so his search explains an answer it did not pick. |
| 5 | **"my drawings are less sensitive than yours… look at your touch points boxes, its based on nothing"** | the swing size and the cluster floor (>= 2 dots) are unsearched guesses; at 7% the chart carries 1,013-1,067 points, and the dots a line is built from are not turning points to his eye. |
| 7 | **"i want only the related boxes to the calculated lines. now i see a million boxes"** (2026-10-05) | DONE: boxes are the touch zones of the lines the code drew, not one per dot (one box per turning point put 1,012 on the chart at 7%). |
| 8 | **"and those boxes dont look like what i wanted"** - a box is a TOUCH ZONE, a stretch of bars as tall as the band, with the line through it | DONE: `modules/shapes/touch_zones.py`, reproducing his own 2023 example to 2.84% against his 2.85% / 2.72%, and telling a touch from a break by which side price leaves on. |
| 6 | **the trade mindset: "what this setup leads to with plans - what if it goes up and what if down, where do we expect the move to reach"** | the roster names roles and the diary records the plan (buy the break, stop at the rung below, targets up the ladder, in R), but the card does not state the two branches or where the move is expected to reach. |

## Drawn, not written: the two pictures he made to show the base (2026-10-05)
Two "just showing you" sketches in `data/ground_truth/sr_annotations.json`, drawn at "now" =
2024-12-06. They are the spec for what a box and a touch are. Measured from the saved strokes:

**A. The range** (group `gmuubw57d`, 2 strokes) - a box around the whole 2024 consolidation:
2024-02-21 -> 2024-11-09, **50,301 - 74,593** outer and **53,589 - 71,174** inner. Nine months,
holding many peaks AND valleys. In his words: *"look how i showed the range inside. the peaks and
valleys i saw. the ones i ignored because its too sensitive. overall i looked at moves that are
from line to line or at least close without small spikes between. there was a candle who broke the
support in a tail but got back and i ignored this spike."*

**B. The line and its touch zones** (group `gmuuca0qu`, 3 strokes): a flat line at **~30,800**
running 2023-04-03 -> 2023-11-03 (0.5% drift in seven months), with two zones drawn ON it -
**2023-04-09 -> 04-21, 29,947-30,800 (12 days, 2.85% tall)** and **2023-06-19 -> 07-18,
30,409-31,236 (29 days, 2.72% tall)**. His note: *"here is another example of a line and the boxes
with touch zones. not touch dots like you do. touch zones. when you draw lines and explain to me
based on what you drew them i expect to see things like"*.

### The rules those two pictures state
1. **A box is one of three things** [owner]: one turning point's journey (support -> resistance ->
   support); a **flat zone**, several same-kind extremes at one height; or a **range**, a flat top
   and a flat bottom holding together over time. Only the first exists in the code.
2. **A turning point counts when its move runs from line to line, or close** [owner]. The swings he
   ignored inside the range are not smaller than some percentage - they are the ones that do not
   cross the range. This is what "too sensitive" means, and it makes the swing size RELATIVE to the
   structure instead of a constant.
3. **A spike through a boundary that comes back is not a break and not a turning point** [owner] -
   a tail broke his support and he ignored it. The code has no such rule: a wick that exceeds the
   threshold creates a point.
4. **A touch is a ZONE, not a dot** [owner]: a span of time and a band of price where price worked
   the level. His two are 12 and 29 days wide and ~2.8% tall. The code marks single bars.
5. **Everything drawn must show what it was drawn from, inside it** [owner]: *"when you show me
   your boxes i want to see what you did in them."*

## C. The pipe, the trend and the sizes (drawn 2026-10-05, group `gmuv72nhv`, at "now" = 2026-02-13)
Eight strokes and a note, measured off the saved points:

- **the pipe**: a flat top at **72,500** and a flat bottom at **54,450**, both running 2024 -> 2026
  - 25% tall. "i would consider the pipe top as resistance for the current price and bottom as
  support but the trend is also kind of resistance."
- **the down trend**: lower peaks at **-0.205%/day** (2025-09-17 130,558 -> 2026-06-18 74,507) and
  lower valleys at **-0.355%/day**. "this is a downtrend. i sketched the lower and lower peaks and
  valleys."
- **two arrows, which is what a size means**: the pipe's height **71,255 -> 55,311 = 22%**, and the
  descent running now **94,935 -> 67,071 = 29%**. He calls both "about 20%" - the point is that
  they are THE SAME SIZE, which is why that pipe is the relevant one: "i also drew the last similar
  20% size pipe which i saw at the current price".
- "you can also see the peaks and valley i used and noises i ignored."

## The order he works in (owner, 2026-10-05)
> "i look what happens now, which price, latest peak or valley, current move from it including its
> size, trend, and then look for support and resistance from the history. thats it."

1. price now 2. the latest peak or valley 3. the move from it, and its size 4. the trend
5. the support and resistance, searched in history **by the relation to that move**.

The code narrates in this order but is not built in it: it clusters all of history by price first
and computes the trend separately, so the trend influences nothing and the move only sets a band.

## The roster: three lines, four if price is on a level (owner, 2026-10-05)
> "i dont want no next and i want the last trend. should be 3 or 4 if price is on the level" /
> "if we are not on a level i want the above and below sr lines and if we are i want that level too
> which based on the trend you classify it."

- **the trend** (one line)
- **the level above** and **the level below**
- **the level price is on**, when it is on one, named by the trend: resistance in a down trend,
  support in an up one.

## The trend, as he defines it (owner, 2026-10-05)
> "i want a last trend line which is the last line with at least 2 peaks and valleys at changing
> levels. it possible we already broke it and dont have 2 peaks and valleys yet so we didnt change
> the trend yet ... if it horizontal thats a trend too." / "if its a horizontal move with same
> hight peaks and valley ok but if not you need to find the last trend that had it."

- **up**: the peaks are higher AND the valleys are higher. **down**: both lower.
- **horizontal**: the peaks are at one height AND the valleys are at one height - a range is a trend.
- **unchanged**: when they disagree, nothing has replaced the old trend yet; walk back to the last
  one that had two peaks and two valleys.

> [!warning] Refined 2026-10-07 - see the counted version below. The four states above stay true;
> what changed is how many steps it takes to start or end a trend.

## The trend, counted in steps (owner, 2026-10-07, at 2023-03-24)
> "up trend is 2 higher highs and 2 higher lows. downtrend is the opposite. there is no trend change
> if not at least 2 such. as you can see sometimes there are spikes and noises but the rule applies
> here. can also be higher high higher low lower high higher low which is a closing triangle. here
> is the opposite which is forming an opening triangle and i didnt draw it because we dont care
> about those because there is no breakout in them."

His sketch at 2023-03-24 (note: "two higher highs but not two higher lows only one and than a lower
low but not another lower low after that so no change to downtrend and then came a higher high so a
continue of the trend"): zigzag 16,657 -> 23,777 -> 21,547 -> 25,092 -> 19,836 -> 28,689.

| state | the steps | what it means |
|---|---|---|
| **up** | 2 higher highs AND 2 higher lows | a trend |
| **down** | 2 lower highs AND 2 lower lows | a trend |
| **unchanged** | anything less than 2 opposite steps | one lower low in an up trend is noise (2023-03-10) |
| **closing triangle** | higher high, higher low, then lower high, higher low | converging - it can break out, so it matters |
| **opening triangle** | higher highs with lower lows | widening - no breakout, ignored ("we dont care about those") |

- "Higher" is relative: a step smaller than "the same level" (a share of the move) is no step.
- The rule is only as good as the zigzag it counts: at 2023-03-24 the algorithm's zigzag carries
  one wiggle he ignored (26,387 -> 23,897 on 03-14/15, a wick) and otherwise matches his to ~2%.
- OPEN (asked 2026-10-07): the trend LINE. His line here runs from the low that started the trend
  (16,657) to the latest high (28,538), crossing the candles; his down lines at 2026-02-13 and
  2026-09-04 run over the highs. Not yet decided which rule draws the line.
- Status: written here, not yet in the code (trend_state.last_trend still compares one step).

## No magic numbers: every threshold is a share of the move (owner, 2026-10-05)
> "flat 2% what if we traded scalping? the threshold will be meaningless. its relative to the move.
> no flat magic numbers. its structural/geometrical. we talked about it. compare it to the move
> size." / "i dont care about 3% when the move is 10%, so dont write shity code."

Bounded by his own dates rather than chosen:

| what | share of the move running now | what bounds it |
|---|---|---|
| how wide one level is (`MOVE_BAND`) | **0.25** | > 0.11 merges his two supports at 2025-10-03; < 0.56 keeps his two lines 7.1% apart at 2026-09-04 |
| "the same level" for the trend (`FLAT_SHARE`) | **0.45** | >= 0.35 makes 2026-04-10 horizontal as he reads it; < 0.57 keeps 2026-09-04 a trend |

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

## The line layer as it stands (2026-10-07) - the current WHAT
> [!warning] Supersedes "The line layer as it stands (2026-09-24)" and "The roster: three lines,
> four if price is on a level" above as the description of the code. Their why stays in the diary.

Built over 2026-10-06/07 from his reports at his own dates, each change measured at every date he
had reviewed before it was kept. In his order:

1. **Peaks and valleys (the dots).** A zigzag on candle highs and lows; a point is confirmed only by
   a LATER candle, never its own (`modules/shapes/sr_turning_points.py`). The old "drop the second
   point on one candle" fix kept a fake 70,000 peak at 2026-08-19; "9 is better" was measured on it.
2. **The move running now** - from the latest peak or valley to today's close
   (`modules/shapes/swing_moves.py`). Matches him at 2026-09-04 (30.2% off his 62k valley) and
   2026-02-13 (29.7%).
3. **The yardstick** - what "relative" is measured against (`business_logic_services/structure_scale.py`):
   the move running now, unless the leg into the latest peak or valley, read at its own scale, finds
   a RANGE price is inside - then that range's size (2024-08-02: 25.7%, his "about 25%"). Never in a
   trend: there every larger scale finds a larger leg (2024-01-19 ran away to 77.6%).
4. **The structure** - peaks and valleys at the yardstick's scale: a swing counts when it is "the
   same move" (`precedents.SIMILAR_LO`, 0.7 of it). This is the zigzag drawn by the **zigzag** checkbox,
   and his 2023-03-24 zigzag matches it to ~2% but for one wick.
5. **The trend** (`business_logic_services/trend_structure.py`, `trend_state.py`):
   - up / down / horizontal from the last peaks and valleys; a range PRICE IS INSIDE is horizontal;
   - sideways also reads **the previous trend** - before the range's first peak or valley;
   - the line runs over the highs (down) / under the lows (up) from where the trend began, through
     the point that keeps the later ones on the far side, allowing a poke of a level's width; a line
     steeper than one swing per "same level" is one leg, so the trend began earlier;
   - a trend line further than the move can reach (1.45x) is drawn DOTTED and said so, never hidden;
   - each trend says its size: start -> furthest point, % and days.
   - NOT YET IN THE CODE: the counted rule ("2 higher highs and 2 higher lows", see "The trend,
     counted in steps") and the start-to-end line - the open question above.
6. **Support and resistance** from the same structure's dots (targets still from the 2.5x zigzag -
   moving them broke 2026-05-15). Then, in `business_logic_services/setup_roster.py`:
   - a level comes from a PREVIOUS support or resistance: dots of the move running now don't count
     (2022-07-22: 24,286 -> his ~29k);
   - the level price is on must be where the move running now turned, not one price passes through
     (2024-10-25: 66,867 dropped);
   - in an up trend the resistance above is the latest peak (2023-04-21: his ~31,400);
   - inside a range the levels are its walls, built from its two peaks and two valleys;
   - the card and the chart share one answer to "is price on it".
7. **What is shown** (his definition, 2026-10-06): support and resistance always; the trend if it is
   up or down (the previous trend if sideways); the level price is on plus the next one past it;
   at most 4 lines.
8. **Strength** of each level, measured - see "Line strength, measured" below.

Visibility added with it: close-only line chart, close dots, zigzag, and his checkbox state printed
in the server's VIEW line (`on: ...`).

**The frozen zigzag (2026-10-07)** - "i want the before 7d to be roughly like the date im looking".
Read at today's scale, the whole history was redrawn daily (a date shared a median 71% of its
zigzag with the date 7 days earlier, 44% in the worst quarter). Now every peak and valley is decided
at the scale of the day it was confirmed and stays (`business_logic_services/frozen_zigzag.py`):
100% / 96%. The drawn zigzag, the support and resistance, and their strength use it; 2025-04-25 is
back on his lines (103,404 / 88,878). The TREND is still read at today's scale, because on the
frozen zigzag it lost four of his readings (2023-08-11, 2025-07-04, 2026-05-15, 2026-09-04) - so the
trend line's points need not be on the drawn zigzag. One approved line moved: 2026-09-04 support
69,000 against his 72,799 (was 72,396).

Tried and not kept: a steady ruler (the size capped to keep 2 peaks + 2 valleys in the move) - steady
only because it sat at the 7% floor on 93% of dates; and the counted trend rule as first built -
requiring two lower highs AND two lower lows in a row never ends a trend on a zigzag with small
swings in it ("up" everywhere since 2020, 3 of 10 of his readings). The rule is right; "2 such" needs
a reading that a single small bounce cannot interrupt. Still to build.

## Line strength, measured (2026-10-07)
His ideas: closer = stronger; held a long time = stronger; the move afterwards; many flips = weak;
broken many times = weak, never broken = strong - "a strength score based on both?". Each became a
feature and was measured rather than weighted by hand (`business_logic_services/level_strength.py`):

- Every level within the move's reach, weekly 2018-06 -> 2026-07: 2,419 levels. Outcome: at the next
  visit, did price turn (a touch) or go through (a break)? Base rate **50.3%**.
- Alone, every idea is weak (AUC 0.46-0.54): recent, long-lived and a big move afterwards each help
  a little; **levels broken before turned slightly MORE often** - the flip, not weakness.
- Together, fitted on 2018-2022, tested on 2023-2026: AUC **0.568**; the strongest quarter turned
  **61%** of the time, the other three quarters **47-48%**.
- So the card labels a level **strong** (top quarter) or **ordinary**, with that measured rate. It
  does not choose the lines: an effect this size is a label and a tie-breaker, not a rule.
- Each line also says how often price held at it and how often it broke through - "dont count only
  how many times they were respected but also broken" (2026-10-07).

## Highs and lows, or closes? (measured 2026-10-07)
His question: "highs and lows have the most noise, open close less, close only has the minimum noise."
True of the noise. Measured through the whole pipeline at his dates, closes (and candle bodies) do
worse - at the same threshold they also drop real swings (258 dots against 619), and at a matched
scale they still lose his approved lines (2022-07-22, 2024-10-25, 2026-02-13, 2026-09-04) - because
his lines sit where the wicks reached. The dots stay on highs and lows; the wick noise is for the
tail rule and the scale. The close-only line chart and the close dots are in the page to look at.
His friend's habit of 1 year of history was measured too: better at 2 dates, broke 4 (his old flips).

## His ideas not yet built (found in the conversations, 2026-10-06)
- **The trend from the timeframe above** (2026-09-23): "swing trades that take about 10 days ... we
  use the daily and hourly graphs to manage the trades it makes sense to understand the trend from
  the weekly for example."
- **Speed in a turning point** (2026-09-22): "peak as minimum 10% up in a couple of candles and then
  down" - the "couple of candles" part was never answered and dropped. Claude's read: it belongs to
  events (how fast a breakout runs), not to the dots.
- **Searching the size by profit, later** (2026-09-23): "its just one setting ... when we get to the
  strategy stage ... we could backtest to see the most profitable setting." Behind it: 3 days / 7%
  shows the peak in the middle of the small pipe but the rest is noisy; 14 days is clean.
- **Pick the structure that is there** (2026-10-05, at 2025-10-03): "maybe horizontal pipe is not
  the right tool here because there is no horizontal move with 2 peaks and valleys at the same
  hight" - and the pipe should be about as tall as the move. (Partly built since: the range rule.)
- **The counted trend rule** and **the start-to-end trend line** - see above. Second build
  (2026-10-07, a step back the trend's way cancels a noisy one): lost 6 of his readings and was
  reverted. Cause, measured: at the scale that gets his dates right there are not enough points for
  "2 such" - at 2026-02-13 only one lower high (126.2k -> 97.9k) and one lower low (80.6k -> 60k)
  exist, so the 2023-2025 up trend never ends. The rule needs a finer zigzag than the one his levels
  and trend lines are matched on.
- **The tail rule on the dots** (2026-10-05): a wick through a level that comes back is not a turning
  point - still makes dots. His two examples do not share a cut: 2020-12-20 fell 10.2% on the wick
  and 6.5% on closes; 2023-03-14 fell 9.4% on the wick and 8.0% on closes. Any line between them is
  fitted to two cases, and the blanket close-confirmed version broke four approved dates. Needs more
  of his marked tails before it can be a rule.
- **Strength as a tie-breaker** between close candidates - measured, not wired.

## Ideas from other sources - indicators and literature (collected 2026-10-08)
> Not his ideas: what the popular TradingView scripts and the books do, collected at his request -
> "id like to get the ideas from them to my ideas collection ... the most important thing to me is
> the ideas". Each says which of our open problems it touches. Nothing here is a rule until he picks it.

### Where a level comes from (the swing points)
- **Pivot of N bars each side** - a high higher than N bars before and after (every pivot script;
  LuxAlgo "S/R Levels with Breaks", 65.5K uses: the latest pivot high IS the resistance, the latest
  pivot low IS the support - nothing more). A fixed lag of N bars.
- **Donchian alternating** (LuxAlgo S/R Pro Toolkit): a state machine - a new higher high confirms
  the previous low at once. No fixed lag.
- **CSID** (same toolkit): a level where a run of N same-colour candles began - where a strong move
  started, not where it ended.
- **Zigzag by %** (ours), **by ATR** (a multiple of the average candle range, so it widens when the
  market is wild - touches "the zigzag is too fine after big tops"), and **MT4 / ZigZag++**: three
  rules together - deviation (the % move), depth (minimum bars between points) and backstep (how many
  bars a point can still be replaced) - size AND time.
- **Recursive zigzag** (Trendoscope): the zigzag of the zigzag - level 2 is built from level 1's
  points, and so on. Every size is a level, and each level's points are a subset of the one below:
  never two zigzags that disagree. Touches "the trend needs a finer zigzag than the lines".

### Which levels count, and how strong
- **Channels of pivots** (LonesomeTheBlue "S/R Channels", 47.5K uses - on the page as a rule): pivots
  within a width (5% of the 300-bar range) are ONE level; strength = 20 per pivot + 1 per bar that
  touched it; the strongest non-overlapping ones shown.
- **Tests counted until a close goes through** (LuxAlgo Zones Strength Classifier): a test = price
  came back and did not close through; a CLOSE through deletes the zone ("mitigated"). Zone height
  from the average candle range.
- **Super zone** (Pro Toolkit): when two zones overlap, the OLDER one grows to take the newer one.
- **Liquidity sweep** (Pro Toolkit, SMC): a wick through the level that closes back is not a break -
  it is a sweep, and it adds strength. This is his tail rule ("broke the support in a tail but got
  back and i ignored this spike"), stated as a feature rather than a filter.
- **Volume** (ChartPrime High Volume Boxes; LuxAlgo Breaks): a pivot made on high volume is a
  stronger level; a break counts only with a volume surge.
- **Equal highs / lows** (SMC): two peaks at one height are where stops sit - a target, likely to be
  taken, not a wall.
- **Strong / weak high** (SMC): the high that made the latest break of structure is protected
  (strong); the other is weak and likely to be taken.
- **Premium / discount** (SMC): above the middle of the current range is expensive, below is cheap.
- **Round numbers** (Osler 2000, 2003): banks' published levels ended in 0 or 5 96% of the time;
  take-profits cluster AT round numbers (price turns), stop-losses just PAST them (breaks speed up).

### How the trend changes
- **Protected low / BOS-CHoCH** (Dow; LuxAlgo Market Structure, SMC): an up trend lasts until a CLOSE
  under the low that launched the latest higher high. Small bounces never move it. Tried on the page
  2026-10-08 (business_logic_services/protected_trend.py): 1 break matches all 7 of his up/down dates
  but turns 2022-07-22 up (loses his 29,000); his "2 such" keeps 29,000 but loses 2026-02-13.
- **Two sizes of structure**: internal (small pivots) and swing (large) - each with its own trend;
  Dow's three degrees. A secondary reaction retraces 1/3-2/3 of the primary move; more than 100%
  means a new trend.

### When a line is broken (Murphy)
- A close beyond counts, a wick does not; filters: 3% beyond (long lines), or 2 closes in a row.

### Measured on BTC daily 2018-2025 (2026-10-08)
- Zigzag levels turned price at the next visit 55.1% (7%) / 57.6% (14%) against 49.8% / 52.4% for
  arbitrary prices: +5 points - Osler's banks got +4.6.
- No decay with age: 1-4 year old levels turn as often as 3-month ones - no reason to cut the
  history. Touches or breaks before: no clear effect. Whole 10,000s: +3 to +7 points (small samples).
- The channels script against his lines: his 10 reviewed dates, 13 of 20 found with 31 drawn (ours
  12 of 20, 28 drawn); his 11 drawn lines at their dates, 6 found (ours 2) - 4 of 8 vs 2 of 8
  without the three 2026-02-20 supports that may be a check's.

Sources: LuxAlgo S/R Levels with Breaks, S/R Zones Strength Classifier, S/R Pro Toolkit, Market
Structure, Smart Money Concepts; LonesomeTheBlue S/R Channels and S/R Dynamic v2; ChartPrime High
Volume Boxes; DevLucem ZigZag++; Trendoscope Recursive Zigzag; Osler 2000 (NY Fed); Chung & Bellotti
2021; Murphy, Technical Analysis of the Financial Markets; Dow Theory.

## The line concepts as switches (built 2026-10-08)
His decision: "implementing these concepts with flags will help in testing it" - and "i wanna know
what made the algorithm draw each line". Rule "concepts" in the page's Swing points panel; code in
`business_logic_services/line_concepts.py` (the steps), `level_parts.py` (strength),
`concept_story.py` (the card), `modules/shapes/swing_sources.py` (pivots, ATR zigzag). The server's
VIEW line prints the switches.

| switch | choices | default |
|---|---|---|
| swing points | our zigzag (frozen) / pivots, 10 bars each side / ATR zigzag, 2.5 ATR | zigzag |
| grouping | channels (points within the band are one level) / off | channels |
| band | a share of the move (MOVE_BAND) / 5% of the 300-bar range | move |
| strength | pivots x20, bars touching, wick sweeps x20, round number +20, measured % | first three |
| trend | protected low 1 break / 2 breaks / last peaks and valleys / off | 1 break |
| which lines | his roster / nearest each side / strongest each side, N per side | roster |

The strength weights are the S/R Channels script's units, not measured - the backtest weighs them.
Every line on the card says its points (dates), its band, its score and parts, and what kept it.

Measured at his 10 reviewed dates (20 lines) and his 11 drawn lines, within 2.85%:

| combination | his dates | his drawn lines | lines drawn |
|---|---|---|---|
| zigzag + channels + move band + nearest 2 | 18/20 | 5/11 | 54 (~5 a date) |
| ATR zigzag + channels + range band + nearest 2 | 16/20 | 7/11 | 55 |
| best with his roster (ATR + channels + move) | 14/20 | 3/11 | 31 |
| the hand-tuned rule (before) | 12/20 | 2/11 | 28 |
| the S/R Channels script, nearest 2 | 13/20 | 6/11 | 31 |

Grouping into channels is the switch that matters most: every top combination has it.

## The events and patterns as switches (built 2026-10-08)
His words: "make sure its well separated so we could choose the specific breakout pattern or patterns
with flags and assemble full strategies ... and make sure its visible". Layers, each using only the
one below:

| layer | what | code |
|---|---|---|
| lines of each day | the concept lines computed for EVERY day from 2018-06, cached on disk per setting; an event on day d sees only day d's lines | `business_logic_services/line_history.py` |
| event detectors | one function per event, at one line, from bars <= d | `modules/events/detectors.py` |
| patterns | from the peaks and valleys known on day d, decided on the first close through the neckline | `modules/patterns/` |
| candles | pin bar, engulfing, piercing / dark cloud - both directions | `modules/candlesticks/candle_signals.py` |
| events over history | every switch in `EventFlags`; each event says why | `business_logic_services/event_service.py`, `event_story.py` |
| strategy blocks | `EventBlock(kinds, direction)`: fires on the day an event was decided; strategies combine blocks ALL / ANY / N-of-M | `business_logic_services/event_blocks.py` |

| event | decided on | source |
|---|---|---|
| breakout | the Nth close in a row beyond the zone, coming from the other side (N = 1, or 2 = Murphy's 2-day rule) | Murphy, Edwards & Magee |
| fakeout | a close beyond the zone, then within K bars a close back across the line | Wyckoff spring / upthrust, Raschke's Turtle Soup |
| sweep | one candle's wick through the zone, its close back across the line (his tail) | SMC |
| retest | the first return to the zone after a breakout, closing on the breakout side | Edwards & Magee (role reversal), Bulkowski (throwback) |
| bounce | in the zone from one side, the first close out of it on that side | Wyckoff test |
| trend change | the day the trend's direction (the concept's trend switch) changes | Dow / CHoCH |
| confluence | every line event lists the other lines in its zone that day | general |
| double top / bottom, head and shoulders (+ inverse), cup and handle, bull / bear flag | the first close through the neckline; target = the measured move | Edwards & Magee, Bulkowski, O'Neil |

The zone of a line is its band (half the day's band each side, a share of the move). The detectors'
windows (fakeout 5 bars, retest 20) are stated guesses and switches, not measured.

**Seeing them** - "too messy. i want a dot that i can click and it opens a card and explains"
(2026-10-08, replacing letters on every event plus boxes on the last 120 bars): ONE small dot per day
with events, under the candle (up) or over it (down), grey when that day's events point both ways.
Clicking the dot opens a card beside it with each event of that day and its why, and only then is
its line, its box over the move and a pattern's points drawn; ✕ or a click elsewhere clears it. The
Events card keeps the switches, previous / next event across history, and the list newest first.
The lines the same way ("the lines dont write text show a dot at the end of the line"): no words on
the chart - no role beside the points, no label on the touch boxes - and a dot at each line's end
(now + 30 days) that opens the same card with the line's role, price and how it was made. One card
for every dot (`ui/js/sr_playground/chart_card.js`).

**Stars replaced the dots (same day).** "i would say the events arent good ... currently i see a
million dots ... lets think more simply about whats related to the current price and current lines."
Checked at his 2025-12-28: of the last 20 events, 5 made sense (breakouts and retests of lines on
screen 12-18 of the previous 30 days, 2.7-16% follow-through), 7 went the other way (bounces, a sweep,
two retests), 8 were December chop on lines 0-6 days old, two labels on one candle; the 47 events in
view sat on 25 different levels, 3 of them on a line he could see. So the chart now shows only
breakout / retest / fakeout at the lines ON THE SCREEN, during the move running now, one per candle
and line, judged in the page's touch zone (+-1.4%) - a gold star on the line, clicked for the card with
its picture and why (`business_logic_services/line_events.py`, `ui/js/sr_playground/line_dots.js`).
At 2026-09-04: 2026-08-19 breakout up through the trend line at 67,262 (his confluence breakout) and
08-20 through 69,000; at 2025-12-28 none - nothing happened at today's lines since 12-09. The events
over all history (Events card) are off by default; they stay for the backtest.

## Lines from the zigzag, kept (built 2026-10-08) - rule "from the zigzag (kept lines)"
His: "if we dont keep what we drew previously how are we gonna find a breakout or retest on that? ...
i like the zigzag use that for the lines." Code: `business_logic_services/zigzag_lines.py` (the lines),
`zigzag_view.py` (page and card), `screen_lines.py` (the one source of lines the page, events and
strategy read), `setup_history.py` (those lines for every day, cached).
- Levels: ~~every frozen-zigzag point, the nearest above and below price~~ - replaced the same day:
  "too recent they dont really show the trend ... i click next 7d and it changes drastically" ... "zigzag
  didnt make a new point you dont create a new sr line and even if it does you dont necessarily create
  a new line" ... "simple rule lines are based on zigzag". Now: the line of the zigzag's LAST PEAK and
  of its LAST VALLEY; a new point within 1.5% of an existing line is a touch of it, not a new line;
  they change only when the zigzag makes a point (measured 2018-2026: 262 change days, 0 without a new
  point; 70% of lines still there a week later, against 47%). Price going through one is its breakout.
  At 2025-04: resistance 89.3k (the March peaks) held all of April and was broken on 04-22; the 04-07
  valley 74,508 touched the 73.8k line (the March 2024 high). The old rule left the page's menu.
- Strength of every component (`business_logic_services/zigzag_strength.py`, 2026-10-08) - "you really
  need to add strengths of everything. from dots to lines to sizes to touches to duration. its not even
  part of the strategy its part of its components": a dot's swing (the move into it and out of it); a
  level's zigzag points, their biggest swing, days held from first to last touch, age; a trend line's
  move (% and days) and its points; each level's swing as a share of the trend's (2022-07-27: 22,527 on
  one point, a 19.9% swing = 0.31x the down trend's 63%). Shown on every line's card and the trade card;
  the strategy has switches min_touches and min_share (a quarter of the trend - a stated guess).
  Backtest (touch retest, zigzag lines): plain 19 + 8 trades, PF 2.56 / 0.80; with 2+ points and >= 0.25x
  the trend 17 + 6 trades, PF 3.16 / 1.53 - better in both periods, on too few trades to prove it.
- A level needs TWO zigzag points ("why is this a resistance ... it touches one zigzag point"): one
  point is a point. Shown: the most recently touched two-point line above and below price, decided when
  the zigzag makes a point. 2022-07-08: the one-point 20,918 is gone; 21,723 (06-21, 06-26) and 18,626.
- The trend by his counted rule (`zigzag_trend.py`): it stays until 2 higher highs AND 2 higher lows
  (or 2 lower) replace it; a new extreme the trend's way starts the count again. Matches him at 5 of 8
  reviewed dates (misses 2023-08-11 up, 2024-08-02 sideways, 2026-09-04). On the trade card and as a
  strategy switch.

### Improvement round 1 (2026-10-09) - "improve and backtest ... you can read all the trades yourself"
Strategy on the two-point zigzag lines, every switch combination (retest touch / hold / zigzag x trend
any / not_down / up x all / strong lines): every variant makes 1-30 trades in 8 years. Best looking:
touch retest + trend not down, 9 + 7 trades, PF 3.02 / 0.84 - opposite in the two periods. Reading the
30 trades of the plain variant: no fault separates winners from losers (a candle retest 10 vs 12,
mid-range 8 vs 9, down trend 8 vs 8); only "never got going" (0 vs 10), which is the outcome itself.
By the counted trend: bought in an up trend 14 trades +3.8% a trade, in a down trend 16 trades -0.2%.
Conclusion: with daily BTC and 7% swings the setup happens 2-4 times a year - no rule can be judged.

### Improvement round 2 (2026-10-09) - "does not make sense when the price made hundreds if not thousands of percents moves"
Two causes, measured. The exit: selling at the next line capped every trade (avg risk 9-10% for 4-5%
reward). The entry: at an all-time high there is no line above to break, so the breakout entry was out
of the market all of 2020-10 -> 2021-04 (+493%, 0 of 195 days) - his note: "there is no next
resistance because its all time high". Fixes, from his rules and Dow:
- exit: no target; the stop rides the zigzag's higher lows (an up trend holds while its higher lows
  hold), never down (`trade_simulator.simulate_ladder`, `strategies/trend_entries.last_higher_low`).
  Tried first: the stop on the nearest line under price - +86% but in the market 16% of days.
- entry added: in an up trend by his counted rule, the day the zigzag confirms a new higher low
  (`strategies/trend_entries.higher_low_entries`).

| 2018-06 -> 2026-09 | trades | win | avg | PF | compounded |
|---|---|---|---|---|---|
| breakout -> retest, target the next line (before) | 30 | 47% | +1.7% | 1.31 | +14% |
| breakout -> retest, stop rides the higher lows | 33 | 24% | +4.0% | 1.68 | +85% |
| higher low in an up trend alone | 25 | 28% | +7.6% | 2.85 | +236% |
| both entries (on the page) | 44 | 25% | +5.3% | 1.97 | +249% |
| - 2018-2022 / 2023-2026 | 28 / 16 | 25% / 25% | +5.0% / +5.8% | 1.86 / 2.19 | +93% / +81% |
| buy and hold | | | | | +978% |
First result that holds in both periods. Still in the market only ~40% of days: 2020-10 -> 2021-04 83 of
195 days, 2023 -> 2024-03 246 of 438.

### One answer per question (2026-10-09) - "when you find the line you can see its slope why is there another direction algorithm"
- The trend's direction is the trend LINE's (`zigzag_lines.direction`): an unbroken down line over price -
  down; an up line under it - up; both - narrowing; none - no trend. The counted-rule module
  (`zigzag_trend.py`) and "the last swings" left the cards and the strategy; the higher-low entry now
  needs an unbroken up trend line under price. Backtest: 47 trades, PF 1.83, +185% compounded (2018-2022
  PF 1.54, 2023-2026 PF 2.51) - against +249% with the counted rule; the higher-low entry 20 trades PF 2.69.
- Every line's card, one format (`zigzag_strength.words`): size (a level: its biggest turn, and its share
  of the trend; a trend line: the move it carried) · slope · duration · touches with dates · score (the
  total % price turned at it - the sum of its touches' swings) · age, last touch · distance from price ·
  broken or not. A trend line's touches are every zigzag point on it, not only the two that drew it.
- Clicking a line's end dot shows that line alone, drawn as it is (a trend line keeps its slope), with
  the zigzag dots it is made of on their own prices.

### OPEN: the trend line he draws (2026-10-09, his sketch at 2022-03-04)
"its a huge downtrend that wasnt broken and missing it make you buy in a downtrend and lose trades ...
if it wasnt broken its the trend." His stroke: 2021-11-10 top (69,000) through 2021-12-27 (52,088), at
39,176 on 2022-03-04; the March high 45,400 poked ~15% over it and he still reads it unbroken. Ours that
day: two small lines, both broken in February. Tried against his six drawn trend lines (2022-03-04,
2022-10-14, 2023-08-11, 2025-04-14, 2026-02-13, 2026-09-04), within 2.85%:
consecutive peaks (live) - the 2022 line never drawn; from the extreme through the biggest swing 0/6,
the hull 1/6, the hull over significant peaks 0/6, the first major lower high 0/6 at 40% and 50%; the
old daily move-scale reading 3/6 (two more within 3.5-4.6%), and that reading kept until a log break of
a quarter of the move 1/6. Not kept: none was his. His lines disagree on the second point - 2022 skips the
first lower high (59,177) and tolerates a 15% poke, 2025 runs through the very next peak (106,457) - so
there is a judgement not yet stated. Breaks are measured in log terms (a quarter of a +1,200% up move is
not "300% under the line"). Asked him.

**His answer (same day):** "even the trends you did draw are bad and dont rely on 2 dots ... read the ideas
youll find something. a trend is not over with a close above its with 2 zigzag dots that get higher and
higher. not same height. before that its noise." Built (`zigzag_trend.trend_line`, used by
`zigzag_lines.trend_lines`): the trend is his counted rule, from where it began (its extreme since the
trend before it); its line runs from that first dot over the trend's own zigzag dots - the one that leaves
the fewest dots poking through, then touches the most; it lives as long as the trend; a close beyond it
(by the touch zone) is marked as its breakout, not its end. Direction = the trend's (one source).
Against his lines: 2022-10-14 -1%, 2025-04-14 +1% (his dots 109,588 -> 106,457), 2026-02-13 -2% (126,200
-> 97,924); 2022-03-04 starts at his 69,000 top but runs through the March high he calls noise (+15%);
2023-08-11 and 2026-09-04 the counted trend reads the other way from him. Backtest: 40 trades, PF 1.78,
+143%; the higher-low entry 19 trades PF 3.08 +217%, the breakout -> retest entry 21 trades PF 1.09 -23%.
- Trend line: two lower peaks in a row (higher valleys) draw it; it stays until a close breaks it;
  broken, it stays 20 bars for its retest, then a new one may form from points after the break.
- Built from the zigzag as it stood that day - a test cuts the data at 2025-04-17 and gets the same.
- His 2025-04 example: the down line through 109,588 (01-20) and 106,457 (01-30), drawn 02-02, kept to
  its break on 04-19 (his drawn line crossed 04-17; ours was 85,164 vs his 84,027 that day). His 84k
  level is not a zigzag point at this size, so it is not drawn.
- Stability: the trend line never vanishes (0 times, against 424 before). Shown levels change with
  price (80% next day, 51% a week) because the nearest kept point changes - the points themselves stay.

His strategy on these lines (breakout of a resistance on his screen, buy the retest of THAT line, stop
the rung below, target the next line up): 2018-2022 66 trades, win 70%, -0.7% a trade, PF 0.68;
2023-2026 46 trades, win 87%, +0.9%, PF 2.48 - against PF 0.54 / 0.48 for any day between the same
lines. Wins often, small: the next line above is near, the stop further.

Measured 2026-10-08 on the default switches: 1,030 events 2018-06 -> now (250 breakouts, 193 bounces,
130 retests, 79 fakeouts, 75 sweeps, 112 trend changes, 191 patterns). No lookahead: events computed on
data cut at 2024-06-30 are identical to the full history's up to that day (845 = 845), and a test
breaks when a day is given the next day's lines.

Known: the trend reading flickers (2026-08-19 up, 08-21 down again) because the move's scale changes
day to day - 112 trend changes in 8 years. And his 2026-08-19 confluence breakout (range top + falling
trend line) shows only the range top: our falling line was at 70,938, above that day's close of 69,335.
