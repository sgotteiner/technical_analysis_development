"""
S/R playground / annotator (owner, 2026-09-22): change the S/R settings and see the lines at once,
show several pipes and single lines per level, and draw your own lines and pattern boxes, saved
as ground truth to data/ground_truth/sr_annotations.json.

Usage:  python scripts/sr_playground.py        -> http://127.0.0.1:8765
"""
import os
import sys
import webbrowser
from datetime import datetime, timezone
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from repositories.json_doc import JsonDoc
from repositories.sr_drawings_repo import DrawingStore
from repositories.sr_setups_repo import SetupStore
from repositories.sr_verdicts_repo import VerdictStore
from routes.sr_view_routes import make_view_router
from routes.sr_ground_truth_routes import make_ground_truth_router
from routes.setup_routes import make_setup_router
from routes.preset_routes import make_preset_router
from repositories.sr_preset_repo import PresetStore, SHIPPED as PRESETS

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UI_DIR = os.path.join(ROOT, "ui")
DATA = os.path.join(ROOT, "data", "btc_1d_extended.csv")
GROUND_TRUTH = os.path.join(ROOT, "data", "ground_truth", "sr_annotations.json")
HOST, PORT = "127.0.0.1", 8765


def load_daily(path: str = DATA) -> pd.DataFrame:
    df = pd.read_csv(path, index_col=0)
    df.index = pd.to_datetime(df.index, utc=True)
    return df


def ui_build_slug(ui_dir: str = UI_DIR) -> str:
    """The same build, as a URL-safe token."""
    return ui_build(ui_dir).replace("-", "").replace(":", "").replace(" ", "-")


def ui_build(ui_dir: str = UI_DIR) -> str:
    """When the page's own files were last changed. Shown in the toolbar so the owner can see at a
    glance whether what he is looking at is the code on disk - four stale-code incidents in one
    session were each mistaken for a broken feature."""
    newest = max((os.path.getmtime(os.path.join(root, f))
                  for root, _, files in os.walk(ui_dir) for f in files
                  if f.endswith((".js", ".css", ".html"))), default=0)
    return datetime.fromtimestamp(newest, timezone.utc).strftime("%Y-%m-%d %H:%M")


def create_app(df: pd.DataFrame, ground_truth_path: str = GROUND_TRUTH, presets_path=PRESETS) -> FastAPI:
    app = FastAPI(title="S/R Playground")
    doc = JsonDoc(ground_truth_path)          # one file, three collections over it
    app.include_router(make_setup_router(df, SetupStore(doc)))
    app.include_router(make_preset_router(PresetStore(presets_path)))
    app.include_router(make_view_router(df))
    app.include_router(make_ground_truth_router(df, DrawingStore(doc), VerdictStore(doc)))
    app.mount("/ui", StaticFiles(directory=UI_DIR), name="ui")

    @app.middleware("http")
    async def never_cache_the_ui(request, call_next):
        """`no-store`, not `no-cache`: the owner ran stale code four times in one session, and twice
        it was ES modules the browser kept serving from its own map after a reload. This is a local
        dev tool on localhost - refetching a few KB costs nothing, and being unable to trust that
        the page is the code costs a round trip every time."""
        response = await call_next(request)
        if request.url.path == "/" or request.url.path.startswith(("/ui", "/build")):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

    @app.get("/build/{build}/{path:path}")       # own prefix: the /ui mount would swallow it
    def versioned_asset(build: str, path: str):
        """The page's files under a URL that changes with every edit. Relative imports inside a
        module resolve against the module's own URL, so the whole import graph moves with the
        build and the browser cannot serve one file from an old version next to a new one -
        which is exactly what kept happening (new page, old drawings.js)."""
        full = os.path.normpath(os.path.join(UI_DIR, path))
        if not full.startswith(UI_DIR) or not os.path.isfile(full):
            raise HTTPException(404, "no such file")
        return FileResponse(full)

    @app.get("/")
    def page():
        html = open(os.path.join(UI_DIR, "sr_playground.html"), encoding="utf-8").read()
        return HTMLResponse(html.replace('"/ui/', f'"/build/{ui_build_slug()}/'))

    return app


if __name__ == "__main__":
    import uvicorn
    webbrowser.open(f"http://{HOST}:{PORT}")
    uvicorn.run(create_app(load_daily()), host=HOST, port=PORT)
