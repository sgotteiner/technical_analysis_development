"""
Trading Microservice Application Entrypoint.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.settings import settings
from routes import backtest_router, data_router

app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    description="Microservices API for Strategy Backtesting, Market Data, and AI Trading Agents."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(backtest_router)
app.include_router(data_router)

@app.get("/")
def root():
    return {
        "status": "online",
        "service": settings.project_name,
        "version": settings.version,
        "docs_url": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
