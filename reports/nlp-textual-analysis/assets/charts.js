/*
 * Charts for: Textual Analysis and NLP in Accounting and Finance Research
 * Author: Dr Yuqian Zhang
 * Date: 10 July 2026
 */
(function () {
  "use strict";

  window._echartsReady = true;
  if (typeof echarts === "undefined") {
    return;
  }

  var css = getComputedStyle(document.documentElement);
  function v(name, fallback) {
    var value = css.getPropertyValue(name);
    return value ? value.trim() : fallback;
  }

  var INK = v("--ink", "#1f1e1a");
  var MUTED = v("--muted", "#6a6760");
  var RULE = v("--rule", "#e2ddd1");
  var ACCENT = v("--accent", "#1a3a2a");
  var ACCENT2 = v("--accent2", "#9e6b1f");
  var BG = v("--bg", "#faf9f3");

  var FONT_BODY = "Instrument Sans, -apple-system, sans-serif";
  var FONT_HEAD = "Crimson Pro, Georgia, serif";

  var PALETTE = [
    ACCENT,
    ACCENT2,
    "#3d6b5b",
    "#9e6b1f",
    "#2f6b4f",
    "#a33b2f",
    "#6a6760",
    "#c5a059"
  ];

  var registry = [];

  function baseGrid(extra) {
    var g = {
      left: 60,
      right: 24,
      top: 56,
      bottom: 48,
      containLabel: true
    };
    if (extra) {
      for (var k in extra) {
        if (Object.prototype.hasOwnProperty.call(extra, k)) {
          g[k] = extra[k];
        }
      }
    }
    return g;
  }

  function titleOpt(text) {
    return {
      text: text,
      left: 0,
      top: 6,
      textStyle: {
        color: INK,
        fontFamily: FONT_HEAD,
        fontWeight: 700,
        fontSize: 14,
        lineHeight: 18,
        width: 720,
        overflow: "break"
      }
    };
  }

  function baseTooltip(trigger) {
    return {
      trigger: trigger || "axis",
      appendToBody: true,
      backgroundColor: "#ffffff",
      borderColor: RULE,
      borderWidth: 1,
      textStyle: { color: INK, fontFamily: FONT_BODY, fontSize: 12 },
      axisPointer: { type: "shadow", shadowStyle: { color: "rgba(26,58,42,0.06)" } }
    };
  }

  function baseLegend(top, extra) {
    var l = {
      top: top || 30,
      left: 0,
      type: "scroll",
      itemWidth: 12,
      itemHeight: 12,
      itemGap: 12,
      textStyle: { color: MUTED, fontFamily: FONT_BODY, fontSize: 11 }
    };
    if (extra) {
      for (var k in extra) {
        if (Object.prototype.hasOwnProperty.call(extra, k)) {
          l[k] = extra[k];
        }
      }
    }
    return l;
  }

  function axisLabel() {
    return { color: MUTED, fontFamily: FONT_BODY, fontSize: 11 };
  }
  function axisLine() {
    return { lineStyle: { color: RULE } };
  }
  function splitLine() {
    return { lineStyle: { color: RULE, type: "dashed" } };
  }

  function mount(id, option) {
    var el = document.getElementById(id);
    if (!el) {
      return;
    }
    var chart = echarts.init(el, null, { renderer: "svg" });
    option.color = option.color || PALETTE;
    option.textStyle = { fontFamily: FONT_BODY };
    option.animation = false;
    chart.setOption(option);
    registry.push(chart);
  }

  /* ---------------------------------------------------------------
   * Embedded data (from data/*.csv, verified against source files)
   * --------------------------------------------------------------- */

  // nlp_publication_trends.csv
  var pubYears = [2005,2006,2007,2008,2009,2010,2011,2012,2013,2014,2015,2016,2017,2018,2019,2020,2021,2022,2023,2024,2025];
  var pubTop5 = [1,1,2,3,3,4,6,7,9,11,13,15,18,22,26,30,35,40,46,43,23];
  var pubTop4 = [1,2,2,2,3,4,6,8,9,11,12,15,17,20,24,28,33,38,44,42,22];
  var pubTotal = [2,3,4,5,6,8,12,15,18,22,25,30,35,42,50,58,68,78,90,85,45];
  var pubPhase = ["Early","Early","Early","Early","Early","Early","Growth","Growth","Growth","Growth","Growth","Growth","ML-Adoption","ML-Adoption","ML-Adoption","ML-Adoption","ML-Adoption","Deep-Learning","Deep-Learning","Deep-Learning","Deep-Learning"];

  // nlp_method_evolution.csv
  var methodPeriods = ["2005-2008","2009-2012","2013-2016","2017-2020","2021-2023","2024-2025"];
  var methodSeries = [
    { name: "Dictionary / bag-of-words", data: [85,70,55,40,25,15] },
    { name: "Readability", data: [10,15,15,10,5,5] },
    { name: "Topic modeling", data: [5,10,18,20,15,10] },
    { name: "Word embeddings", data: [0,5,10,20,20,15] },
    { name: "Traditional ML", data: [0,0,2,10,15,15] },
    { name: "Transformers / BERT", data: [0,0,0,5,20,25] },
    { name: "Large language models", data: [0,0,0,0,5,15] }
  ];

  // nlp_journal_distribution.csv (sorted ascending for horizontal bar)
  var journalRaw = [
    { abbr: "JAR", count: 52 },
    { abbr: "CAR", count: 48 },
    { abbr: "TAR", count: 45 },
    { abbr: "JAE", count: 38 },
    { abbr: "RAST", count: 35 },
    { abbr: "Other", count: 31 },
    { abbr: "JFE", count: 30 },
    { abbr: "RFS", count: 28 },
    { abbr: "JF", count: 25 },
    { abbr: "MS", count: 22 },
    { abbr: "JPE", count: 5 }
  ];
  journalRaw.sort(function (a, b) { return a.count - b.count; });
  var journalNames = journalRaw.map(function (d) { return d.abbr; });
  var journalCounts = journalRaw.map(function (d) { return d.count; });

  // nlp_citation_analysis.csv (top 10 by citations)
  var citationRaw = [
    { title: "Loughran & McDonald (2011): When Is a Liability Not a Liability?", cites: 5760 },
    { title: "Tetlock (2007): Giving Content to Investor Sentiment", cites: 4210 },
    { title: "Li (2008): Annual Report Readability", cites: 3710 },
    { title: "Loughran & McDonald (2016): Textual Analysis Survey", cites: 2580 },
    { title: "Hoberg & Phillips (2016): Text-Based Network Industries", cites: 2050 },
    { title: "Li (2010): Forward-Looking Statements", cites: 1890 },
    { title: "Gentzkow et al. (2019): Text as Data", cites: 1820 },
    { title: "Hoberg & Phillips (2010): Product Market Synergies", cites: 1410 },
    { title: "Loughran & McDonald (2014): Measuring Readability", cites: 1280 },
    { title: "Larcker & Zakolyukina (2012): Detecting Deceptive Discussions", cites: 1160 }
  ];
  citationRaw.sort(function (a, b) { return a.cites - b.cites; });
  var citationNames = citationRaw.map(function (d) { return d.title; });
  var citationValues = citationRaw.map(function (d) { return d.cites; });

  // nlp_application_area_trends.csv
  var appPeriods = ["2005-2008","2009-2012","2013-2016","2017-2020","2021-2023","2024-2025"];
  var appSeries = [
    { name: "Tone / sentiment", data: [6,15,25,40,50,28] },
    { name: "Readability / complexity", data: [3,8,15,20,18,10] },
    { name: "Similarity / novelty", data: [1,4,10,18,22,12] },
    { name: "Forward-looking / risk", data: [2,5,12,22,28,18] },
    { name: "Deception / fraud", data: [0,3,6,12,18,12] },
    { name: "Disclosure quality", data: [2,5,10,15,20,12] },
    { name: "Other", data: [1,3,5,8,12,8] }
  ];

  // nlp_data_source_trends.csv
  var srcPeriods = ["2005-2008","2009-2012","2013-2016","2017-2020","2021-2023","2024-2025"];
  var srcSeries = [
    { name: "10-K / 10-Q filings", data: [8,25,55,80,95,50] },
    { name: "MD&A section", data: [5,18,35,45,50,30] },
    { name: "Earnings calls", data: [2,8,25,45,60,35] },
    { name: "Analyst reports", data: [1,5,15,25,35,20] },
    { name: "Financial news", data: [3,10,22,35,40,25] },
    { name: "Social media", data: [0,2,5,12,20,15] },
    { name: "Patents", data: [0,1,3,8,12,8] },
    { name: "Regulatory communications", data: [0,3,8,15,22,15] }
  ];

  /* ---------------------------------------------------------------
   * Chart 1: Publication trends (stacked area)
   * --------------------------------------------------------------- */
  function chartPubTrends() {
    mount("chart-pub-trends", {
      title: titleOpt("Figure 1: Publication Trends of Textual Analysis Papers in Top Accounting and Finance Journals (2005-2025)"),
      tooltip: baseTooltip("axis"),
      legend: baseLegend(46, { data: ["Accounting Top 5", "Finance Top 4"] }),
      grid: baseGrid({ top: 82 }),
      xAxis: {
        type: "category",
        data: pubYears,
        boundaryGap: false,
        axisLabel: axisLabel(),
        axisLine: axisLine(),
        axisTick: { show: false }
      },
      yAxis: {
        type: "value",
        name: "Papers",
        nameTextStyle: { color: MUTED, fontFamily: FONT_BODY, fontSize: 11 },
        axisLabel: axisLabel(),
        axisLine: { show: false },
        splitLine: splitLine()
      },
      series: [
        {
          name: "Accounting Top 5",
          type: "line",
          stack: "total",
          areaStyle: { color: ACCENT, opacity: 0.55 },
          lineStyle: { color: ACCENT, width: 1.5 },
          itemStyle: { color: ACCENT },
          symbol: "none",
          data: pubTop5
        },
        {
          name: "Finance Top 4",
          type: "line",
          stack: "total",
          areaStyle: { color: ACCENT2, opacity: 0.55 },
          lineStyle: { color: ACCENT2, width: 1.5 },
          itemStyle: { color: ACCENT2 },
          symbol: "none",
          data: pubTop4
        }
      ]
    });
  }

  /* ---------------------------------------------------------------
   * Chart 2: Method evolution (stacked bar)
   * --------------------------------------------------------------- */
  function chartMethodEvolution() {
    var series = methodSeries.map(function (s) {
      return {
        name: s.name,
        type: "bar",
        stack: "method",
        emphasis: { focus: "series" },
        data: s.data
      };
    });
    mount("chart-method-evolution", {
      title: titleOpt("Figure 2: Evolution of NLP Methods in Accounting and Finance Research"),
      tooltip: baseTooltip("axis"),
      legend: baseLegend(30),
      grid: baseGrid({ top: 96 }),
      xAxis: {
        type: "category",
        data: methodPeriods,
        axisLabel: axisLabel(),
        axisLine: axisLine(),
        axisTick: { show: false }
      },
      yAxis: {
        type: "value",
        name: "Share of papers (%)",
        nameTextStyle: { color: MUTED, fontFamily: FONT_BODY, fontSize: 11 },
        axisLabel: axisLabel(),
        axisLine: { show: false },
        splitLine: splitLine()
      },
      series: series
    });
  }

  /* ---------------------------------------------------------------
   * Chart 3: Journal distribution (horizontal bar)
   * --------------------------------------------------------------- */
  function chartJournalDist() {
    mount("chart-journal-dist", {
      title: titleOpt("Figure 3: Distribution of Textual Analysis Publications by Journal"),
      tooltip: baseTooltip("axis"),
      grid: baseGrid({ top: 56, left: 70 }),
      xAxis: {
        type: "value",
        name: "Papers",
        nameTextStyle: { color: MUTED, fontFamily: FONT_BODY, fontSize: 11 },
        axisLabel: axisLabel(),
        axisLine: { show: false },
        splitLine: splitLine()
      },
      yAxis: {
        type: "category",
        data: journalNames,
        axisLabel: axisLabel(),
        axisLine: axisLine(),
        axisTick: { show: false }
      },
      series: [
        {
          name: "Papers",
          type: "bar",
          barWidth: "58%",
          itemStyle: { color: ACCENT },
          label: {
            show: true,
            position: "right",
            color: MUTED,
            fontFamily: FONT_BODY,
            fontSize: 11
          },
          data: journalCounts
        }
      ]
    });
  }

  /* ---------------------------------------------------------------
   * Chart 4: Most-cited papers (horizontal bar)
   * --------------------------------------------------------------- */
  function chartCitations() {
    mount("chart-citations", {
      title: titleOpt("Figure 4: Most-Cited Textual Analysis Papers in Accounting and Finance"),
      tooltip: baseTooltip("axis"),
      grid: baseGrid({ top: 56, left: 30, right: 60 }),
      xAxis: {
        type: "value",
        name: "Google Scholar citations",
        nameTextStyle: { color: MUTED, fontFamily: FONT_BODY, fontSize: 11 },
        axisLabel: axisLabel(),
        axisLine: { show: false },
        splitLine: splitLine()
      },
      yAxis: {
        type: "category",
        data: citationNames,
        axisLabel: {
          color: MUTED,
          fontFamily: FONT_BODY,
          fontSize: 10,
          width: 260,
          overflow: "break"
        },
        axisLine: axisLine(),
        axisTick: { show: false }
      },
      series: [
        {
          name: "Citations",
          type: "bar",
          barWidth: "60%",
          itemStyle: { color: ACCENT2 },
          label: {
            show: true,
            position: "right",
            color: MUTED,
            fontFamily: FONT_BODY,
            fontSize: 10
          },
          data: citationValues
        }
      ]
    });
  }

  /* ---------------------------------------------------------------
   * Chart 5: Application trends (stacked area)
   * --------------------------------------------------------------- */
  function chartAppTrends() {
    var series = appSeries.map(function (s) {
      return {
        name: s.name,
        type: "line",
        stack: "app",
        areaStyle: { opacity: 0.5 },
        lineStyle: { width: 1 },
        symbol: "none",
        emphasis: { focus: "series" },
        data: s.data
      };
    });
    mount("chart-app-trends", {
      title: titleOpt("Figure 5: Research Applications of Textual Analysis by Theme"),
      tooltip: baseTooltip("axis"),
      legend: baseLegend(30),
      grid: baseGrid({ top: 96 }),
      xAxis: {
        type: "category",
        data: appPeriods,
        boundaryGap: false,
        axisLabel: axisLabel(),
        axisLine: axisLine(),
        axisTick: { show: false }
      },
      yAxis: {
        type: "value",
        name: "Paper count",
        nameTextStyle: { color: MUTED, fontFamily: FONT_BODY, fontSize: 11 },
        axisLabel: axisLabel(),
        axisLine: { show: false },
        splitLine: splitLine()
      },
      series: series
    });
  }

  /* ---------------------------------------------------------------
   * Chart 6: Data sources (stacked area)
   * --------------------------------------------------------------- */
  function chartDataSources() {
    var series = srcSeries.map(function (s) {
      return {
        name: s.name,
        type: "line",
        stack: "src",
        areaStyle: { opacity: 0.5 },
        lineStyle: { width: 1 },
        symbol: "none",
        emphasis: { focus: "series" },
        data: s.data
      };
    });
    mount("chart-data-sources", {
      title: titleOpt("Figure 6: Textual Data Sources Used in Accounting and Finance Research"),
      tooltip: baseTooltip("axis"),
      legend: baseLegend(30),
      grid: baseGrid({ top: 96 }),
      xAxis: {
        type: "category",
        data: srcPeriods,
        boundaryGap: false,
        axisLabel: axisLabel(),
        axisLine: axisLine(),
        axisTick: { show: false }
      },
      yAxis: {
        type: "value",
        name: "Paper count",
        nameTextStyle: { color: MUTED, fontFamily: FONT_BODY, fontSize: 11 },
        axisLabel: axisLabel(),
        axisLine: { show: false },
        splitLine: splitLine()
      },
      series: series
    });
  }

  /* ---------------------------------------------------------------
   * Chart 7: Average annual publications by research phase (line)
   * --------------------------------------------------------------- */
  function chartPhaseGrowth() {
    var phaseOrder = ["Early", "Growth", "ML-Adoption", "Deep-Learning"];
    var phaseLabels = {
      "Early": "Early (2005-2010)",
      "Growth": "Growth (2011-2016)",
      "ML-Adoption": "ML-Adoption (2017-2021)",
      "Deep-Learning": "Deep-Learning (2022-2025)"
    };
    var sums = {};
    var counts = {};
    phaseOrder.forEach(function (p) { sums[p] = 0; counts[p] = 0; });
    for (var i = 0; i < pubTotal.length; i++) {
      var ph = pubPhase[i];
      sums[ph] += pubTotal[i];
      counts[ph] += 1;
    }
    var avgs = phaseOrder.map(function (p) {
      return Math.round((sums[p] / counts[p]) * 10) / 10;
    });
    var labels = phaseOrder.map(function (p) { return phaseLabels[p]; });
    mount("chart-phase-growth", {
      title: titleOpt("Figure 7: Average Annual Publications by Research Phase"),
      tooltip: baseTooltip("axis"),
      grid: baseGrid({ top: 60 }),
      xAxis: {
        type: "category",
        data: labels,
        boundaryGap: false,
        axisLabel: {
          color: MUTED,
          fontFamily: FONT_BODY,
          fontSize: 10,
          interval: 0,
          width: 120,
          overflow: "break"
        },
        axisLine: axisLine(),
        axisTick: { show: false }
      },
      yAxis: {
        type: "value",
        name: "Average papers per year",
        nameTextStyle: { color: MUTED, fontFamily: FONT_BODY, fontSize: 11 },
        axisLabel: axisLabel(),
        axisLine: { show: false },
        splitLine: splitLine()
      },
      series: [
        {
          name: "Average annual publications",
          type: "line",
          smooth: true,
          symbol: "circle",
          symbolSize: 9,
          lineStyle: { color: ACCENT, width: 2.5 },
          itemStyle: { color: ACCENT, borderColor: BG, borderWidth: 2 },
          areaStyle: { color: ACCENT, opacity: 0.12 },
          label: {
            show: true,
            position: "top",
            color: ACCENT,
            fontFamily: FONT_HEAD,
            fontWeight: 700,
            fontSize: 12
          },
          data: avgs
        }
      ]
    });
  }

  /* ---------------------------------------------------------------
   * Chart 8: Sentiment classification accuracy by method (grouped bar)
   * --------------------------------------------------------------- */
  function chartMethodAccuracy() {
    var methods = ["Dictionary", "Naive Bayes", "SVM", "Random Forest", "CNN", "LSTM", "BERT", "FinBERT"];
    var accuracy = [62, 74, 73, 72, 75, 76, 85, 88];
    var colors = methods.map(function (m, i) {
      if (m === "FinBERT" || m === "BERT") {
        return ACCENT2;
      }
      return i < 6 ? ACCENT : ACCENT2;
    });
    mount("chart-method-accuracy", {
      title: titleOpt("Figure 8: Sentiment Classification Accuracy by NLP Method"),
      tooltip: baseTooltip("axis"),
      grid: baseGrid({ top: 56 }),
      xAxis: {
        type: "category",
        data: methods,
        axisLabel: {
          color: MUTED,
          fontFamily: FONT_BODY,
          fontSize: 10,
          interval: 0,
          rotate: 20
        },
        axisLine: axisLine(),
        axisTick: { show: false }
      },
      yAxis: {
        type: "value",
        name: "Accuracy (%)",
        min: 50,
        max: 100,
        nameTextStyle: { color: MUTED, fontFamily: FONT_BODY, fontSize: 11 },
        axisLabel: axisLabel(),
        axisLine: { show: false },
        splitLine: splitLine()
      },
      series: [
        {
          name: "Accuracy",
          type: "bar",
          barWidth: "56%",
          data: accuracy.map(function (val, i) {
            return { value: val, itemStyle: { color: colors[i] } };
          }),
          label: {
            show: true,
            position: "top",
            color: INK,
            fontFamily: FONT_HEAD,
            fontWeight: 700,
            fontSize: 11,
            formatter: "{c}%"
          }
        }
      ]
    });
  }

  /* ---------------------------------------------------------------
   * Init + resize
   * --------------------------------------------------------------- */
  function renderAll() {
    chartPubTrends();
    chartMethodEvolution();
    chartJournalDist();
    chartCitations();
    chartAppTrends();
    chartDataSources();
    chartPhaseGrowth();
    chartMethodAccuracy();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", renderAll);
  } else {
    renderAll();
  }

  window.addEventListener("resize", function () {
    for (var i = 0; i < registry.length; i++) {
      registry[i].resize();
    }
  });

  if (typeof mermaid !== "undefined") {
    try {
      mermaid.initialize({
        startOnLoad: true,
        theme: "base",
        themeVariables: {
          fontFamily: FONT_HEAD,
          primaryColor: "#ffffff",
          primaryTextColor: INK,
          primaryBorderColor: ACCENT,
          lineColor: ACCENT2,
          tertiaryColor: BG
        }
      });
    } catch (e) {
      /* mermaid optional */
    }
  }
})();
