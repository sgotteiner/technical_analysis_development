"""
Market Data API Routes (FastAPI Microservice Endpoints).
"""
from fastapi import APIRouter, HTTPException, Query
from schemas.market_data_schema import MarketDataRequestSchema, MarketDataResponseSchema
from repositories.market_data_repo import MarketDataRepository

router = APIRouter(prefix="/api/v1/data", tags=["Market Data"])
repo = MarketDataRepository()

@router.get("/fetch", response_model=MarketDataResponseSchema)
def fetch_market_data(
    symbol: str = Query("BTC-USD", description="Asset symbol"),
    interval: str = Query("1d", description="Timeframe interval"),
    range_str: str = Query("10y", description="Data range")
):
    """Fetch market candles from Yahoo Finance."""
    try:
        df = repo.fetch_yahoo_chart(symbol=symbol, interval=interval, range_str=range_str)
        if df.empty:
            raise HTTPException(status_code=404, detail="No data returned for symbol.")
            
        start_date = str(df.index[0].date())
        end_date = str(df.index[-1].date())
        
        return MarketDataResponseSchema(
            symbol=symbol,
            interval=interval,
            candle_count=len(df),
            start_date=start_date,
            end_date=end_date
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch market data: {str(e)}")
