// Timeframe Resampling, Multi-Timeframe Loading & Window Lifecycle Handlers

function showLoading(text) {
    const overlay = document.getElementById('tv-loading-overlay');
    const textEl = document.getElementById('tv-loading-text');
    if (textEl) textEl.textContent = text || 'Loading Candles...';
    if (overlay) overlay.classList.remove('hidden');
}

function hideLoading() {
    const overlay = document.getElementById('tv-loading-overlay');
    if (overlay) overlay.classList.add('hidden');
}

function getBucketTime(t, sec) {
    let b = Math.floor(t / sec) * sec;
    if (sec === 604800) {
        b = Math.floor((t - 345600) / 604800) * 604800 + 345600;
    }
    return b;
}

function aggregateLineSeries(data, sec) {
    if (!data || !Array.isArray(data)) return [];
    const aggMap = new Map();
    data.forEach(d => {
        if (!d) return;
        const rawTime = (typeof d.time === 'number') ? d.time : Math.floor(new Date(d.time).getTime() / 1000);
        if (isNaN(rawTime)) return;
        const bucket = getBucketTime(rawTime, sec);
        aggMap.set(bucket, d.value);
    });
    const result = [];
    aggMap.forEach((val, time) => {
        if (typeof val === 'number' && !isNaN(val)) {
            result.push({ time: time, value: val });
        }
    });
    result.sort((a, b) => a.time - b.time);
    return result;
}

function setTimeframe(tf) {
    const key = tf.toLowerCase();
    showLoading(`Rendering ${tf.toUpperCase()} Candle Chart...`);

    setTimeout(() => {
        document.querySelectorAll('.tv-tf-btn').forEach(btn => btn.classList.remove('active'));
        const btn = document.getElementById('tf-' + key);
        if (btn) btn.classList.add('active');

        let sec = 3600;
        if (key === '5m') sec = 300;
        if (key === '1h') sec = 3600;
        if (key === '4h') sec = 14400;
        if (key === '1d') sec = 86400;
        if (key === '1w') sec = 604800;

        const tfObj = (typeof timeframeData !== 'undefined' && timeframeData[key]) ? timeframeData[key] : null;

        let aggCandles = [];
        let aggVol = [];

        if (tfObj && tfObj.candles && Array.isArray(tfObj.candles) && tfObj.candles.length > 0) {
            aggCandles = tfObj.candles;
            aggVol = tfObj.volume || [];
        } else {
            let curC = null;
            let curV = null;
            candleData.forEach((c, idx) => {
                const bucket = getBucketTime(c.time, sec);
                const v = volumeData[idx];
                if (!curC || curC.time !== bucket) {
                    if (curC) { aggCandles.push(curC); aggVol.push(curV); }
                    curC = { time: bucket, open: c.open, high: c.high, low: c.low, close: c.close };
                    curV = { time: bucket, value: v ? v.value : 0, color: c.close >= c.open ? 'rgba(8, 153, 129, 0.35)' : 'rgba(242, 54, 69, 0.35)' };
                } else {
                    curC.high = Math.max(curC.high, c.high);
                    curC.low = Math.min(curC.low, c.low);
                    curC.close = c.close;
                    if (v) curV.value += v.value;
                    curV.color = curC.close >= curC.open ? 'rgba(8, 153, 129, 0.35)' : 'rgba(242, 54, 69, 0.35)';
                }
            });
            if (curC) { aggCandles.push(curC); aggVol.push(curV); }
        }

        mainSeries.setData(aggCandles);
        volumeSeries.setData(aggVol);

        // 2. Resample Indicators & Dotted Lines in lockstep
        let resampledEma20 = aggregateLineSeries(typeof ema20Data !== 'undefined' ? ema20Data : [], sec);
        let resampledEma50 = aggregateLineSeries(typeof ema50Data !== 'undefined' ? ema50Data : [], sec);
        let resampledSma200 = aggregateLineSeries(typeof sma200Data !== 'undefined' ? sma200Data : [], sec);
        let resampledRsi = aggregateLineSeries(typeof rsiData !== 'undefined' ? rsiData : [], sec);
        let resampledAdx = aggregateLineSeries(typeof adxData !== 'undefined' ? adxData : [], sec);

        if (key === '1w' && aggCandles.length > 0) {
            const mapWTimes = (seriesArr) => {
                if (!seriesArr || seriesArr.length === 0) return [];
                return seriesArr.map((d, idx) => ({
                    time: aggCandles[Math.min(idx, aggCandles.length - 1)].time,
                    value: d.value
                }));
            };
            resampledEma20 = mapWTimes(resampledEma20);
            resampledEma50 = mapWTimes(resampledEma50);
            resampledSma200 = mapWTimes(resampledSma200);
            resampledRsi = mapWTimes(resampledRsi);
            resampledAdx = mapWTimes(resampledAdx);
        }

        if (typeof ema20Series !== 'undefined' && ema20Series) ema20Series.setData(resampledEma20);
        if (typeof ema50Series !== 'undefined' && ema50Series) ema50Series.setData(resampledEma50);
        if (typeof smaSeries !== 'undefined' && smaSeries) smaSeries.setData(resampledSma200);
        if (typeof rsiSeries !== 'undefined' && rsiSeries) rsiSeries.setData(resampledRsi);
        if (typeof adxSeries !== 'undefined' && adxSeries) adxSeries.setData(resampledAdx);

        if (typeof rsi50Series !== 'undefined' && rsi50Series) {
            rsi50Series.setData(resampledRsi.map(d => ({ time: d.time, value: 50.0 })));
        }
        if (typeof adx20Series !== 'undefined' && adx20Series) {
            adx20Series.setData(resampledAdx.map(d => ({ time: d.time, value: 20.0 })));
        }

        // 3. Resample Markers
        if (multiStrategyData[currentStrategyKey] && multiStrategyData[currentStrategyKey].markers) {
            const rawMarkers = multiStrategyData[currentStrategyKey].markers;
            const resampledMarkers = [];
            const seenKeys = new Set();
            const hData = (typeof candleData !== 'undefined') ? candleData : [];
            const firstT = (hData.length > 0) ? hData[0].time : 0;
            const lastT = (hData.length > 0) ? hData[hData.length - 1].time : 1;
            const span = Math.max(1, lastT - firstT);

            rawMarkers.forEach(m => {
                let mappedTime = m.time;
                if (key === '1w' && aggCandles.length > 0) {
                    const ratio = Math.max(0, Math.min(1, (m.time - firstT) / span));
                    const cIdx = Math.min(aggCandles.length - 1, Math.floor(ratio * aggCandles.length));
                    mappedTime = aggCandles[cIdx].time;
                } else {
                    mappedTime = getBucketTime(m.time, sec);
                }

                const keyStr = mappedTime + '_' + m.position + '_' + (m.shape || '') + '_' + (m.text || '');
                if (!seenKeys.has(keyStr)) {
                    seenKeys.add(keyStr);
                    resampledMarkers.push({ ...m, time: mappedTime });
                }
            });

            resampledMarkers.sort((a, b) => a.time - b.time);
            mainSeries.setMarkers(resampledMarkers);
        }

        // 4. Uniform Dynamic Candle Scaling across ALL Timeframes
        const totalBars = aggCandles.length;
        if (totalBars > 0) {
            const containerWidth = (typeof container !== 'undefined' && container && container.clientWidth > 0) ? container.clientWidth : 1200;
            const targetBarSpacing = 7;
            const fitBars = Math.max(20, Math.floor(containerWidth / targetBarSpacing));

            chart.timeScale().applyOptions({
                barSpacing: targetBarSpacing,
                minBarSpacing: 2,
                rightOffset: 5
            });

            chart.timeScale().setVisibleLogicalRange({
                from: Math.max(0, totalBars - fitBars),
                to: totalBars + 5
            });
        }

        // 5. Re-draw active trade box on active timeframe
        if (typeof focusTrade === 'function' && typeof currentTradeIdx === 'number') {
            focusTrade(currentTradeIdx);
        }

        hideLoading();
    }, 25);
}

window.addEventListener('resize', () => {
    chart.applyOptions({ width: container.clientWidth, height: container.clientHeight });
});

function initApp() {
    loadStrategy('daily_supertrend');
}

if (document.readyState === 'complete' || document.readyState === 'interactive') {
    setTimeout(initApp, 50);
} else {
    document.addEventListener('DOMContentLoaded', () => setTimeout(initApp, 50));
}
