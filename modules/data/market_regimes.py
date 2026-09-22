"""
Labelled BTC market regimes — the answer key for trend classifiers.

Each period is a batch of one regime (bull / bear / sideways) and one shape:
  bull, bear:  STRAIGHT (one clean leg) or STAIRS (moves separated by flat steps)
  sideways:    FLAT (tight band) or RANGE (wide band, crossed top-to-bottom repeatedly)
The measurable rule for every regime + shape is in tests/test_market_regimes_data.py.

Every period was also reviewed by eye on the chart (2026-09-21). REJECTED periods pass
the measurable rule but are poor examples; they are kept here with the reason and are
NOT part of the answer key (ACCEPTED_PERIODS).

Rules for the accepted set:
  - Periods of DIFFERENT regimes never share a day (a day has one true label).
    Periods of the SAME regime may overlap.
  - Each accepted batch is saved with LEAD_IN_DAYS of preceding data
    (modules/data/regime_batches.py), so a classifier warms up and must then notice it.
Oct 2025 onward is labelled from the data itself (beyond common market consensus).
"""
from dataclasses import dataclass

BULL, SIDEWAYS, BEAR = "bull", "sideways", "bear"
STRAIGHT, STAIRS, FLAT, RANGE = "straight", "stairs", "flat", "range"
GREAT, OK, REJECTED = "great", "ok", "rejected"
LEAD_IN_DAYS = 365         # saved before every batch; >= 200 so 200-day indicators can warm up


@dataclass(frozen=True)
class RegimePeriod:
    name: str
    regime: str
    shape: str
    start: str
    end: str
    review: str
    note: str = ""

    @property
    def slug(self) -> str:
        return f"{self.start}_{self.regime}_{self.shape}"


REGIME_PERIODS = [
    RegimePeriod("2018 fall flat", SIDEWAYS, FLAT, "2018-09-05", "2018-11-13", REJECTED,
                 "starts with a huge bear candle, then flat but weird"),
    RegimePeriod("2018 Nov capitulation", BEAR, STRAIGHT, "2018-11-14", "2018-12-15", OK),
    RegimePeriod("2020 COVID crash", BEAR, STRAIGHT, "2020-01-28", "2020-03-12", REJECTED,
                 "completely flat except one huge last bear candle"),
    RegimePeriod("2020 post-COVID recovery", BULL, STAIRS, "2020-03-13", "2020-08-17", OK,
                 "nice bull but most of it is very flat"),
    RegimePeriod("2020 Q4 breakout", BULL, STRAIGHT, "2020-10-01", "2021-01-08", GREAT,
                 "nice straight bull"),
    RegimePeriod("2021 spring top range", SIDEWAYS, RANGE, "2021-03-06", "2021-05-14", OK,
                 "touches support/resistance about 1.5 times - close but not quite"),
    RegimePeriod("2021 bull, second leg", BULL, STAIRS, "2021-07-20", "2021-11-10", OK,
                 "bull stairs but not many stairs"),
    RegimePeriod("2022 bear (Luna, FTX)", BEAR, STAIRS, "2021-11-11", "2022-11-21", GREAT,
                 "very nice bear stairs"),
    RegimePeriod("2022 January slide", BEAR, STRAIGHT, "2021-12-24", "2022-01-22", REJECTED,
                 "very short"),
    RegimePeriod("2023 spring flat", SIDEWAYS, FLAT, "2023-03-17", "2023-05-20", GREAT,
                 "beautiful flat sideways"),
    RegimePeriod("2023-24 ETF bull", BULL, STAIRS, "2023-10-15", "2024-03-14", REJECTED,
                 "only one stair"),
    RegimePeriod("2024 consolidation range", SIDEWAYS, RANGE, "2024-03-15", "2024-10-15", GREAT,
                 "beautiful sideways range"),
    RegimePeriod("2024 post-election run", BULL, STRAIGHT, "2024-11-05", "2024-12-17", REJECTED,
                 "short and didn't go up much"),
    RegimePeriod("2025 winter flat", SIDEWAYS, FLAT, "2024-12-18", "2025-02-23", GREAT,
                 "beautiful flat sideways"),
    RegimePeriod("2025 bull to the Oct top", BULL, STAIRS, "2025-04-07", "2025-10-06", GREAT,
                 "nice bull stairs, although very long"),
    RegimePeriod("2025-26 bear", BEAR, STAIRS, "2025-10-07", "2026-07-01", GREAT,
                 "nice bear stairs"),
    RegimePeriod("2026 summer flat", SIDEWAYS, FLAT, "2026-07-02", "2026-08-17", GREAT,
                 "nice flat"),
]

ACCEPTED_PERIODS = [p for p in REGIME_PERIODS if p.review != REJECTED]
