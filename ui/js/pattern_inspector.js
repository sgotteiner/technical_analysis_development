// --- TA Module & Pattern Inspector Engine (Current Visible Screen Dynamic Overlays) ---
let activeTAPatternKey = 'hammer';
let visibleScreenInstances = [];

// Dynamic series lists for visible screen shapes
let activeScreenSeries = [];

function clearTAPatternOverlays() {
    try {
        activeScreenSeries.forEach(s => {
            try { chart.removeSeries(s); } catch(e) {}
        });
        activeScreenSeries = [];

        if (typeof mainSeries !== 'undefined' && mainSeries) {
            try { mainSeries.setMarkers([]); } catch(e) {}
        }
    } catch(e) {}
}

function renderTAPattern(patternKey) {
    activeTAPatternKey = patternKey || 'hammer';
    updateVisibleScreenPatterns();
}

function updateVisibleScreenPatterns() {
    if (typeof chart === 'undefined' || !chart || typeof taModulesData === 'undefined' || !taModulesData) return;
    try {
        const inspectorTab = document.getElementById('tab-inspector');
        if (inspectorTab && inspectorTab.classList.contains('hidden')) {
            return;
        }

        clearTAPatternOverlays();

        const range = chart.timeScale().getVisibleRange();
        if (!range || !range.from || !range.to) return;

        const minT = typeof range.from === 'number' ? range.from : (range.from.timestamp ? range.from.timestamp : 0);
        const maxT = typeof range.to === 'number' ? range.to : (range.to.timestamp ? range.to.timestamp : 9999999999);

        let moduleInstances = [];
        if (taModulesData[activeTAPatternKey]) {
            moduleInstances = taModulesData[activeTAPatternKey].instances || [];
        } else if (activeTAPatternKey === 'all') {
            Object.keys(taModulesData).forEach(k => {
                if (taModulesData[k] && taModulesData[k].instances) {
                    moduleInstances = moduleInstances.concat(taModulesData[k].instances);
                }
            });
        }

        visibleScreenInstances = moduleInstances.filter(inst => inst.time >= minT && inst.time <= maxT);

        // Draw Markers for Screen Instances
        let markers = [];
        visibleScreenInstances.slice(0, 150).forEach(inst => {
            markers.push({
                time: inst.time,
                position: 'aboveBar',
                color: '#8b5cf6',
                shape: 'arrowDown',
                text: ''
            });

            // Draw Resistance Trendline
            if (inst.res && inst.res.length > 1) {
                const resLine = chart.addLineSeries({ color: '#f23645', lineWidth: 2, title: `${inst.label} Res` });
                resLine.setData(inst.res);
                activeScreenSeries.push(resLine);
            }

            // Draw Support Trendline
            if (inst.sup && inst.sup.length > 1) {
                const supLine = chart.addLineSeries({ color: '#089981', lineWidth: 2, title: `${inst.label} Sup` });
                supLine.setData(inst.sup);
                activeScreenSeries.push(supLine);
            }

            // Draw Translucent Box Bounds
            if (inst.startTime && inst.endTime && inst.priceHigh && inst.priceLow) {
                let t1 = inst.startTime;
                let t2 = inst.endTime;
                if (t1 >= t2) t2 = t1 + 3600;

                const boxTop = chart.addLineSeries({ color: '#8b5cf6', lineWidth: 1, lineStyle: 2 });
                const boxBot = chart.addLineSeries({ color: '#8b5cf6', lineWidth: 1, lineStyle: 2 });
                boxTop.setData([{ time: t1, value: inst.priceHigh }, { time: t2, value: inst.priceHigh }]);
                boxBot.setData([{ time: t1, value: inst.priceLow }, { time: t2, value: inst.priceLow }]);

                activeScreenSeries.push(boxTop);
                activeScreenSeries.push(boxBot);
            }
        });

        if (typeof mainSeries !== 'undefined' && mainSeries) {
            try { mainSeries.setMarkers(markers); } catch(e) {}
        }
    } catch(e) {}
}

function inspectBoxRegion(t1, t2, v1, v2) {
    const minT = Math.min(t1, t2);
    const maxT = Math.max(t1, t2);
    const minV = Math.min(v1, v2);
    const maxV = Math.max(v1, v2);

    let moduleInstances = [];
    if (typeof taModulesData !== 'undefined') {
        Object.keys(taModulesData).forEach(k => {
            if (taModulesData[k] && taModulesData[k].instances) {
                moduleInstances = moduleInstances.concat(taModulesData[k].instances);
            }
        });
    }

    const filtered = moduleInstances.filter(inst => {
        const tMatch = inst.time >= minT && inst.time <= maxT;
        return tMatch;
    });

    clearTAPatternOverlays();
    let markers = [];
    filtered.slice(0, 100).forEach(inst => {
        markers.push({ time: inst.time, position: 'aboveBar', color: '#8b5cf6', shape: 'arrowDown', text: '' });
        if (inst.res && inst.res.length > 1) {
            const resLine = chart.addLineSeries({ color: '#f23645', lineWidth: 2 });
            resLine.setData(inst.res);
            activeScreenSeries.push(resLine);
        }
        if (inst.sup && inst.sup.length > 1) {
            const supLine = chart.addLineSeries({ color: '#089981', lineWidth: 2 });
            supLine.setData(inst.sup);
            activeScreenSeries.push(supLine);
        }
    });

    if (typeof mainSeries !== 'undefined' && mainSeries) {
        try { mainSeries.setMarkers(markers); } catch(e) {}
    }

    if (typeof showNotification === 'function') {
        showNotification(`Box Region Audited: ${filtered.length} pattern(s) detected inside box!`);
    }
}

// Auto-update visible screen drawings on chart pan/zoom
setTimeout(() => {
    if (typeof chart !== 'undefined' && chart && chart.timeScale) {
        try {
            chart.timeScale().subscribeVisibleTimeRangeChange(() => {
                updateVisibleScreenPatterns();
            });
        } catch(e) {}
    }
}, 1000);
