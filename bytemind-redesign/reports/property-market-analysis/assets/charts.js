// charts.js — NZ & AU Housing Market Analysis
// Author: Dr Yuqian Zhang, 8 July 2026

(function() {
  var style = getComputedStyle(document.documentElement);
  var accent = style.getPropertyValue('--accent').trim();
  var accent2 = style.getPropertyValue('--accent2').trim();
  var ink = style.getPropertyValue('--ink').trim();
  var muted = style.getPropertyValue('--muted').trim();
  var rule = style.getPropertyValue('--rule').trim();
  var bg2 = style.getPropertyValue('--bg2').trim();

  var commonTooltip = { trigger: 'axis', appendToBody: true };
  var commonGrid = { left: 60, right: 30, top: 40, bottom: 50 };

  // ============================================================
  // Chart 1: NZ & AU Real House Price Indices (BIS, 2010=100)
  // ============================================================
  (function() {
    var years = [];
    var nzReal = [];
    var auReal = [];
    var nzBIS = [
      [1970,40],[1975,48],[1980,48],[1985,55],[1990,60],
      [1995,68],[2000,72],[2005,90],[2010,100],[2015,120],
      [2018,138],[2019,142],[2020,155],[2021,178],[2022,168],
      [2023,168],[2024,163],[2025,159]
    ];
    var auBIS = [
      [1970,44],[1975,50],[1980,52],[1985,56],[1990,58],
      [1995,62],[2000,68],[2005,85],[2010,100],[2015,112],
      [2018,122],[2019,118],[2020,125],[2021,140],[2022,138],
      [2023,135],[2024,138],[2025,141]
    ];
    nzBIS.forEach(function(d) { years.push(d[0]+''); nzReal.push(d[1]); });
    auBIS.forEach(function(d) { auReal.push(d[1]); });

    var chart = echarts.init(document.getElementById('chart-real-hpi'), null, { renderer: 'svg' });
    chart.setOption({
      animation: false,
      tooltip: commonTooltip,
      grid: commonGrid,
      xAxis: { type: 'category', data: years, axisLabel: { color: muted, rotate: 45, fontSize: 10 }, axisLine: { lineStyle: { color: rule } } },
      yAxis: { type: 'value', name: 'Index (2010=100)', nameTextStyle: { color: muted }, axisLabel: { color: muted }, splitLine: { lineStyle: { color: rule } } },
      color: [accent, accent2],
      series: [
        { name: 'New Zealand', type: 'line', data: nzReal, smooth: true, lineStyle: { width: 2.5 }, symbol: 'none' },
        { name: 'Australia', type: 'line', data: auReal, smooth: true, lineStyle: { width: 2.5 }, symbol: 'none' }
      ]
    });
    window.addEventListener('resize', function() { chart.resize(); });
  })();

  // ============================================================
  // Chart 2: NZ Price-to-Income Ratio (OECD, 2015=100)
  // ============================================================
  (function() {
    var years = [
      '1986','1988','1990','1992','1994','1996','1998','2000','2002',
      '2004','2006','2008','2010','2012','2014','2016','2018','2019',
      '2020','2021','2022','2023','2024','2025'
    ];
    var pti = [
      56,58,60,55,57,62,64,63,72,86,93,88,89,94,100,112,118,
      122,132,142.9,135,117,107.3,105.8
    ];
    var median = 88.9;

    var chart = echarts.init(document.getElementById('chart-pti'), null, { renderer: 'svg' });
    chart.setOption({
      animation: false,
      tooltip: commonTooltip,
      grid: { left: 60, right: 30, top: 40, bottom: 50 },
      xAxis: { type: 'category', data: years, axisLabel: { color: muted, rotate: 45, fontSize: 10 }, axisLine: { lineStyle: { color: rule } } },
      yAxis: { type: 'value', name: 'Index (2015=100)', nameTextStyle: { color: muted }, axisLabel: { color: muted }, splitLine: { lineStyle: { color: rule } } },
      color: [accent],
      series: [
        { name: 'Price-to-Income Ratio', type: 'line', data: pti, smooth: true, lineStyle: { width: 2.5 }, symbol: 'none', areaStyle: { color: accent + '18' } },
        {
          name: 'Long-Run Median',
          type: 'line',
          data: Array(years.length).fill(median),
          lineStyle: { color: muted, type: 'dashed', width: 1.5 },
          symbol: 'none',
          itemStyle: { color: muted }
        }
      ]
    });
    window.addEventListener('resize', function() { chart.resize(); });
  })();

  // ============================================================
  // Chart 3: Real Price Deviation from Trend (NZ)
  // ============================================================
  (function() {
    var years = [
      '1990','1992','1994','1996','1998','2000','2002','2004',
      '2006','2008','2010','2012','2014','2016','2018','2019',
      '2020','2021','2022','2023','2024','2025'
    ];
    // Approximate deviation of real HPI from long-run trend (%)
    var deviation = [
      -12,-15,-10,-5,-8,-10,-6,2,12,5,0,2,8,18,22,24,30,38,
      28,20,12,8
    ];

    var chart = echarts.init(document.getElementById('chart-deviation'), null, { renderer: 'svg' });
    chart.setOption({
      animation: false,
      tooltip: { trigger: 'axis', appendToBody: true, formatter: function(p) { return p[0].axisValue + ': ' + (p[0].value >= 0 ? '+' : '') + p[0].value + '%'; } },
      grid: { left: 60, right: 30, top: 40, bottom: 50 },
      xAxis: { type: 'category', data: years, axisLabel: { color: muted, rotate: 45, fontSize: 10 }, axisLine: { lineStyle: { color: rule } } },
      yAxis: { type: 'value', name: 'Deviation (%)', nameTextStyle: { color: muted }, axisLabel: { color: muted }, splitLine: { lineStyle: { color: rule } } },
      series: [{
        name: 'Deviation from Trend',
        type: 'bar',
        data: deviation.map(function(v) { return { value: v, itemStyle: { color: v >= 0 ? accent2 : accent } }; }),
        barWidth: '60%'
      }]
    });
    window.addEventListener('resize', function() { chart.resize(); });
  })();

  // ============================================================
  // Chart 4: International Real House Price Comparison
  // ============================================================
  (function() {
    var countries = ['New Zealand', 'Australia', 'Ireland', 'Spain', 'Canada', 'Sweden'];
    var peakToTrough = [
      { val: 12, label: '-12%*' },  // NZ ongoing correction, approx -12% real from 2021 peak
      { val: 5, label: '-5%*' },    // AU minimal real correction
      { val: 54, label: '-54%' },   // Ireland 2007-2012
      { val: 41, label: '-41%' },   // Spain 2007-2015
      { val: 17, label: '-17%' },   // Canada 2022-
      { val: 30, label: '-30%' }    // Sweden 2022-2024 (real)
    ];

    var chart = echarts.init(document.getElementById('chart-intl-crashes'), null, { renderer: 'svg' });
    chart.setOption({
      animation: false,
      tooltip: { trigger: 'axis', appendToBody: true, formatter: function(p) { return p[0].name + ': peak-to-trough real decline ' + p[0].data.label; } },
      grid: { left: 120, right: 60, top: 30, bottom: 30 },
      xAxis: { type: 'value', name: 'Real Price Decline (%)', nameTextStyle: { color: muted }, axisLabel: { color: muted }, splitLine: { lineStyle: { color: rule } }, inverse: true },
      yAxis: { type: 'category', data: countries, axisLabel: { color: ink, fontWeight: 600 }, axisLine: { lineStyle: { color: rule } } },
      series: [{
        type: 'bar',
        data: peakToTrough.map(function(d) {
          return {
            value: d.val,
            itemStyle: { color: d.val >= 30 ? accent2 : (d.val >= 15 ? accent2 + 'aa' : accent) }
          };
        }),
        barWidth: '50%',
        label: { show: true, position: 'left', formatter: function(p) { return p.data.label; }, color: ink, fontSize: 11 }
      }]
    });
    window.addEventListener('resize', function() { chart.resize(); });
  })();

  // ============================================================
  // Chart 5: NZ Building Consents & Net Migration (1995-2025)
  // ============================================================
  (function() {
    var years = [];
    var consents = [];
    var migration = [];
    // Annual data: building consents (dwellings, thousands) & net migration (thousands)
    var data = [
      [1995, 21, 28], [1996, 20, 26], [1997, 18, 15], [1998, 17, -5], [1999, 20, -8],
      [2000, 20, -10], [2001, 21, 10], [2002, 26, 38], [2003, 31, 42], [2004, 31, 15],
      [2005, 25, 10], [2006, 24, 15], [2007, 26, 8], [2008, 19, 5], [2009, 15, 18],
      [2010, 17, 10], [2011, 14, -3], [2012, 17, -2], [2013, 21, 8], [2014, 24, 38],
      [2015, 28, 58], [2016, 30, 70], [2017, 31, 53], [2018, 33, 50], [2019, 35, 56],
      [2020, 39, 92], [2021, 48, 25], [2022, 50, 12], [2023, 45, 135], [2024, 34, 24],
      [2025, 36, 14]
    ];
    data.forEach(function(d) { years.push(d[0]+''); consents.push(d[1]); migration.push(d[2]); });

    var chart = echarts.init(document.getElementById('chart-supply'), null, { renderer: 'svg' });
    chart.setOption({
      animation: false,
      tooltip: commonTooltip,
      legend: { data: ['Building Consents (000s)', 'Net Migration (000s)'], textStyle: { color: muted }, top: 5 },
      grid: { left: 60, right: 60, top: 60, bottom: 50 },
      xAxis: { type: 'category', data: years, axisLabel: { color: muted, rotate: 45, fontSize: 10 }, axisLine: { lineStyle: { color: rule } } },
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
    window.addEventListener('resize', function() { chart.resize(); });
  })();

  // ============================================================
  // Chart 6: NZ Mortgage Rates (1-yr fixed) & Household DTI
  // ============================================================
  (function() {
    var years = [
      '2000','2002','2004','2006','2008','2010','2012','2014','2016','2018',
      '2019','2020','2021','2022','2023','2024','2025'
    ];
    var mortgageRate = [
      7.8,7.5,7.8,8.5,9.0,7.4,5.8,5.9,5.0,5.0,
      4.5,3.0,2.8,5.5,7.2,7.6,5.3
    ];
    var householdDTI = [
      95,105,115,125,140,145,142,145,155,160,
      162,165,170,170,168,167,165
    ];

    var chart = echarts.init(document.getElementById('chart-rates-dti'), null, { renderer: 'svg' });
    chart.setOption({
      animation: false,
      tooltip: commonTooltip,
      legend: { data: ['1-Year Fixed Mortgage Rate (%)', 'Household DTI (%)'], textStyle: { color: muted }, top: 5 },
      grid: { left: 60, right: 60, top: 60, bottom: 50 },
      xAxis: { type: 'category', data: years, axisLabel: { color: muted, rotate: 45, fontSize: 10 }, axisLine: { lineStyle: { color: rule } } },
      yAxis: [
        { type: 'value', name: 'Rate (%)', nameTextStyle: { color: muted }, axisLabel: { color: muted }, splitLine: { lineStyle: { color: rule } } },
        { type: 'value', name: 'DTI (%)', nameTextStyle: { color: muted }, axisLabel: { color: muted }, splitLine: { show: false }, min: 80 }
      ],
      color: [accent2, accent],
      series: [
        { name: '1-Year Fixed Mortgage Rate (%)', type: 'line', data: mortgageRate, smooth: true, lineStyle: { width: 2.5 }, symbol: 'circle', symbolSize: 4 },
        { name: 'Household DTI (%)', type: 'line', yAxisIndex: 1, data: householdDTI, smooth: true, lineStyle: { width: 2.5 }, symbol: 'circle', symbolSize: 4 }
      ]
    });
    window.addEventListener('resize', function() { chart.resize(); });
  })();

  // ============================================================
  // Chart 7: NZ Annual Real Price Growth with Policy Events
  // ============================================================
  (function() {
    var categories = [
      'RBNZ Inflation\nTargeting (1990)',
      'Low Rate Era\n(2002-07)',
      'GFC\n(2008)',
      'LVR Limits\n(2013)',
      'Auckland Unitary\nPlan (2016)',
      'Foreign Buyer\nBan (2018)',
      'COVID\nStimulus (2020)',
      'Bright-Line\n10yr (2021)',
      'OCR Hikes\n(2022-23)',
      'DTI Rules\n(2024)',
      'OCR Cuts\n(2024-25)'
    ];
    var growth = [3.5, 8.0, -8.5, 9.0, 12.0, 2.5, 25.0, -12.0, -16.0, -3.5, 1.2];

    var chart = echarts.init(document.getElementById('chart-policy'), null, { renderer: 'svg' });
    chart.setOption({
      animation: false,
      tooltip: { trigger: 'axis', appendToBody: true, formatter: function(p) { return p[0].name.replace(/\n/g,' ') + ': ' + (p[0].value >= 0 ? '+' : '') + p[0].value + '%'; } },
      grid: { left: 60, right: 30, top: 40, bottom: 80 },
      xAxis: { type: 'category', data: categories, axisLabel: { color: muted, fontSize: 9, rotate: 0, interval: 0 }, axisLine: { lineStyle: { color: rule } } },
      yAxis: { type: 'value', name: 'Real HPI Growth (% y/y)', nameTextStyle: { color: muted }, axisLabel: { color: muted }, splitLine: { lineStyle: { color: rule } } },
      series: [{
        name: 'Real HPI Growth',
        type: 'bar',
        data: growth.map(function(v) {
          return { value: v, itemStyle: { color: v >= 0 ? accent : accent2 } };
        }),
        barWidth: '55%'
      }]
    });
    window.addEventListener('resize', function() { chart.resize(); });
  })();

  // ============================================================
  // Chart 8: NZ Valuation Metrics Z-Score (Composite Overvaluation)
  // ============================================================
  (function() {
    var metrics = ['Price-to-\nIncome', 'Price-to-\nRent', 'Real HPI\nvs Trend', 'Household\nDTI'];
    var currentZScores = [0.85, 1.10, 0.65, 1.40];
    var peakZScores = [2.80, 2.95, 2.45, 1.55];

    var chart = echarts.init(document.getElementById('chart-zscores'), null, { renderer: 'svg' });
    chart.setOption({
      animation: false,
      tooltip: { trigger: 'axis', appendToBody: true },
      legend: { data: ['Current (Q1 2025)', 'Peak (Q4 2021)'], textStyle: { color: muted }, top: 5 },
      grid: { left: 90, right: 30, top: 60, bottom: 40 },
      xAxis: { type: 'value', name: 'Z-Score (standard deviations from mean)', nameTextStyle: { color: muted }, axisLabel: { color: muted }, splitLine: { lineStyle: { color: rule } } },
      yAxis: { type: 'category', data: metrics, axisLabel: { color: ink, fontWeight: 600 }, axisLine: { lineStyle: { color: rule } } },
      color: [accent, accent2 + '88'],
      series: [
        { name: 'Current (Q1 2025)', type: 'bar', data: currentZScores, barWidth: '40%', barGap: '10%' },
        { name: 'Peak (Q4 2021)', type: 'bar', data: peakZScores, barWidth: '40%' }
      ]
    });
    window.addEventListener('resize', function() { chart.resize(); });
  })();

})();
