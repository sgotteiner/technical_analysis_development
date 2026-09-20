// Strategy Setup Inspection & Audit Sidebar Handlers
let activeBoxTopSeries = null;
let activeBoxBottomSeries = null;
let activeBoxLeftSeries = null;
let activeBoxRightSeries = null;

function focusTrade(inputIdx) {
    let idx = parseInt(inputIdx, 10);
    if (isNaN(idx)) idx = 0;

    if (activeBoxTopSeries) { try { chart.removeSeries(activeBoxTopSeries); } catch(e) {} activeBoxTopSeries = null; }
    if (activeBoxBottomSeries) { try { chart.removeSeries(activeBoxBottomSeries); } catch(e) {} activeBoxBottomSeries = null; }
    if (activeBoxLeftSeries) { try { chart.removeSeries(activeBoxLeftSeries); } catch(e) {} activeBoxLeftSeries = null; }
    if (activeBoxRightSeries) { try { chart.removeSeries(activeBoxRightSeries); } catch(e) {} activeBoxRightSeries = null; }

    const stratTrades = (multiStrategyData[currentStrategyKey] && Array.isArray(multiStrategyData[currentStrategyKey].trades)) ? multiStrategyData[currentStrategyKey].trades : [];
    
    if (stratTrades.length === 0 || idx < 0 || idx >= stratTrades.length) {
        try { chart.timeScale().fitContent(); } catch(e) {}
        const titleEl = document.getElementById('card-title');
        if (titleEl) titleEl.textContent = 'Strategy Overview';
        const badgeEl = document.getElementById('card-badge');
        if (badgeEl) {
            badgeEl.textContent = 'Overview Mode';
            badgeEl.className = 'tv-badge tv-badge-win';
        }
        return;
    }

    const t = stratTrades[idx] || {};
    currentTradeIdx = idx;

    const tradeId = t.id || (idx + 1);
    const entryTimeStr = t.entryTime || 'N/A';
    const entryP = (typeof t.entryPrice === 'number' && !isNaN(t.entryPrice)) ? t.entryPrice : 0.0;
    const exitP = (typeof t.exitPrice === 'number' && !isNaN(t.exitPrice)) ? t.exitPrice : 0.0;
    const retPct = (typeof t.returnPct === 'number' && !isNaN(t.returnPct)) ? t.returnPct : 0.0;
    const durHours = (typeof t.duration === 'number' && !isNaN(t.duration)) ? t.duration : 0.0;

    // Preserve regular chart zoom & candle size completely across all timeframes

    let t1 = (t.boxTop && Array.isArray(t.boxTop) && t.boxTop.length >= 2) ? t.boxTop[0].time : t.fromTime;
    let t2 = (t.boxTop && Array.isArray(t.boxTop) && t.boxTop.length >= 2) ? t.boxTop[t.boxTop.length - 1].time : t.toTime;

    let highP = Math.max(entryP, exitP);
    let lowP = Math.min(entryP, exitP);
    if (highP === lowP || isNaN(highP) || isNaN(lowP) || highP <= 0 || lowP <= 0) {
        const refP = (entryP > 0) ? entryP : (exitP > 0 ? exitP : 50000);
        highP = refP * 1.002;
        lowP = refP * 0.998;
    }

    if (t1 && t2 && t1 < t2) {
        const boxColor = '#8b5cf6'; // Always Light Purple / Light Blue

        try {
            activeBoxTopSeries = chart.addLineSeries({ color: boxColor, lineWidth: 2, lineStyle: LightweightCharts.LineStyle.Solid, title: 'Trade Box Top' });
            activeBoxTopSeries.setData([{ time: t1, value: highP }, { time: t2, value: highP }]);

            activeBoxBottomSeries = chart.addLineSeries({ color: boxColor, lineWidth: 2, lineStyle: LightweightCharts.LineStyle.Solid, title: 'Trade Box Bottom' });
            activeBoxBottomSeries.setData([{ time: t1, value: lowP }, { time: t2, value: lowP }]);

            activeBoxLeftSeries = chart.addLineSeries({ color: boxColor, lineWidth: 2, lineStyle: LightweightCharts.LineStyle.Solid, title: 'Trade Box Left' });
            activeBoxLeftSeries.setData([{ time: t1, value: lowP }, { time: t1, value: highP }]);

            activeBoxRightSeries = chart.addLineSeries({ color: boxColor, lineWidth: 2, lineStyle: LightweightCharts.LineStyle.Solid, title: 'Trade Box Right' });
            activeBoxRightSeries.setData([{ time: t2, value: lowP }, { time: t2, value: highP }]);
        } catch(e) {}
    }

    // Smoothly scroll chart to center the active trade on screen
    if (typeof mainSeries !== 'undefined' && typeof chart !== 'undefined' && t1 && t2) {
        try {
            const curData = mainSeries.data();
            if (Array.isArray(curData) && curData.length > 0) {
                let entryIdx = -1;
                let exitIdx = -1;
                for (let i = 0; i < curData.length; i++) {
                    const cdTime = (typeof curData[i].time === 'number') ? curData[i].time : 0;
                    if (entryIdx === -1 && cdTime >= t1) entryIdx = i;
                    if (cdTime <= t2) exitIdx = i;
                }
                if (entryIdx === -1) entryIdx = 0;
                if (exitIdx < entryIdx) exitIdx = entryIdx;

                const midIdx = Math.floor((entryIdx + exitIdx) / 2);
                const containerW = (typeof container !== 'undefined' && container && container.clientWidth > 0) ? container.clientWidth : 1200;
                const targetSpacing = 7;
                const fitBars = Math.max(20, Math.floor(containerW / targetSpacing));
                const halfFit = Math.floor(fitBars / 2);

                const fromBar = Math.max(0, midIdx - halfFit);
                const toBar = fromBar + fitBars;

                chart.timeScale().setVisibleLogicalRange({
                    from: fromBar,
                    to: toBar
                });
            }
        } catch(e) {}
    }

    try {
        const titleEl = document.getElementById('card-title');
        if (titleEl) titleEl.textContent = `Trade #${tradeId}`;
        
        const badgeEl = document.getElementById('card-badge');
        if (badgeEl) {
            badgeEl.textContent = (retPct >= 0 ? '+' : '') + retPct.toFixed(1) + '%';
            badgeEl.className = 'tv-badge ' + (retPct >= 0 ? 'tv-badge-win' : 'tv-badge-loss');
        }

        const counterEl = document.getElementById('trade-counter');
        if (counterEl) counterEl.textContent = `Trade ${idx + 1} of ${stratTrades.length}`;

        const entryEl = document.getElementById('card-entry');
        if (entryEl) entryEl.textContent = '$' + entryP.toLocaleString(undefined, {minimumFractionDigits: 1});
        
        const entryTimeEl = document.getElementById('card-entry-time');
        if (entryTimeEl) entryTimeEl.textContent = entryTimeStr;

        const exitEl = document.getElementById('card-exit');
        if (exitEl) exitEl.textContent = '$' + exitP.toLocaleString(undefined, {minimumFractionDigits: 1});
        
        const exitTimeEl = document.getElementById('card-exit-time');
        if (exitTimeEl) exitTimeEl.textContent = t.exitTime || 'N/A';

        const durEl = document.getElementById('card-duration');
        if (durEl) durEl.textContent = durHours + ' Hours (' + (durHours / 24.0).toFixed(1) + ' Days)';
        
        const resEl = document.getElementById('card-result');
        if (resEl) {
            resEl.textContent = (retPct >= 0 ? '+' : '') + retPct.toFixed(1) + '%';
            resEl.style.color = retPct >= 0 ? '#089981' : '#f23645';
        }
        
        const selectEl = document.getElementById('tradeSelect');
        if (selectEl && selectEl.value != idx) {
            selectEl.value = idx;
        }
    } catch(err) {}
}

function loadStrategy(stratKey) {
    currentStrategyKey = stratKey;
    const stratData = multiStrategyData[stratKey];
    if (!stratData) return;

    const retEl = document.getElementById('stat-return');
    if (retEl && stratData.stats && typeof stratData.stats.return === 'number') {
        retEl.textContent = (stratData.stats.return >= 0 ? '+' : '') + stratData.stats.return.toFixed(2) + '%';
        retEl.style.color = stratData.stats.return >= 0 ? '#089981' : '#f23645';
    }
    const winEl = document.getElementById('stat-winrate');
    if (winEl && stratData.stats && typeof stratData.stats.winRate === 'number') {
        winEl.textContent = stratData.stats.winRate.toFixed(1) + '%';
    }
    const tradesEl = document.getElementById('stat-trades');
    if (tradesEl && stratData.stats && typeof stratData.stats.numTrades === 'number') {
        tradesEl.textContent = stratData.stats.numTrades;
    }
    const medianEl = document.getElementById('stat-median');
    if (medianEl && stratData.stats && typeof stratData.stats.medianReturn === 'number') {
        medianEl.textContent = (stratData.stats.medianReturn >= 0 ? '+' : '') + stratData.stats.medianReturn.toFixed(2) + '%';
        medianEl.style.color = stratData.stats.medianReturn >= 0 ? '#8b5cf6' : '#f23645';
    }
    const meanEl = document.getElementById('stat-mean');
    if (meanEl && stratData.stats && typeof stratData.stats.meanReturn === 'number') {
        meanEl.textContent = (stratData.stats.meanReturn >= 0 ? '+' : '') + stratData.stats.meanReturn.toFixed(2) + '%';
    }
    const minmaxEl = document.getElementById('stat-minmax');
    if (minmaxEl && stratData.stats && typeof stratData.stats.minReturn === 'number' && typeof stratData.stats.maxReturn === 'number') {
        minmaxEl.textContent = `${stratData.stats.minReturn.toFixed(1)}% / +${stratData.stats.maxReturn.toFixed(1)}%`;
    }

    try { mainSeries.setMarkers(stratData.markers || []); } catch(e) {}

    const selectEl = document.getElementById('tradeSelect');
    if (selectEl) {
        selectEl.innerHTML = '';
        if (!stratData.trades || !Array.isArray(stratData.trades) || stratData.trades.length === 0) {
            const opt = document.createElement('option');
            opt.value = "-1";
            opt.textContent = "-- Strategy Overview --";
            selectEl.appendChild(opt);
            focusTrade(-1);
        } else {
            stratData.trades.forEach((t, i) => {
                const opt = document.createElement('option');
                opt.value = i;
                const retVal = (typeof t.returnPct === 'number') ? t.returnPct : 0;
                const sign = retVal >= 0 ? '+' : '';
                opt.textContent = `Trade #${t.id || (i+1)} (${sign}${retVal.toFixed(1)}%)`;
                selectEl.appendChild(opt);
            });
            selectEl.value = 0;
            currentTradeIdx = 0;
            focusTrade(0);
        }
    }
}

function onStrategySelected(val) { loadStrategy(val); }
function onTradeSelected(val) { const idx = parseInt(val, 10); if (!isNaN(idx)) focusTrade(idx); }

function nextTrade() {
    let idx = parseInt(currentTradeIdx, 10);
    if (isNaN(idx)) idx = 0;
    const stratTrades = (multiStrategyData[currentStrategyKey] && Array.isArray(multiStrategyData[currentStrategyKey].trades)) ? multiStrategyData[currentStrategyKey].trades : [];
    if (idx < stratTrades.length - 1) focusTrade(idx + 1);
}

function prevTrade() {
    let idx = parseInt(currentTradeIdx, 10);
    if (isNaN(idx)) idx = 0;
    if (idx > 0) focusTrade(idx - 1);
}
