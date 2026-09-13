// Interactive Drawing Tools & Crosshair Engine
let previewSeries1 = null;
let previewSeries2 = null;
let isDrawing = false;
let startPoint = null;

function showNotification(msg) {
    try {
        const toast = document.getElementById('tv-toast');
        if (!toast) return;
        toast.textContent = msg;
        toast.classList.remove('hidden');
        clearTimeout(window.toastTimer);
        window.toastTimer = setTimeout(() => {
            try { toast.classList.add('hidden'); } catch(e) {}
        }, 2500);
    } catch(e) {}
}

function ensurePreviewSeries() {
    if (!previewSeries1 && typeof chart !== 'undefined' && chart) {
        try {
            previewSeries1 = chart.addLineSeries({
                color: '#FFEA00',
                lineWidth: 2
            });
        } catch(e) {}
    }
    if (!previewSeries2 && typeof chart !== 'undefined' && chart) {
        try {
            previewSeries2 = chart.addLineSeries({
                color: '#FF007F',
                lineWidth: 2
            });
        } catch(e) {}
    }
}

function clearPreviewSeries() {
    if (previewSeries1) { try { previewSeries1.setData([]); } catch(e) {} }
    if (previewSeries2) { try { previewSeries2.setData([]); } catch(e) {} }
}

function resetDrawingState() {
    isDrawing = false;
    startPoint = null;
    clearPreviewSeries();
}

function getEventData(param) {
    if (!param || !param.point || typeof candleData === 'undefined' || !candleData || candleData.length === 0) {
        return null;
    }

    try {
        let idx = null;
        if (typeof chart !== 'undefined' && chart.timeScale) {
            const logical = chart.timeScale().coordinateToLogical(param.point.x);
            if (logical !== null && typeof logical === 'number' && !isNaN(logical)) {
                idx = Math.max(0, Math.min(candleData.length - 1, Math.round(logical)));
            }
        }
        if (idx === null && param.time) {
            idx = candleData.findIndex(c => c.time === param.time);
        }
        if (idx === null || idx < 0) {
            idx = candleData.length - 1;
        }

        const time = candleData[idx].time;

        let price = null;
        if (typeof mainSeries !== 'undefined' && mainSeries && typeof mainSeries.coordinateToPrice === 'function') {
            const p = mainSeries.coordinateToPrice(param.point.y);
            if (p !== null && typeof p === 'number' && !isNaN(p)) {
                price = p;
            }
        }
        if (price === null && typeof container !== 'undefined' && container) {
            const containerH = container.clientHeight || 500;
            const ratio = Math.max(0, Math.min(1, param.point.y / containerH));
            const c = candleData[idx];
            const pHigh = c.high || c.close;
            const pLow = c.low || c.close;
            price = pHigh - (ratio * (pHigh - pLow));
        }

        if (price === null) price = candleData[idx].close;

        return { idx, time, value: price };
    } catch(e) {
        return null;
    }
}

chart.subscribeCrosshairMove(param => {
    try {
        if (!param || !param.point) return;

        if (param.seriesPrices && typeof mainSeries !== 'undefined' && mainSeries) {
            const candlePrice = param.seriesPrices.get(mainSeries);
            if (candlePrice) {
                const oEl = document.getElementById('ohlc-o'); if (oEl) oEl.textContent = candlePrice.open.toLocaleString(undefined, {minimumFractionDigits: 1});
                const hEl = document.getElementById('ohlc-h'); if (hEl) hEl.textContent = candlePrice.high.toLocaleString(undefined, {minimumFractionDigits: 1});
                const lEl = document.getElementById('ohlc-l'); if (lEl) lEl.textContent = candlePrice.low.toLocaleString(undefined, {minimumFractionDigits: 1});
                const cEl = document.getElementById('ohlc-c'); if (cEl) cEl.textContent = candlePrice.close.toLocaleString(undefined, {minimumFractionDigits: 1});
                
                const chg = ((candlePrice.close - candlePrice.open) / candlePrice.open) * 100;
                const chgEl = document.getElementById('ohlc-change');
                if (chgEl) {
                    chgEl.textContent = (chg >= 0 ? '+' : '') + chg.toFixed(2) + '%';
                    chgEl.className = chg >= 0 ? 'tv-ohlc-up' : 'tv-ohlc-down';
                }
            }
            
            if (typeof ema20Series !== 'undefined' && ema20Series) {
                const e20 = param.seriesPrices.get(ema20Series);
                const legE20 = document.getElementById('leg-ema20');
                if (typeof e20 === 'number' && !isNaN(e20) && legE20) legE20.textContent = 'EMA 20: ' + e20.toFixed(1);
            }
            if (typeof ema50Series !== 'undefined' && ema50Series) {
                const e50 = param.seriesPrices.get(ema50Series);
                const legE50 = document.getElementById('leg-ema50');
                if (typeof e50 === 'number' && !isNaN(e50) && legE50) legE50.textContent = 'EMA 50: ' + e50.toFixed(1);
            }
            if (typeof smaSeries !== 'undefined' && smaSeries) {
                const s200 = param.seriesPrices.get(smaSeries);
                const legS200 = document.getElementById('leg-sma200');
                if (typeof s200 === 'number' && !isNaN(s200) && legS200) legS200.textContent = 'SMA 200: ' + s200.toFixed(1);
            }
        }

        if (isDrawing && startPoint && activeTool !== 'cursor') {
            const current = getEventData(param);
            if (!current) return;

            let firstPt = startPoint;
            let secondPt = current;
            if (firstPt.idx > secondPt.idx) {
                firstPt = current;
                secondPt = startPoint;
            }

            let t1 = firstPt.time;
            let t2 = secondPt.time;
            let v1 = firstPt.value;
            let v2 = secondPt.value;

            if (t1 >= t2) {
                t2 = t1 + 1;
            }

            ensurePreviewSeries();

            if (activeTool === 'trendline' && previewSeries1) {
                previewSeries1.setData([{ time: t1, value: v1 }, { time: t2, value: v2 }]);
            } else if (activeTool === 'rect' && previewSeries1 && previewSeries2) {
                const highP = Math.max(startPoint.value, current.value);
                const lowP = Math.min(startPoint.value, current.value);
                previewSeries1.setData([{ time: t1, value: highP }, { time: t2, value: highP }]);
                previewSeries2.setData([{ time: t1, value: lowP }, { time: t2, value: lowP }]);
            }
        }
    } catch(err) {}
});

chart.subscribeClick(param => {
    try {
        if (!param || !param.point || activeTool === 'cursor') return;
        const pt = getEventData(param);
        if (!pt) return;

        if (activeTool === 'ray') {
            const rayLine = chart.addLineSeries({
                color: '#00E5FF',
                lineWidth: 2,
                title: `Ray @ $${pt.value.toFixed(1)}`
            });
            if (candleData && candleData.length > 0) {
                const tStart = candleData[0].time;
                const tEnd = candleData[candleData.length - 1].time;
                rayLine.setData([
                    { time: tStart, value: pt.value },
                    { time: tEnd, value: pt.value }
                ]);
                userSeries.push(rayLine);
                showNotification(`Horizontal Ray placed @ $${pt.value.toLocaleString(undefined, {maximumFractionDigits: 1})}`);
            }
        } else if (activeTool === 'trendline' || activeTool === 'rect') {
            if (!isDrawing || !startPoint) {
                startPoint = pt;
                isDrawing = true;
                ensurePreviewSeries();
                const toolTitle = activeTool === 'trendline' ? 'Trendline Point 1' : 'Rectangle Corner 1';
                showNotification(`${toolTitle} anchored ($${pt.value.toLocaleString(undefined, {maximumFractionDigits: 1})}). Move cursor & click Point 2.`);
            } else {
                const endPoint = pt;
                clearPreviewSeries();

                let firstPt = startPoint;
                let secondPt = endPoint;
                if (firstPt.idx > secondPt.idx) {
                    firstPt = endPoint;
                    secondPt = startPoint;
                }

                let t1 = firstPt.time;
                let t2 = secondPt.time;
                let v1 = firstPt.value;
                let v2 = secondPt.value;

                if (t1 >= t2) {
                    t2 = t1 + 3600;
                }

                try {
                    if (activeTool === 'trendline') {
                        const tLine = chart.addLineSeries({ color: '#FFEA00', lineWidth: 2, title: 'Trendline' });
                        tLine.setData([{ time: t1, value: v1 }, { time: t2, value: v2 }]);
                        userSeries.push(tLine);
                        showNotification('Trendline created!');
                    } else if (activeTool === 'rect') {
                        const highP = Math.max(startPoint.value, endPoint.value);
                        const lowP = Math.min(startPoint.value, endPoint.value);

                        const rectTop = chart.addLineSeries({ color: '#FF007F', lineWidth: 2 });
                        const rectBot = chart.addLineSeries({ color: '#FF007F', lineWidth: 2 });

                        rectTop.setData([{ time: t1, value: highP }, { time: t2, value: highP }]);
                        rectBot.setData([{ time: t1, value: lowP }, { time: t2, value: lowP }]);

                        userSeries.push(rectTop);
                        userSeries.push(rectBot);
                        if (typeof inspectBoxRegion === 'function') {
                            inspectBoxRegion(t1, t2, highP, lowP);
                        } else {
                            showNotification('Rectangle Zone created!');
                        }
                    }
                } catch(err) {
                    console.error('Drawing error:', err);
                }

                isDrawing = false;
                startPoint = null;
                clearPreviewSeries();
            }
        }
    } catch(e) {
        resetDrawingState();
    }
});

function selectTool(toolName) {
    try {
        activeTool = toolName;
        resetDrawingState();

        const chartBox = document.getElementById('chart-container');
        if (chartBox) {
            chartBox.style.cursor = toolName !== 'cursor' ? 'crosshair' : 'default';
        }

        document.querySelectorAll('.tv-tool-btn').forEach(btn => btn.classList.remove('active'));
        const btn = document.getElementById('tool-' + toolName);
        if (btn) btn.classList.add('active');
        
        if (toolName === 'ray') showNotification('Ray Tool active: Click chart to place Horizontal Ray.');
        if (toolName === 'trendline') showNotification('Trendline Tool active: Click Point 1 on chart.');
        if (toolName === 'rect') showNotification('Rectangle Tool active: Click Corner 1 on chart.');
        if (toolName === 'cursor') showNotification('Cursor Tool active: Normal pan & zoom mode.');
    } catch(e) {}
}

function clearUserDrawings() {
    try {
        resetDrawingState();
        userSeries.forEach(s => {
            try { chart.removeSeries(s); } catch(e) {}
        });
        userSeries = [];
        showNotification('Cleared all custom drawings.');
    } catch(e) {}
}

function switchTab(tabName) {
    try {
        const auditBtn = document.getElementById('tab-audit-btn');
        const inspectorBtn = document.getElementById('tab-inspector-btn');
        const auditTab = document.getElementById('tab-audit');
        const inspectorTab = document.getElementById('tab-inspector');

        if (tabName === 'inspector') {
            if (auditBtn) auditBtn.classList.remove('active');
            if (inspectorBtn) inspectorBtn.classList.add('active');
            if (auditTab) auditTab.classList.add('hidden');
            if (inspectorTab) inspectorTab.classList.remove('hidden');

            if (typeof renderTAPattern === 'function') {
                const modSelect = document.getElementById('taModuleSelect');
                renderTAPattern(modSelect ? modSelect.value : 'all');
            }
        } else {
            if (inspectorBtn) inspectorBtn.classList.remove('active');
            if (auditBtn) auditBtn.classList.add('active');
            if (inspectorTab) inspectorTab.classList.add('hidden');
            if (auditTab) auditTab.classList.remove('hidden');

            if (typeof clearTAPatternOverlays === 'function') {
                clearTAPatternOverlays();
            }
            if (typeof currentStrategyKey !== 'undefined' && typeof loadStrategy === 'function') {
                const stratSelect = document.getElementById('strategySelect');
                const key = (stratSelect && stratSelect.value) ? stratSelect.value : currentStrategyKey;
                loadStrategy(key);
            }
        }
    } catch(e) {}
}
