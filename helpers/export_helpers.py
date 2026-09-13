"""
TradingView Exporter Helpers.
Handles payload extraction and standalone HTML template interpolation.
"""
import os
import re
import json
from helpers.trade_formatter import make_smooth_series, format_strategy_trades_and_markers

__all__ = ['make_smooth_series', 'format_strategy_trades_and_markers', 'render_dashboard_html']


def read_ui_file(ui_dir: str, rel_path: str) -> str:
    full_path = os.path.join(ui_dir, rel_path)
    if os.path.exists(full_path):
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""


def render_dashboard_html(
    ui_dir: str,
    multi_strategy_payload: dict,
    ema20_data: list,
    ema50_data: list,
    sma200_data: list,
    rsi_data: list,
    adx_data: list,
    volume_data: list,
    candle_data: list,
    tf_data: dict = None,
    ta_modules_data: dict = None
) -> str:
    """Export dashboard payload and render fully inlined standalone HTML."""
    data_dir = os.path.join(ui_dir, 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)

    tf_payload = json.dumps(tf_data) if tf_data else "{}"
    ta_payload = json.dumps(ta_modules_data) if ta_modules_data else "{}"

    # 1. Write Data Payload
    data_content = (
        f"const multiStrategyData = {json.dumps(multi_strategy_payload)};\n"
        f"const taModulesData = {ta_payload};\n"
        f"const ema20Data = {json.dumps(ema20_data)};\n"
        f"const ema50Data = {json.dumps(ema50_data)};\n"
        f"const sma200Data = {json.dumps(sma200_data)};\n"
        f"const rsiData = {json.dumps(rsi_data)};\n"
        f"const adxData = {json.dumps(adx_data)};\n"
        f"const volumeData = {json.dumps(volume_data)};\n"
        f"const candleData = {json.dumps(candle_data)};\n"
        f"const timeframeData = {tf_payload};\n"
    )
    with open(os.path.join(data_dir, 'dashboard_data.js'), 'w', encoding='utf-8') as f:
        f.write(data_content)

    # 2. Read Assets
    layout_css = read_ui_file(ui_dir, 'css/layout.css')
    toolbar_css = read_ui_file(ui_dir, 'css/toolbar.css')
    sidebar_css = read_ui_file(ui_dir, 'css/sidebar.css')
    combined_css = f"{layout_css}\n{toolbar_css}\n{sidebar_css}"

    lw_js = read_ui_file(ui_dir, 'lightweight-charts.js')
    chart_init_js = read_ui_file(ui_dir, 'js/chart_init.js')
    drawing_tools_js = read_ui_file(ui_dir, 'js/drawing_tools.js')
    trade_nav_js = read_ui_file(ui_dir, 'js/trade_navigation.js')
    tf_mgr_js = read_ui_file(ui_dir, 'js/timeframe_manager.js')
    pattern_inspector_js = read_ui_file(ui_dir, 'js/pattern_inspector.js')

    combined_engine_js = (
        f"// --- Chart Engine Modules ---\n"
        f"{chart_init_js}\n\n"
        f"{drawing_tools_js}\n\n"
        f"{trade_nav_js}\n\n"
        f"{tf_mgr_js}\n\n"
        f"{pattern_inspector_js}\n"
    )

    # 3. Read HTML Template
    with open(os.path.join(ui_dir, 'index.html'), 'r', encoding='utf-8') as f:
        html = f.read()

    # Clean CDN script tags
    html = re.sub(r'^\s*<script\s+src="https://cdn\.jsdelivr\.net/[^"]+"></script>\s*$', '', html, flags=re.MULTILINE)

    # Direct String Replacements
    html = html.replace('/* LIGHTWEIGHT_CHARTS_JS_PLACEHOLDER */', lw_js)
    html = html.replace('/* CSS_STYLES_PLACEHOLDER */', combined_css)

    # Data replacements
    html = html.replace('/* DATA_MULTI_STRATEGY */', json.dumps(multi_strategy_payload))
    html = html.replace('/* DATA_TA_MODULES */', ta_payload)
    html = html.replace('/* DATA_EMA20 */', json.dumps(ema20_data))
    html = html.replace('/* DATA_EMA50 */', json.dumps(ema50_data))
    html = html.replace('/* DATA_SMA200 */', json.dumps(sma200_data))
    html = html.replace('/* DATA_RSI */', json.dumps(rsi_data))
    html = html.replace('/* DATA_ADX */', json.dumps(adx_data))
    html = html.replace('/* DATA_VOLUME */', json.dumps(volume_data))
    html = html.replace('/* DATA_CANDLES */', json.dumps(candle_data))
    html = html.replace('/* DATA_TIMEFRAMES */', tf_payload)

    # Engine JS Replacement
    html = html.replace('/* CHART_ENGINE_JS_PLACEHOLDER */', combined_engine_js)

    return html
