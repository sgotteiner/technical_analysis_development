"""
S/R pipes — each level's lower and upper line (modules/shapes/sr_lines.py) chosen TOGETHER.

Owner rules:
  (2026-09-21) two levels — higher (long period, big swings) and lower (short period, small
               swings) — each with a support (lower) and a resistance (upper) line: 4 lines.
  (2026-09-22) peaks / valleys by magnitude (10%; the higher level's 20% is Claude's default).
  (2026-09-22) not a widening shape, not too wide, not really narrow; a nice channel with a
               range inside or a triangle is what a pipe should be.
  (2026-09-22) the levels are found independently (no nesting).

The pipe is the (lower, upper) pair with the most significant touches in total such that
  together   both lines act at the same time: their touch periods overlap
  shape      upper slope <= lower slope (parallel or narrowing, never widening)
  width      median swing <= width <= largest swing, measured where both lines start (the widest
             point of a non-widening pipe); upper bound strict (owner), lower bound Claude's
  at now     at `end` the pipe is still open (lower below upper) and not wider than the largest
             swing — a triangle past its apex opens up the other way
Ties: the better lower line, then the better upper line. Exact over all pairs (vectorised).
Every bound above is a setting in modules/shapes/sr_settings.py (defaults = the rules above).
  swing moves  legs of the `magnitude` zigzag inside the period, confirmed by `end`
"""
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from modules.shapes.sr_lines import candidate_lines, line_key
from modules.shapes.sr_settings import SRRules, DEFAULT_RULES, DEFAULT_LEVELS
from modules.shapes.sr_turning_points import turning_points

LEVELS = DEFAULT_LEVELS
CHUNK_CELLS = 4_000_000     # pairs evaluated per numpy block (memory bound)


def swing_legs(df: pd.DataFrame, end: int, period: int, magnitude: float, tp: Optional[Dict] = None) -> np.ndarray:
    tp = tp if tp is not None else turning_points(df, magnitude)
    keep = (tp["conf"] <= end) & (tp["idx"] >= end - period + 1)
    return np.abs(np.diff(tp["y"][keep]))


def pipe_width(lower: Dict, upper: Dict) -> float:
    x0 = max(lower["x1"], upper["x1"])
    return (upper["y1"] + upper["slope"] * (x0 - upper["x1"])) - (lower["y1"] + lower["slope"] * (x0 - lower["x1"]))


def _ranks(lines):
    order = sorted(range(len(lines)), key=lambda i: line_key(lines[i]))
    rank = np.empty(len(lines), dtype=np.int64)
    rank[order] = np.arange(len(lines))
    return rank


def _pair_ok(i, j, col, end, lo_w, hi_w, rules):
    """Rows = lower lines i, cols = upper lines j: which pairs pass the pipe rules."""
    s, x1, y1, last = col["slope"], col["x1"], col["y1"], col["last_touch"]
    x0 = np.maximum(x1[i][:, None], x1[j][None, :])
    width = (y1[j][None, :] + s[j][None, :] * (x0 - x1[j][None, :])) - (y1[i][:, None] + s[i][:, None] * (x0 - x1[i][:, None]))
    ok = (s[j][None, :] - s[i][:, None] <= rules.max_divergence) & (width > 0) & (width >= lo_w) & (width <= hi_w)
    if rules.act_together:
        ok &= x0 < np.minimum(last[i][:, None], last[j][None, :])
    if rules.check_now:
        at_end = y1 + s * (end - x1)
        width_now = at_end[j][None, :] - at_end[i][:, None]
        ok &= (width_now > 0) & (width_now <= hi_w)
    return ok


def _bucket(groups, total, col, end, lo_w, hi_w, rules):
    """Every valid (lower, upper) pair whose touches add up to `total`, and how many were checked."""
    found_i, found_j, checked = [], [], 0
    for ta, rows in groups.items():
        cols = groups.get(total - ta)
        if cols is None:
            continue
        step = max(1, CHUNK_CELLS // len(cols))
        for c in range(0, len(rows), step):
            r, k = np.nonzero(_pair_ok(rows[c:c + step], cols, col, end, lo_w, hi_w, rules))
            found_i.append(rows[c:c + step][r]); found_j.append(cols[k])
            checked += len(rows[c:c + step]) * len(cols)
    return np.concatenate(found_i or [[]]).astype(int), np.concatenate(found_j or [[]]).astype(int), checked


def ranked_pipes(df: pd.DataFrame, end: int, period: int, magnitude: float, k: int = 1, tp_half: Optional[Dict] = None,
                 tp_full: Optional[Dict] = None, rules: SRRules = DEFAULT_RULES, max_pairs: Optional[int] = None,
                 info: Optional[Dict] = None, lines: Optional[List[Dict]] = None) -> List[Tuple[Dict, Dict]]:
    """The k best pipes, no line (line_key) in two of them. Pairs are checked in buckets of equal
    total touches, best first; inside a bucket by rank. If `max_pairs` runs out before k pipes are
    found, `info` says so (complete=False) and which total was the last fully checked. `lines` may be
    the candidate_lines already computed for these arguments."""
    info = info if info is not None else {}
    lines = lines if lines is not None else candidate_lines(df, end, period, magnitude, tp_half, rules)
    legs = swing_legs(df, end, period, magnitude, tp_full)
    info.update(complete=True, checked_down_to=None, lines=len(lines), pairs_checked=0)
    if len(lines) < 2 or not len(legs):
        return []
    lo_w = float(np.quantile(legs, rules.min_width_q)) if rules.min_width_q > 0 else 0.0
    hi_w = rules.max_width_mult * float(legs.max())
    col = {key: np.array([l[key] for l in lines], dtype=float) for key in ("slope", "x1", "y1", "last_touch")}
    touches, rank, keys = np.array([l["touches"] for l in lines]), _ranks(lines), [line_key(l) for l in lines]
    groups = {int(t): np.flatnonzero(touches == t) for t in sorted(set(touches), reverse=True)}
    out, used = [], set()
    for total in sorted({a + b for a in groups for b in groups}, reverse=True):
        if max_pairs is not None and info["pairs_checked"] >= max_pairs:
            info["complete"] = False
            break
        fi, fj, checked = _bucket(groups, total, col, end, lo_w, hi_w, rules)
        info["pairs_checked"] += checked
        info["checked_down_to"] = total
        for o in np.lexsort((rank[fj], rank[fi]))[::-1]:          # better lower line, then better upper
            i, j = fi[o], fj[o]
            if keys[i] in used or keys[j] in used or keys[i] == keys[j]:
                continue
            out.append((lines[i], lines[j])); used |= {keys[i], keys[j]}
            if len(out) == k:
                return out
    return out


def find_pipe(df: pd.DataFrame, end: int, period: int, magnitude: float, tp_half: Optional[Dict] = None,
              tp_full: Optional[Dict] = None, rules: SRRules = DEFAULT_RULES) -> Tuple[Optional[Dict], Optional[Dict]]:
    top = ranked_pipes(df, end, period, magnitude, 1, tp_half, tp_full, rules)
    return top[0] if top else (None, None)


def sr_lines_at(df: pd.DataFrame, end: int, levels: Dict = LEVELS, cache: Optional[Dict] = None,
                rules: SRRules = DEFAULT_RULES) -> Dict[str, Optional[Dict]]:
    """The 4 lines at bar `end`. `cache` may hold turning points computed once on the whole df
    ({threshold: turning_points(df, threshold)}); only points confirmed by `end` are used."""
    cache = cache if cache is not None else {}
    tp = lambda th: cache.setdefault(th, turning_points(df, th))
    out = {}
    for lvl, cfg in levels.items():
        m = cfg["magnitude"]
        out[f"{lvl}_support"], out[f"{lvl}_resistance"] = find_pipe(df, end, cfg["period"], m, tp(m * rules.candidate_ratio),
                                                                    tp(m), rules)
    return out
