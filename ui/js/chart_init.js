// Chart Container & Sub-Pane Initialization
let currentStrategyKey = 'daily_supertrend';
let currentTradeIdx = 0;
let activeTool = 'cursor';
let drawPoints = [];
let userSeries = [];

const container = document.getElementById('chart-container');
const chart = LightweightCharts.createChart(container, {
    width: container.clientWidth,
    height: container.clientHeight,
    layout: {
        background: { type: 'solid', color: '#131722' },
        textColor: '#d1d4dc',
        fontSize: 11,
        fontFamily: 'Trebuchet MS, Roboto, sans-serif'
    },
    grid: {
        vertLines: { color: '#1f2430' },
        horzLines: { color: '#1f2430' }
    },
    crosshair: {
        mode: LightweightCharts.CrosshairMode.Normal
    },
    priceScale: {
        borderColor: '#2a2e39',
        scaleMargins: { top: 0.04, bottom: 0.28 }
    },
    timeScale: {
        borderColor: '#2a2e39',
        timeVisible: true,
        rightOffset: 2,
        fixLeftEdge: true
    }
});

// 1. Main Candlestick Series
const mainSeries = chart.addCandlestickSeries({
    upColor: '#089981',
    downColor: '#f23645',
    borderDownColor: '#f23645',
    borderUpColor: '#089981',
    wickDownColor: '#f23645',
    wickUpColor: '#089981'
});
if (typeof candleData !== 'undefined' && candleData) {
    try { mainSeries.setData(candleData); } catch(e) {}
}

// 2. Volume Sub-Pane
const volumeSeries = chart.addHistogramSeries({
    priceFormat: { type: 'volume' },
    priceScaleId: 'volume_scale'
});
try {
    chart.priceScale('volume_scale').applyOptions({ scaleMargins: { top: 0.56, bottom: 0.28 } });
    if (typeof volumeData !== 'undefined' && volumeData) volumeSeries.setData(volumeData);
} catch(e) {}

// 3. Moving Averages
const ema20Series = chart.addLineSeries({ color: '#089981', lineWidth: 2, title: 'EMA 20' });
if (typeof ema20Data !== 'undefined' && ema20Data) { try { ema20Series.setData(ema20Data); } catch(e) {} }

const ema50Series = chart.addLineSeries({ color: '#f23645', lineWidth: 2, title: 'EMA 50' });
if (typeof ema50Data !== 'undefined' && ema50Data) { try { ema50Series.setData(ema50Data); } catch(e) {} }

const smaSeries = chart.addLineSeries({ color: '#2962ff', lineWidth: 2, title: 'SMA 200' });
if (typeof sma200Data !== 'undefined' && sma200Data) { try { smaSeries.setData(sma200Data); } catch(e) {} }

let rsi50Series = null;
let adx20Series = null;

// 4. Sub-Pane 1: RSI 14
const rsiSeries = chart.addLineSeries({ color: '#B25AFF', lineWidth: 2, priceScaleId: 'rsi_scale', title: 'RSI (14)' });
try {
    chart.priceScale('rsi_scale').applyOptions({ scaleMargins: { top: 0.74, bottom: 0.14 } });
    if (typeof rsiData !== 'undefined' && rsiData && rsiData.length > 0) {
        rsiSeries.setData(rsiData);
        rsi50Series = chart.addLineSeries({ color: 'rgba(255, 255, 255, 0.25)', lineWidth: 1, lineStyle: LightweightCharts.LineStyle.Dotted, priceScaleId: 'rsi_scale' });
        rsi50Series.setData(rsiData.map(d => ({ time: d.time, value: 50.0 })));
    }
} catch(e) {}

// 5. Sub-Pane 2: ADX 14
const adxSeries = chart.addLineSeries({ color: '#FFEA00', lineWidth: 2, priceScaleId: 'adx_scale', title: 'ADX (14)' });
try {
    chart.priceScale('adx_scale').applyOptions({ scaleMargins: { top: 0.87, bottom: 0.02 } });
    if (typeof adxData !== 'undefined' && adxData && adxData.length > 0) {
        adxSeries.setData(adxData);
        adx20Series = chart.addLineSeries({ color: 'rgba(255, 234, 0, 0.4)', lineWidth: 1, lineStyle: LightweightCharts.LineStyle.Dotted, priceScaleId: 'adx_scale' });
        adx20Series.setData(adxData.map(d => ({ time: d.time, value: 20.0 })));
    }
} catch(e) {}

// 6. Live OHLC + % Change Streamer
function updateOhlcDisplay(c) {
    if (!c) return;
    const o = c.open || 0;
    const h = c.high || 0;
    const l = c.low || 0;
    const cl = c.close || 0;
    const chg = o > 0 ? ((cl - o) / o) * 100.0 : 0.0;

    const elO = document.getElementById('ohlc-o');
    const elH = document.getElementById('ohlc-h');
    const elL = document.getElementById('ohlc-l');
    const elC = document.getElementById('ohlc-c');
    const elChg = document.getElementById('ohlc-change');

    if (elO) elO.textContent = '$' + o.toLocaleString(undefined, {minimumFractionDigits: 1});
    if (elH) elH.textContent = '$' + h.toLocaleString(undefined, {minimumFractionDigits: 1});
    if (elL) elL.textContent = '$' + l.toLocaleString(undefined, {minimumFractionDigits: 1});
    if (elC) elC.textContent = '$' + cl.toLocaleString(undefined, {minimumFractionDigits: 1});

    if (elChg) {
        elChg.textContent = (chg >= 0 ? '+' : '') + chg.toFixed(2) + '%';
        elChg.className = chg >= 0 ? 'tv-ohlc-up' : 'tv-ohlc-down';
    }
}

chart.subscribeCrosshairMove((param) => {
    if (param && param.time && param.seriesData && param.seriesData.get(mainSeries)) {
        updateOhlcDisplay(param.seriesData.get(mainSeries));
    } else if (typeof candleData !== 'undefined' && Array.isArray(candleData) && candleData.length > 0) {
        updateOhlcDisplay(candleData[candleData.length - 1]);
    }
});

if (typeof candleData !== 'undefined' && Array.isArray(candleData) && candleData.length > 0) {
    updateOhlcDisplay(candleData[candleData.length - 1]);
}
