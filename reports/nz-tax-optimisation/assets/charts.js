// charts.js — NZ SME & Personal Tax Optimisation
// Author: Dr Yuqian Zhang, 9 July 2026

(function() {
  var style = getComputedStyle(document.documentElement);
  var accent = style.getPropertyValue('--accent').trim();
  var accent2 = style.getPropertyValue('--accent2').trim();
  var ink = style.getPropertyValue('--ink').trim();
  var muted = style.getPropertyValue('--muted').trim();
  var rule = style.getPropertyValue('--rule').trim();
  var bg2 = style.getPropertyValue('--bg2').trim();

  var commonTooltip = { trigger: 'axis', appendToBody: true };

  // ============================================================
  // Chart 1: Marginal vs Effective Personal Tax Rate (2025/26)
  // Brackets: 10.5% to 15,600; 17.5% to 53,500; 30% to 78,100;
  //           33% to 180,000; 39% above.
  // ============================================================
  (function() {
    var incomes = [10,20,30,40,50,60,70,80,90,100,120,140,160,180,200,220,250,280,300];
    var effective = [10.5,12.0,13.9,14.8,15.3,17.0,18.9,20.3,21.8,22.9,24.6,25.8,26.7,27.4,28.5,29.5,30.6,31.5,32.0];
    var marginal = [10.5,17.5,17.5,17.5,17.5,30,30,33,33,33,33,33,33,33,39,39,39,39,39];
    var labels = incomes.map(function(v){ return '$' + v + 'k'; });

    var chart = echarts.init(document.getElementById('chart-marginal-effective'), null, { renderer: 'svg' });
    chart.setOption({
      animation: false,
      tooltip: {
        trigger: 'axis', appendToBody: true,
        formatter: function(p) {
          var out = p[0].axisValue;
          p.forEach(function(s){ out += '<br>' + s.marker + s.seriesName + ': ' + s.value + '%'; });
          return out;
        }
      },
      legend: { data: ['Marginal rate', 'Effective (average) rate'], textStyle: { color: muted }, top: 5 },
      grid: { left: 60, right: 30, top: 55, bottom: 60 },
      xAxis: { type: 'category', data: labels, name: 'Taxable income', nameLocation: 'middle', nameGap: 40, nameTextStyle: { color: muted }, axisLabel: { color: muted, rotate: 45, fontSize: 10 }, axisLine: { lineStyle: { color: rule } } },
      yAxis: { type: 'value', name: 'Rate (%)', max: 40, nameTextStyle: { color: muted }, axisLabel: { color: muted, formatter: '{value}%' }, splitLine: { lineStyle: { color: rule } } },
      color: [accent2, accent],
      series: [
        { name: 'Marginal rate', type: 'line', data: marginal, step: 'end', lineStyle: { width: 2.5 }, symbol: 'none' },
        { name: 'Effective (average) rate', type: 'line', data: effective, smooth: true, lineStyle: { width: 2.5 }, symbol: 'none', areaStyle: { color: accent + '14' } }
      ]
    });
    window.addEventListener('resize', function() { chart.resize(); });
  })();

  // ============================================================
  // Chart 2: Current-year tax on $250,000 profit, by structure
  // Sole trader: 76,578; Company (retain all): 70,000;
  // Salary $180k + retain $70k: 49,278 + 19,600 = 68,878.
  // ============================================================
  (function() {
    var categories = ['Sole trader\n(all personal)', 'Company\n(retain all $250k)', 'Salary $180k +\nretain $70k'];
    var tax = [76578, 70000, 68878];

    var chart = echarts.init(document.getElementById('chart-entity'), null, { renderer: 'svg' });
    chart.setOption({
      animation: false,
      tooltip: { trigger: 'axis', appendToBody: true, formatter: function(p) { return p[0].name.replace(/\n/g,' ') + ': $' + p[0].value.toLocaleString(); } },
      grid: { left: 75, right: 40, top: 30, bottom: 60 },
      xAxis: { type: 'category', data: categories, axisLabel: { color: muted, fontSize: 10, interval: 0 }, axisLine: { lineStyle: { color: rule } } },
      yAxis: { type: 'value', name: 'Current-year tax ($)', nameTextStyle: { color: muted }, axisLabel: { color: muted, formatter: function(v){ return '$' + (v/1000) + 'k'; } }, splitLine: { lineStyle: { color: rule } } },
      series: [{
        name: 'Current-year tax',
        type: 'bar',
        data: tax.map(function(v, i) { return { value: v, itemStyle: { color: i === 0 ? accent2 : accent } }; }),
        barWidth: '50%',
        label: { show: true, position: 'top', formatter: function(p){ return '$' + p.value.toLocaleString(); }, color: ink, fontSize: 11 }
      }]
    });
    window.addEventListener('resize', function() { chart.resize(); });
  })();

  // ============================================================
  // Chart 3: Investment Boost year-one deduction ($100k asset, 10% DV)
  // Without: 10,000. With: 20,000 boost + 8,000 depreciation = 28,000.
  // ============================================================
  (function() {
    var categories = ['Standard\ndepreciation only', 'Investment Boost\n+ depreciation'];

    var chart = echarts.init(document.getElementById('chart-invboost'), null, { renderer: 'svg' });
    chart.setOption({
      animation: false,
      tooltip: { trigger: 'axis', appendToBody: true, axisPointer: { type: 'shadow' } },
      legend: { data: ['20% Investment Boost', 'Year-one depreciation'], textStyle: { color: muted }, top: 5 },
      grid: { left: 70, right: 40, top: 55, bottom: 45 },
      xAxis: { type: 'category', data: categories, axisLabel: { color: muted, fontSize: 10, interval: 0 }, axisLine: { lineStyle: { color: rule } } },
      yAxis: { type: 'value', name: 'Year-one deduction ($)', nameTextStyle: { color: muted }, axisLabel: { color: muted, formatter: function(v){ return '$' + (v/1000) + 'k'; } }, splitLine: { lineStyle: { color: rule } } },
      color: [accent2, accent],
      series: [
        { name: '20% Investment Boost', type: 'bar', stack: 'total', data: [0, 20000], barWidth: '45%' },
        { name: 'Year-one depreciation', type: 'bar', stack: 'total', data: [10000, 8000], barWidth: '45%',
          label: { show: true, position: 'top', formatter: function(p){ return p.dataIndex === 0 ? '$10,000' : '$28,000'; }, color: ink, fontSize: 11 } }
      ]
    });
    window.addEventListener('resize', function() { chart.resize(); });
  })();

  // ============================================================
  // Chart 4: KiwiSaver default minimum contribution rate (Budget 2025)
  // ============================================================
  (function() {
    var categories = ['To 31 Mar 2026', 'From 1 Apr 2026', 'From 1 Apr 2028'];
    var rates = [3.0, 3.5, 4.0];

    var chart = echarts.init(document.getElementById('chart-kiwisaver'), null, { renderer: 'svg' });
    chart.setOption({
      animation: false,
      tooltip: { trigger: 'axis', appendToBody: true, formatter: function(p) { return p[0].name + ': ' + p[0].value + '% (employee and matching employer)'; } },
      grid: { left: 55, right: 30, top: 30, bottom: 40 },
      xAxis: { type: 'category', data: categories, axisLabel: { color: muted, fontSize: 11, interval: 0 }, axisLine: { lineStyle: { color: rule } } },
      yAxis: { type: 'value', name: 'Rate (%)', min: 0, max: 5, nameTextStyle: { color: muted }, axisLabel: { color: muted, formatter: '{value}%' }, splitLine: { lineStyle: { color: rule } } },
      series: [{
        name: 'Default minimum rate',
        type: 'bar',
        data: rates,
        barWidth: '45%',
        itemStyle: { color: accent },
        label: { show: true, position: 'top', formatter: '{c}%', color: ink, fontSize: 12 }
      }]
    });
    window.addEventListener('resize', function() { chart.resize(); });
  })();

  // ============================================================
  // Chart 5: Headline tax rates on income vehicles
  // ============================================================
  (function() {
    var items = [
      { name: 'Top personal rate', val: 39 },
      { name: 'Trustee (trust) rate', val: 39 },
      { name: 'Company profit\ndistributed to top shareholder', val: 39 },
      { name: 'Company rate (retained)', val: 28 },
      { name: 'PIE income (max PIR)', val: 28 }
    ];

    var chart = echarts.init(document.getElementById('chart-rate-arbitrage'), null, { renderer: 'svg' });
    chart.setOption({
      animation: false,
      tooltip: { trigger: 'axis', appendToBody: true, formatter: function(p) { return p[0].name.replace(/\n/g,' ') + ': ' + p[0].value + '%'; } },
      grid: { left: 180, right: 50, top: 20, bottom: 40 },
      xAxis: { type: 'value', name: 'Headline rate (%)', max: 45, nameTextStyle: { color: muted }, axisLabel: { color: muted, formatter: '{value}%' }, splitLine: { lineStyle: { color: rule } } },
      yAxis: { type: 'category', data: items.map(function(d){ return d.name; }), axisLabel: { color: ink, fontSize: 10, fontWeight: 600 }, axisLine: { lineStyle: { color: rule } } },
      series: [{
        type: 'bar',
        data: items.map(function(d) { return { value: d.val, itemStyle: { color: d.val <= 28 ? accent : accent2 } }; }),
        barWidth: '55%',
        label: { show: true, position: 'right', formatter: '{c}%', color: ink, fontSize: 11 }
      }]
    });
    window.addEventListener('resize', function() { chart.resize(); });
  })();

})();
