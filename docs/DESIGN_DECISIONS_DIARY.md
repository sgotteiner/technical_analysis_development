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
