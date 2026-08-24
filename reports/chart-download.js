/**
 * Chart download utility with copyright overlay
 * Author: Dr Yuqian Zhang, Auckland University of Technology & ByteMind Ltd
 * Date: 29 July 2026
 *
 * This script adds a download button below each ECharts figure and embeds
 * a copyright notice and citation on exported PNG images.
 */
(function () {
  "use strict";

  if (typeof echarts === "undefined") {
    console.warn("ECharts not loaded; chart-download.js skipped.");
    return;
  }

  var BUTTON_DELAY_MS = 600;

  function getReportTitle() {
    var t = document.querySelector("title");
    return t ? t.textContent.trim() : "Research Brief";
  }

  function getReportUrl() {
    return window.location.href.replace(/\/$/, "");
  }

  function getReportDate() {
    var meta = document.querySelector("header .meta, footer, .footer-note");
    if (meta) {
      var txt = meta.textContent;
      var m = txt.match(/(\d{1,2}\s+\w+\s+\d{4})/);
      if (m) return m[1];
      m = txt.match(/(\d{4}-\d{2}-\d{2})/);
      if (m) return m[1];
    }
    return "2026";
  }

  var REPORT_TITLE = getReportTitle();
  var REPORT_URL = getReportUrl();
  var REPORT_DATE = getReportDate();

  var copyrightLine = "\u00A9 Dr Yuqian Zhang, Auckland University of Technology & ByteMind Ltd. All rights reserved.";
  var citationLine = "Source: Zhang, Y. (" + REPORT_DATE.split(" ").pop() + "). " + REPORT_TITLE + ". Available at: " + REPORT_URL;

  function addDownloadButtons() {
    var containers = document.querySelectorAll(".chart-container, .chart-figure");
    if (containers.length === 0) {
      return;
    }
    containers.forEach(function (container) {
      if (container.querySelector(".chart-download-btn")) return;

      var figureTitle = container.querySelector("h4, figcaption, .chart-title");
      var figureId = figureTitle ? figureTitle.textContent.trim().replace(/^Figure\s+\d+[:.\s]*/, "").replace(/[^a-zA-Z0-9_\-]/g, "_").substring(0, 60) : "chart";

      var boxes = container.querySelectorAll(".chart-box[id], .chart-box-tall[id], .chart-box-short[id], .chart-box[id][role]");
      boxes.forEach(function (chartBox) {
        if (!chartBox.id) return;
        if (chartBox.parentNode.querySelector(".chart-download-btn")) return;

        var btn = document.createElement("button");
        btn.className = "chart-download-btn";
        btn.textContent = "Download PNG";
        btn.title = "Download chart as PNG with copyright notice";

        btn.addEventListener("click", function (e) {
          e.preventDefault();
          e.stopPropagation();
          downloadChart(chartBox, chartBox.id);
        });

        chartBox.insertAdjacentElement("afterend", btn);
      });
    });
  }

  function wrapText(ctx, text, maxWidth) {
    var words = text.split(" ");
    var lines = [];
    var currentLine = "";
    for (var i = 0; i < words.length; i++) {
      var testLine = currentLine ? currentLine + " " + words[i] : words[i];
      var metrics = ctx.measureText(testLine);
      if (metrics.width > maxWidth && currentLine) {
        lines.push(currentLine);
        currentLine = words[i];
      } else {
        currentLine = testLine;
      }
    }
    if (currentLine) lines.push(currentLine);
    return lines;
  }

  function downloadChart(domEl, filename) {
    var chart = echarts.getInstanceByDom(domEl);
    if (!chart) return;

    try {
      var imgDataUrl = chart.getDataURL({
        type: "png",
        pixelRatio: 2,
        backgroundColor: "#ffffff",
      });
    } catch (err) {
      console.error("Failed to export chart image:", err);
      return;
    }

    var img = new Image();
    img.onload = function () {
      var canvas = document.createElement("canvas");
      var ctx = canvas.getContext("2d");

      var MIN_WIDTH = 1200;
      var paddingTop = 24;
      var paddingX = 40;
      var lineHeight = 18;

      canvas.width = Math.max(img.width, MIN_WIDTH);
      var contentWidth = canvas.width - paddingX * 2;

      ctx.font = "11px Georgia, 'Times New Roman', serif";
      var citationLines = wrapText(ctx, citationLine, contentWidth);

      ctx.font = "12px Georgia, 'Times New Roman', serif";
      var copyrightLines = wrapText(ctx, copyrightLine, contentWidth);

      var footerHeight = (copyrightLines.length + citationLines.length) * lineHeight + 20;
      canvas.height = img.height + footerHeight + paddingTop;

      ctx.fillStyle = "#ffffff";
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      var imgX = Math.max(0, (canvas.width - img.width) / 2);
      ctx.drawImage(img, imgX, paddingTop, img.width, img.height);

      ctx.fillStyle = "#44403c";
      ctx.textAlign = "center";

      var y = img.height + paddingTop + 12;
      ctx.font = "12px Georgia, 'Times New Roman', serif";
      for (var i = 0; i < copyrightLines.length; i++) {
        ctx.fillText(copyrightLines[i], canvas.width / 2, y);
        y += lineHeight;
      }

      ctx.font = "11px Georgia, 'Times New Roman', serif";
      for (var j = 0; j < citationLines.length; j++) {
        ctx.fillText(citationLines[j], canvas.width / 2, y);
        y += lineHeight;
      }

      var link = document.createElement("a");
      link.download = filename + ".png";
      link.href = canvas.toDataURL("image/png");
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    };
    img.onerror = function () {
      console.error("Failed to load chart image for download.");
    };
    img.src = imgDataUrl;
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      setTimeout(addDownloadButtons, BUTTON_DELAY_MS);
    });
  } else {
    setTimeout(addDownloadButtons, BUTTON_DELAY_MS);
  }
})();
