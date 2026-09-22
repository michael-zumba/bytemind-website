/* The handbook reader: contents on a small screen, search, and a memory of
   where you were. No dependencies, no network calls except its own index. */
(function () {
  "use strict";

  var STORE_KEY = "bytebook-handbook";
  var book = readStore();

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

  var chapterSlug = (location.pathname.split("/").pop() || "index.html").replace(".html", "");
  var lastPosition = 0;
  var embedded = /[?&]embed=1\b/.test(location.search);

  if (embedded) {
    document.body.classList.add("embed");
    // A reader who follows a previous/next link inside the frame must stay in
    // reading mode, so every link that stays in the book keeps the flag.
    var localLinks = document.querySelectorAll('a[href$=".html"]');
    for (var i = 0; i < localLinks.length; i++) {
      var href = localLinks[i].getAttribute("href");
      if (!href || href.charAt(0) === "#" || href.indexOf("://") !== -1) continue;
      if (href.indexOf("embed=1") !== -1) continue;
      localLinks[i].setAttribute(
        "href",
        href + (href.indexOf("?") === -1 ? "?embed=1" : "&embed=1")
      );
    }
    // Tell the host page which chapter is showing, so its own chapter list
    // keeps up when a reader uses the previous or next link inside the frame.
    window.addEventListener("load", function () {
      if (window.parent !== window) {
        window.parent.postMessage(
          { type: "bytebook-handbook", slug: chapterSlug, title: document.title },
          "*"
        );
      }
    });
  }

  function rememberPosition() {
    var main = document.getElementById("book-main");
    if (!main) return;
    var total = document.documentElement.scrollHeight - window.innerHeight;
    var ratio = total > 0 ? Math.min(1, window.scrollY / total) : 0;
    var bar = document.getElementById("reading-progress");
    if (bar) bar.style.width = (ratio * 100).toFixed(2) + "%";
    if (chapterSlug === "index" || chapterSlug === "all" || chapterSlug === "citations") return;
    if (Math.abs(ratio - lastPosition) < 0.05) return;
    lastPosition = ratio;
    writeStore({
      chapter: chapterSlug,
      ratio: ratio,
      seen: Object.assign(book.seen || {}, { [chapterSlug]: Math.max((book.seen || {})[chapterSlug] || 0, ratio) })
    });
  }

  var ticking = false;
  window.addEventListener(
    "scroll",
    function () {
      if (ticking) return;
      ticking = true;
      window.requestAnimationFrame(function () {
        ticking = false;
        rememberPosition();
      });
    },
    { passive: true }
  );

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
    // A tap on the page behind the drawer closes it.
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

  /* ── Arrow keys move between chapters ───────────────────────────────── */
  document.addEventListener("keydown", function (event) {
    if (event.metaKey || event.ctrlKey || event.altKey) return;
    var tag = (event.target.tagName || "").toLowerCase();
    if (tag === "input" || tag === "textarea" || tag === "select") return;
    if (searchOpen()) return;
    var link = null;
    if (event.key === "ArrowRight") link = document.querySelector(".book-pager-next");
    if (event.key === "ArrowLeft") link = document.querySelector(".book-pager-link:not(.book-pager-next)");
    if (link && link.href) {
      event.preventDefault();
      location.href = link.href;
    }
  });

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
      escaped = escaped.replace(new RegExp("(" + term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "gi"), "<mark>$1</mark>");
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

  if (searchToggle) {
    searchToggle.addEventListener("click", openSearch);
  }
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

  /* ── Keyboard focus target for the contents toggle ──────────────────── */
  var main = document.getElementById("book-main");
  if (main) main.setAttribute("tabindex", "-1");

  rememberPosition();
  if (book.chapter === chapterSlug && book.ratio > 0.1) {
    var resume = document.createElement("button");
    resume.type = "button";
    resume.className = "book-bar-btn";
    resume.textContent = "Resume";
    resume.addEventListener("click", function () {
      var total = document.documentElement.scrollHeight - window.innerHeight;
      window.scrollTo({ top: book.ratio * total, behavior: "smooth" });
    });
    var bar = document.querySelector(".book-bar");
    if (bar) bar.appendChild(resume);
  }
})();
