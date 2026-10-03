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


def price_zones(x: np.ndarray, y: np.ndarray, kind: np.ndarray, band_pct: float,
                now_price: float, now_bar: float, tol_now_pct: float = 1.5) -> List[Dict]:
    """`x` bars, `y` log prices of the turning points, `kind` peak/valley. Returns ranked zones.

    Every point's price is a candidate centre (plus the current price); the fullest band is taken
    first and the ones it already covers drop out. Which point falls in which band is worked out
    once, as a matrix, rather than per candidate."""
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    if not len(x):
        return []
    band = np.log(1 + band_pct / 100) / 2          # half a band each side of the centre
    order = np.argsort(x)
    x, y, kind = x[order], y[order], np.asarray(kind)[order]
    centres = np.append(y, float(np.log(now_price)))   # the current price is always a candidate
    near_all = np.abs(y[:, None] - centres[None, :]) <= band       # (point, candidate)
    # fullest band first; ties keep the order the points came in (sort is stable)
    ranked = sorted(range(len(centres)), key=lambda c: -near_all[:, c].sum())
    zones: List[Dict] = []
    taken = np.empty(len(centres))                 # the y of each zone already accepted
    for c in ranked:
        centre = float(centres[c])
        if len(zones) and (np.abs(taken[:len(zones)] - centre) <= band).any():
            continue                                # already covered by a stronger zone
        near = near_all[:, c]
        if not near.any():
            continue
        touched, zone_y = x[near], float(np.median(y[near]))
        taken[len(zones)] = zone_y
        zones.append({"y": zone_y, "price": float(np.exp(zone_y)),
                      "low": float(np.exp(centre - band)), "high": float(np.exp(centre + band)),
                      "touches": int(near.sum()), "visits": _visits(near),
                      "first_visit": float(touched[0]), "last_visit": float(touched[-1]),
                      "points": touched.tolist(),
                      "at_price_now": bool(abs(np.log(now_price) - centre) <= np.log(1 + tol_now_pct / 100))})
    zones.sort(key=lambda z: (z["visits"], z["last_visit"]), reverse=True)
    return zones
