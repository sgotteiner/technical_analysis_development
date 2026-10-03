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


def _built_from(level: Dict, day) -> str:
    """How the rule actually built this line: the dots it is made of."""
    dots = level.get("points") or []
    touches = level.get("touches", len(dots))
    visits = level.get("visits")
    span = f" between {day(level['first'])} and {day(level['last'])}" if dots else ""
    visited = f", visited {visits} times" if visits else ""
    return f"A cluster of {touches} dot{'s' if touches != 1 else ''}{visited}{span}."


def setup_story(levels: List[Dict], trend: Optional[Dict], price_now: float, price_before: float,
                current_move: float, move_from_bar: float, now_bar: float, band_pct: float, day,
                bars: np.ndarray, prices: np.ndarray, moves: np.ndarray,
                boxes_by_bar: Optional[Dict] = None) -> Dict:
    """`levels` are the lines the chart is drawing, exactly as it drew them."""
    boxes_by_bar = boxes_by_bar or {}
    band = np.log(1 + band_pct / 100)
    lines: List[Dict] = []

    def entry(role: str, price: float, how: str, points: List[float]) -> Dict:
        return {"role": role, "price": float(price), "how": how,
                "points": [float(b) for b in points],
                "boxes": [boxes_by_bar[int(b)] for b in points if int(b) in boxes_by_bar]}

    if trend:
        lines.append(entry(
            "the trend", trend["at_now"],
            f"{'Falling' if trend['slope_pct_day'] < 0 else 'Rising'} "
            f"{trend['slope_pct_day']:+.2f}%/day on the "
            f"{'peaks' if trend['slope_pct_day'] < 0 else 'valleys'}, "
            f"{trend['touches']} touches from {day(trend['first'])} to {day(trend['last'])} - "
            f"still touched now, which is what keeps it on the chart.",
            trend.get("points", [])))

    on = next((l for l in levels if abs(np.log(l["price"] / price_now)) <= band), None)
    above = sorted([l for l in levels if l is not on and l["price"] > price_now],
                   key=lambda l: l["price"])
    below = sorted([l for l in levels if l is not on and l["price"] < price_now],
                   key=lambda l: -l["price"])
    came_up = price_before < price_now

    def describe(level: Dict, role: str) -> None:
        p = precedent_at(level["price"], current_move, bars, prices, moves, band_pct, now_bar)
        how = _built_from(level, day) + " " + _precedent_sentence(p, current_move, day)
        e = entry(role, level["price"], how, level.get("points") or [])
        e["precedent"] = None if p is None else day(p["bar"])
        e["matched"] = bool(p and p["matched"])
        lines.append(e)

    if on is not None:
        # "came up to it = resistance, came down to it = support" - his label for the line price is on
        describe(on, "current " + ("resistance" if came_up else "support"))
    for role, level in zip(ROLES_UP[1:] if on is not None and came_up else ROLES_UP, above):
        describe(level, role)
    for role, level in zip(ROLES_DOWN[1:] if on is not None and not came_up else ROLES_DOWN, below):
        describe(level, role)

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
