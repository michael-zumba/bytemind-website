// charts.js -- Lotto NZ: Two Lenses of Probability
// Author: Dr Yuqian Zhang, 20 July 2026
// Data sources: Lotto NZ official draw results Excel + lotto.net jackpot history

(function() {

var style = getComputedStyle(document.documentElement);
var accent  = style.getPropertyValue('--accent').trim();
var accent2 = style.getPropertyValue('--accent2').trim();
var ink = style.getPropertyValue('--ink').trim();
var muted = style.getPropertyValue('--muted').trim();
var rule = style.getPropertyValue('--rule').trim();

/* ==================================================================
   Figure 1: Published Lotto NZ Odds by Game and Division
   Source: Lotto NZ game information, mylotto.co.nz
   ================================================================== */
(function() {
    var chart = echarts.init(document.getElementById('chart-lotto-odds'), null, { renderer: 'svg' });

    var lottoOdds = [3838380, 639730, 19386, 7754, 485, 363, 35];
    var powerballOdds = [38383800, 6397300, 193858, 77543, 4846, 3635, 352];
    var strikeOdds = [2193360, 15244, 256, 12];
    var divLabels = ['Div 1', 'Div 2', 'Div 3', 'Div 4', 'Div 5', 'Div 6', 'Div 7'];

    chart.setOption({
        animation: false,
        color: [accent, accent2, muted],
        tooltip: {
            trigger: 'axis',
            backgroundColor: '#1f2937',
            borderColor: '#374151',
            textStyle: { color: '#f9fafb', fontSize: 13 },
            formatter: function(params) {
                var s = params[0].axisValue + '<br/>';
                params.forEach(function(p) {
                    s += p.marker + ' ' + p.seriesName + ': 1 in ' + p.value.toLocaleString('en-NZ') + '<br/>';
                });
                return s;
            }
        },
        grid: { left: 100, right: 40, top: 50, bottom: 50 },
        title: {
            text: 'Published Lotto NZ Odds (1 in X)',
            left: 'center',
            top: 8,
            textStyle: { fontSize: 15, fontWeight: 600, color: ink }
        },
        legend: { bottom: 0, textStyle: { color: ink, fontSize: 11 }, itemWidth: 18, itemHeight: 10 },
        xAxis: {
            type: 'category', data: divLabels,
            name: 'Division', nameLocation: 'middle', nameGap: 30,
            nameTextStyle: { color: muted, fontSize: 12 },
            axisLine: { lineStyle: { color: rule } }, axisTick: { show: false },
            axisLabel: { color: ink, fontSize: 11 }
        },
        yAxis: {
            type: 'log', name: 'Odds (1 in X)',
            nameTextStyle: { color: muted, fontSize: 12 },
            axisLine: { show: false }, axisTick: { show: false },
            splitLine: { lineStyle: { color: rule } },
            axisLabel: { color: ink, fontSize: 11,
                formatter: function(val) {
                    if (val >= 1000000) return (val / 1000000).toFixed(0) + 'M';
                    if (val >= 1000) return (val / 1000).toFixed(0) + 'k';
                    return val;
                }
            },
            min: 10, max: 50000000
        },
        series: [
            { name: 'Lotto', type: 'bar', data: lottoOdds, barGap: '10%', barWidth: '25%', itemStyle: { borderRadius: [4, 4, 0, 0] } },
            { name: 'Powerball', type: 'bar', data: powerballOdds, barWidth: '25%', itemStyle: { borderRadius: [4, 4, 0, 0] } },
            { name: 'Strike', type: 'bar', data: strikeOdds, barWidth: '25%', itemStyle: { borderRadius: [4, 4, 0, 0] } }
        ]
    });
    window.addEventListener('resize', function() { chart.resize(); });
})();

/* ==================================================================
   Figure 2: Powerball Jackpot History, 2025-2026
   Draw dates: Lotto NZ official results Excel
   Jackpot amounts & status: lotto.net, verified 20 July 2026
   ================================================================== */
(function() {
    var chart = echarts.init(document.getElementById('chart-powerball-history'), null, { renderer: 'svg' });

    var dates = ['1 Jan', '4 Jan', '8 Jan', '11 Jan', '15 Jan', '18 Jan', '22 Jan', '25 Jan', '29 Jan', '1 Feb', '5 Feb', '8 Feb', '12 Feb', '15 Feb', '19 Feb', '22 Feb', '26 Feb', '1 Mar', '5 Mar', '8 Mar', '12 Mar', '15 Mar', '19 Mar', '22 Mar', '26 Mar', '29 Mar', '2 Apr', '5 Apr', '9 Apr', '12 Apr', '16 Apr', '19 Apr', '23 Apr', '26 Apr', '30 Apr', '3 May', '7 May', '10 May', '14 May', '17 May', '21 May', '24 May', '28 May', '31 May', '4 Jun', '7 Jun', '11 Jun', '14 Jun', '18 Jun', '21 Jun', '25 Jun', '28 Jun', '2 Jul', '5 Jul', '9 Jul', '12 Jul', '16 Jul', '19 Jul', '23 Jul', '26 Jul', '30 Jul', '2 Aug', '6 Aug', '9 Aug', '13 Aug', '16 Aug', '20 Aug', '23 Aug', '27 Aug', '30 Aug', '3 Sep', '6 Sep', '10 Sep', '13 Sep', '17 Sep', '20 Sep', '24 Sep', '27 Sep', '1 Oct', '4 Oct', '8 Oct', '11 Oct', '15 Oct', '18 Oct', '22 Oct', '25 Oct', '29 Oct', '1 Nov', '5 Nov', '8 Nov', '12 Nov', '15 Nov', '19 Nov', '22 Nov', '26 Nov', '29 Nov', '3 Dec', '6 Dec', '10 Dec', '13 Dec', '17 Dec', '20 Dec', '24 Dec', '27 Dec', '31 Dec', '3 Jan', '7 Jan', '10 Jan', '14 Jan', '17 Jan', '21 Jan', '24 Jan', '28 Jan', '31 Jan', '4 Feb', '7 Feb', '11 Feb', '14 Feb', '18 Feb', '21 Feb', '25 Feb', '28 Feb', '4 Mar', '7 Mar', '11 Mar', '14 Mar', '18 Mar', '21 Mar', '25 Mar', '28 Mar', '1 Apr', '4 Apr', '8 Apr', '11 Apr', '15 Apr', '18 Apr', '22 Apr', '25 Apr', '29 Apr', '2 May', '6 May', '9 May', '13 May', '16 May', '20 May', '23 May', '27 May', '30 May', '3 Jun', '6 Jun', '10 Jun', '13 Jun', '17 Jun', '20 Jun', '24 Jun', '27 Jun'];
    var jackpots = [4.0, 5.0, 7.0, 4.0, 5.0, 6.0, 8.3, 4.0, 5.0, 6.0, 8.0, 10.5, 4.0, 5.0, 6.0, 8.0, 10.5, 4.0, 5.0, 6.0, 8.0, 11.0, 4.0, 5.3, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0, 15.0, 20.0, 23.3, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0, 15.0, 17.2, 4.0, 5.0, 10.0, 12.0, 15.0, 17.0, 20.0, 25.0, 30.2, 4.0, 5.0, 6.0, 8.0, 10.3, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0, 15.0, 17.0, 20.2, 4.0, 5.0, 6.0, 8.0, 10.0, 12.5, 4.0, 5.0, 6.0, 10.0, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0, 15.0, 17.0, 20.0, 23.0, 25.0, 28.0, 30.0, 33.0, 36.0, 40.0, 45.0, 55.2, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0, 16.0, 4.0, 5.0, 6.2, 4.0, 5.5, 4.0, 5.0, 6.0, 8.0, 10.2, 4.0, 5.3, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0, 15.2, 4.5, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0, 15.0, 17.0, 20.0, 23.0, 25.5, 4.0, 8.0, 10.0, 12.0, 14.3, 4.0, 5.5, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0, 15.0, 18.0, 20.0, 23.0, 25.0, 28.2, 4.5, 4.0, 5.0, 7.0, 10.0, 12.0, 15.0];
    var statuses = ['Rollover', 'Rollover', 'Won', 'Rollover', 'Rollover', 'Rollover', 'Won', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Won', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Won', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Won', 'Rollover', 'Won', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Won', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Won', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Won', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Won', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Won', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Won', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Won', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Won', 'Rollover', 'Rollover', 'Won', 'Rollover', 'Won', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Won', 'Rollover', 'Won', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Won', 'Won', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Won', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Won', 'Rollover', 'Won', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Won', 'Won', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover', 'Rollover'];

    var wonData = [], rolloverData = [];
    for (var i = 0; i < jackpots.length; i++) {
        if (statuses[i] === 'Won') {
            wonData.push({ value: jackpots[i], itemStyle: { color: accent, borderRadius: [4, 4, 0, 0] } });
            rolloverData.push(null);
        } else {
            wonData.push(null);
            rolloverData.push({ value: jackpots[i], itemStyle: { color: rule, borderRadius: [4, 4, 0, 0] } });
        }
    }
    var recordIdx = jackpots.indexOf(55.2);

    chart.setOption({
        animation: false, color: [accent, rule],
        tooltip: {
            trigger: 'axis', backgroundColor: '#1f2937', borderColor: '#374151',
            textStyle: { color: '#f9fafb', fontSize: 13 },
            formatter: function(params) {
                var s = params[0].axisValue + '<br/>';
                params.forEach(function(p) {
                    if (p.value != null) s += p.marker + ' ' + p.seriesName + ': $' + p.value.toFixed(1) + 'M<br/>';
                });
                return s;
            }
        },
        grid: { left: 60, right: 40, top: 50, bottom: 50 },
        title: { text: 'Powerball Jackpot History, 2025-2026', left: 'center', top: 8, textStyle: { fontSize: 15, fontWeight: 600, color: ink } },
        legend: { bottom: 0, textStyle: { color: ink, fontSize: 11 }, itemWidth: 18, itemHeight: 10 },
        dataZoom: [{ type: 'slider', bottom: 25, height: 18, borderColor: rule, backgroundColor: 'transparent', fillerColor: 'rgba(128,128,128,0.15)', handleStyle: { color: accent, borderColor: accent }, textStyle: { color: ink, fontSize: 10 }, start: 0, end: 100 }],
        xAxis: { type: 'category', data: dates, name: 'Draw date (2025-2026)', nameLocation: 'middle', nameGap: 35, nameTextStyle: { color: muted, fontSize: 12 }, axisLine: { lineStyle: { color: rule } }, axisTick: { show: false }, axisLabel: { color: ink, fontSize: 9, interval: 8, rotate: 45 } },
        yAxis: { type: 'value', name: 'Jackpot (NZD millions)', nameTextStyle: { color: muted, fontSize: 12 }, axisLine: { show: false }, axisTick: { show: false }, splitLine: { lineStyle: { color: rule } }, axisLabel: { color: ink, fontSize: 11, formatter: function(val) { return '$' + val + 'M'; } }, max: 60 },
        series: [
            { name: 'Rollover', type: 'bar', data: rolloverData, barWidth: '70%', stack: 'jackpot' },
            { name: 'Won', type: 'bar', data: wonData, barWidth: '70%', stack: 'jackpot', itemStyle: { color: accent },
                markLine: { silent: true, symbol: 'none', lineStyle: { color: accent2, type: 'dashed', width: 1.5 }, label: { show: true, position: 'start', color: accent2, fontSize: 10, fontWeight: 600, formatter: 'NZ Record $55.2M' }, data: [{ xAxis: dates[recordIdx] }] } }
        ]
    });
    window.addEventListener('resize', function() { chart.resize(); });
})();

/* ==================================================================
   Figure 3: Two Lenses of Probability
   ================================================================== */
(function() {
    var chart = echarts.init(document.getElementById('chart-two-lenses'), null, { renderer: 'svg' });

    var cats = [
        'Powerball Div 1\n(single line)',
        'Powerball Div 1\n(annual, 4 lines x 104 draws)',
        'Powerball Div 1\n(annual, 10 lines x 104 draws)',
        'Powerball struck\n(any given draw, ~2.5M lines)',
        'Powerball struck\n(annual, 25 wins in 156 draws)'
    ];
    var odds = [38383800, 92269, 36907, 15.9, 6.2];

    chart.setOption({
        animation: false, color: [accent, accent2],
        tooltip: { trigger: 'axis', backgroundColor: '#1f2937', borderColor: '#374151', textStyle: { color: '#f9fafb', fontSize: 13 },
            formatter: function(params) { return params[0].axisValue.replace(/\\n/g, ' ') + '<br/>' + params[0].marker + ' Odds: 1 in ' + Number(params[0].value).toLocaleString('en-NZ', { maximumFractionDigits: 1 }); }
        },
        grid: { left: 90, right: 80, top: 50, bottom: 70 },
        title: { text: 'Two Lenses of Probability: Raw Odds vs Empirical Reality', left: 'center', top: 8, textStyle: { fontSize: 14, fontWeight: 600, color: ink } },
        xAxis: { type: 'category', data: cats, axisLine: { lineStyle: { color: rule } }, axisTick: { show: false }, axisLabel: { color: ink, fontSize: 9, interval: 0 } },
        yAxis: { type: 'log', name: 'Odds (1 in X)', nameTextStyle: { color: muted, fontSize: 12 }, axisLine: { show: false }, axisTick: { show: false }, splitLine: { lineStyle: { color: rule } }, axisLabel: { color: ink, fontSize: 11, formatter: function(val) { if (val >= 1000000) return (val / 1000000).toFixed(0) + 'M'; if (val >= 1000) return (val / 1000).toFixed(0) + 'k'; return val.toFixed(0); } }, min: 1, max: 100000000 },
        series: [
            { type: 'bar', barWidth: '50%',
                data: odds.map(function(v, i) { return { value: v, itemStyle: { color: i < 3 ? accent : accent2, borderRadius: [6, 6, 0, 0] } }; }),
                label: { show: true, position: 'top', color: ink, fontSize: 10,
                    formatter: function(p) { var v = p.value; if (v >= 1000000) return '1 in ' + (v / 1000000).toFixed(1) + 'M'; if (v >= 1000) return '1 in ' + (v / 1000).toFixed(1) + 'k'; return '1 in ' + v.toFixed(1); }
                },
                markArea: { silent: true, label: { show: false },
                    data: [[[{ xAxis: cats[0], itemStyle: { color: 'rgba(128,128,128,0.04)' } }, { xAxis: cats[2], itemStyle: { color: 'rgba(128,128,128,0.04)' } }], [{ xAxis: cats[3], itemStyle: { color: 'rgba(128,128,128,0.04)' } }, { xAxis: cats[4], itemStyle: { color: 'rgba(128,128,128,0.04)' } }]] }
            },
            { type: 'scatter', data: [{ value: [cats[0], 38383800], symbolSize: 0 }, { value: [cats[4], 6.2], symbolSize: 0 }],
                markLine: { silent: true, symbol: 'none', lineStyle: { color: accent2, type: 'dashed', width: 2 }, label: { show: true, position: 'insideEndTop', color: accent2, fontSize: 9, fontWeight: 600, formatter: 'Unconditional\n(per-line)' }, data: [{ xAxis: cats[0] }] } }
        ]
    });
    window.addEventListener('resize', function() { chart.resize(); });
})();

})();
