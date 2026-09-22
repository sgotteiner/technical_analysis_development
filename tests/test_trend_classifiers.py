"""
Grades every trend classifier against the saved regime batches (the answer key).
Add a classifier to CLASSIFIERS and it is graded on every batch automatically.

Pass bars (fixed before grading; see business_logic_services/regime_grader.py for metrics),
measured from SETTLE days into each batch:
  bull / bear batch: agreement >= 70% and opposite-trend calls <= 10%
  sideways batch:    agreement >= 50%
Lag and flips are reported in the failure message, not graded (no target set yet).
Every classifier must also be causal (no lookahead) on the batches.
"""
import pytest
from business_logic_services.regime_grader import grade, check_causal
from modules.data.market_regimes import SIDEWAYS
from modules.data.regime_batches import load_regime_sets
from modules.trends.market_structure import MarketStructureBlock
from modules.trends.trend_classifier import TrendClassifierBlock

SETTLE, HOLD = 20, 5
TREND_AGREEMENT, TREND_OPPOSITE, SIDEWAYS_AGREEMENT = 0.70, 0.10, 0.50

CLASSIFIERS = {
    "market_structure_5d": lambda df: MarketStructureBlock("1D", pivot_span=5).evaluate(df, None).metadata["state"],
    "trend_classifier_30d": lambda df: TrendClassifierBlock("1D", n=30).evaluate(df, None).metadata["state"],
}
SETS = load_regime_sets()
CASES = [(name, s) for name in CLASSIFIERS for s in SETS]


def _case_id(case):
    name, s = case
    return f"{name} | {s.period.regime}-{s.period.shape} | {s.period.name}"


@pytest.mark.parametrize("case", CASES, ids=[_case_id(c) for c in CASES])
def test_classifier_reads_labelled_regime(case):
    name, s = case
    r = grade(CLASSIFIERS[name], [s], settle=SETTLE, hold=HOLD)[0]
    detail = (f"agreement {r['agreement']:.0%}, opposite {r['opposite']:.0%}, "
              f"bull/side/bear {r['shares']['bull']:.0%}/{r['shares']['sideways']:.0%}/{r['shares']['bear']:.0%}, "
              f"lag {r['lag_days']}d, flips {r['flips']} in {r['days']}d")
    if s.period.regime == SIDEWAYS:
        assert r["agreement"] >= SIDEWAYS_AGREEMENT, detail
    else:
        assert r["agreement"] >= TREND_AGREEMENT and r["opposite"] <= TREND_OPPOSITE, detail


@pytest.mark.parametrize("name", CLASSIFIERS)
def test_classifier_is_causal_on_every_batch(name):
    for s in SETS:
        bad = check_causal(CLASSIFIERS[name], s.df_daily, start=s.start_daily)
        assert not bad, f"{s.period.name}: live answer differs from backtest on {len(bad)} days"
