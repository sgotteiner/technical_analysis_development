import os
import sys
import json
import pandas as pd
from ta.trend import ema_indicator, sma_indicator, adx
from ta.momentum import rsi

sys.path.append(os.path.abspath("."))
from business_logic_services.backtest_service import BacktestService
from strategies.daily_supertrend_strategy import DailySupertrendStrategy
from strategies.agent_confluence_strategy import AgentConfluenceStrategy
from helpers.export_helpers import make_smooth_series, format_strategy_trades_and_markers, render_dashboard_html
from helpers.ta_export_helpers import evaluate_all_ta_modules


def build_tf_payload(cycle_instance):
    df_1h = cycle_instance.df_1h.copy()
    df_daily = cycle_instance.df_daily.copy()
    df_5m = cycle_instance.df_5m.copy()

    df_5m_slice = df_5m.iloc[-20000:] if len(df_5m) > 20000 else df_5m
    df_4h = df_1h.resample('4h').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'}).dropna()
    df_1d = df_daily.copy() if not df_daily.empty else df_1h.resample('1D').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'}).dropna()

    full_daily_path = os.path.join("data", "btc_1d_extended.csv")
    if os.path.exists(full_daily_path):
        df_full_d = pd.read_csv(full_daily_path, index_col=0, parse_dates=True)
        df_full_d.index = pd.to_datetime(df_full_d.index, utc=True)
        df_1w = df_full_d.resample('1W').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'}).dropna()
    else:
        df_1w = df_1h.resample('1W').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'}).dropna()

    def to_c(df):
        if df.empty: return []
        ts = (df.index.astype('int64') // 10**9).tolist()
        return [{'time': t, 'open': o, 'high': h, 'low': l, 'close': c} for t, o, h, l, c in zip(ts, df['Open'].round(1), df['High'].round(1), df['Low'].round(1), df['Close'].round(1))]

    def to_v(df):
        if df.empty: return []
        ts = (df.index.astype('int64') // 10**9).tolist()
        vols = df['Volume'].round(2).tolist()
        is_up = (df['Close'] >= df['Open']).tolist()
        c_up, c_down = 'rgba(8, 153, 129, 0.35)', 'rgba(242, 54, 69, 0.35)'
        return [{'time': t, 'value': v, 'color': c_up if up else c_down} for t, v, up in zip(ts, vols, is_up)]

    def to_c_step(df, step_sec=86400):
        if df.empty: return []
        base_ts = int(df.index[0].timestamp())
        ts = [base_ts + i * step_sec for i in range(len(df))]
        return [{'time': t, 'open': o, 'high': h, 'low': l, 'close': c} for t, o, h, l, c in zip(ts, df['Open'].round(1), df['High'].round(1), df['Low'].round(1), df['Close'].round(1))]

    def to_v_step(df, step_sec=86400):
        if df.empty: return []
        base_ts = int(df.index[0].timestamp())
        ts = [base_ts + i * step_sec for i in range(len(df))]
        vols = df['Volume'].round(2).tolist()
        is_up = (df['Close'] >= df['Open']).tolist()
        c_up, c_down = 'rgba(8, 153, 129, 0.35)', 'rgba(242, 54, 69, 0.35)'
        return [{'time': t, 'value': v, 'color': c_up if up else c_down} for t, v, up in zip(ts, vols, is_up)]

    return {
        '5m': {'candles': to_c(df_5m_slice), 'volume': to_v(df_5m_slice)},
        '1h': {'candles': to_c(df_1h), 'volume': to_v(df_1h)},
        '4h': {'candles': to_c(df_4h), 'volume': to_v(df_4h)},
        '1d': {'candles': to_c(df_1d), 'volume': to_v(df_1d)},
        '1w': {'candles': to_c_step(df_1w, 86400), 'volume': to_v_step(df_1w, 86400)},
    }


def export_tradingview_dashboard(cycle_instance=None, filename="tradingview_chart.html"):
    if cycle_instance is None:
        from modules.data.data_container import CYCLE_2
        cycle_instance = CYCLE_2

    print(f"Exporting TradingView Dashboard for dataset: [{cycle_instance.name}] -> '{filename}'...")
    df_daily = cycle_instance.df_daily.copy()
    df_1h = cycle_instance.df_1h.copy()

    daily_sma200 = sma_indicator(df_daily['Close'], window=200).fillna(0)
    daily_ema20 = ema_indicator(df_daily['Close'], window=20).fillna(0)
    daily_ema50 = ema_indicator(df_daily['Close'], window=50).fillna(0)
    daily_rsi = rsi(df_daily['Close'], window=14).fillna(50.0)
    daily_adx = adx(df_daily['High'], df_daily['Low'], df_daily['Close'], window=14).fillna(0.0)

    smooth_sma200 = make_smooth_series(daily_sma200, df_1h.index)
    smooth_ema20 = make_smooth_series(daily_ema20, df_1h.index)
    smooth_ema50 = make_smooth_series(daily_ema50, df_1h.index)
    smooth_rsi = make_smooth_series(daily_rsi, df_1h.index)
    smooth_adx = make_smooth_series(daily_adx, df_1h.index)

    sma200_data = [{'time': int(idx.timestamp()), 'value': float(smooth_sma200.loc[idx])} for idx in df_1h.index if not pd.isna(smooth_sma200.loc[idx]) and float(smooth_sma200.loc[idx]) > 0]
    ema20_data = [{'time': int(idx.timestamp()), 'value': float(smooth_ema20.loc[idx])} for idx in df_1h.index if not pd.isna(smooth_ema20.loc[idx]) and float(smooth_ema20.loc[idx]) > 0]
    ema50_data = [{'time': int(idx.timestamp()), 'value': float(smooth_ema50.loc[idx])} for idx in df_1h.index if not pd.isna(smooth_ema50.loc[idx]) and float(smooth_ema50.loc[idx]) > 0]
    rsi_data = [{'time': int(idx.timestamp()), 'value': float(smooth_rsi.loc[idx])} for idx in df_1h.index if not pd.isna(smooth_rsi.loc[idx]) and float(smooth_rsi.loc[idx]) > 0]
    adx_data = [{'time': int(idx.timestamp()), 'value': float(smooth_adx.loc[idx])} for idx in df_1h.index if not pd.isna(smooth_adx.loc[idx]) and float(smooth_adx.loc[idx]) >= 0]

    tf_data = build_tf_payload(cycle_instance)
    candle_data = tf_data['1h']['candles']
    volume_data = tf_data['1h']['volume']

    registered_strategies = [
        ('daily_supertrend', DailySupertrendStrategy()),
        ('agent_confluence', AgentConfluenceStrategy())
    ]

    multi_strategy_payload = {}
    for strat_key, strat_obj in registered_strategies:
        res = BacktestService.execute_backtest(strat_obj, cycle_instance)
        markers, formatted_trades = format_strategy_trades_and_markers(res.get('trades_list', []))
        multi_strategy_payload[strat_key] = {
            'name': strat_obj.name,
            'stats': {
                'return': res['net_return'],
                'winRate': res['win_rate'],
                'numTrades': res['total_trades'],
                'medianReturn': res['median_return'],
                'p33Return': res['p33_return'],
                'p66Return': res['p66_return'],
                'meanReturn': res['mean_return'],
                'minReturn': res['min_return'],
                'maxReturn': res['max_return'],
                'maxDrawdown': 0.0
            },
            'markers': markers,
            'trades': formatted_trades
        }

    ta_modules_data = evaluate_all_ta_modules(df_daily, df_1h)

    ui_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ui')
    if not os.path.exists(ui_dir):
        ui_dir = "ui"

    html_output = render_dashboard_html(
        ui_dir, multi_strategy_payload, ema20_data, ema50_data,
        sma200_data, rsi_data, adx_data, volume_data, candle_data, tf_data, ta_modules_data
    )

    ui_path = os.path.join("ui", filename)
    with open(ui_path, 'w', encoding='utf-8') as f:
        f.write(html_output)

    print(f"TradingView Dashboard successfully exported to '{ui_path}'!")


if __name__ == "__main__":
    from modules.data.data_container import CYCLE_2
    export_tradingview_dashboard(CYCLE_2, "tradingview_chart.html")
