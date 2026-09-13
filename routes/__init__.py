"""
Routes Package Initializer.
"""
from routes.backtest_routes import router as backtest_router
from routes.data_routes import router as data_router

__all__ = [
    "backtest_router",
    "data_router"
]
