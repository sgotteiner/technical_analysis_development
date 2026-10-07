"""
Price zones — the owner's rules (2026-09-24).

A level is not a line through points, it is a BAND of price:
  width    from the swing size in percent (about half a swing), so it is scale-free -
           "you can count on the same metric of percentage to see similar moves"
  visits   the strength. Price must LEAVE the band and come back for a new visit, so three
           wiggles in one week count once - "measure the moves time"
  price    the strongest price inside the band (the median of its touches in log price)
  now      the current price is always a candidate zone, whether or not a swing point sits there
           (the 80.3k level price was standing on was missed without this)
  label    a zone price stands on is named by where price came from: up to it = resistance,
           down to it = support; otherwise below price = support, above = resistance

Ranked by visits, then by the most recent visit.
"""
from typing import Dict, List
import numpy as np


def label_for(zone_price: float, price_now: float, price_before: float, tol_pct: float = 1.5) -> str:
    """Support or resistance. Standing ON the zone (within tol), the direction price came from
    decides: up to it = resistance, down to it = support (owner, 2026-09-24)."""
    if abs(np.log(price_now / zone_price)) <= np.log(1 + tol_pct / 100):
        return "resistance" if price_before < zone_price else "support"
    return "resistance" if zone_price > price_now else "support"


def ladder(zones: List[Dict], price_now: float, price_before: float, n_each: int = 3,
           min_visits: int = 2) -> Dict:
    """The answer from where price is: the zone it stands on (if any), then the next ones up and
    down. Each is labelled support / resistance (owner, 2026-09-24)."""
    named = [{**z, "label": label_for(z["price"], price_now, price_before)}
             for z in zones if z["visits"] >= min_visits]
    on = next((z for z in named if z["at_price_now"]), None)
    rest = [z for z in named if z is not on and not z["at_price_now"]]
    return {"price_now": price_now, "on": on,
            "above": sorted([z for z in rest if z["price"] > price_now], key=lambda z: z["price"])[:n_each],
            "below": sorted([z for z in rest if z["price"] < price_now], key=lambda z: -z["price"])[:n_each]}


def _visits(inside: np.ndarray) -> int:
    """Touches grouped into visits: a new visit starts after price has been outside the band, so a
    visit is a rising edge of `inside` (the points are in bar order)."""
    return int(inside[0]) + int(np.count_nonzero(inside[1:] & ~inside[:-1]))


def _cluster(y: np.ndarray, band: float) -> List[np.ndarray]:
    """Group log prices so that no cluster is wider than `band`, by repeatedly merging the CLOSEST
    neighbouring pair that still fits.

    Not "a band around whichever point came first", which is what this used to be: that split two
    peaks 1.02% apart while the band was nominally 1.5%, because the band was halved around a
    centre and the centre was the earlier point. The owner saw the result before the cause -
    "2 lines too close in a way that doesnt align with the move size ... takes the first next peak
    even if its just noise" (2026-10-05). Merging the closest pair is order-independent: the same
    points give the same clusters whatever order they arrive in.
    """
    order = np.argsort(y)
    groups: List[List[int]] = [[int(i)] for i in order]
    while len(groups) > 1:
        lo = np.array([y[g[0]] for g in groups])        # each group is sorted, and groups are too
        hi = np.array([y[g[-1]] for g in groups])
        width = hi[1:] - lo[:-1]                        # width if neighbours i and i+1 merged
        fits = np.flatnonzero(width <= band)
        if not len(fits):
            break
        j = int(fits[np.argmin(width[fits])])           # the closest pair that still fits
        groups[j:j + 2] = [groups[j] + groups[j + 1]]
    return [np.array(sorted(g)) for g in groups]


def price_zones(x: np.ndarray, y: np.ndarray, kind: np.ndarray, band_pct: float,
                now_price: float, now_bar: float, tol_now_pct: float = 1.5) -> List[Dict]:
    """`x` bars, `y` log prices of the turning points, `kind` peak/valley. Returns ranked zones.

    `band_pct` is the widest a level may be, end to end - not a radius. Two dots within it are one
    level; the clusters come out the same whatever order the dots arrive in.
    """
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    if not len(x):
        return []
    band = np.log(1 + band_pct / 100)
    order = np.argsort(x)
    x, y, kind = x[order], y[order], np.asarray(kind)[order]
    tol_now = np.log(1 + tol_now_pct / 100)
    zones: List[Dict] = []
    for idx in _cluster(y, band):
        near = np.zeros(len(y), dtype=bool)
        near[idx] = True
        touched, zone_y = x[near], float(np.median(y[near]))
        zones.append({"y": zone_y, "price": float(np.exp(zone_y)),
                      "low": float(np.exp(float(np.min(y[near])))),
                      "high": float(np.exp(float(np.max(y[near])))),
                      "touches": int(near.sum()), "visits": _visits(near),
                      "first_visit": float(touched[0]), "last_visit": float(touched[-1]),
                      "points": touched.tolist(),
                      "at_price_now": bool(abs(np.log(now_price) - zone_y) <= tol_now)})
    zones.sort(key=lambda z: (z["visits"], z["last_visit"]), reverse=True)
    return zones
