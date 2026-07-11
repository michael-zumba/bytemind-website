// charts.js -- NZ First-Home Buyer Market Analysis
// Author: Dr Yuqian Zhang, 11 July 2026

(function() {

var style = getComputedStyle(document.documentElement);
var accent  = style.getPropertyValue('--accent').trim();
var accent2 = style.getPropertyValue('--accent2').trim();
var ink = style.getPropertyValue('--ink').trim();
var muted = style.getPropertyValue('--muted').trim();
var rule = style.getPropertyValue('--rule').trim();

/* ==================================================================
   Figure 1: First-Home Buyer Share of Property Purchases
   ================================================================== */
(function() {
    var chart = echarts.init(document.getElementById('chart-fhb-share'), null, { renderer: 'svg' });
    var years = [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025];
    var shares = [21.0, 21.0, 21.5, 22.0, 24.0, 23.1, 21.0, 25.8, 26.1, 27.5];

    chart.setOption({
        animation: false,
        color: [accent],
        tooltip: {
            trigger: 'axis',
            backgroundColor: '#1f2937',
            borderColor: '#374151',
            textStyle: { color: '#f9fafb', fontSize: 13 },
            valueFormatter: function(value) { return value + '%'; }
        },
        grid: { left: 60, right: 30, top: 50, bottom: 40 },
        title: {
            text: 'First-Home Buyer Share of Property Purchases',
            left: 'center',
            top: 8,
            textStyle: { fontSize: 15, fontWeight: 600, color: ink }
        },
        xAxis: {
            type: 'category',
            data: years,
            name: 'Year',
            nameLocation: 'middle',
            nameGap: 28,
            nameTextStyle: { color: muted, fontSize: 12 },
            axisLine: { lineStyle: { color: rule } },
            axisTick: { show: false },
            axisLabel: { color: ink, fontSize: 11 }
        },
        yAxis: {
            type: 'value',
            name: '% of total purchases',
            nameTextStyle: { color: muted, fontSize: 12 },
            axisLine: { show: false },
            axisTick: { show: false },
            splitLine: { lineStyle: { color: rule } },
            axisLabel: {
                color: ink,
                fontSize: 11,
                formatter: '{value}%'
            },
            min: 18,
            max: 30
        },
        series: [{
            type: 'bar',
            data: shares,
            barWidth: '50%',
            label: {
                show: true,
                position: 'top',
                color: ink,
                fontSize: 11,
                formatter: '{c}%'
            },
            itemStyle: { borderRadius: [4, 4, 0, 0] }
        }]
    });

    window.addEventListener('resize', function() { chart.resize(); });
})();

/* ==================================================================
   Figure 2: National Median House Price
   ================================================================== */
(function() {
    var chart = echarts.init(document.getElementById('chart-median-price'), null, { renderer: 'svg' });
    var years = [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025];
    var prices = [515000, 551750, 560000, 628000, 745000, 900000, 785300, 779830, 776000, 786977];

    var peakLabel = 'Peak $900,000';
    var peakIdx = years.indexOf(2021);

    chart.setOption({
        animation: false,
        color: [accent],
        tooltip: {
            trigger: 'axis',
            backgroundColor: '#1f2937',
            borderColor: '#374151',
            textStyle: { color: '#f9fafb', fontSize: 13 },
            valueFormatter: function(value) { return '$' + value.toLocaleString('en-NZ'); }
        },
        grid: { left: 80, right: 40, top: 50, bottom: 40 },
        title: {
            text: 'National Median House Price',
            left: 'center',
            top: 8,
            textStyle: { fontSize: 15, fontWeight: 600, color: ink }
        },
        xAxis: {
            type: 'category',
            data: years,
            name: 'Year',
            nameLocation: 'middle',
            nameGap: 28,
            nameTextStyle: { color: muted, fontSize: 12 },
            axisLine: { lineStyle: { color: rule } },
            axisTick: { show: false },
            axisLabel: { color: ink, fontSize: 11 }
        },
        yAxis: {
            type: 'value',
            name: 'NZD',
            nameTextStyle: { color: muted, fontSize: 12 },
            axisLine: { show: false },
            axisTick: { show: false },
            splitLine: { lineStyle: { color: rule } },
            axisLabel: {
                color: ink,
                fontSize: 11,
                formatter: function(val) { return '$' + (val / 1000).toFixed(0) + 'k'; }
            }
        },
        series: [{
            type: 'bar',
            data: prices.map(function(v, i) {
                return i === peakIdx
                    ? { value: v, itemStyle: { color: accent, borderRadius: [4, 4, 0, 0] }, label: { show: true, position: 'top', color: accent2, fontSize: 11, fontWeight: 600, formatter: peakLabel } }
                    : { value: v, itemStyle: { borderRadius: [4, 4, 0, 0] } };
            }),
            barWidth: '55%',
            markLine: {
                silent: true,
                symbol: 'none',
                lineStyle: { color: accent2, type: 'dashed', width: 1.5 },
                label: {
                    show: true,
                    position: 'insideEndTop',
                    color: accent2,
                    fontSize: 11,
                    fontWeight: 600,
                    formatter: peakLabel
                },
                data: [{ yAxis: 900000 }]
            }
        }]
    });

    window.addEventListener('resize', function() { chart.resize(); });
})();

/* ==================================================================
   Figure 3: Median House Prices by Region
   ================================================================== */
(function() {
    var chart = echarts.init(document.getElementById('chart-regional-prices'), null, { renderer: 'svg' });
    var years = [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025];
    var auckland   = [850000, 860000, 910000, 1040000, 1250000, 1130000, 1050000, 1010000, 1015000];
    var wellington = [550000, 575000, 640000, 755000, 945000, 820000, 795000, 770000, 770000];
    var chch       = [450000, 455000, 470000, 530000, 660000, 685000, 690000, 700000, 725000];
    var national   = [551750, 560000, 628000, 745000, 900000, 785300, 779830, 776000, 786977];

    chart.setOption({
        animation: false,
        color: [accent, '#2563eb', '#6b7280', accent2],
        tooltip: {
            trigger: 'axis',
            backgroundColor: '#1f2937',
            borderColor: '#374151',
            textStyle: { color: '#f9fafb', fontSize: 13 },
            valueFormatter: function(value) { return '$' + value.toLocaleString('en-NZ'); }
        },
        grid: { left: 80, right: 30, top: 50, bottom: 40 },
        title: {
            text: 'Median House Prices by Region',
            left: 'center',
            top: 8,
            textStyle: { fontSize: 15, fontWeight: 600, color: ink }
        },
        legend: {
            bottom: 0,
            textStyle: { color: ink, fontSize: 11 },
            itemWidth: 18,
            itemHeight: 10
        },
        xAxis: {
            type: 'category',
            data: years,
            name: 'Year',
            nameLocation: 'middle',
            nameGap: 28,
            nameTextStyle: { color: muted, fontSize: 12 },
            axisLine: { lineStyle: { color: rule } },
            axisTick: { show: false },
            axisLabel: { color: ink, fontSize: 11 }
        },
        yAxis: {
            type: 'value',
            name: 'NZD',
            nameTextStyle: { color: muted, fontSize: 12 },
            axisLine: { show: false },
            axisTick: { show: false },
            splitLine: { lineStyle: { color: rule } },
            axisLabel: {
                color: ink,
                fontSize: 11,
                formatter: function(val) { return '$' + (val / 1000).toFixed(0) + 'k'; }
            }
        },
        series: [
            { name: 'Auckland',    type: 'line', data: auckland,   smooth: true, symbol: 'circle', symbolSize: 6, lineStyle: { width: 2.5 } },
            { name: 'Wellington',  type: 'line', data: wellington, smooth: true, symbol: 'circle', symbolSize: 6, lineStyle: { width: 2 } },
            { name: 'National',    type: 'line', data: national,   smooth: true, symbol: 'diamond', symbolSize: 6, lineStyle: { width: 2.5, type: 'dashed' } },
            { name: 'Christchurch', type: 'line', data: chch,      smooth: true, symbol: 'circle', symbolSize: 6, lineStyle: { width: 2 } }
        ]
    });

    window.addEventListener('resize', function() { chart.resize(); });
})();

/* ==================================================================
   Figure 4: National Median Days to Sell
   ================================================================== */
(function() {
    var chart = echarts.init(document.getElementById('chart-days-to-sell'), null, { renderer: 'svg' });
    var years = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025];
    var days  = [38, 39, 35, 31, 43, 45, 44, 44];

    chart.setOption({
        animation: false,
        color: [accent],
        tooltip: {
            trigger: 'axis',
            backgroundColor: '#1f2937',
            borderColor: '#374151',
            textStyle: { color: '#f9fafb', fontSize: 13 },
            valueFormatter: function(value) { return value + ' days'; }
        },
        grid: { left: 55, right: 30, top: 50, bottom: 40 },
        title: {
            text: 'National Median Days to Sell',
            left: 'center',
            top: 8,
            textStyle: { fontSize: 15, fontWeight: 600, color: ink }
        },
        xAxis: {
            type: 'category',
            data: years,
            name: 'Year',
            nameLocation: 'middle',
            nameGap: 28,
            nameTextStyle: { color: muted, fontSize: 12 },
            axisLine: { lineStyle: { color: rule } },
            axisTick: { show: false },
            axisLabel: { color: ink, fontSize: 11 }
        },
        yAxis: {
            type: 'value',
            name: 'Days',
            nameTextStyle: { color: muted, fontSize: 12 },
            axisLine: { show: false },
            axisTick: { show: false },
            splitLine: { lineStyle: { color: rule } },
            axisLabel: { color: ink, fontSize: 11 },
            min: 25,
            max: 50
        },
        series: [{
            type: 'bar',
            data: days,
            barWidth: '50%',
            label: {
                show: true,
                position: 'top',
                color: ink,
                fontSize: 11,
                formatter: '{c}d'
            },
            itemStyle: { borderRadius: [4, 4, 0, 0] }
        }]
    });

    window.addEventListener('resize', function() { chart.resize(); });
})();

/* ==================================================================
   Figure 5: Annual Residential Property Sales
   ================================================================== */
(function() {
    var chart = echarts.init(document.getElementById('chart-sales-volumes'), null, { renderer: 'svg' });
    var years  = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025];
    var sales  = [77848, 77111, 82165, 88588, 62383, 63414, 72617, 80655];

    chart.setOption({
        animation: false,
        color: [accent],
        tooltip: {
            trigger: 'axis',
            backgroundColor: '#1f2937',
            borderColor: '#374151',
            textStyle: { color: '#f9fafb', fontSize: 13 },
            valueFormatter: function(value) { return value.toLocaleString('en-NZ'); }
        },
        grid: { left: 75, right: 30, top: 50, bottom: 40 },
        title: {
            text: 'Annual Residential Property Sales',
            left: 'center',
            top: 8,
            textStyle: { fontSize: 15, fontWeight: 600, color: ink }
        },
        xAxis: {
            type: 'category',
            data: years,
            name: 'Year',
            nameLocation: 'middle',
            nameGap: 28,
            nameTextStyle: { color: muted, fontSize: 12 },
            axisLine: { lineStyle: { color: rule } },
            axisTick: { show: false },
            axisLabel: { color: ink, fontSize: 11 }
        },
        yAxis: {
            type: 'value',
            name: 'Sales count',
            nameTextStyle: { color: muted, fontSize: 12 },
            axisLine: { show: false },
            axisTick: { show: false },
            splitLine: { lineStyle: { color: rule } },
            axisLabel: {
                color: ink,
                fontSize: 11,
                formatter: function(val) { return (val / 1000).toFixed(0) + 'k'; }
            }
        },
        series: [{
            type: 'bar',
            data: sales,
            barWidth: '50%',
            label: {
                show: true,
                position: 'top',
                color: ink,
                fontSize: 10,
                formatter: function(p) { return (p.value / 1000).toFixed(1) + 'k'; }
            },
            itemStyle: { borderRadius: [4, 4, 0, 0] }
        }]
    });

    window.addEventListener('resize', function() { chart.resize(); });
})();

/* ==================================================================
   Figure 6: Home Transfers to Overseas Buyers
   ================================================================== */
(function() {
    var chart = echarts.init(document.getElementById('chart-overseas-buyers'), null, { renderer: 'svg' });
    var labels = ['2017', '2018\nPeak', '2019', '2020', '2021', '2022', '2023', '2024'];
    var pcts   = [2.4, 3.3, 0.6, 0.5, 0.4, 0.4, 0.4, 0.3];

    var idx2018 = 1;

    chart.setOption({
        animation: false,
        color: [accent],
        tooltip: {
            trigger: 'axis',
            backgroundColor: '#1f2937',
            borderColor: '#374151',
            textStyle: { color: '#f9fafb', fontSize: 13 },
            valueFormatter: function(value) { return value + '%'; }
        },
        grid: { left: 55, right: 30, top: 50, bottom: 55 },
        title: {
            text: 'Home Transfers to Overseas Buyers (No NZ Citizenship/Residency)',
            left: 'center',
            top: 8,
            textStyle: { fontSize: 13, fontWeight: 600, color: ink }
        },
        xAxis: {
            type: 'category',
            data: labels,
            name: 'Year',
            nameLocation: 'middle',
            nameGap: 40,
            nameTextStyle: { color: muted, fontSize: 12 },
            axisLine: { lineStyle: { color: rule } },
            axisTick: { show: false },
            axisLabel: { color: ink, fontSize: 11 }
        },
        yAxis: {
            type: 'value',
            name: '% of transfers',
            nameTextStyle: { color: muted, fontSize: 12 },
            axisLine: { show: false },
            axisTick: { show: false },
            splitLine: { lineStyle: { color: rule } },
            axisLabel: { color: ink, fontSize: 11, formatter: '{value}%' },
            max: 4.0
        },
        series: [{
            type: 'bar',
            data: pcts.map(function(v, i) {
                return i === idx2018
                    ? { value: v, itemStyle: { color: accent2, borderRadius: [4, 4, 0, 0] }, label: { show: true, position: 'top', color: accent2, fontSize: 11, fontWeight: 600, formatter: '{c}%' } }
                    : { value: v, itemStyle: { borderRadius: [4, 4, 0, 0] } };
            }),
            barWidth: '55%',
            markLine: {
                silent: true,
                symbol: 'none',
                lineStyle: { color: accent2, type: 'dashed', width: 1.5 },
                label: {
                    show: true,
                    position: 'start',
                    color: accent2,
                    fontSize: 10,
                    fontWeight: 600,
                    formatter: 'Overseas Investment\nAmendment Act (Oct 2018)',
                    lineHeight: 13
                },
                data: [{ xAxis: '2018\nPeak' }]
            },
            label: {
                show: true,
                position: 'top',
                color: ink,
                fontSize: 10,
                formatter: function(p) {
                    return p.dataIndex === idx2018 ? '' : p.value + '%';
                }
            }
        }]
    });

    window.addEventListener('resize', function() { chart.resize(); });
})();

/* ==================================================================
   Figure 7: Official Cash Rate and 1-Year Special Mortgage Rate
   ================================================================== */
(function() {
    var chart = echarts.init(document.getElementById('chart-rates'), null, { renderer: 'svg' });
    var years = [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026];
    var ocr   = [1.75, 1.75, 1.75, 1.00, 0.25, 0.75, 4.25, 5.50, 4.25, 2.25, 2.50];
    var mortgage = [4.55, 4.59, 4.55, 3.64, 2.49, 3.15, 6.07, 7.06, 5.52, 4.38, 4.67];

    chart.setOption({
        animation: false,
        color: [accent, accent2],
        tooltip: {
            trigger: 'axis',
            backgroundColor: '#1f2937',
            borderColor: '#374151',
            textStyle: { color: '#f9fafb', fontSize: 13 },
            valueFormatter: function(value) { return value.toFixed(2) + '%'; }
        },
        grid: { left: 60, right: 30, top: 50, bottom: 40 },
        title: {
            text: 'Official Cash Rate and 1-Year Special Mortgage Rate',
            left: 'center',
            top: 8,
            textStyle: { fontSize: 14, fontWeight: 600, color: ink }
        },
        legend: {
            bottom: 0,
            textStyle: { color: ink, fontSize: 11 },
            itemWidth: 18,
            itemHeight: 10
        },
        xAxis: {
            type: 'category',
            data: years,
            name: 'Year',
            nameLocation: 'middle',
            nameGap: 28,
            nameTextStyle: { color: muted, fontSize: 12 },
            axisLine: { lineStyle: { color: rule } },
            axisTick: { show: false },
            axisLabel: { color: ink, fontSize: 11 }
        },
        yAxis: {
            type: 'value',
            name: 'Rate (%)',
            nameTextStyle: { color: muted, fontSize: 12 },
            axisLine: { show: false },
            axisTick: { show: false },
            splitLine: { lineStyle: { color: rule } },
            axisLabel: { color: ink, fontSize: 11, formatter: '{value}%' },
            min: 0,
            max: 8
        },
        series: [
            {
                name: 'OCR',
                type: 'line',
                data: ocr,
                smooth: false,
                symbol: 'circle',
                symbolSize: 7,
                lineStyle: { width: 2.5 },
                markLine: {
                    silent: true,
                    symbol: 'none',
                    lineStyle: { color: muted, type: 'dashed', width: 1 },
                    label: { show: false },
                    data: [{ yAxis: 0 }]
                }
            },
            {
                name: '1yr Special Mortgage',
                type: 'line',
                data: mortgage,
                smooth: false,
                symbol: 'diamond',
                symbolSize: 7,
                lineStyle: { width: 2.5 }
            }
        ]
    });

    window.addEventListener('resize', function() { chart.resize(); });
})();

/* ==================================================================
   Figure 8: Annual Net Migration (Outcomes-Based Measure)
   ================================================================== */
(function() {
    var chart = echarts.init(document.getElementById('chart-net-migration'), null, { renderer: 'svg' });
    var years = [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025];
    var nzCitizen    = [-2226, -4846, -7612, 2902, 21608, 927, -25185, -43540, -43714, -40033];
    var nonNzCitizen = [65115, 58126, 57179, 69686, 15236, -15877, 50085, 171491, 67535, 54205];

    chart.setOption({
        animation: false,
        color: [accent, accent2],
        tooltip: {
            trigger: 'axis',
            backgroundColor: '#1f2937',
            borderColor: '#374151',
            textStyle: { color: '#f9fafb', fontSize: 13 },
            valueFormatter: function(value) { return value.toLocaleString('en-NZ'); }
        },
        grid: { left: 80, right: 30, top: 50, bottom: 40 },
        title: {
            text: 'Annual Net Migration (Outcomes-Based Measure)',
            left: 'center',
            top: 8,
            textStyle: { fontSize: 14, fontWeight: 600, color: ink }
        },
        legend: {
            bottom: 0,
            textStyle: { color: ink, fontSize: 11 },
            itemWidth: 18,
            itemHeight: 10
        },
        xAxis: {
            type: 'category',
            data: years,
            name: 'Calendar year',
            nameLocation: 'middle',
            nameGap: 28,
            nameTextStyle: { color: muted, fontSize: 12 },
            axisLine: { lineStyle: { color: rule } },
            axisTick: { show: false },
            axisLabel: { color: ink, fontSize: 11 }
        },
        yAxis: {
            type: 'value',
            name: 'Net migration',
            nameTextStyle: { color: muted, fontSize: 12 },
            axisLine: { show: false },
            axisTick: { show: false },
            splitLine: { lineStyle: { color: rule } },
            axisLabel: {
                color: ink,
                fontSize: 11,
                formatter: function(val) { return (val / 1000).toFixed(0) + 'k'; }
            }
        },
        series: [
            {
                name: 'Non-NZ Citizen Net',
                type: 'bar',
                data: nonNzCitizen,
                barWidth: '45%',
                itemStyle: { borderRadius: [4, 4, 0, 0] }
            },
            {
                name: 'NZ Citizen Net',
                type: 'bar',
                data: nzCitizen,
                barWidth: '45%',
                itemStyle: { borderRadius: [4, 4, 0, 0] }
            }
        ]
    });

    window.addEventListener('resize', function() { chart.resize(); });
})();

/* ==================================================================
   Figure 9: New Dwellings Consented Annually
   ================================================================== */
(function() {
    var chart = echarts.init(document.getElementById('chart-building-consents'), null, { renderer: 'svg' });
    var years     = [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025];
    var consents  = [29900, 31500, 33500, 38000, 39400, 48899, 49900, 37200, 33600, 36619];

    chart.setOption({
        animation: false,
        color: [accent],
        tooltip: {
            trigger: 'axis',
            backgroundColor: '#1f2937',
            borderColor: '#374151',
            textStyle: { color: '#f9fafb', fontSize: 13 },
            valueFormatter: function(value) { return value.toLocaleString('en-NZ'); }
        },
        grid: { left: 75, right: 30, top: 50, bottom: 40 },
        title: {
            text: 'New Dwellings Consented Annually',
            left: 'center',
            top: 8,
            textStyle: { fontSize: 15, fontWeight: 600, color: ink }
        },
        xAxis: {
            type: 'category',
            data: years,
            name: 'Year',
            nameLocation: 'middle',
            nameGap: 28,
            nameTextStyle: { color: muted, fontSize: 12 },
            axisLine: { lineStyle: { color: rule } },
            axisTick: { show: false },
            axisLabel: { color: ink, fontSize: 11 }
        },
        yAxis: {
            type: 'value',
            name: 'Dwellings consented',
            nameTextStyle: { color: muted, fontSize: 12 },
            axisLine: { show: false },
            axisTick: { show: false },
            splitLine: { lineStyle: { color: rule } },
            axisLabel: {
                color: ink,
                fontSize: 11,
                formatter: function(val) { return (val / 1000).toFixed(0) + 'k'; }
            }
        },
        series: [{
            type: 'bar',
            data: consents,
            barWidth: '50%',
            label: {
                show: true,
                position: 'top',
                color: ink,
                fontSize: 10,
                formatter: function(p) { return (p.value / 1000).toFixed(1) + 'k'; }
            },
            itemStyle: { borderRadius: [4, 4, 0, 0] }
        }]
    });

    window.addEventListener('resize', function() { chart.resize(); });
})();

/* ==================================================================
   Figure 10: First-Home Buyer Median Purchase Price and Average Age
   ================================================================== */
(function() {
    var chart = echarts.init(document.getElementById('chart-fhb-characteristics'), null, { renderer: 'svg' });
    var years = [2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026];
    var price = [null, null, 740000, 719000, 700000, 698000, 700000, 720000];
    var age   = [34.0, 34.4, 34.6, 35.0, 35.4, 35.6, 35.6, 35.0];

    chart.setOption({
        animation: false,
        color: [accent, accent2],
        tooltip: {
            trigger: 'axis',
            backgroundColor: '#1f2937',
            borderColor: '#374151',
            textStyle: { color: '#f9fafb', fontSize: 13 }
        },
        grid: { left: 70, right: 70, top: 50, bottom: 40 },
        title: {
            text: 'First-Home Buyer Median Purchase Price and Average Age',
            left: 'center',
            top: 8,
            textStyle: { fontSize: 13, fontWeight: 600, color: ink }
        },
        legend: {
            bottom: 0,
            textStyle: { color: ink, fontSize: 11 },
            itemWidth: 18,
            itemHeight: 10
        },
        xAxis: {
            type: 'category',
            data: years,
            name: 'Year',
            nameLocation: 'middle',
            nameGap: 28,
            nameTextStyle: { color: muted, fontSize: 12 },
            axisLine: { lineStyle: { color: rule } },
            axisTick: { show: false },
            axisLabel: { color: ink, fontSize: 11 }
        },
        yAxis: [
            {
                type: 'value',
                name: 'NZD',
                nameTextStyle: { color: muted, fontSize: 12 },
                axisLine: { show: false },
                axisTick: { show: false },
                splitLine: { lineStyle: { color: rule } },
                axisLabel: {
                    color: ink,
                    fontSize: 11,
                    formatter: function(val) { return '$' + (val / 1000).toFixed(0) + 'k'; }
                },
                min: 650000,
                max: 800000
            },
            {
                type: 'value',
                name: 'Age (years)',
                nameTextStyle: { color: muted, fontSize: 12 },
                axisLine: { show: false },
                axisTick: { show: false },
                splitLine: { show: false },
                axisLabel: { color: ink, fontSize: 11 },
                min: 33,
                max: 37
            }
        ],
        series: [
            {
                name: 'Median Purchase Price',
                type: 'bar',
                data: price,
                barWidth: '40%',
                itemStyle: { borderRadius: [4, 4, 0, 0] },
                label: {
                    show: true,
                    position: 'top',
                    color: ink,
                    fontSize: 10,
                    formatter: function(p) { return p.value ? '$' + (p.value / 1000).toFixed(0) + 'k' : ''; }
                }
            },
            {
                name: 'Average Age',
                type: 'line',
                yAxisIndex: 1,
                data: age,
                smooth: true,
                symbol: 'diamond',
                symbolSize: 8,
                lineStyle: { width: 2.5 },
                label: {
                    show: true,
                    position: 'top',
                    color: accent2,
                    fontSize: 10,
                    formatter: '{c}yr'
                }
            }
        ]
    });

    window.addEventListener('resize', function() { chart.resize(); });
})();

})();
