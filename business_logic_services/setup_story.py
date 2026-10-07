"""
The setup, explained the way he explains his (owner, 2026-10-03):

  "i explained to you what i did and i expect to get the same explanation. what is each line which
   is minimum the trend and current and next support and resistance but maybe a bit more not a lot
   more and how did you find them."

This EXPLAINS THE LINES THE CHART DRAWS. It does not find its own.

The first version did find its own - a second, parallel level-finder - and the result was two
different answers in one page with no line in common ("the sidebar setup where i look at individual
parts is different (and worse) then the full setup. completely different numbers... what is this
joke"). The explanation is a description of the answer, never a rival to it.

Each line gets: its role from where price is, how the rule built it (the dots it is made of), the
precedent behind it (the previous time price was at that level, after what size of move), and the
dots themselves so they can be picked out and their boxes shown.
"""
from typing import Dict, List, Optional
import numpy as np
from business_logic_services.precedents import precedent_at

ROLES_UP = ["current resistance", "next resistance", "next next resistance", "further resistance"]
ROLES_DOWN = ["current support", "next support", "next next support", "further support"]


def _precedent_sentence(p: Optional[Dict], current_move: float, day) -> str:
    if p is None:
        return "Price has never been at this level before."
    when, move, ratio = day(p["bar"]), p["move"], p["vs_now"]
    if p["matched"]:
        return (f"The previous time price was here was {when} at {p['price']:,.0f}, after a "
                f"+{move:.0f}% move - {ratio:.2f}x the +{current_move:.0f}% running now, the same "
                f"move, so the search stopped there (read {p['checked']}).")
    return (f"The last time price was here was {when} at {p['price']:,.0f}, but after a +{move:.0f}% "
            f"move ({ratio:.2f}x) - not the same size, so nothing similar was found (read "
            f"{p['checked']}).")


def _strength(level: Dict) -> str:
    """How likely price is to turn at it, as measured (business_logic_services/level_strength.py)."""
    if "strength_label" not in level:
        return ""
    from business_logic_services.level_strength import TURNED
    label = level["strength_label"]
    return (f" Price held at it {level['held']} times and broke through it {level['broken']} times."
            f" Strength: {label} - levels scoring like this turned price {TURNED[label]}% of the time"
            f" at the next visit (2023-2026).")


def _built_from(level: Dict, day) -> str:
    """How the rule actually built this line: the dots it is made of."""
    dots = level.get("points") or []
    if level.get("wall"):
        kind = "peaks" if level["wall"] == "ceiling" else "valleys"
        at = " and ".join(f"{p:,.0f} ({day(b)})" for b, p in zip(dots, level["point_prices"]))
        where = "over price" if level["wall"] == "ceiling" else "under price"
        return f"The flat {level['wall']} {where}: its {kind} at one height, {at}."
    touches = level.get("touches", len(dots))
    visits = level.get("visits")
    span = f" between {day(level['first'])} and {day(level['last'])}" if dots else ""
    visited = f", visited {visits} times" if visits else ""
    return f"A cluster of {touches} dot{'s' if touches != 1 else ''}{visited}{span}."


def setup_story(levels: List[Dict], trend: Optional[Dict], price_now: float, came_up: bool,
                current_move: float, move_from_bar: float, now_bar: float, band_pct: float, day,
                bars: np.ndarray, prices: np.ndarray, moves: np.ndarray,
                boxes_by_bar: Optional[Dict] = None) -> Dict:
    """`levels` are the lines the chart is drawing, exactly as it drew them."""
    boxes_by_bar = boxes_by_bar or {}
    lines: List[Dict] = []

    def entry(role: str, price: float, how: str, points: List[float]) -> Dict:
        return {"role": role, "price": float(price), "how": how, "kind": "level",
                "slope_pct_day": None,
                "points": [float(b) for b in points],
                "boxes": [boxes_by_bar[int(b)] for b in points if int(b) in boxes_by_bar]}

    if trend:
        # the slope goes out with it: a verdict on a TREND is keyed by its slope as well as its
        # price, so the story card can carry his ✓/✗ the same way the found-lines card does
        direction = trend.get("direction") or ("down" if trend["slope_pct_day"] < 0 else "up")
        over = {"down": "over the peaks", "up": "under the valleys"}.get(direction, "along the ceiling of the range")
        broken = ((direction == "down" and price_now > trend["at_now"])
                  or (direction == "up" and price_now < trend["at_now"]))
        lines.append({**entry(
            "the previous trend" if trend.get("previous") else "the trend", trend["at_now"],
            ("Before the range price is in now - " if trend.get("previous") else "")
            + f"{direction.capitalize()}: {trend['slope_pct_day']:+.2f}%/day {over}, from "
            f"{day(trend['first'])} where the trend began to {day(trend['last'])}"
            + (" - price has broken it, and no two new peaks and valleys have replaced it yet."
               if broken else ".")
            + (f" Its line is {trend['away_pct']:.1f}% {'under' if trend['at_now'] < price_now else 'over'}"
               f" price - further than this move can reach."
               if trend.get("far") else "")
            + (f" Its size: {trend['size_pct']:+.0f}%, from {trend['size_from'][1]:,.0f} ({day(trend['size_from'][0])})"
               f" to {trend['size_to'][1]:,.0f} ({day(trend['size_to'][0])}),"
               f" {int(trend['size_to'][0] - trend['size_from'][0])} days."
               if "size_pct" in trend else ""),
            trend.get("points", [])),
            "kind": "trend", "slope_pct_day": float(trend["slope_pct_day"])})

    # the roster decides which level price is on (setup_roster.keep_roster marks it); deciding it
    # again here with another tolerance made the card call 64,478 "on" with price 3.3% above it
    on = next((l for l in levels if l.get("on")), None)
    above = sorted([l for l in levels if l is not on and l["price"] > price_now],
                   key=lambda l: l["price"])
    below = sorted([l for l in levels if l is not on and l["price"] < price_now],
                   key=lambda l: -l["price"])

    def describe(level: Dict, role: str) -> None:
        p = precedent_at(level["price"], current_move, bars, prices, moves, band_pct, now_bar)
        how = _built_from(level, day) + " " + _precedent_sentence(p, current_move, day) + _strength(level)
        e = entry(role, level["price"], how, level.get("points") or [])
        e["precedent"] = None if p is None else day(p["bar"])
        e["matched"] = bool(p and p["matched"])
        lines.append(e)

    # His roster has no "next": the level above, the level below, and the one price is standing on
    # ("i dont want no next", 2026-10-05). The names say where they are, not how far down a ladder.
    if on is not None:
        # "came up to it = resistance, came down to it = support" (2026-09-24), where "came" is the
        # move running now - the leg from the latest peak or valley, his order - not the last ten
        # days. Ten days called it support at 2026-05-15, two percent under a fresh high, while he
        # read "price is on a peak in this downtrend"; his 2025-10-03 note reads "the price is at the
        # resistance" in an up trend. Both are price that came UP to the level, whatever the trend.
        describe(on, "the level price is on (" + ("resistance" if came_up else "support") + ")")
    for level in above[:1]:
        describe(level, "resistance above")
    for level in below[:1]:
        describe(level, "support below")

    return {"price_now": price_now, "current_move": current_move,
            "move_from": day(move_from_bar), "lines": lines}


def as_text(story: Dict) -> str:
    """The same thing as prose, so it reads like the explanation he wrote for his own setup."""
    out = [f"price {story['price_now']:,.0f}; the move running now is +{story['current_move']:.1f}% "
           f"from {story['move_from']}.", ""]
    for l in story["lines"]:
        out.append(f"{l['role']}  {l['price']:,.0f}")
        out.append(f"    {l['how']}")
    return "\n".join(out)
