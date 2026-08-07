// indices.js — ByteMind Indices
// Data sources: BIS, OECD, RBNZ, Stats NZ

document.addEventListener('DOMContentLoaded', function () {

    // Theme colours — match the ByteMind green editorial palette
    var accent = '#1a3a2a';      // deep forest green
    var accent2 = '#4d8763';     // mid green
    var warn = '#9e6b1f';        // warm amber
    var error = '#a23b32';       // muted red
    var muted = '#6a6760';       // muted text
    var rule = '#e2ddd1';        // border
    var ink = '#1f1e1a';         // near-black text
    var font = 'Inter, system-ui, sans-serif';

    var charts = [];

    function setOption(domId, option) {
        var dom = document.getElementById(domId);
        if (!dom) return;
        var chart = echarts.init(dom, null, { renderer: 'svg' });
        option.textStyle = { fontFamily: font, color: muted };
        chart.setOption(option);
        charts.push(chart);
    }

    function resizeCharts() {
        charts.forEach(function (chart) { chart.resize(); });
    }
    window.resizeCharts = resizeCharts;

    window.addEventListener('resize', resizeCharts);
    // Charts that start inside hidden tabs/panels init at a tiny width.
    // Re-measure after the page settles so every chart fills its container.
    setTimeout(resizeCharts, 120);

    function renderTable(domId, columns, rows) {
        var dom = document.getElementById(domId);
        if (!dom) return;
        var html = '<table><thead><tr>';
        columns.forEach(function (c) { html += '<th>' + c + '</th>'; });
        html += '</tr></thead><tbody>';
        rows.forEach(function (row) {
            html += '<tr>';
            row.forEach(function (cell) { html += '<td>' + (cell != null ? cell : '') + '</td>'; });
            html += '</tr>';
        });
        html += '</tbody></table>';
        dom.innerHTML = html;
    }

    // Shared axis styles
    function catAxis(data) {
        return {
            type: 'category',
            data: data,
            axisLabel: { color: muted, fontSize: 11, hideOverlap: true },
            axisLine: { lineStyle: { color: rule } },
            axisTick: { show: false }
        };
    }
    function valAxis(name, extra) {
        return Object.assign({
            type: 'value',
            name: name,
            nameTextStyle: { color: muted },
            axisLabel: { color: muted, fontSize: 11 },
            splitLine: { lineStyle: { color: rule } }
        }, extra || {});
    }
    function shadowTooltip() {
        return { trigger: 'axis', appendToBody: true, axisPointer: { type: 'shadow' } };
    }
    function lineTooltip() {
        return { trigger: 'axis', appendToBody: true, axisPointer: { type: 'line' } };
    }

    // ============================================================
    // Housing — 1. NZ & AU Real HPI (BIS 2010=100)
    // ============================================================
    var hpiData = [
        [1970, 40, 44], [1975, 48, 50], [1980, 48, 52], [1985, 55, 56], [1990, 60, 58],
        [1995, 68, 62], [2000, 72, 68], [2005, 90, 85], [2010, 100, 100], [2015, 120, 112],
        [2018, 138, 122], [2019, 142, 118], [2020, 155, 125], [2021, 178, 140], [2022, 168, 138],
        [2023, 168, 135], [2024, 163, 138], [2025, 159, 141]
    ];
    var hpiYears = hpiData.map(function (d) { return d[0] + ''; });
    var nzHpi = hpiData.map(function (d) { return d[1]; });
    var auHpi = hpiData.map(function (d) { return d[2]; });

    setOption('chart-hpi', {
        tooltip: lineTooltip(),
        legend: { data: ['New Zealand', 'Australia'], top: 0, textStyle: { color: muted } },
        grid: { left: 48, right: 24, top: 44, bottom: 40 },
        xAxis: catAxis(hpiYears),
        yAxis: valAxis('Index (2010=100)'),
        color: [accent, accent2],
        series: [
            { name: 'New Zealand', type: 'line', data: nzHpi, smooth: true, lineStyle: { width: 2.5 }, symbol: 'circle', symbolSize: 5 },
            { name: 'Australia', type: 'line', data: auHpi, smooth: true, lineStyle: { width: 2.5 }, symbol: 'circle', symbolSize: 5 }
        ]
    });

    renderTable('hpi-table', ['Year', 'NZ Real HPI', 'AU Real HPI'],
        hpiData.map(function (d) { return [d[0], d[1], d[2]]; }));

    // ============================================================
    // Housing — 2. Valuation Metrics
    // ============================================================
    var valData = [
        [1986, 56, null, null, null], [1988, 58, null, null, null], [1990, 60, -12, null, null],
        [1992, 55, -15, null, null], [1994, 57, -10, null, null], [1996, 62, -5, null, null],
        [1998, 64, -8, null, null], [2000, 63, -10, 7.8, 95], [2002, 72, -6, 7.5, 105],
        [2004, 86, 2, 7.8, 115], [2006, 93, 12, 8.5, 125], [2008, 88, 5, 9.0, 140],
        [2010, 89, 0, 7.4, 145], [2012, 94, 2, 5.8, 142], [2014, 100, 8, 5.9, 145],
        [2016, 112, 18, 5.0, 155], [2018, 118, 22, 5.0, 160], [2019, 122, 24, 4.5, 162],
        [2020, 132, 30, 3.0, 165], [2021, 142.9, 38, 2.8, 170], [2022, 135, 28, 5.5, 170],
        [2023, 117, 20, 7.2, 168], [2024, 107.3, 12, 7.6, 167], [2025, 105.8, 8, 5.3, 165]
    ];
    var ptiYears = valData.map(function (d) { return d[0] + ''; });
    var ptiVals = valData.map(function (d) { return d[1]; });
    var medianVal = 88.9;

    setOption('chart-pti', {
        tooltip: lineTooltip(),
        legend: { data: ['Price-to-Income', 'Long-Run Median'], top: 0, textStyle: { color: muted } },
        grid: { left: 48, right: 24, top: 44, bottom: 40 },
        xAxis: catAxis(ptiYears),
        yAxis: valAxis('Index (2015=100)'),
        color: [accent, muted],
        series: [
            {
                name: 'Price-to-Income', type: 'line', data: ptiVals, smooth: true,
                lineStyle: { width: 2.5 }, symbol: 'circle', symbolSize: 5,
                areaStyle: { color: accent2, opacity: 0.12 }
            },
            { name: 'Long-Run Median', type: 'line', data: Array(ptiYears.length).fill(medianVal), lineStyle: { color: muted, type: 'dashed', width: 1.5 }, symbol: 'none' }
        ]
    });

    var devYears = valData.filter(function (d) { return d[2] != null; }).map(function (d) { return d[0] + ''; });
    var devVals = valData.filter(function (d) { return d[2] != null; }).map(function (d) { return d[2]; });

    setOption('chart-deviation', {
        tooltip: shadowTooltip(),
        grid: { left: 48, right: 24, top: 24, bottom: 40 },
        xAxis: catAxis(devYears),
        yAxis: valAxis('Deviation (%)'),
        series: [{
            name: 'Deviation from Trend', type: 'bar', barWidth: '62%',
            data: devVals.map(function (v) {
                return { value: v, itemStyle: { color: v >= 0 ? error : accent2, borderRadius: [3, 3, 0, 0] } };
            }),
            markLine: { silent: true, symbol: 'none', lineStyle: { color: muted, type: 'dashed' }, data: [{ yAxis: 0 }] }
        }]
    });

    var rateYears = valData.filter(function (d) { return d[3] != null; }).map(function (d) { return d[0] + ''; });
    var rateVals = valData.filter(function (d) { return d[3] != null; }).map(function (d) { return d[3]; });
    var dtiVals = valData.filter(function (d) { return d[3] != null; }).map(function (d) { return d[4]; });

    setOption('chart-rates-dti', {
        tooltip: lineTooltip(),
        legend: { data: ['1-Year Fixed Rate (%)', 'Debt-to-Income (% of income)'], top: 0, textStyle: { color: muted } },
        grid: { left: 48, right: 56, top: 44, bottom: 40 },
        xAxis: catAxis(rateYears),
        yAxis: [
            valAxis('Rate (%)'),
            Object.assign(valAxis('DTI (% of income)'), { splitLine: { show: false } })
        ],
        color: [accent, warn],
        series: [
            { name: '1-Year Fixed Rate (%)', type: 'line', data: rateVals, smooth: true, lineStyle: { width: 2.5 }, symbol: 'circle', symbolSize: 5 },
            { name: 'Debt-to-Income (% of income)', type: 'line', yAxisIndex: 1, data: dtiVals, smooth: true, lineStyle: { width: 2.5 }, symbol: 'circle', symbolSize: 5 }
        ]
    });

    renderTable('valuation-table', ['Year', 'Price-to-Income', 'Real HPI Deviation (%)', 'Mortgage Rate 1yr (%)', 'Household DTI (%)'],
        valData.map(function (d) { return d; }));

    // ============================================================
    // Housing — 3. Supply & Demographics
    // ============================================================
    var supplyData = [
        [1995, 21, 28], [1996, 20, 26], [1997, 18, 15], [1998, 17, -5], [1999, 20, -8],
        [2000, 20, -10], [2001, 21, 10], [2002, 26, 38], [2003, 31, 42], [2004, 31, 15],
        [2005, 25, 10], [2006, 24, 15], [2007, 26, 8], [2008, 19, 5], [2009, 15, 18],
        [2010, 17, 10], [2011, 14, -3], [2012, 17, -2], [2013, 21, 8], [2014, 24, 38],
        [2015, 28, 58], [2016, 30, 70], [2017, 31, 53], [2018, 33, 50], [2019, 35, 56],
        [2020, 39, 92], [2021, 48, 25], [2022, 50, 12], [2023, 45, 135], [2024, 34, 24],
        [2025, 36, 14]
    ];
    var supplyYears = supplyData.map(function (d) { return d[0] + ''; });
    var consents = supplyData.map(function (d) { return d[1]; });
    var migration = supplyData.map(function (d) { return d[2]; });

    setOption('chart-supply', {
        tooltip: shadowTooltip(),
        legend: { data: ['Building Consents (000s)', 'Net Migration (000s)'], top: 0, textStyle: { color: muted } },
        grid: { left: 48, right: 56, top: 44, bottom: 40 },
        xAxis: catAxis(supplyYears),
        yAxis: [
            valAxis('Dwellings (000s)'),
            Object.assign(valAxis('People (000s)'), { splitLine: { show: false } })
        ],
        color: [accent, warn],
        series: [
            { name: 'Building Consents (000s)', type: 'bar', data: consents, barWidth: '58%', itemStyle: { color: accent2, opacity: 0.85, borderRadius: [2, 2, 0, 0] } },
            { name: 'Net Migration (000s)', type: 'line', yAxisIndex: 1, data: migration, smooth: true, lineStyle: { width: 2.5 }, symbol: 'circle', symbolSize: 5, itemStyle: { color: warn } }
        ]
    });

    renderTable('supply-table', ['Year', 'Building Consents (000s)', 'Net Migration (000s)'],
        supplyData.map(function (d) { return d; }));

    // ============================================================
    // Housing — 4. International Comparison
    // ============================================================
    var intlData = [
        { country: 'Ireland', decline: 54, detail: 'Banking crisis', recovered: 'Recovered above peak' },
        { country: 'Spain', decline: 41, detail: 'Banking crisis', recovered: 'Prime markets recovered' },
        { country: 'Sweden', decline: 30, detail: 'No banking crisis', recovered: 'Early recovery' },
        { country: 'Canada', decline: 17, detail: 'No banking crisis', recovered: 'Stabilising' },
        { country: 'New Zealand', decline: 12, detail: 'No banking crisis', recovered: 'In correction' },
        { country: 'Australia', decline: 5, detail: 'No banking crisis', recovered: 'Fully recovered' }
    ];
    var intlCountries = intlData.map(function (d) { return d.country; });

    setOption('chart-intl', {
        tooltip: {
            trigger: 'axis', appendToBody: true,
            formatter: function (p) {
                var d = intlData[p[0].dataIndex];
                return d.country + ': ' + d.decline + '% peak-to-trough decline<br>' + d.detail + ' · ' + d.recovered;
            }
        },
        grid: { left: 110, right: 44, top: 16, bottom: 36 },
        xAxis: Object.assign(valAxis('Real price decline (%)'), { nameLocation: 'middle', nameGap: 30 }),
        yAxis: Object.assign(catAxis(intlCountries), { axisLabel: { color: ink, fontWeight: 600, fontSize: 12 } }),
        series: [{
            type: 'bar', barWidth: '55%',
            data: intlData.map(function (d) {
                return {
                    value: d.decline,
                    itemStyle: { color: d.decline >= 30 ? error : (d.decline >= 15 ? warn : accent2), borderRadius: [0, 3, 3, 0] }
                };
            }),
            label: {
                show: true, position: 'right',
                formatter: function (p) { return '-' + p.value + '%'; },
                color: ink, fontSize: 11, fontWeight: 600
            }
        }]
    });

    renderTable('intl-table', ['Country', 'Real Price Decline (%)', 'Peak-to-Trough', 'Banking Crisis', 'Recovery Status'],
        intlData.map(function (d) { return [d.country, d.decline, '-' + d.decline + '%', d.detail, d.recovered]; }));

    // ============================================================
    // TEFI — Tax Efficiency & Friction Index (0 = best, 100 = worst)
    // ============================================================
    var tefiData = [
        { country: 'Ireland', rate: 12.5, hours: 82, score: 0.0 },
        { country: 'Singapore', rate: 17.0, hours: 80, score: 11.9 },
        { country: 'United Kingdom', rate: 25.0, hours: 110, score: 45.7 },
        { country: 'Canada', rate: 26.5, hours: 130, score: 57.4 },
        { country: 'New Zealand', rate: 28.0, hours: 140, score: 65.4 },
        { country: 'France', rate: 25.83, hours: 160, score: 66.8 },
        { country: 'USA', rate: 25.81, hours: 175, score: 72.4 },
        { country: 'Australia', rate: 30.0, hours: 150, score: 74.8 },
        { country: 'Japan', rate: 30.62, hours: 190, score: 91.5 },
        { country: 'Germany', rate: 29.9, hours: 218, score: 100.0 }
    ];
    var tefiSorted = tefiData.slice().sort(function (a, b) { return a.score - b.score; });

    setOption('chart-tefi', {
        tooltip: {
            trigger: 'axis', appendToBody: true,
            formatter: function (p) {
                var d = tefiData[p[0].dataIndex];
                return d.country + '<br>TEFI score: ' + d.score.toFixed(1) + ' / 100' +
                    '<br>Corporate tax: ' + d.rate + '%' +
                    '<br>Compliance: ~' + d.hours + ' hours/yr';
            }
        },
        grid: { left: 110, right: 52, top: 16, bottom: 36 },
        xAxis: Object.assign(valAxis('TEFI score (0-100)'), { nameLocation: 'middle', nameGap: 30 }),
        yAxis: Object.assign(catAxis(tefiSorted.map(function (d) { return d.country; })), {
            inverse: true,
            axisLabel: {
                fontSize: 12,
                formatter: function (value) {
                    return value === 'New Zealand' ? '{nz|' + value + '}' : value;
                },
                rich: { nz: { color: accent, fontWeight: 700 } }
            }
        }),
        series: [{
            type: 'bar', barWidth: '55%',
            data: tefiSorted.map(function (d) {
                return {
                    value: d.score,
                    itemStyle: {
                        color: d.country === 'New Zealand' ? accent : 'rgba(26, 58, 42, ' + (0.25 + (d.score / 100) * 0.6) + ')',
                        borderRadius: [0, 3, 3, 0]
                    }
                };
            }),
            label: {
                show: true, position: 'right',
                formatter: function (p) { return p.value.toFixed(1); },
                color: ink, fontSize: 11, fontWeight: 600
            }
        }]
    });

    renderTable('tefi-table', ['Country', 'Corporate Tax Rate (%)', 'Compliance Hours', 'TEFI Score (0-100)'],
        tefiSorted.map(function (d) { return [d.country, d.rate, d.hours, d.score.toFixed(1)]; }));

    // ============================================================
    // NZ SME Resilience — component changes
    // ============================================================
    var smeData = [
        { metric: 'Retail Spending (monthly)', value: -1.1, source: 'Stats NZ ECT (Jan 2026)' },
        { metric: 'Enterprise Growth (YoY)', value: 0.5, source: 'Stats NZ Demography (Feb 2025)' },
        { metric: 'Employment Growth (YoY)', value: -2.2, source: 'Stats NZ Demography (Feb 2025)' }
    ];

    setOption('chart-sme', {
        tooltip: shadowTooltip(),
        grid: { left: 185, right: 56, top: 16, bottom: 36 },
        xAxis: Object.assign(valAxis('Change (%)'), { nameLocation: 'middle', nameGap: 30 }),
        yAxis: Object.assign(catAxis(smeData.map(function (d) { return d.metric; })), {
            axisLabel: { color: ink, fontSize: 12 }
        }),
        series: [{
            type: 'bar', barWidth: '45%',
            data: smeData.map(function (d) {
                return {
                    value: d.value,
                    itemStyle: { color: d.value >= 0 ? accent2 : error, borderRadius: [3, 3, 3, 3] }
                };
            }),
            label: {
                show: true, position: 'right',
                formatter: function (p) { return (p.value >= 0 ? '+' : '') + p.value + '%'; },
                color: ink, fontSize: 12, fontWeight: 600
            },
            markLine: { silent: true, symbol: 'none', lineStyle: { color: muted, type: 'dashed' }, data: [{ xAxis: 0 }] }
        }]
    });

    renderTable('sme-table', ['Metric', 'Value (%)', 'Source', 'Impact on Resilience'],
        smeData.map(function (d) { return [d.metric, d.value, d.source, d.value >= 0 ? 'Positive' : 'Negative']; }));
});
