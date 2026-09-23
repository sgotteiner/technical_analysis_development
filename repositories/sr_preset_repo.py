"""
Saved playground presets (owner, 2026-09-24: "i want a dedicated yaml file or whatever along with
the code they worked on. what if we change the code or settings? we lose it?").

A preset = a name, the playground settings, the git commit they were produced on, when it was
saved and an optional note. Kept in config/sr_presets.yaml, in the repo, so a state can always be
brought back together with the code that made it (`git checkout <commit>`).
Saving a name that exists keeps the older one as "<name> (saved YYYY-MM-DD HH:MM)".
"""
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
import yaml

ROOT = Path(__file__).resolve().parents[1]
SHIPPED = ROOT / "config" / "sr_presets.yaml"
FIELDS = {"sizesText", "targetDays", "anchorDays", "minTouches", "maxHistory", "tolPct", "top",
          "mode", "maxSlope", "lookback", "show", "drawLines"}


def current_commit(root: Path = ROOT) -> Optional[str]:
    try:
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=root, capture_output=True,
                             text=True, timeout=10)
        return out.stdout.strip() or None
    except Exception:
        return None


class PresetStore:
    def __init__(self, path=SHIPPED, commit: Optional[str] = None):
        self.path = Path(path)
        self._commit = commit

    def list(self) -> List[Dict]:
        if not self.path.exists():
            return []
        return yaml.safe_load(self.path.read_text(encoding="utf-8")).get("presets", [])

    def get(self, name: str) -> Optional[Dict]:
        return next((p for p in self.list() if p["name"] == name), None)

    def save(self, name: str, settings: Dict, note: str = "") -> Dict:
        name = str(name).strip()
        unknown = set(settings) - FIELDS
        if not name or not settings or unknown:
            raise ValueError(f"a preset needs a name and known settings (unknown: {sorted(unknown)})")
        now = datetime.now(timezone.utc)
        preset = {"name": name, "saved_at": now.isoformat(timespec="seconds"),
                  "commit": self._commit if self._commit is not None else current_commit(),
                  "note": note, "settings": dict(settings)}
        presets = [{**p, "name": f'{p["name"]} (saved {p["saved_at"][:16].replace("T", " ")})'}
                   if p["name"] == name else p for p in self.list()]
        presets.append(preset)
        self._write(presets)
        return preset

    def _write(self, presets: List[Dict]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(HEADER + yaml.safe_dump({"presets": presets}, sort_keys=False, allow_unicode=True),
                       encoding="utf-8")
        os.replace(tmp, self.path)


HEADER = ("# Saved S/R playground presets (repositories/sr_preset_repo.py).\n"
          "# Each preset keeps the settings AND the commit they were produced on, so a state can be\n"
          "# brought back with its code:  git checkout <commit>   (or the tag, where there is one).\n"
          "# Written by the playground's \"save current...\" button; safe to edit by hand.\n")
