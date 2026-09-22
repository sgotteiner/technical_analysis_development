"""
Tests that the answer key is TRUE: the saved batches are the right data, and every label
holds on it. If a label is wrong, every classifier graded against it is graded wrong.

Rule per regime + shape (metrics from helpers/regime_metrics.py):
  trend (bull up / bear down), both shapes: moves >= 30% in its direction and ends at its
      extreme (bull: highest High, bear: lowest Low) within the last 5 days
    straight: efficiency >= 0.45, counter-move <= 15%, at most 1 flat step
    stairs:   at least 2 flat steps (21+ days within a 15% band)
  sideways:
    flat:  highest close <= 1.15 x lowest close, and |start->end| <= 5%
    range: band 1.25-1.6x, |start->end| <= 10%, and >= 4 alternating top/bottom touches
"""
import os
import pandas as pd
import pytest
from helpers.regime_metrics import period_metrics
from modules.data.market_regimes import (ACCEPTED_PERIODS, REGIME_PERIODS, LEAD_IN_DAYS, REJECTED,
                                         BULL, BEAR, SIDEWAYS, STRAIGHT, STAIRS, FLAT, RANGE)
from modules.data.regime_batches import BATCH_DIR, RAW_DAILY, load_regime_sets, cut_batch, _read

SETS = load_regime_sets()
IDS = [s.period.name for s in SETS]


def _check_trend(w, m, regime, shape):
    direction = 1 if regime == BULL else -1
    counter = m["max_pullback"] if regime == BULL else m["max_bounce"]
    extreme = w["High"].idxmax() if regime == BULL else w["Low"].idxmin()
    assert direction * m["return"] >= 0.30, f"return {m['return']:+.0%}"
    assert (w.index[-1] - extreme).days <= 5, "period does not end at its extreme"
    if shape == STRAIGHT:
        assert m["efficiency"] >= 0.45, f"efficiency {m['efficiency']:.2f}"
        assert counter <= 0.15, f"counter-move {counter:.0%}"
        assert m["steps"] <= 1, f"{m['steps']} flat steps"
    else:
        assert shape == STAIRS and m["steps"] >= 2, f"{shape}: {m['steps']} flat steps"


def _check_sideways(m, shape):
    if shape == FLAT:
        assert m["band"] <= 1.15, f"band {m['band']:.2f}"
        assert abs(m["return"]) <= 0.05, f"return {m['return']:+.0%}"
    else:
        assert shape == RANGE
        assert 1.25 <= m["band"] <= 1.6, f"band {m['band']:.2f}"
        assert abs(m["return"]) <= 0.10, f"return {m['return']:+.0%}"
        assert m["touches"] >= 4, f"{m['touches']} touches"


@pytest.mark.parametrize("s", SETS, ids=IDS)
def test_label_holds_on_data(s):
    m = period_metrics(s.batch)
    if s.period.regime in (BULL, BEAR):
        _check_trend(s.batch, m, s.period.regime, s.period.shape)
    else:
        assert s.period.regime == SIDEWAYS
        _check_sideways(m, s.period.shape)


@pytest.mark.parametrize("s", SETS, ids=IDS)
def test_saved_batch_has_lead_in_and_exact_bounds(s):
    assert s.history_days == LEAD_IN_DAYS >= 200
    assert s.batch.index[0] == pd.Timestamp(s.period.start, tz="UTC")
    assert s.df_daily.index[-1] == pd.Timestamp(s.period.end, tz="UTC")     # nothing after the batch
    assert s.df_daily.index.is_monotonic_increasing and s.df_daily.index.is_unique
    assert (s.df_daily.index.to_series().diff().dropna() == pd.Timedelta(days=1)).all(), "gap in daily data"


def test_saved_folder_holds_exactly_the_accepted_batches():
    expected = {f"{p.slug}.csv" for p in ACCEPTED_PERIODS}
    assert set(os.listdir(BATCH_DIR)) == expected


def test_rejected_periods_are_not_in_the_key():
    rejected = {p.name for p in REGIME_PERIODS if p.review == REJECTED}
    assert rejected and not rejected & {s.period.name for s in SETS}


@pytest.mark.skipif(not os.path.exists(RAW_DAILY), reason="raw daily data not present")
def test_saved_batches_match_raw_data():
    raw = _read(RAW_DAILY)
    for s in SETS:
        pd.testing.assert_frame_equal(s.df_daily, cut_batch(raw, s.period), check_freq=False)


def test_different_regimes_never_share_a_day():
    owner = {}
    for p in ACCEPTED_PERIODS:
        for day in pd.date_range(p.start, p.end):
            assert owner.setdefault(day, p.regime) == p.regime, f"{day.date()}: {owner[day]} vs {p.regime} ({p.name})"


def test_periods_sorted_by_start():
    starts = [p.start for p in REGIME_PERIODS]
    assert starts == sorted(starts)
