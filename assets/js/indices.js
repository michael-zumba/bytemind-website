document.addEventListener('DOMContentLoaded', function () {

    var accent = '#0B3D91';
    var accent2 = '#B91C1C';
    var muted = '#64748B';
    var rule = '#E2E8F0';
    var ink = '#0F172A';

    var commonTooltip = { trigger: 'axis', appendToBody: true };

    function setOption(domId, option) {
        var dom = document.getElementById(domId);
        if (!dom) return;
        var chart = echarts.init(dom, null, { renderer: 'svg' });
        chart.setOption(option);
        window.addEventListener('resize', function () { chart.resize(); });
    }

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

    // ============================================================
    // Tab 1: NZ & AU Real HPI (BIS 2010=100)
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
        tooltip: commonTooltip,
        grid: { left: 60, right: 30, top: 40, bottom: 50 },
        xAxis: { type: 'category', data: hpiYears, axisLabel: { color: muted, rotate: 45, fontSize: 10 }, axisLine: { lineStyle: { color: rule } } },
        yAxis: { type: 'value', name: 'Index (2010=100)', nameTextStyle: { color: muted }, axisLabel: { color: muted }, splitLine: { lineStyle: { color: rule } } },
        color: [accent, accent2],
        series: [
            { name: 'New Zealand', type: 'line', data: nzHpi, smooth: true, lineStyle: { width: 2.5 }, symbol: 'none' },
            { name: 'Australia', type: 'line', data: auHpi, smooth: true, lineStyle: { width: 2.5 }, symbol: 'none' }
        ]
    });

    renderTable('hpi-table', ['Year', 'NZ Real HPI', 'AU Real HPI'],
        hpiData.map(function (d) { return [d[0], d[1], d[2]]; }));

    // ============================================================
    // Tab 2: Valuation Metrics
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
        tooltip: commonTooltip,
        grid: { left: 60, right: 30, top: 40, bottom: 50 },
        xAxis: { type: 'category', data: ptiYears, axisLabel: { color: muted, rotate: 45, fontSize: 10 }, axisLine: { lineStyle: { color: rule } } },
        yAxis: { type: 'value', name: 'Index (2015=100)', nameTextStyle: { color: muted }, axisLabel: { color: muted }, splitLine: { lineStyle: { color: rule } } },
        color: [accent],
        series: [
            { name: 'Price-to-Income', type: 'line', data: ptiVals, smooth: true, lineStyle: { width: 2.5 }, symbol: 'none', areaStyle: { color: accent + '18' } },
            { name: 'Long-Run Median', type: 'line', data: Array(ptiYears.length).fill(medianVal), lineStyle: { color: muted, type: 'dashed', width: 1.5 }, symbol: 'none' }
        ]
    });

    var devYears = valData.filter(function (d) { return d[2] != null; }).map(function (d) { return d[0] + ''; });
    var devVals = valData.filter(function (d) { return d[2] != null; }).map(function (d) { return d[2]; });

    setOption('chart-deviation', {
        tooltip: {
            trigger: 'axis', appendToBody: true,
            formatter: function (p) { return p[0].axisValue + ': ' + (p[0].value >= 0 ? '+' : '') + p[0].value + '%'; }
        },
        grid: { left: 60, right: 30, top: 40, bottom: 50 },
        xAxis: { type: 'category', data: devYears, axisLabel: { color: muted, rotate: 45, fontSize: 10 }, axisLine: { lineStyle: { color: rule } } },
        yAxis: { type: 'value', name: 'Deviation (%)', nameTextStyle: { color: muted }, axisLabel: { color: muted }, splitLine: { lineStyle: { color: rule } } },
        series: [{
            name: 'Deviation from Trend', type: 'bar',
            data: devVals.map(function (v) { return { value: v, itemStyle: { color: v >= 0 ? accent2 : accent } }; }),
            barWidth: '60%'
        }]
    });

    var rateYears = valData.filter(function (d) { return d[3] != null; }).map(function (d) { return d[0] + ''; });
    var rateVals = valData.filter(function (d) { return d[3] != null; }).map(function (d) { return d[3]; });
    var dtiVals = valData.filter(function (d) { return d[3] != null; }).map(function (d) { return d[4]; });

    setOption('chart-rates-dti', {
        tooltip: commonTooltip,
        legend: { data: ['1-Year Fixed Rate (%)', 'Household DTI (%)'], textStyle: { color: muted }, top: 5 },
        grid: { left: 60, right: 60, top: 60, bottom: 50 },
        xAxis: { type: 'category', data: rateYears, axisLabel: { color: muted, rotate: 45, fontSize: 10 }, axisLine: { lineStyle: { color: rule } } },
        yAxis: [
            { type: 'value', name: 'Rate (%)', nameTextStyle: { color: muted }, axisLabel: { color: muted }, splitLine: { lineStyle: { color: rule } } },
            { type: 'value', name: 'DTI (%)', nameTextStyle: { color: muted }, axisLabel: { color: muted }, splitLine: { show: false }, min: 80 }
        ],
        color: [accent2, accent],
        series: [
            { name: '1-Year Fixed Rate (%)', type: 'line', data: rateVals, smooth: true, lineStyle: { width: 2.5 }, symbol: 'circle', symbolSize: 4 },
            { name: 'Household DTI (%)', type: 'line', yAxisIndex: 1, data: dtiVals, smooth: true, lineStyle: { width: 2.5 }, symbol: 'circle', symbolSize: 4 }
        ]
    });

    renderTable('valuation-table', ['Year', 'Price-to-Income', 'Real HPI Deviation (%)', 'Mortgage Rate 1yr (%)', 'Household DTI (%)'],
        valData.map(function (d) { return d; }));

    // ============================================================
    // Tab 3: Supply & Demographics
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
        tooltip: commonTooltip,
        legend: { data: ['Building Consents (000s)', 'Net Migration (000s)'], textStyle: { color: muted }, top: 5 },
        grid: { left: 60, right: 60, top: 60, bottom: 50 },
        xAxis: { type: 'category', data: supplyYears, axisLabel: { color: muted, rotate: 45, fontSize: 10 }, axisLine: { lineStyle: { color: rule } } },
        yAxis: [
            { type: 'value', name: 'Dwellings (000s)', nameTextStyle: { color: muted }, axisLabel: { color: muted }, splitLine: { lineStyle: { color: rule } } },
            { type: 'value', name: 'People (000s)', nameTextStyle: { color: muted }, axisLabel: { color: muted }, splitLine: { show: false } }
        ],
        color: [accent, accent2],
        series: [
            { name: 'Building Consents (000s)', type: 'bar', data: consents, barWidth: '60%', itemStyle: { color: accent + 'cc' } },
            { name: 'Net Migration (000s)', type: 'line', yAxisIndex: 1, data: migration, smooth: true, lineStyle: { width: 2.5 }, symbol: 'none' }
        ]
    });

    renderTable('supply-table', ['Year', 'Building Consents (000s)', 'Net Migration (000s)'],
        supplyData.map(function (d) { return d; }));

    // ============================================================
    // Tab 4: International Comparison
    // ============================================================
    var intlData = [
        ['New Zealand', 12, '-12% (ongoing)', 'No', 'In correction'],
        ['Australia', 5, '-5% (minimal)', 'No', 'Fully recovered'],
        ['Ireland', 54, '-54%', 'Yes', 'Recovered above peak'],
        ['Spain', 41, '-41%', 'Yes', 'Prime markets recovered'],
        ['Canada', 17, '-17%', 'No', 'Stabilising'],
        ['Sweden', 30, '-30%', 'No', 'Early recovery']
    ];
    var intlCountries = intlData.map(function (d) { return d[0]; });
    var intlDeclines = intlData.map(function (d) { return { value: d[1], label: d[2] }; });

    setOption('chart-intl', {
        tooltip: {
            trigger: 'axis', appendToBody: true,
            formatter: function (p) { return p[0].name + ': real decline ' + p[0].data.label; }
        },
        grid: { left: 100, right: 60, top: 30, bottom: 30 },
        xAxis: { type: 'value', name: 'Real Price Decline (%)', nameTextStyle: { color: muted }, axisLabel: { color: muted }, splitLine: { lineStyle: { color: rule } }, inverse: true },
        yAxis: { type: 'category', data: intlCountries, axisLabel: { color: ink, fontWeight: 600 }, axisLine: { lineStyle: { color: rule } } },
        series: [{
            type: 'bar',
            data: intlData.map(function (d) {
                return { value: d[1], itemStyle: { color: d[1] >= 30 ? accent2 : (d[1] >= 15 ? accent2 + 'aa' : accent) } };
            }),
            barWidth: '50%',
            label: { show: true, position: 'left', formatter: function (p) { return p.data.label; }, color: ink, fontSize: 11 }
        }]
    });

    renderTable('intl-table', ['Country', 'Real Price Decline (%)', 'Peak-to-Trough', 'Banking Crisis', 'Recovery Status'],
        intlData);
});
