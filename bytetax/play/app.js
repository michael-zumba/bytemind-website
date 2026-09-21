/* ByteTax interface.

   The content comes from bundle.js, which tools/build_bundle.py writes from the
   knowledge base. Marking follows the same rules as src/engine.py, so a round
   behaves the same here and in the terminal player.

   Progress is kept in the browser's own storage: no account, no server, and a
   round plays with the network switched off. */

(function () {
  "use strict";

  var bundle = window.BYTETAX_BUNDLE;
  var LETTERS = ["A", "B", "C", "D"];
  var BOX_INTERVALS = [0, 1, 3, 7, 21];
  var STORAGE_KEY = "bytetax.progress.v1";
  var ROUND_SIZE = 8;

  var screens = {
    streakChip: document.getElementById("streak-chip"),
    streak: document.getElementById("streak"),
    quit: document.getElementById("quit"),
    pips: document.getElementById("pips"),
    screen: document.getElementById("screen"),
    checked: document.getElementById("checked"),
    petStage: document.getElementById("pet-stage"),
    togglePet: document.getElementById("toggle-pet"),
    about: document.getElementById("about")
  };

  var state = { screen: "home", round: null, moduleId: null };
  var progress = loadProgress();
  var pet = window.ByteTaxPet || null;

  /* ---------------------------------------------------------------- storage */

  function loadProgress() {
    var empty = { records: {}, streak_days: 0, last_played: "", sessions: 0 };
    try {
      var raw = window.localStorage.getItem(STORAGE_KEY);
      return raw ? Object.assign(empty, JSON.parse(raw)) : empty;
    } catch (error) {
      return empty;
    }
  }

  function saveProgress() {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(progress));
    } catch (error) {
      /* A browser that blocks storage still plays; it just forgets. */
    }
  }

  function todayIso() {
    return new Date().toISOString().slice(0, 10);
  }

  function addDays(iso, days) {
    var when = new Date(iso + "T00:00:00Z");
    when.setUTCDate(when.getUTCDate() + days);
    return when.toISOString().slice(0, 10);
  }

  function recordAnswer(itemId, correct) {
    var today = todayIso();
    var record = progress.records[itemId] || { box: 0, seen: 0, correct: 0 };
    record.seen += 1;
    if (correct) {
      record.correct += 1;
      record.box = Math.min(record.box + 1, BOX_INTERVALS.length - 1);
    } else {
      record.box = 0;
    }
    record.due = addDays(today, BOX_INTERVALS[record.box]);
    record.last_seen = today;
    progress.records[itemId] = record;
    saveProgress();
  }

  function registerSession() {
    var today = todayIso();
    if (progress.last_played !== today) {
      var yesterday = addDays(today, -1);
      progress.streak_days = progress.last_played === yesterday ? progress.streak_days + 1 : 1;
      progress.sessions += 1;
    }
    progress.last_played = today;
    saveProgress();
  }

  function moduleMastery(moduleId) {
    var items = bundle.items.filter(function (item) { return item.module === moduleId; });
    var known = items.filter(function (item) {
      var record = progress.records[item.id];
      return record && record.box >= 3;
    });
    return { total: items.length, known: known.length };
  }

  function masteredCount() {
    return Object.keys(progress.records).filter(function (id) {
      return progress.records[id].box >= 3;
    }).length;
  }

  /* Six rings of growth, one for every eight items the player knows well. */
  function petLevel() {
    return Math.min(6, 1 + Math.floor(masteredCount() / 8));
  }

  function syncPet(levelUpMessage) {
    if (!pet || !pet.root) { return; }
    var level = petLevel();
    var grew = level > pet.level;
    pet.setLevel(level);
    if (grew && levelUpMessage) { pet.setMood("happy", "I grew a ring. " + masteredCount() + " items known."); }
  }

  /* ------------------------------------------------------------ round logic */

  function itemsFor(moduleId) {
    var items = moduleId
      ? bundle.items.filter(function (item) { return item.module === moduleId; })
      : bundle.items.slice();
    return items.sort(function (a, b) { return a.id < b.id ? -1 : 1; });
  }

  function weakestFirst(items) {
    return items.slice().sort(function (a, b) {
      function accuracy(item) {
        var record = progress.records[item.id];
        if (!record) { return 2; }
        return record.correct / Math.max(record.seen, 1);
      }
      return accuracy(a) - accuracy(b) || (a.id < b.id ? -1 : 1);
    });
  }

  function interleave(items) {
    var buckets = {};
    items.forEach(function (item) {
      (buckets[item.module] = buckets[item.module] || []).push(item);
    });
    var ordered = [];
    var modules = Object.keys(buckets).sort();
    var more = true;
    while (more) {
      more = false;
      modules.forEach(function (module) {
        if (buckets[module].length) {
          ordered.push(buckets[module].shift());
          more = true;
        }
      });
    }
    return ordered;
  }

  function buildRound(moduleId, size) {
    var pool = itemsFor(moduleId);
    var today = todayIso();
    var chosen = [];

    function take(item) {
      if (item && chosen.indexOf(item) === -1 && chosen.length < size) { chosen.push(item); }
    }

    function unseen(item) { return !progress.records[item.id]; }

    // Reserve part of the round for variety, so practice is not a wall of
    // multiple choice. One item is picked per format before anything else.
    var formats = {};
    pool.forEach(function (item) { formats[item.format] = true; });
    shuffle(Object.keys(formats)).forEach(function (format) {
      if (chosen.length >= Math.ceil(size / 2)) { return; }
      var candidates = pool.filter(function (item) { return item.format === format; });
      take(candidates.filter(unseen)[0] || candidates[0]);
    });

    pool
      .filter(function (item) {
        var record = progress.records[item.id];
        return record && record.due <= today;
      })
      .sort(function (a, b) {
        return progress.records[a.id].due < progress.records[b.id].due ? -1 : 1;
      })
      .slice(0, Math.max(1, Math.floor(size / 2)))
      .forEach(take);

    pool.filter(unseen).forEach(take);
    weakestFirst(pool).forEach(take);

    return moduleId ? chosen : interleave(chosen);
  }

  function factsOf(item) {
    return (item.facts || [])
      .map(function (id) { return bundle.facts.find(function (fact) { return fact.id === id; }); })
      .filter(Boolean);
  }

  function sourcesOf(item) {
    var seen = {};
    var out = [];
    factsOf(item).forEach(function (fact) {
      (fact.sources || []).forEach(function (id) {
        if (seen[id]) { return; }
        var source = bundle.sources.find(function (entry) { return entry.id === id; });
        if (source) { seen[id] = true; out.push(source); }
      });
    });
    return out;
  }

  function moduleTitle(moduleId) {
    var module = bundle.modules.find(function (entry) { return entry.id === moduleId; });
    return module ? module.title : moduleId;
  }

  /* ---------------------------------------------------------------- helpers */

  function el(tag, props, children) {
    var node = document.createElement(tag);
    Object.keys(props || {}).forEach(function (key) {
      if (key === "class") { node.className = props[key]; }
      else if (key === "text") { node.textContent = props[key]; }
      else if (key === "html") { node.innerHTML = props[key]; }
      else if (key.indexOf("on") === 0) { node.addEventListener(key.slice(2), props[key]); }
      else if (props[key] === true) { node.setAttribute(key, ""); }
      else if (props[key] !== false && props[key] != null) { node.setAttribute(key, props[key]); }
    });
    (children || []).forEach(function (child) { if (child) { node.appendChild(child); } });
    return node;
  }

  function clear(node) { while (node.firstChild) { node.removeChild(node.firstChild); } }

  /** Show a panel and put the reader back at the top of it. */
  function paint(panel) {
    panel.classList.add("screen-enter");
    clear(screens.screen);
    screens.screen.appendChild(panel);
    if (window.scrollTo) { window.scrollTo(0, 0); }
  }

  function shuffle(list) {
    var copy = list.slice();
    for (var i = copy.length - 1; i > 0; i -= 1) {
      var j = Math.floor(Math.random() * (i + 1));
      var swap = copy[i]; copy[i] = copy[j]; copy[j] = swap;
    }
    return copy;
  }

  /* --------------------------------------------------------------- dragging */

  /* Pointer events rather than the HTML drag-and-drop API, because the same
     code then works with a mouse, a trackpad and a finger, and inside the
     desktop web view. Dragging is added on top of the tap flow, never instead
     of it: a tap still selects, which keeps the game playable from a keyboard. */
  var DRAG_THRESHOLD = 5;

  function dragify(node, options) {
    node.classList.add("draggable");
    node.addEventListener("pointerdown", function (event) {
      if (event.pointerType === "mouse" && event.button !== 0) { return; }
      if (options.disabled && options.disabled()) { return; }

      var startX = event.clientX;
      var startY = event.clientY;
      var ghost = null;
      var moved = false;
      var hovered = null;

      function highlight(target) {
        if (hovered === target) { return; }
        if (hovered) { hovered.classList.remove("drop-active"); }
        hovered = target;
        if (hovered) { hovered.classList.add("drop-active"); }
      }

      function targetUnder(x, y) {
        var found = document.elementFromPoint(x, y);
        return found && found.closest ? found.closest(options.targetSelector) : null;
      }

      function onMove(moveEvent) {
        var dx = moveEvent.clientX - startX;
        var dy = moveEvent.clientY - startY;
        if (!moved && Math.sqrt(dx * dx + dy * dy) < DRAG_THRESHOLD) { return; }
        if (!moved) {
          moved = true;
          node.classList.add("dragging");
          ghost = node.cloneNode(true);
          ghost.classList.add("drag-ghost");
          ghost.classList.remove("dragging");
          document.body.appendChild(ghost);
        }
        ghost.style.left = moveEvent.clientX + "px";
        ghost.style.top = moveEvent.clientY + "px";
        highlight(targetUnder(moveEvent.clientX, moveEvent.clientY));
      }

      function onEnd(endEvent) {
        document.removeEventListener("pointermove", onMove);
        document.removeEventListener("pointerup", onEnd);
        document.removeEventListener("pointercancel", onEnd);
        var target = moved ? targetUnder(endEvent.clientX, endEvent.clientY) : null;
        highlight(null);
        if (ghost) { ghost.remove(); }
        node.classList.remove("dragging");
        if (!moved) { return; }
        // A drag ends with a click event; mark it so the tap handler ignores it.
        node.dataset.justDragged = "1";
        window.setTimeout(function () { delete node.dataset.justDragged; }, 60);
        if (target && target !== node) { options.onDrop(target); }
      }

      document.addEventListener("pointermove", onMove);
      document.addEventListener("pointerup", onEnd);
      document.addEventListener("pointercancel", onEnd);
    });
  }

  function wasDragged(node) {
    return node.dataset.justDragged === "1";
  }

  function feedbackPanel(result, item, next) {
    var panel = el("div", { class: "feedback" });
    if (item.format !== "card") {
      panel.appendChild(el("p", {
        class: "verdict " + (result ? "good" : "bad"),
        text: result ? "Correct" : "Not this time"
      }));
    }
    panel.appendChild(el("p", { text: item.explanation }));
    var sources = sourcesOf(item);
    if (sources.length) {
      var line = el("p", { class: "source", text: "Where this comes from: " });
      sources.forEach(function (source, index) {
        if (index) { line.appendChild(document.createTextNode(" · ")); }
        line.appendChild(el("a", {
          href: source.url, target: "_blank", rel: "noopener noreferrer",
          text: source.title || source.url
        }));
      });
      line.appendChild(document.createTextNode(
        " (Inland Revenue" + (sources[0].source_date ? ", updated " + sources[0].source_date : "") + ")"
      ));
      panel.appendChild(line);
    }
    panel.appendChild(el("div", { class: "actions" }, [
      el("button", { class: "primary", onclick: next, text: state.round.index + 1 >= state.round.items.length ? "See results" : "Next" })
    ]));
    return panel;
  }

  /* ----------------------------------------------------------------- screens */

  function renderHome() {
    state.screen = "home";
    state.round = null;
    if (pet) { pet.setMood("idle", ""); }
    screens.pips.hidden = true;
    screens.quit.hidden = true;
    screens.streakChip.hidden = false;
    screens.streak.textContent = progress.streak_days;

    var panel = el("div", { class: "panel" });
    panel.appendChild(el("p", { class: "eyebrow", text: "Choose what to practise" }));
    panel.appendChild(el("h1", { text: "Pick up where the course left off." }));

    var list = el("div", { class: "modules" });
    var playable = bundle.modules.filter(function (module) { return module.playable; });
    playable.forEach(function (module) {
      var mastery = moduleMastery(module.id);
      var share = mastery.total ? Math.round((mastery.known / mastery.total) * 100) : 0;
      list.appendChild(el("button", {
        class: "module",
        onclick: function () { startRound(module.id); }
      }, [
        el("span", {}, [
          el("span", { class: "title", text: module.title }),
          el("span", { class: "blurb", text: module.blurb }),
          el("span", { class: "bar" }, [el("i", { style: "width: " + share + "%" })])
        ]),
        el("span", { class: "count", text: mastery.known + "/" + mastery.total + " known" })
      ]));
    });
    if (playable.length > 1) {
      list.appendChild(el("button", {
        class: "module",
        onclick: function () { startRound(null); }
      }, [
        el("span", {}, [
          el("span", { class: "title", text: "Mixed round" }),
          el("span", { class: "blurb", text: "A spread of modules, with anything overdue first." })
        ]),
        el("span", { class: "count", text: bundle.items.length + " items" })
      ]));
    }
    panel.appendChild(list);

    paint(panel);
    screens.checked.textContent = " Content checked " + bundle.checked_on + ".";
  }

  function startRound(moduleId) {
    var items = buildRound(moduleId, ROUND_SIZE);
    if (!items.length) { return; }
    state.screen = "round";
    state.round = { moduleId: moduleId, items: items, index: 0, answers: [], marked: false };
    registerSession();
    bumpStreak();
    screens.quit.hidden = false;
    screens.streakChip.hidden = false;
    screens.streak.textContent = progress.streak_days;
    renderRound();
  }

  function renderPips() {
    clear(screens.pips);
    screens.pips.hidden = false;
    state.round.items.forEach(function (item, index) {
      var cls = "pip";
      var answer = state.round.answers[index];
      if (answer) { cls += answer.correct ? " done" : " missed"; }
      else if (index === state.round.index) { cls += " now"; }
      screens.pips.appendChild(el("span", { class: cls }));
    });
  }

  function completeItem(correct) {
    var round = state.round;
    var item = round.items[round.index];
    round.answers[round.index] = { item_id: item.id, module: item.module, format: item.format, correct: correct };
    recordAnswer(item.id, correct);
    round.marked = true;
    screens.streak.textContent = progress.streak_days;
    if (pet) {
      pet.setMood(correct ? "happy" : "encourage");
      if (correct) { pet.burst(); }
    }
  }

  function advance() {
    state.round.index += 1;
    state.round.marked = false;
    if (state.round.index >= state.round.items.length) { renderSummary(); }
    else { renderRound(); }
  }

  function renderRound() {
    var round = state.round;
    var item = round.items[round.index];
    renderPips();

    var panel = el("div", { class: "panel" });
    panel.appendChild(el("p", {
      class: "eyebrow",
      text: moduleTitle(item.module) + " · " + (round.index + 1) + " of " + round.items.length
    }));

    if (item.format === "card") { renderCard(panel, item); }
    else if (item.format === "match") { renderMatch(panel, item); }
    else if (item.format === "sort") { renderSort(panel, item); }
    else if (item.format === "order") { renderOrder(panel, item); }
    else { renderChoice(panel, item); }

    panel.classList.add("screen-enter");
    paint(panel);
    if (pet && !round.marked) { pet.setMood("thinking"); }
  }

  /* ------------------------------------------------------------ item formats */

  function renderChoice(panel, item) {
    panel.appendChild(el("h1", { text: item.stem }));
    var options = el("div", { class: "options" });
    var buttons = [];

    item.options.forEach(function (option, index) {
      var button = el("button", {
        class: "option",
        onclick: function () { choose(index); }
      }, [
        el("span", { class: "key", text: LETTERS[index] }),
        el("span", { text: option })
      ]);
      buttons.push(button);
      options.appendChild(button);
    });
    panel.appendChild(options);

    function choose(index) {
      if (state.round.marked) { return; }
      var correct = index === item.answer;
      buttons.forEach(function (button, position) {
        button.disabled = true;
        if (position === item.answer) { button.className = "option correct"; }
        else if (position === index) { button.className = "option wrong"; }
        else { button.className = "option faded"; }
      });
      completeItem(correct);
      panel.appendChild(feedbackPanel(correct, item, advance));
    }
  }

  function renderCard(panel, item) {
    var flip = el("div", { class: "flip" });
    var front = el("div", {
      class: "flip-face flip-front", role: "button", tabindex: "0",
      "aria-label": "Reveal the answer"
    }, [
      el("span", {}, [
        el("span", { text: item.front }),
        el("span", { class: "hint", text: "Tap to reveal" })
      ])
    ]);
    var back = el("div", { class: "flip-face flip-back" }, [
      el("span", {}, [
        el("span", { text: item.back }),
        el("span", { class: "hint", text: item.front })
      ])
    ]);
    flip.appendChild(el("div", { class: "flip-inner" }, [front, back]));

    var actions = el("div", { class: "actions" });
    actions.hidden = true;

    function reveal() {
      if (flip.classList.contains("is-flipped")) { return; }
      flip.classList.add("is-flipped");
      actions.hidden = false;
      front.removeAttribute("tabindex");
      if (pet) { pet.setMood("thinking", "Did you know it?"); }
    }

    front.addEventListener("click", reveal);
    front.addEventListener("keydown", function (event) {
      if (event.key === "Enter" || event.key === " ") { event.preventDefault(); reveal(); }
    });

    actions.appendChild(el("button", {
      class: "primary",
      text: "I knew it",
      onclick: function () { finish(true); }
    }));
    actions.appendChild(el("button", {
      class: "ghost",
      text: "Not yet",
      onclick: function () { finish(false); }
    }));

    function finish(knew) {
      if (state.round.marked) { return; }
      completeItem(knew);
      panel.appendChild(feedbackPanel(knew, item, advance));
      actions.hidden = true;
    }

    panel.appendChild(el("h1", { text: "Flip card" }));
    panel.appendChild(flip);
    panel.appendChild(actions);
  }

  function renderMatch(panel, item) {
    panel.appendChild(el("h1", { text: item.stem }));
    panel.appendChild(el("p", {
      class: "hint",
      text: "Drag a card onto its partner, or tap one and then the other."
    }));
    var pickedLeft = null;
    var pairs = {};
    var leftButtons = [];
    var rightButtons = [];

    var leftColumn = el("div", { class: "pair-col" });
    var rightColumn = el("div", { class: "pair-col" });

    item.pairs.forEach(function (pair) {
      var button = el("button", {
        class: "tile", text: pair.left, "data-side": "left",
        onclick: function () { if (!wasDragged(button)) { pickLeft(pair.left); } }
      });
      dragify(button, {
        targetSelector: '[data-side="right"]',
        disabled: function () { return state.round.marked; },
        onDrop: function (target) { connect(pair.left, target.textContent); }
      });
      leftButtons.push(button);
    });
    shuffle(item.pairs.map(function (pair) { return pair.right; })).forEach(function (right) {
      var button = el("button", {
        class: "tile", text: right, "data-side": "right",
        onclick: function () { if (!wasDragged(button)) { pickRight(right); } }
      });
      dragify(button, {
        targetSelector: '[data-side="left"]',
        disabled: function () { return state.round.marked; },
        onDrop: function (target) { connect(target.textContent, right); }
      });
      rightButtons.push(button);
    });
    leftButtons.forEach(function (button) { leftColumn.appendChild(button); });
    rightButtons.forEach(function (button) { rightColumn.appendChild(button); });

    var check = el("button", { class: "primary", text: "Check", disabled: true, onclick: check_ });
    var actions = el("div", { class: "actions" }, [check]);

    function refresh() {
      leftButtons.forEach(function (button) {
        button.className = "tile" + (pairs[button.textContent] ? " paired" : "");
      });
      rightButtons.forEach(function (button) {
        var used = Object.keys(pairs).some(function (left) { return pairs[left] === button.textContent; });
        button.className = "tile" + (used ? " paired" : "");
      });
      check.disabled = Object.keys(pairs).length !== item.pairs.length;
    }

    function pickLeft(left) {
      if (state.round.marked) { return; }
      pickedLeft = left;
      leftButtons.forEach(function (button) {
        if (button.textContent === left) { button.className = "tile picked"; }
      });
    }

    function pickRight(right) {
      if (!pickedLeft) { return; }
      connect(pickedLeft, right);
    }

    /** Record a pairing, whether it came from a drag or from two taps. */
    function connect(left, right) {
      if (state.round.marked) { return; }
      pairs[left] = right;
      pickedLeft = null;
      refresh();
    }

    function check_() {
      var expected = {};
      item.pairs.forEach(function (pair) { expected[pair.left] = pair.right; });
      var correct = item.pairs.every(function (pair) { return pairs[pair.left] === pair.right; });
      item.pairs.forEach(function (pair) {
        var button = leftButtons.find(function (entry) { return entry.textContent === pair.left; });
        if (button) {
          button.className = "tile " + (pairs[pair.left] === pair.right ? "paired" : "wrong");
        }
      });
      check.disabled = true;
      completeItem(correct);
      panel.appendChild(feedbackPanel(correct, item, advance));
    }

    panel.appendChild(el("div", { class: "pairs" }, [leftColumn, rightColumn]));
    panel.appendChild(actions);
    refresh();
  }

  function renderSort(panel, item) {
    panel.appendChild(el("h1", { text: item.stem }));
    panel.appendChild(el("p", {
      class: "hint",
      text: "Drag each card into a group, or tap a card and then the group."
    }));
    var placed = {};
    var picked = null;
    var pool = el("div", { class: "pool", "data-drop": "pool" });
    var buckets = el("div", { class: "buckets" });
    var check = el("button", { class: "primary", text: "Check", disabled: true, onclick: check_ });
    var actions = el("div", { class: "actions" }, [check]);

    function tile(text) {
      var button = el("button", {
        class: "tile" + (picked === text ? " picked" : ""), text: text,
        onclick: function () { if (!wasDragged(button)) { pick(text); } }
      });
      dragify(button, {
        targetSelector: '[data-drop="bucket"]',
        disabled: function () { return state.round.marked; },
        onDrop: function (target) { place(text, target.dataset.bucket); }
      });
      return button;
    }

    /* A card already in a group can be dragged somewhere else, or back out. */
    function chip(text) {
      var node = el("span", { class: "placed", text: text, "data-entry": text });
      dragify(node, {
        targetSelector: '[data-drop="pool"], [data-drop="bucket"]',
        disabled: function () { return state.round.marked; },
        onDrop: function (target) {
          if (target.dataset.drop === "pool") { unplace(text); }
          else { place(text, target.dataset.bucket); }
        }
      });
      node.addEventListener("click", function (event) {
        if (state.round.marked || wasDragged(node)) { return; }
        // If a card is waiting to be placed, let the tap reach the group so it
        // lands there. Removing a placed card is what a tap means only when
        // nothing is being carried.
        if (picked) { return; }
        event.stopPropagation();
        unplace(text);
      });
      return node;
    }

    function render() {
      clear(pool);
      clear(buckets);
      item.entries.forEach(function (entry) {
        if (!placed[entry.text]) { pool.appendChild(tile(entry.text)); }
      });
      item.buckets.forEach(function (name) {
        var items = el("div", { class: "items" });
        item.entries.forEach(function (entry) {
          if (placed[entry.text] === name) { items.appendChild(chip(entry.text)); }
        });
        buckets.appendChild(el("div", {
          class: "bucket" + (picked ? " picked" : ""),
          "data-drop": "bucket", "data-bucket": name,
          onclick: function () { if (picked) { place(picked, name); } }
        }, [el("div", { class: "label", text: name }), items]));
      });
      check.disabled = Object.keys(placed).length !== item.entries.length;
    }

    function pick(text) {
      if (state.round.marked) { return; }
      picked = picked === text ? null : text;
      render();
    }

    function place(text, bucketName) {
      if (state.round.marked || !bucketName) { return; }
      placed[text] = bucketName;
      picked = null;
      render();
    }

    function unplace(text) {
      if (state.round.marked) { return; }
      delete placed[text];
      picked = null;
      render();
    }

    function check_() {
      var correct = item.entries.every(function (entry) { return placed[entry.text] === entry.bucket; });
      var expected = {};
      item.entries.forEach(function (entry) { expected[entry.text] = entry.bucket; });
      Array.prototype.forEach.call(buckets.querySelectorAll(".placed"), function (node) {
        node.classList.add(
          placed[node.textContent] === expected[node.textContent] ? "correct" : "wrong"
        );
      });
      check.disabled = true;
      completeItem(correct);
      panel.appendChild(feedbackPanel(correct, item, advance));
    }

    panel.appendChild(pool);
    panel.appendChild(buckets);
    panel.appendChild(actions);
    render();
  }

  function renderOrder(panel, item) {
    panel.appendChild(el("h1", { text: item.stem }));
    panel.appendChild(el("p", { class: "hint", text: "Use the arrows, or tap two rows to swap them." }));
    var order = shuffle(item.steps);
    var picked = null;
    var list = el("div", { class: "order" });

    function paint() {
      clear(list);
      order.forEach(function (step, index) {
        var row = el("div", {
          class: "order-row" + (picked === step ? " picked" : ""),
          onclick: function () { pick(step); }
        }, [
          el("span", { class: "handle", text: String(index + 1) }),
          el("span", { text: step }),
          el("span", { class: "moves" }, [
            el("button", { text: "↑", title: "Move up", onclick: function (event) { event.stopPropagation(); move(index, -1); } }),
            el("button", { text: "↓", title: "Move down", onclick: function (event) { event.stopPropagation(); move(index, 1); } })
          ])
        ]);
        list.appendChild(row);
      });
    }

    function pick(step) {
      if (state.round.marked) { return; }
      if (picked === null) { picked = step; }
      else if (picked === step) { picked = null; }
      else {
        var from = order.indexOf(picked);
        var to = order.indexOf(step);
        order[from] = step;
        order[to] = picked;
        picked = null;
      }
      paint();
    }

    function move(index, delta) {
      if (state.round.marked) { return; }
      var target = index + delta;
      if (target < 0 || target >= order.length) { return; }
      var swap = order[target];
      order[target] = order[index];
      order[index] = swap;
      paint();
    }

    var check = el("button", {
      class: "primary", text: "Check",
      onclick: function () {
        var correct = order.join("|") === item.steps.join("|");
        check.disabled = true;
        completeItem(correct);
        panel.appendChild(feedbackPanel(correct, item, advance));
      }
    });

    panel.appendChild(list);
    panel.appendChild(el("div", { class: "actions" }, [check]));
    paint();
  }

  /* ----------------------------------------------------------------- summary */

  function renderAbout() {
    if (pet) { pet.setMood("idle", "Hello."); }
    screens.pips.hidden = true;
    screens.quit.hidden = true;

    var panel = el("div", { class: "panel screen-enter" });
    panel.appendChild(el("p", { class: "eyebrow", text: "About" }));
    panel.appendChild(el("h1", { text: bundle.product || "ByteTax" }));
    panel.appendChild(el("p", {
      text: (bundle.company || "ByteMind Ltd") + " · version " + (bundle.version || "0.1.0")
    }));

    var rows = [
      ["Items", String(bundle.items.length)],
      ["Facts behind them", String(bundle.facts.length)],
      ["Inland Revenue sources", String(bundle.sources.length)],
      ["Modules", bundle.modules.length + ", mapped to the ACCT 862 schedule"],
      ["Content checked against Inland Revenue", bundle.content_checked || bundle.checked_on],
      ["Built", (bundle.built_at || "").slice(0, 10)]
    ];
    var table = el("table", { class: "breakdown" });
    rows.forEach(function (row) {
      table.appendChild(el("tr", {}, [
        el("td", { text: row[0] }),
        el("td", { text: row[1] })
      ]));
    });
    panel.appendChild(table);

    var note = el("div", { class: "note" });
    note.appendChild(el("p", {
      text: "Every question, card and rate in ByteTax carries the Inland Revenue "
        + "page it came from, the exact words that prove it, and the date it was "
        + "checked. Nothing is written from memory."
    }));
    note.appendChild(el("p", {
      text: "ByteTax is general information about New Zealand tax. It is not tax "
        + "advice. Inland Revenue is the authority for every rule it covers."
    }));
    note.appendChild(el("p", {
      text: "Playing works with no network. Progress is kept on this machine and "
        + "nothing is sent anywhere."
    }));
    note.appendChild(el("p", {}, [
      el("a", {
        href: "https://www.ird.govt.nz/", target: "_blank", rel: "noopener noreferrer",
        text: "ird.govt.nz"
      })
    ]));
    panel.appendChild(note);

    panel.appendChild(el("div", { class: "actions" }, [
      el("button", { class: "primary", text: "Back", onclick: renderHome })
    ]));

    paint(panel);
  }

  function renderSummary() {
    var round = state.round;
    var scored = round.answers.filter(function (answer) { return answer && answer.format !== "card"; });
    var correct = scored.filter(function (answer) { return answer.correct; });
    var panel = el("div", { class: "panel" });

    screens.pips.hidden = true;
    screens.quit.hidden = true;

    panel.appendChild(el("p", { class: "eyebrow", text: "Round finished" }));
    if (scored.length) {
      panel.appendChild(el("p", { class: "score", text: correct.length + " / " + scored.length }));
      panel.appendChild(el("p", { text: "answers correct this round" }));
    } else {
      panel.appendChild(el("h1", { text: "Cards reviewed" }));
    }

    var byModule = {};
    scored.forEach(function (answer) {
      var entry = byModule[answer.module] || (byModule[answer.module] = { answered: 0, correct: 0 });
      entry.answered += 1;
      if (answer.correct) { entry.correct += 1; }
    });
    var rows = Object.keys(byModule);
    if (rows.length) {
      var table = el("table", { class: "breakdown" });
      rows.forEach(function (moduleId) {
        var entry = byModule[moduleId];
        table.appendChild(el("tr", {}, [
          el("td", { text: moduleTitle(moduleId) }),
          el("td", { text: entry.correct + " / " + entry.answered })
        ]));
      });
      panel.appendChild(table);
    }

    var revisit = round.answers.filter(function (answer) { return answer && !answer.correct; });
    if (revisit.length) {
      panel.appendChild(el("p", {
        class: "watermark",
        text: "Coming back tomorrow: " + revisit.map(function (answer) {
          var item = bundle.items.find(function (entry) { return entry.id === answer.item_id; });
          return item && item.stem ? item.stem : answer.item_id;
        }).join(" · ")
      }));
    }

    panel.appendChild(el("div", { class: "actions" }, [
      el("button", {
        class: "primary",
        text: "Another round",
        onclick: function () { startRound(round.moduleId); }
      }),
      el("button", { class: "ghost", text: "Choose a module", onclick: renderHome })
    ]));

    if (pet) {
      var share = scored.length ? correct.length / scored.length : 0;
      pet.setMood(share >= 0.6 ? "celebrate" : "idle", share >= 0.6 ? "" : "Round done.");
      if (share >= 0.6) { pet.burst(10); }
      syncPet(true);
    }

    paint(panel);
  }

  /* -------------------------------------------------------------------- boot */

  screens.quit.addEventListener("click", function () {
    if (state.round && state.round.answers.filter(Boolean).length) { renderSummary(); }
    else { renderHome(); }
  });

  /* ------------------------------------------------------------- companion */

  var PET_PREF = "bytetax.pip";

  function petWanted() {
    try { return window.localStorage.getItem(PET_PREF) !== "off"; } catch (error) { return true; }
  }

  function showPet(on) {
    screens.petStage.hidden = !on;
    screens.togglePet.setAttribute("aria-pressed", on ? "true" : "false");
    try { window.localStorage.setItem(PET_PREF, on ? "on" : "off"); } catch (error) { /* fine */ }
  }

  function bumpStreak() {
    screens.streakChip.classList.remove("bump");
    void screens.streakChip.offsetWidth;
    screens.streakChip.classList.add("bump");
  }

  if (pet) {
    pet.mount(screens.petStage);
    pet.setLevel(petLevel());
    pet.setMood("idle", "");
    showPet(petWanted());
  } else {
    screens.togglePet.hidden = true;
  }

  screens.togglePet.addEventListener("click", function () {
    var turningOn = screens.petStage.hidden;
    showPet(turningOn);
    if (turningOn && pet) { pet.setMood("happy", "Hello again."); pet.burst(5); }
  });

  screens.about.addEventListener("click", renderAbout);

  if (!bundle || !bundle.items || !bundle.items.length) {
    screens.screen.appendChild(el("div", { class: "panel" }, [
      el("h1", { text: "No content found" }),
      el("p", { text: "Run tools/build_bundle.py to build the content the app reads." })
    ]));
  } else {
    renderHome();
  }

  // Test seam: lets the verification pass open a single item of a chosen
  // format. Normal play never calls it.
  window.bytetax = {
    openItem: function (itemId) {
      var item = bundle.items.find(function (entry) { return entry.id === itemId; });
      if (!item) { return false; }
      state.screen = "round";
      state.round = { moduleId: item.module, items: [item], index: 0, answers: [], marked: false };
      screens.quit.hidden = false;
      renderRound();
      return true;
    },
    openHome: renderHome,
    itemIds: function () { return bundle.items.map(function (item) { return item.id; }); }
  };
})();
