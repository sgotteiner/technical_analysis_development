# Design Decisions Diary — algo-trading (trading_projects)

Append-only WHY-log of the owner's design. The WHAT lives in the code; this file keeps
*why* it is that way. Never edit or delete an entry — only append. Claude's own decisions
and known debt live in [DIARY_FLAGS.md](DIARY_FLAGS.md), never here.

Sources: git (be1f59c, 8906f42), Click Click Claude session `9cb15704` (2026-09-20),
Claude Code session `2c206b2f` (2026-09-21). Session times are UTC. Work after 8906f42 is
not committed yet, so later anchors are `uncommitted`.

---

## F0 — Foundations (built in Antigravity)

### Strategies are composed from categorized blocks
tags: kind=decision · attribution=your-design · portable=yes · signature=no · importance=high
anchor: 2026-09-13 · be1f59c · 9cb15704 @ 11:52Z
**Idea:** Strategies are built from small reusable blocks in four categories — trend, shape, candlestick, indicator — each evaluated on its own timeframe, and kept as separate modules so a single tool (e.g. the S/R lines) can be improved on its own.
**Why:** The owner confirmed this was "the whole design from the start" when Claude called the unused block lists vaporware. Separation is so specific tools can be updated easily (9cb15704 @ 15:33Z). The block layer also carries the chart drawings that make a trade explainable.
**Links:** [[Honest measurement is infrastructure]], [[Minimal, trusted, separated tools]]

### Train on one halving cycle, test on the next, always against Buy & Hold
tags: kind=decision · attribution=your-design · portable=yes · signature=no · importance=high
anchor: 2026-09-13 · be1f59c · —
**Idea:** Data is split chronologically by BTC halving cycle (Cycle 1 develop, Cycle 2 out-of-sample), and every result is scored as alpha against simply holding BTC over the same cycle.
**Why:** (inferred) A chronological, cycle-sized split avoids leaking the future into development. Buy & Hold is the null model a strategy has to beat to be worth running.

### Measure the median trade, not just the mean
tags: kind=decision · attribution=your-design · portable=yes · signature=no · importance=normal
anchor: 2026-09-20 · 8906f42 · 9cb15704 @ 11:08Z
**Idea:** The return distribution reports the median (plus 33rd/66th percentiles) next to the mean.
**Why:** (inferred) The owner pointed it out as something to look at. It later exposed that the typical trade loses while a few outliers carry the mean.

---

## F1 — Honest multi-timeframe infrastructure (2026-09-20)

### Honest measurement is infrastructure, not a per-strategy fix
tags: kind=principle · attribution=your-correction · portable=yes · signature=no · importance=high
anchor: 2026-09-20 · uncommitted · 9cb15704 @ 11:22Z, 11:32Z
**Idea:** A lookahead bug found in one strategy is fixed once, in the shared infrastructure, so no strategy can reintroduce it.
**Why:** The owner asked whether only the strategy or the infrastructure had been fixed, then said he wants infrastructure "so i do it once and from now on i wont 'miss' it". (inferred) A per-strategy fix leaves every future strategy free to repeat the bug.
**Links:** [[Each timeframe signals on its own; one component connects them]]

### Each timeframe signals on its own; one component connects them
tags: kind=decision · attribution=your-design · portable=yes · signature=yes · importance=high
anchor: 2026-09-20 · uncommitted · 9cb15704 @ 11:37Z
**Idea:** For any multi-timeframe strategy and any timeframe pair, each timeframe produces its signal separately, and a single shared component connects those signals onto the trading timeframe correctly. That means a bar only sees higher-timeframe bars that have already closed.
**Why:** This is the owner's model of the problem ("at the end of the day you get signals from each timerange separately… then connect the signals correctly"). (inferred) It turns "no lookahead" from something every strategy must remember into one property of one component. It generalises beyond the daily→1H case that surfaced the bug.

### Parked: fees and slippage
tags: kind=decision · attribution=your-design · portable=no · signature=no · importance=normal
anchor: 2026-09-20 · — · 9cb15704 @ 12:04Z
**Idea:** Trading costs are deliberately left out of the engine for now. Work focuses on the strategy logic.
**Why:** Priority: "lets focus on the algorithm hold on with the fees and slippage". Results are therefore read as relative, not as real P&L.

---

## F2 — Purpose and scope (2026-09-20)

### The goal: good tools and a strategy that makes money and lets you sleep at night
tags: kind=principle · attribution=your-design · portable=yes · signature=yes · importance=high
anchor: 2026-09-20 · — · 9cb15704 @ 12:10Z, 14:03Z
**Idea:** Judge the system in a trader's mindset: profitable, reliable, traceable, manageable, "my goal is to use it one day". The target is not the perfect strategy.
**Why:** In his words: "i dont need the perfect strategy i need one that will make money and i could sleep at night." Risk (drawdown) is a first-class objective next to profit.

### What the system is for: measure, explain, improve — later in a self-correction loop
tags: kind=feature-motivation · attribution=your-design · portable=yes · signature=yes · importance=high
anchor: 2026-09-20 · — · 9cb15704 @ 13:33Z, 14:03Z
**Idea:** The product is the ability to measure strategies, analyze them and improve them, repeated until one is good. The owner weighs profitability, risk, trade duration, eventually portfolio management, and explainability: knowing what was good and bad in a strategy and how to improve it. Shapes are displayed on the chart for that reason. Once the infrastructure is ready it will run in a self-correction loop with AI, possibly an LLM brain or an ML/DL model.
**Why:** The owner framed it as "the real mindset… its a self correction loop infrastructure". Traceability comes first ("right now i want to see if i can trace a strategy"); (inferred) a loop, or a model, can only improve what it can read.

### Exits are signals too, not only TP/SL/expiry
tags: kind=idea · attribution=your-design · portable=yes · signature=no · importance=normal
anchor: 2026-09-20 · — · 9cb15704 @ 14:42Z
**Idea:** Unlike Cryptron (where the entry is given and exits are price levels), here both entry and exit are strategy signals.
**Why:** It is the structural difference the owner pointed out between the two projects. (inferred) It means exits carry the same lookahead and attribution concerns as entries.

### The tuning space is not one space
tags: kind=idea · attribution=your-design · portable=yes · signature=no · importance=normal
anchor: 2026-09-20 · — · 9cb15704 @ 14:14Z
**Idea:** "What am I tuning?" has different kinds of answers: a single indicator parameter, a timeframe, a trade-management rule, or adding a new indicator or pattern. Each comes with its own parameters and timeframes.
**Why:** The owner raised it as the core difficulty of improving strategies (the input space is huge). (inferred) Any improvement loop has to handle these kinds of change differently.

### Smaller than Cryptron, on purpose
tags: kind=decision · attribution=your-design · portable=no · signature=no · importance=high
anchor: 2026-09-20 · — · 9cb15704 @ 15:10Z, 15:13Z
**Idea:** This project exists to run algo-trading experiments without Cryptron's overkill. It is "not tiny", but it must not grow as big as Cryptron, even though the problem is bigger.
**Why:** Cryptron's loop is well designed but "a huge thing"; the owner wanted something simpler to experiment with. He also said it wasn't *only* about wanting algo trading. The fuller reason was not stated (open question).

### Claude is the improver for now; Cryptron was shown for the mindset, not the machinery
tags: kind=decision · attribution=your-design · portable=yes · signature=no · importance=high
anchor: 2026-09-20 · — · 9cb15704 @ 15:18Z
**Idea:** Once the infrastructure measures reliably, the owner will say "run, measure and improve based on what you think". Claude plays the improver inside the loop, instead of an automated loop being built now.
**Why:** He showed Cryptron "not because i want such a correction loop but because i wanted to show you my mindset and how i evaluate things". The evaluation standards transfer; the machinery does not.

### Minimal, trusted, separated tools — test and explain before improving
tags: kind=decision · attribution=your-design · portable=yes · signature=no · importance=high
anchor: 2026-09-20 · — · 9cb15704 @ 15:33Z
**Idea:** Make the tools good; don't use a tool you don't trust yet. Start minimal, make sure it can be tested and explained, do it for one strategy, and show an improvement.
**Why:** Tools are separated so each can be fixed on its own (e.g. the S/R lines). (inferred) An untrusted tool poisons both the result and its explanation. The owner also corrected a rule Claude had attributed to him ("a weak result is usually the wrong exit"): that was Cryptron's rule, not his, and it doesn't carry over here.

---

## F3 — Regime answer key and trend-classifier testing (2026-09-21)

### Reliability first — test it well
tags: kind=principle · attribution=your-design · portable=yes · signature=no · importance=high
anchor: 2026-09-21 · uncommitted · 2c206b2f @ 17:39Z, 17:41Z
**Idea:** A bull/bear/sideways tool was wanted as a strategy filter. Before anything else it must be reliable (no lookahead) and well tested.
**Why:** "you know whats important to me. reliability. test it well." (inferred) A regime filter that peeks makes every strategy using it look better than it can be live.

### Test classifiers on real labelled batches, with the data they need before them
tags: kind=decision · attribution=your-design · portable=yes · signature=yes · importance=high
anchor: 2026-09-21 · uncommitted · 2c206b2f @ 18:43Z, 18:45Z, 19:29Z
**Idea:** Take specific batches from the real data that show what the classifier should detect, include enough candles before each batch for the algorithm to warm up, and use them in unit tests. The algorithm runs on the preceding data and must then notice the batch.
**Why:** The owner asked whether hand-picked date ranges were really how the classifier had been checked; they weren't a real test. (inferred) A batch without its preceding data can't be classified at all, and grading "not ready yet" as a regime is a false result. ("we also need to save the data before this batch so we could run the algorithm and notice the batch")

### Ground truth from known market history
tags: kind=decision · attribution=your-design · portable=yes · signature=no · importance=normal
anchor: 2026-09-21 · uncommitted · 2c206b2f @ 18:51Z
**Idea:** Label the batches from market regimes that are commonly known ("we all know 2008 was bear"), not from a statistic that Claude picks.
**Why:** (inferred) Labels chosen by a formula can be tuned to agree with the classifier. Commonly known regimes are an independent answer key.

### Verify the answer key itself
tags: kind=principle · attribution=your-design · portable=yes · signature=yes · importance=high
anchor: 2026-09-21 · uncommitted · 2c206b2f @ 18:54Z
**Idea:** Put the right sets in the data containers and test that each label is actually true on the data, before grading anything against it.
**Why:** "if your expected results are not true we got nothing." (inferred) A wrong answer key silently grades every classifier wrong.

### Define a clear, measurable goal before writing the code
tags: kind=principle · attribution=your-design · portable=yes · signature=yes · importance=high
anchor: 2026-09-21 · uncommitted · 2c206b2f @ 19:05Z
**Idea:** Before building the classifier, understand the batches quantitatively: how strongly bull, how far it moved, how long, how spiky, and how each of these is measured. Then define what is being looked for as a measurable goal.
**Why:** "i want to understand what im trying to find and define a clear measurable goal before writing the code." (inferred) Without a measured target, a classifier can't be said to succeed or fail.

#### Mini-feature: the regime viewer (visibility)
### See each batch, with its label and measurements, one at a time
tags: kind=mini-feature · attribution=your-design · portable=yes · signature=no · importance=normal
anchor: 2026-09-21 · uncommitted · 2c206b2f @ 18:57Z, 19:11Z, 19:16Z
**Idea:** Show the labelled batches on the chart with their labels and metrics, and step through them one by one, the same way trades are browsed.
**Why:** The owner judges examples by eye, and all batches on screen at once was "hard to see". Stepping one at a time mirrors how he reviews trades.

### Shapes of regimes: straight and stairs trends, flat and range sideways
tags: kind=decision · attribution=your-design · portable=yes · signature=yes · importance=high
anchor: 2026-09-21 · uncommitted · 2c206b2f @ 19:29Z
**Idea:** The answer key covers straight and stairs bulls, straight and stairs bears, and flat and range sideways markets, with several examples per type allowed.
**Why:** (inferred) A classifier must be tested on the different shapes a regime takes, not only on clean moves. Stated: the owner liked the wide consolidation range but wanted a flat sideways example as well, because they are different things to detect.

### The owner's eye is the final gate on examples
tags: kind=decision · attribution=your-design · portable=yes · signature=no · importance=high
anchor: 2026-09-21 · uncommitted · 2c206b2f @ 19:50Z
**Idea:** Every candidate batch is reviewed on the chart. Great and OK examples form the answer key; poor ones are rejected with the reason recorded (too short, one big candle, only one stair, a weird start). Unequal numbers per type and uneven lengths are acceptable. The accepted batches are saved in the right place, and trend-finding unit tests are built on them.
**Why:** Measurable rules alone accepted examples a trader would not accept (e.g. "completely flat except a huge last bear candle" passed as a straight bear). (inferred) The owner's judgement of what a real example looks like is the standard the rules must eventually meet. "its a start. we can test a trend classifier tool based on that."

---

## F4 — A better trend classifier, and using it in a strategy (2026-09-21)

### A classifier built from sub-parts
tags: kind=decision · attribution=your-design · portable=yes · signature=no · importance=normal
anchor: 2026-09-21 · uncommitted · 2c206b2f @ 20:14Z
**Idea:** Build the trend classifier from separate parts that each look at the market differently (for example the last 10 candles, the last 20, or indicators), and improve it using the tests.
**Why:** The single swing-based block failed most batches. (inferred) Separate parts can each be checked and explained.

### Judge a filter by the trades it removes; "sideways after a bear" as entry context
tags: kind=idea · attribution=your-design · portable=yes · signature=no · importance=normal
anchor: 2026-09-21 · — · 2c206b2f @ 20:41Z, 20:42Z
**Idea:** Add the classifier to the best strategy as "buy only in bull", and judge it by whether it filtered out bad trades. Then try buying only when the market was bear and then turned sideways.
**Why:** A filter's value is which trades it removes. (Result: "only bull" removed the best trades; "sideways after bear" held the best-quality trades in both cycles; see flags.)

## F5 — Geometry: S/R lines and pipes (2026-09-21 / 22)

### Geometry is the core; indicators only help
tags: kind=principle · attribution=your-design · portable=yes · signature=yes · importance=high
anchor: 2026-09-21 · — · 2c206b2f @ 20:51Z
**Idea:** The most important thing in technical analysis is S/R lines (horizontal or diagonal), the pipes they create, and the breakout patterns out of those pipes, including candle patterns, tests and fakeouts. Indicators can help, but the geometry matters more. It is also harder to put into code.
**Why:** The owner's view of what actually drives trades.

### Tests before development, for every block
tags: kind=principle · attribution=your-design · portable=yes · signature=yes · importance=high
anchor: 2026-09-21 · — · 2c206b2f @ 20:53Z
**Idea:** Every block gets tests before it is developed further.
**Why:** "the most important thing is reliability and there is only one way to get it. tests… without them we cant start because we wouldnt know if we succeeded."

### Ground truth is the real problem, and errors cascade
tags: kind=principle · attribution=your-design · portable=yes · signature=no · importance=high
anchor: 2026-09-21 · — · 2c206b2f @ 20:56Z, 20:58Z, 20:59Z
**Idea:** Retests and fakeouts depend on the trendlines, so an imperfect line breaks everything built on it. Lines differ with zoom and timeframe, and a trader looks only at the important ones. The real problem is getting ground truth for the blocks.
**Why:** Stated by the owner. It led to testing each layer on its own and to the annotator idea.

### Four lines: two levels × support and resistance; a line is just a line
tags: kind=decision · attribution=your-design · portable=yes · signature=yes · importance=high
anchor: 2026-09-21 · — · 2c206b2f @ 21:02Z, 21:04Z; 2026-09-22 @ 08:10Z
**Idea:** A higher and a lower level, each with one support and one resistance line: 4 lines in total. Straight or diagonal doesn't matter ("straight is a type of diagonal"). Tests compare a tool's line with the expected one by slope difference and position. Periods: 400 and 100 days.
**Why:** The owner looks at two sets of important lines, not all lines.

### Pipes: no widening, not too wide, not too narrow; channels and triangles
tags: kind=decision · attribution=your-design · portable=yes · signature=yes · importance=high
anchor: 2026-09-22 · uncommitted · 2c206b2f @ 08:15Z, 08:24Z, 10:20Z, 10:41Z, 10:54Z
**Idea:** A support/resistance pair that opens apart is useless. A pipe wider than any swing move is useless, because pipes are for tracking swing moves. Really narrow pipes are useless too. A nice pipe has a range inside it, or is a triangle.
**Why:** "i cant see a breakout there" (widening); "pipes should help me track swing moves" (too wide).

### Nesting the two levels — tried, then dropped
tags: kind=decision · attribution=your-correction · portable=no · signature=no · importance=normal
anchor: 2026-09-22 · uncommitted · 2c206b2f @ 10:06Z, 10:11Z, 10:29Z, 10:31Z
**Idea:** The levels are found independently.
**Replaces:** "The two pairs have to be related… nested… work together." It was dropped after the owner saw that a perfect big pipe that has just broken out makes the right small pipe lie outside it: "dont make them nested and stuff like that just find the right sr."

### Peaks and valleys by magnitude; a line shows the trend
tags: kind=decision · attribution=your-design · portable=yes · signature=yes · importance=high
anchor: 2026-09-22 · uncommitted · 2c206b2f @ 07:47Z, 10:41Z, 11:24Z, 11:27Z, 11:32Z
**Idea:** A peak is at least a 10% move up and then down (a valley is the opposite). S/R lines run through, or close to, the most peaks and valleys, and don't need to cover the whole window. A single line can touch both peaks and valleys and split the graph. Magnitude is measured against the line, because a rotated pipe would otherwise count differently. A small overshoot must not move the line.
**Why:** "it should show me the trend not tap it on the back and miss most of it or become really wide to not touch it."
**Replaces:** Lines as boundaries that may not be crossed, with swings found by bar windows. Those pushed lines to the edges and made them stale or too wide.

### An annotator / playground for shapes and S/R
tags: kind=idea · attribution=your-design · portable=yes · signature=no · importance=high
anchor: 2026-09-21 · — · 2c206b2f @ 20:25Z, 20:39Z; 2026-09-22 @ 12:40Z
**Idea:** A tool to draw a box around a pattern and label it (flags, S/R and more), to draw lines, to change the settings and see the result, and to show more than two pairs or single lines. It is for improving the shape blocks.
**Why:** Ground truth for geometry has to come from the owner's eye, and experimenting with settings needs a fast visual loop.

### Buy the breakout of a strong resistance, backed by a bullish pattern (maybe after a retest)
tags: kind=idea · attribution=your-design · portable=yes · signature=yes · importance=high
anchor: 2026-09-22 · uncommitted · 54140a1d (playground session, after 14:41Z)
**Idea:** Buy when price breaks a resistance line, possibly waiting for a retest of the line. The setup is stronger when the resistance stopped price the last time it got there and a bullish pattern leads into the breakout. The owner's live example, drawn in the playground as ground truth: a flat resistance at ~$82k (2026-01-09 to 2026-09-03) and a bull flag (2026-08-15 to 2026-09-04) that runs into it.
**Why:** "based on this strong resistance that stopped it the previous time it reached there and the bullish pattern." (Measured, not the owner's words: the previous stop was the 2026-05-06 peak at $82,850, followed by a 30% fall to $57,800 on 2026-07-01.)

### Three stages: setups as ground truth -> code that finds them -> strategies that trade them
tags: kind=principle · attribution=your-design · portable=yes · signature=yes · importance=high
anchor: 2026-09-22 · uncommitted · 54140a1d (playground session)
**Idea:** Strategy development continues, but now built on ground truth. (1) Ground truth: setups, i.e. groups of drawings (S/R lines, pattern boxes, retest / fakeout boxes) with a note on how to trade them, shown by the owner or proposed by Claude. (2) Code that finds the same setups reliably without anyone drawing, in many more places. (3) Strategies that use the found setups, backtested for profit. The stages are coupled: finding a setup in more places needs code, and its profit can only be measured once it is found in more places. The owner does not want to write the rules himself; the tools should find the lines and patterns, with an understanding of how to trade them.
**Why:** "backtesting random lines doesnt help me." Patterns are "the most important thing… more important than indicators", and they were left out so far only because the blocks couldn't find them: "i would prefer not using patterns because its hard to do but its too important so we have to stop and fix that." The owner calls himself "not even a decent trader", so his setups are ideas to test, and profit decides. That he could draw a setup, and Claude could then see it, shows it can be found.

### Start with S/R pairs (pipes and triangles); lines should find their own span
tags: kind=decision · attribution=your-design · portable=yes · signature=no · importance=high
anchor: 2026-09-22 · uncommitted · 54140a1d (after the first setup detector)
**Idea:** The owner annotates more ground truth, starting "as simple as possible" with support / resistance pairs: pipes and triangles. Higher timeframes are more fundamental and patterns belong to shorter ones, but higher timeframes "definitely have support and resistance lines", so drawing them well automatically is already worth a lot. What he liked in the first detector: it found the resistance over what looked like a dynamic number of candles, not a fixed window. "In the general version we will need something like that", and more examples should force the code there.
**Why:** The first detector's results didn't look good, and one example can't define a detector. More ground truth is needed, and S/R pairs are the simplest start.

### The whole of technical analysis: S/R lines, then breakouts, retests and fakeouts
tags: kind=principle · attribution=your-design · portable=yes · signature=yes · importance=high
anchor: 2026-09-23 · uncommitted · 54140a1d (after the owner drew 7 lines and boxes)
**Idea:** "Thats the basics of technical analysis." S/R lines are the basis; on top of them come breakouts and maybe retests and fakeouts. A flag is a breakout pattern, a cup is a retest pattern, and candlestick patterns belong to the same events. Everything else is timing. The lines also mark the goals of a move: the owner labelled his levels "current resistance", "next resistance", "next next resistance". From one setup you can see that price is either breaking out or coming back to the support.
**Why:** The owner's analysis of the current BTC chart, drawn in the playground: support ~56.9k, a broken diagonal from the all-time high, and a ladder of horizontal levels at ~80.3k, ~106.1k and ~124.9k, plus boxes for the breakout of the previous resistance and the test of the current one.

### A setup has a dynamic number of lines; two pairs is not enough
tags: kind=decision · attribution=your-correction · portable=yes · signature=yes · importance=high
anchor: 2026-09-23 · uncommitted · 54140a1d
**Idea:** A setup is one picture "from I don't know when until now" that holds as many relevant lines as the chart has — here 7, some horizontal, some diagonal; another setup has a different number. The algorithm has to find all the relevant ones. Price is not always at a level, and what is relevant depends on the timeframe. "Limiting it to 2 pairs of sr lines is not enough for a setup analysis."
**Replaces:** The 4-line design (2 levels x support + resistance) as the picture of a chart. The magnitude-based line definition stays; what changes is that the number of lines, and how far back each one reaches, come from the chart, not from settings.

### Levels are zones: cluster by percentage, judge by the moves' time
tags: kind=decision · attribution=your-design · portable=yes · signature=yes · importance=high
anchor: 2026-09-24 · 6ce3874 · 54140a1d
**Idea:** Near-identical lines are noise and must be cleaned: 57.8k and 59.1k are one support zone, and 64.2k / 67.3k / 70k are one congestion area ("i like the 58, 67, dont like 59, 64, 69"). Clustering is the way, and it is "tricky because its also relative to the period length but you can count on the same metric of percentage to see similar moves and measure the moves time": the band comes from the swing size in percent (scale-free), and the strength of a zone comes from its visits over time, not from a raw touch count.
**Why:** Three lines through one congestion area say nothing more than one line does, and the count of touches rewards clumps of wiggles.

### Always answer from the current price: what is my support, my resistance, what is next
tags: kind=decision · attribution=your-design · portable=yes · signature=yes · importance=high
anchor: 2026-09-24 · 6ce3874 · 54140a1d
**Idea:** "You should always think about the current price. You should think what is my current support and resistance and if it on a line it can be both and whats the next ones." Price is not always at a level — sometimes it is between two — but the answer is always framed from where price is now. When price sits ON a level, the label comes from the direction it arrived from: **came up to it = resistance, came down to it = support**.
**Why:** The 80.3k level, the most important line on the chart and the one price is standing on, was missed because the search only anchored on recent swing points. The trader's question is never "list all lines", it is "what is above me and what is below me".

### What he likes and dislikes about a drawn result is ground truth too
tags: kind=principle · attribution=your-design · portable=yes · signature=yes · importance=high
anchor: 2026-09-24 · uncommitted · 54140a1d
**Idea:** "I like the 58, 67, dont like 59, 64, 69" and "there are 3 trend lines again" are as much ground truth as the lines he draws. A rule change is judged on both: does it find the lines he drew, and does it avoid the ones he rejected. Tuning by eye without checking those is not allowed - "do you even listen to me and look at my ground truth?", and "we said you need to check yourself before handing it back to me".
**Why:** Claude twice reported a result as good after checking it only against the drawn lines, while it still contained a line the owner had explicitly rejected and had dropped one he had explicitly kept.

### Wrong-side and stale lines are noise; a touch is a visit everywhere
tags: kind=decision · attribution=your-design · portable=yes · signature=yes · importance=high
anchor: 2026-09-24 · uncommitted · 54140a1d
**Idea:** An up-trend line drawn above the graph, or a down-trend below it, is noise. A trend line must still be touched now, but may start as far back as the trend goes. And the visits rule is general, not only for levels: two touches on neighbouring bars are one touch for a trend line as well.
**Why:** The rejected up-trend line claimed three touches - 2020-03-13, 2026-06-05 and 2026-06-06 - two of them on consecutive days, anchored on the COVID low six years back.

## F6 — The lines are a trading plan (2026-10-03)
Why this feature at all: the line layer was being judged by how many of the owner's drawn prices it
hit. He stopped that: the lines are a trade, and the mission was never a fit to his drawings.

### The mission is a generic algorithm, not a fit to my drawings
tags: kind=principle · attribution=your-correction · portable=yes · signature=yes · importance=high
anchor: 2026-10-03 · (chat, no commit)
**Idea:** The drawn lines and the description of how they were found are SOURCE MATERIAL for
deriving a general rule - not a test set to score against, and not a reason to wait for more
drawings. "i drew lines and described how i found them as best as i could with some suggestions for
you to try things. your mission was to find the generic algorithm for sr lines."
**Why:** Claude had inverted it: it scored hit-counts against the 9 drawings, called the owner the
bottleneck for more of them, and reported "5 of 7 found" as success. Measured consequence of the
inversion: the approved preset is 7 hand-set constants fitted to one chart on one date, two of
which replace things the owner had specified as DERIVED (swing size from the trade horizon, band
from the swing size). Run as he stated it, his own rule scores 3/7, not 5/7, and returns 0 lines at
2022-09-05.
**Links:** [[What he likes and dislikes about a drawn result is ground truth too]]

### The lines are a trading plan, so the score is R and rungs - not price hits
tags: kind=principle · attribution=your-correction · portable=yes · signature=yes · importance=high
anchor: 2026-10-03 · (chat, no commit)
**Idea:** The labels are roles in a trade, not names: "current resistance" is what you buy the break
of, "next / next next" are where you take profit in order, the supports are where price goes if it
fails, and a broken "previous resistance" is support beneath you. A line 3% off is not 3% wrong - it
moves the stop, changes R, and a missing line is a missing rung. "do you even have trading plan in
mind while working?"
**Why:** Read as the plan, the same 2026-09-04 chart gives two different trades from "5 of 7 lines
found": his drawn lines -> stop 66,659, risk 17.0%, 1.90 R to 106k; the code's lines -> stop 72,799,
risk 8.4%, 4.40 R. And 124,850, found at no setting at all, is the rung that takes the trade from
1.90 R to 3.27 R. No hit-count can see any of that.
**Links:** [[Always answer from the current price: what is my support, my resistance, what is next]]

### The stop is the previous support - the rung below the one price is standing on
tags: kind=decision · attribution=your-design · portable=yes · signature=no · importance=high
anchor: 2026-10-03 · (chat, no commit)
**Idea:** The invalidation needs no new line type and no new setting: it is the next rung DOWN in the
ladder from the level price is standing on. "the previous support obviously its not rocket science."
It falls straight out of the ladder already specified - the one you are on, the next up, the next
down - which turns that ladder from a list of prices into a complete trade.
**Why:** Claude asked which of the seven drawn lines was the stop, having assumed the nearest DRAWN
one (66,659). The answer made the assumption wrong: 72,799 is also real support, so the rung below
79,500 is 72,799 and the risk is 8.4%, not 17.0%. Corollary he confirmed: a broken resistance is
support by the flip rule, without needing to be retested from above first - Claude's "nothing
bounced there" test was its own invention.
**Links:** [[Flip]] · [[Levels are zones: cluster by percentage, judge by the moves' time]]

## F7 — How he finds a line: the backward search (2026-10-03)

### A line is worth the size of the move that ran into it
tags: kind=decision · attribution=your-design · portable=yes · signature=yes · importance=high
anchor: 2026-10-03 · (chat, no commit)
**Idea:** A touch is not worth its own wiggle; it is worth the leg that arrived at it. "previous 80k
resistance after about 25% move like the current move that is now on this resistance. important line
because its the same move and same resistance." The leg still running counts unfinished - the trade
IS the unfinished part.
**Why:** Measured on his own sketch: the May 2026 peak ran 65,000 -> 82,850 (+27.5%) and the leg
running now ran 64,166 -> 82,300 (+28.3%), off two valleys 1.3% apart. The two statements he made
("about 25%" and "about 30%") are the same number, and they only agree at the 9% swing size he
picked himself.
**Links:** [[Levels are zones: cluster by percentage, judge by the moves' time]]

### Not age, not the era it happened in: walk back and stop at the match
tags: kind=decision · attribution=your-correction · portable=yes · signature=yes · importance=high
anchor: 2026-10-03 · (chat, no commit)
**Idea:** "you have a peak at a certain level and size you look it in the past. thats it ... 30 here
30 then. or whatever you can find in that level. you found something similar like i did and
described you stop. you dont check the entire history." A backward search with an early exit: from
the current state, walk back through the times price was at this level and stop at the first whose
move is a comparable size. No window, no day limit - "because you try to predict the future based on
the past so you have to find relations. not limit to less days."
**Why:** Measured: on his chart the level price is working now matches 2026-05-06 after reading ONE
point of 723; every level in play together reads 11 (2% of the history). It never reaches 2020 - not
by a filter, by stopping.
**Replaces:** Two mechanisms Claude invented and he rejected. (1) An age term, `age_scale`, read out
of "the earlier it is the bigger the move it has to relate to" - "its not about age ... i didnt
mention age. only relative terms." (2) Normalising each move by the swing scale of its own era -
"nothing for then. you dont compare with previous era. 30 here 30 then."

### A level is a cluster of good dots, never a single one
tags: kind=decision · attribution=your-correction · portable=yes · signature=no · importance=high
anchor: 2026-10-03 · (chat, no commit)
**Idea:** "you need the nearest good dot not just any dot and maybe even cluster of dots and not just
a single one because its too sensitive." Walking out from price, a level is the nearest CLUSTER that
is worth something - a single turning point is a dot, not a level.
**Why:** The supports in the first setup roster were the nearest raw swing point below price, which
produced levels nobody would draw (76,606 - one minor swing). He rejected the whole roster except
the one line that came from the search: "i dont like any of your lines maybe except for the current
resistance."

### A setup is a short roster where every line says what it is and how it was found
tags: kind=decision · attribution=your-design · portable=yes · signature=yes · importance=high
anchor: 2026-10-03 · (chat, no commit)
**Idea:** The answer to one question, asked from where price is now, never a list of prices. The move
running now is the yardstick. Five to seven lines - the trend, current support and resistance, the
next ones, "maybe a bit more not a lot more" - and each says **what it is** (its role in the trade)
and **how it was found**. Plus the trade that falls out: buy the break, the stop is the rung below,
the targets are the rungs above in order, with R. Plus the state the structure is in.
**Why:** "i explained to you what i did and i expect to get the same explanation." Confirmed in his
words when read back ("thats correct"). Written up in `docs/GEOMETRY_DEFINITIONS.md`.
**Links:** [[Always answer from the current price: what is my support, my resistance, what is next]]

### Tools to explain with, not only to annotate with
tags: kind=decision · attribution=your-design · portable=yes · signature=yes · importance=high
anchor: 2026-10-03 · cd5ab85 · (chat)
**Idea:** The annotator was for drawing ground truth. This is the other half: tools for him to say
WHY and HOW, and to see what the code did. Asked for one at a time through the session - a note on
every verdict and a drawing to put in its place; freehand sketching ("i want to be able to explain
to you better"), several strokes under one note and his choice whether to keep them; peaks and
valleys as boxes ("i need to see what you do"); an explanation of each line saying what it is and
how it was found ("i explained to you what i did and i expect to get the same explanation"); one
line at a time ("i want to be able to click a line in the setup and see only whats related to it");
and the sidebar as cards.
**Why:** Not scaffolding - it is where the design came from. Six of the corrections that changed the
algorithm this session arrived through a tool built in the same session: the note box on the 67 line
gave "the earlier it is the bigger the move it has to relate to" and "its a weak short term
support"; the sketch gave the May 2026 80k peak and the structural read behind it, which pinned
"same move and same resistance"; the boxes made "why up to 2018?" visible; clicking one line exposed
that the sidebar was a second, rival level-finder. His own summary of the session names them first:
"i have good infrastructure to see it and anotate and communicate about it with you."
**Links:** [[An annotator / playground for shapes and S/R]] · [[Ground truth is the real problem, and errors cascade]]
