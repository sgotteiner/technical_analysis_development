"""
S/R playground / annotator (owner, 2026-09-22): change the S/R settings and see the lines at once,
show several pipes and single lines per level, and draw your own lines and pattern boxes, saved
as ground truth to data/ground_truth/sr_annotations.json.

Usage:  python scripts/sr_playground.py        -> http://127.0.0.1:8765
"""
import os
import sys
import webbrowser
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from repositories.sr_annotation_repo import AnnotationStore
from routes.sr_playground_routes import make_router
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


def create_app(df: pd.DataFrame, ground_truth_path: str = GROUND_TRUTH, presets_path=PRESETS) -> FastAPI:
    app = FastAPI(title="S/R Playground")
    store = AnnotationStore(ground_truth_path)
    app.include_router(make_setup_router(df, store))
    app.include_router(make_preset_router(PresetStore(presets_path)))
    app.include_router(make_router(df, store))
    app.mount("/ui", StaticFiles(directory=UI_DIR), name="ui")

    @app.get("/")
    def page():
        return FileResponse(os.path.join(UI_DIR, "sr_playground.html"))

    return app


if __name__ == "__main__":
    import uvicorn
    webbrowser.open(f"http://{HOST}:{PORT}")
    uvicorn.run(create_app(load_daily()), host=HOST, port=PORT)
