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
