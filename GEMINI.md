# GEMINI.md - Codebase Architecture & Cleanliness Guidelines

## 1. Folder Structure & Modular Architecture
All code in this repository must strictly adhere to the following decoupled modular structure:

- **`strategies/`**: Strategy logic extending `BaseStrategy` (e.g. `DailySupertrendStrategy`, `AgentConfluenceStrategy`).
- **`business_logic_services/`**: Backtest engine and execution services (`BacktestService`, `StrategyService`).
- **`modules/data/`**: Data loading and cycle containers (`CycleData`, `CYCLE_1`, `CYCLE_2`).
- **`helpers/` & `utils/`**: Standalone helper functions (`trade_formatter`, `export_helpers`, `indicator_helpers`).
- **`scripts/`**: CLI tools and exporter launchers (`export_dashboard.py`).
- **`ui/`**: All web dashboard assets (`ui/index.html`, `ui/css/`, `ui/js/`, and standalone export `ui/tradingview_chart.html`).
- **`config/`**: Constants and environment configuration (`settings.py`, `constants.py`).

---

## 2. Code Cleanliness & Quality Standards
- **Strict File Size Limit**: Every core Python file must be **under 150 lines**. Break larger modules into dedicated helpers.
- **Zero Syntax Errors**: All files must pass Python AST validation cleanly.
- **Single Dashboard File**: Export exclusively to `ui/tradingview_chart.html`. Do not write duplicate HTML files in the project root.
- **Zero Scratch Leftovers**: Never leave temporary test scripts, debug files, or scratch scripts in the workspace.

---

## 3. Lightweight Charts & UI Principles
- **Dynamic Viewport Scaling**: Calculate `fitBars = Math.floor(containerWidth / targetBarSpacing)` with `targetBarSpacing = 7`. Never use hardcoded per-timeframe bar counts.
- **Contiguous Candle Alignment**: Use unified integer Unix timestamps or contiguous step timestamps to collapse calendar whitespace gaps.
- **Clean Arrow Markers**: Render trade entry/exit markers as clean arrows (`arrowUp` / `arrowDown`) with `text: ''` to prevent text-driven bar spacing widening.
- **Active Trade Centering**: Navigation (Next ► / Prev ◄ / dropdown) must center the selected trade box dynamically on screen while preserving 7px candle spacing.
- **Spacious Scale Margins**: Main candlestick chart occupies top 68% height (`{ top: 0.04, bottom: 0.28 }`). Sub-panes (Volume, RSI 14, ADX 14) occupy clean, non-overlapping bottom bands.
- **Transparent Light Purple Trade Boxes**: Active trade boxes use vibrant Light Purple (`#8b5cf6`) with 100% transparent interior fill and 4-sided vertical/horizontal boundaries.
- **Real-Time Crosshair OHLC Streamer**: Mouse movement updates Open (O), High (H), Low (L), Close (C), and % Change in real-time in the top bar.
