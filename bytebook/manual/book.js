/* The handbook reader.

   A chapter is laid out as a column of pages one screen wide. Turning a page
   slides that column and swings a copy of the page about the spine, so the
   book behaves like a book rather than a very long web page.

   Everything else here is the furniture around that: a contents rail, search,
   a memory of where you were, and a clean view when the book is embedded in
   another page. No dependencies, and no network calls except its own index. */
(function () {
  "use strict";

  var STORE_KEY = "bytebook-handbook";
  var book = readStore();
  var embedded = /[?&]embed=1\b/.test(location.search);
  var chapterSlug = (location.pathname.split("/").pop() || "index.html").replace(".html", "");

  /* ── Where you were ─────────────────────────────────────────────────── */
  function readStore() {
    try {
      return JSON.parse(localStorage.getItem(STORE_KEY)) || {};
    } catch (error) {
      return {};
    }
  }

  function writeStore(patch) {
    try {
      localStorage.setItem(STORE_KEY, JSON.stringify(Object.assign(book, patch)));
    } catch (error) {
      /* a private window still reads fine without the memory */
    }
  }

  function isAChapter() {
    return chapterSlug !== "index" && chapterSlug !== "all" && chapterSlug !== "citations";
  }

  if (embedded) {
    document.body.classList.add("embed");
    // A reader who follows a previous/next link inside the frame must stay in
    // reading mode, so every link that stays in the book keeps the flag.
    var localLinks = document.querySelectorAll('a[href$=".html"]');
    for (var linkIndex = 0; linkIndex < localLinks.length; linkIndex++) {
      var href = localLinks[linkIndex].getAttribute("href");
      if (!href || href.charAt(0) === "#" || href.indexOf("://") !== -1) continue;
      if (href.indexOf("embed=1") !== -1) continue;
      localLinks[linkIndex].setAttribute(
        "href",
        href + (href.indexOf("?") === -1 ? "?embed=1" : "&embed=1")
      );
    }
    window.addEventListener("load", function () {
      if (window.parent !== window) {
        window.parent.postMessage(
          { type: "bytebook-handbook", slug: chapterSlug, title: document.title },
          "*"
        );
      }
    });
  }

  /* ── The pages ──────────────────────────────────────────────────────── */
  var pageView = document.getElementById("book-pages");
  var pageInner = document.getElementById("book-pages-inner");
  var counter = document.getElementById("book-turn-count");
  var turnButtons = document.querySelectorAll("[data-turn]");
  var chapterPager = document.querySelector(".book-pager");
  var previousChapter = document.querySelector(".book-pager-link:not(.book-pager-next)");
  var nextChapter = document.querySelector(".book-pager-next");
  var progressBar = document.getElementById("reading-progress");
  var still = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  var pageCount = 1;
  var pageIndex = 0;
  var stride = 0;
  var turning = false;

  function gap() {
    if (!pageInner) return 0;
    var value = parseFloat(getComputedStyle(pageInner).columnGap);
    return isNaN(value) ? 0 : value;
  }

  function measure() {
    if (!pageView || !pageInner) return;
    var width = Math.round(pageView.clientWidth);
    if (!width) return;
    var space = gap();
    // One column per page: the width of the column container is the width of a
    // page, so anything longer flows into the pages beside it.
    pageInner.style.columnWidth = width + "px";
    pageInner.style.width = width + "px";
    stride = width + space;
    pageCount = Math.max(1, Math.round((pageInner.scrollWidth + space) / stride));
    if (counter) counter.textContent = "Page " + (pageIndex + 1) + " of " + pageCount;
    updateButtons();
    markProgress();
  }

  function updateButtons() {
    for (var i = 0; i < turnButtons.length; i++) {
      var step = Number(turnButtons[i].getAttribute("data-turn"));
      var atStart = step < 0 && pageIndex === 0 && !previousChapter;
      var atEnd = step > 0 && pageIndex >= pageCount - 1 && !nextChapter;
      turnButtons[i].disabled = atStart || atEnd;
    }
  }

  function markProgress() {
    if (!progressBar || !isAChapter()) return;
    var within = pageCount > 1 ? pageIndex / (pageCount - 1) : 1;
    progressBar.style.width = ((within * 100).toFixed(1)) + "%";
  }

  function remember() {
    if (!isAChapter()) return;
    writeStore({
      chapter: chapterSlug,
      page: pageIndex,
      pages: pageCount,
      seen: Object.assign(book.seen || {}, { [chapterSlug]: pageIndex })
    });
  }

  function place(animate) {
    if (!pageInner) return;
    pageInner.style.transition = animate && !still ? "" : "none";
    pageInner.style.transform = "translateX(" + (-pageIndex * stride) + "px)";
    // A link to a heading makes the browser scroll this box on its own. The
    // pages are moved by the transform above, so that scroll is undone.
    if (pageView) pageView.scrollLeft = 0;
    if (counter) counter.textContent = "Page " + (pageIndex + 1) + " of " + pageCount;
    updateButtons();
    markProgress();
    remember();
  }

  function leaf(showPage, direction) {
    if (!pageView || !pageInner || still) return;
    var clone = pageInner.cloneNode(true);
    clone.removeAttribute("id");
    clone.style.transform = "translateX(" + (-showPage * stride) + "px)";
    var sheet = document.createElement("div");
    sheet.className = "book-leaf " + (direction > 0 ? "leaf-out" : "leaf-in");
    sheet.appendChild(clone);
    pageView.appendChild(sheet);
    window.requestAnimationFrame(function () {
      window.requestAnimationFrame(function () { sheet.classList.add("running"); });
    });
    sheet.addEventListener("animationend", function () {
      if (sheet.parentNode) sheet.parentNode.removeChild(sheet);
    });
  }

  function showPage(target, animate) {
    if (!pageInner || turning) return;
    if (target < 0) {
      if (previousChapter) location.href = previousChapter.getAttribute("href");
      return;
    }
    if (target > pageCount - 1) {
      if (nextChapter) location.href = nextChapter.getAttribute("href");
      return;
    }
    if (target === pageIndex) return;
    var direction = target > pageIndex ? 1 : -1;
    var from = pageIndex;
    pageIndex = target;
    if (animate && !still) {
      turning = true;
      // The page underneath is already the new one; the leaf covers it, or
      // arrives over it, while the turn plays out.
      place(true);
      leaf(direction > 0 ? from : pageIndex, direction);
      window.setTimeout(function () { turning = false; }, 560);
    } else {
      place(false);
    }
  }

  /* A search result points at a heading. Find the page it sits on. */
  function pageOfHash() {
    if (!location.hash || !pageInner || !stride) return 0;
    var id = decodeURIComponent(location.hash.slice(1));
    var target = document.getElementById(id);
    if (!target || !pageInner.contains(target)) return 0;
    return Math.max(0, Math.floor(target.offsetLeft / stride));
  }

  if (pageView && pageInner) {
    measure();
    pageIndex = pageOfHash();
    pageIndex = Math.min(pageIndex, pageCount - 1);
    place(false);
    window.addEventListener("hashchange", function () {
      pageIndex = Math.min(pageOfHash(), pageCount - 1);
      place(true);
    });

    for (var b = 0; b < turnButtons.length; b++) {
      turnButtons[b].addEventListener("click", function (event) {
        showPage(pageIndex + Number(event.currentTarget.getAttribute("data-turn")), true);
      });
    }

    // Keyboard: arrows and space turn the page, and carry on into the next
    // chapter at either end.
    document.addEventListener("keydown", function (event) {
      if (event.metaKey || event.ctrlKey || event.altKey) return;
      var tag = (event.target.tagName || "").toLowerCase();
      if (tag === "input" || tag === "textarea" || tag === "select") return;
      if (searchOpen()) return;
      if (event.key === "ArrowRight" || event.key === "PageDown") {
        event.preventDefault();
        showPage(pageIndex + 1, true);
      } else if (event.key === "ArrowLeft" || event.key === "PageUp") {
        event.preventDefault();
        showPage(pageIndex - 1, true);
      } else if (event.key === " ") {
        event.preventDefault();
        showPage(pageIndex + (event.shiftKey ? -1 : 1), true);
      }
    });

    // A phone or a trackpad: swipe to turn.
    var touchStart = null;
    pageView.addEventListener("touchstart", function (event) {
      touchStart = event.changedTouches[0].clientX;
    }, { passive: true });
    pageView.addEventListener("touchend", function (event) {
      if (touchStart === null) return;
      var moved = event.changedTouches[0].clientX - touchStart;
      touchStart = null;
      if (Math.abs(moved) < 45) return;
      showPage(pageIndex + (moved < 0 ? 1 : -1), true);
    }, { passive: true });

    var resizeTimer = null;
    window.addEventListener("resize", function () {
      window.clearTimeout(resizeTimer);
      resizeTimer = window.setTimeout(function () {
        // Hold the reader's place: find the block they were looking at, and
        // put it back on screen at its new page.
        var marks = pageInner.querySelectorAll("h2, h3, p, li, table, .callout");
        var anchor = null;
        var edge = pageIndex * stride - 8;
        for (var i = 0; i < marks.length; i++) {
          if (marks[i].offsetLeft >= edge) { anchor = marks[i]; break; }
        }
        measure();
        if (anchor) pageIndex = Math.max(0, Math.min(pageCount - 1, Math.floor(anchor.offsetLeft / stride)));
        place(false);
      }, 160);
    });

    // Coming back to a chapter you were reading.
    if (!embedded && book.chapter === chapterSlug && typeof book.page === "number" && book.page > 0) {
      var resume = document.createElement("button");
      resume.type = "button";
      resume.className = "book-bar-btn";
      resume.textContent = "Resume";
      resume.addEventListener("click", function () {
        showPage(Math.min(book.page, pageCount - 1), true);
      });
      var bar = document.querySelector(".book-bar");
      if (bar) bar.appendChild(resume);
    }
  }

  /* ── Contents drawer on a small screen ──────────────────────────────── */
  var nav = document.getElementById("book-nav");
  var contentsToggle = document.getElementById("contents-toggle");
  if (nav && contentsToggle) {
    contentsToggle.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      contentsToggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    nav.addEventListener("click", function (event) {
      if (event.target.closest("a")) {
        nav.classList.remove("open");
        contentsToggle.setAttribute("aria-expanded", "false");
      }
    });
    var main = document.getElementById("book-main");
    if (main) {
      main.addEventListener("click", function () {
        if (nav.classList.contains("open")) {
          nav.classList.remove("open");
          contentsToggle.setAttribute("aria-expanded", "false");
        }
      });
    }
  }

  /* ── Search ─────────────────────────────────────────────────────────── */
  var overlay = document.getElementById("book-search");
  var input = document.getElementById("search-input");
  var results = document.getElementById("search-results");
  var searchToggle = document.getElementById("search-toggle");
  var index = null;
  var matches = [];
  var selected = 0;

  function searchOpen() {
    return overlay && !overlay.hidden;
  }

  function openSearch() {
    if (!overlay) return;
    overlay.hidden = false;
    if (searchToggle) searchToggle.setAttribute("aria-expanded", "true");
    if (!index) {
      results.innerHTML = '<p class="search-empty">Loading…</p>';
      fetch("search-index.json")
        .then(function (response) {
          return response.json();
        })
        .then(function (data) {
          index = data;
          run("");
        })
        .catch(function () {
          results.innerHTML =
            '<p class="search-empty">The index could not be loaded. Open the book from the website to search it.</p>';
        });
    } else {
      run(input.value);
    }
    input.focus();
    input.select();
  }

  function closeSearch() {
    if (!overlay) return;
    overlay.hidden = true;
    if (searchToggle) searchToggle.setAttribute("aria-expanded", "false");
    if (input) input.value = "";
  }

  function highlight(text, terms) {
    var escaped = text.replace(/[&<>"]/g, function (character) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[character];
    });
    terms.forEach(function (term) {
      escaped = escaped.replace(
        new RegExp("(" + term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "gi"),
        "<mark>$1</mark>"
      );
    });
    return escaped;
  }

  function run(query) {
    if (!index) return;
    var terms = query.toLowerCase().split(/\s+/).filter(function (term) {
      return term.length > 1;
    });
    matches = index
      .map(function (entry) {
        var haystack = (entry.title + " " + entry.text + " " + entry.chapterTitle).toLowerCase();
        var score = 0;
        if (!terms.length) score = 0;
        else {
          for (var i = 0; i < terms.length; i++) {
            var at = haystack.indexOf(terms[i]);
            if (at === -1) return null;
            score += 40 - Math.min(30, Math.floor(at / 60));
            if (entry.title.toLowerCase().indexOf(terms[i]) !== -1) score += 45;
            if (entry.chapterTitle.toLowerCase().indexOf(terms[i]) !== -1) score += 25;
          }
        }
        return { entry: entry, score: score };
      })
      .filter(Boolean);

    if (!terms.length) {
      matches = matches.slice(0, 6);
    } else {
      matches.sort(function (a, b) {
        return b.score - a.score;
      });
      matches = matches.slice(0, 20);
    }
    selected = 0;
    render(terms);
  }

  function render(terms) {
    if (!matches.length) {
      results.innerHTML =
        '<p class="search-empty">Nothing matched. Try a shorter word, or a term from the glossary.</p>';
      return;
    }
    var html = matches
      .map(function (match, position) {
        var entry = match.entry;
        var snippet = entry.text;
        if (terms.length) {
          var at = entry.text.toLowerCase().indexOf(terms[0]);
          if (at > 80) snippet = "…" + entry.text.slice(at - 80);
        }
        snippet = snippet.slice(0, 190) + "…";
        return (
          '<a class="search-result" role="option" aria-selected="' +
          (position === selected ? "true" : "false") +
          '" href="' +
          entry.chapter +
          ".html" +
          (entry.section ? "#" + entry.section : "") +
          '">' +
          '<span class="search-result-part">' +
          highlight(entry.part, terms) +
          " · Chapter " +
          entry.chapterNumber +
          "</span>" +
          '<span class="search-result-title">' +
          highlight(entry.title, terms) +
          "</span>" +
          '<span class="search-result-snippet">' +
          highlight(snippet, terms) +
          "</span></a>"
        );
      })
      .join("");
    results.innerHTML = html;
  }

  if (searchToggle) searchToggle.addEventListener("click", openSearch);
  if (overlay) {
    overlay.addEventListener("click", function (event) {
      if (event.target === overlay) closeSearch();
    });
  }
  if (input) {
    input.addEventListener("input", function () {
      run(input.value);
    });
    input.addEventListener("keydown", function (event) {
      if (event.key === "Escape") {
        closeSearch();
        return;
      }
      if (event.key === "ArrowDown" || event.key === "ArrowUp") {
        event.preventDefault();
        selected = Math.max(
          0,
          Math.min(matches.length - 1, selected + (event.key === "ArrowDown" ? 1 : -1))
        );
        run(input.value);
        var chosen = results.querySelector('[aria-selected="true"]');
        if (chosen) chosen.scrollIntoView({ block: "nearest" });
        return;
      }
      if (event.key === "Enter") {
        var chosen = results.querySelector('[aria-selected="true"]') || results.querySelector("a");
        if (chosen) {
          event.preventDefault();
          location.href = chosen.href;
        }
      }
    });
  }

  document.addEventListener("keydown", function (event) {
    var tag = (event.target.tagName || "").toLowerCase();
    if (event.key === "/" && tag !== "input" && tag !== "textarea") {
      event.preventDefault();
      openSearch();
    }
    if (event.key === "Escape" && searchOpen()) closeSearch();
  });

  var main = document.getElementById("book-main");
  if (main) main.setAttribute("tabindex", "-1");
})();
