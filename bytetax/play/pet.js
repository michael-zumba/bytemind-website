/* Pip, the ByteTax companion.

   Drawn as inline SVG rather than a picture so the character stays sharp at any
   size, adds no download, and can be animated from CSS.

   Pip talks. A reaction for every moment in a round, dry asides underneath, a
   running commentary while you work, and — the useful part — real facts read
   out of the knowledge base. Every fact Pip mentions is one that has been
   sourced and checked, so the companion can be chatty without being a
   liability.

   Poses come from a class on the wrapper: idle, thinking, happy, encourage,
   celebrate. Everything here is switched off under prefers-reduced-motion by
   the stylesheet. */

(function () {
  "use strict";

  var LINES = {
    idle: [
      "Ready when you are.",
      "Pick a topic. Any topic.",
      "No rush. It's only tax.",
      "I've been reading the Act. Again.",
      "Take your time. I'm not going anywhere.",
      "Eight questions a round. That's the deal."
    ],
    thinking: [
      "Take your time.",
      "No clock running.",
      "Read it twice if you like.",
      "Two of these look right. Only one is.",
      "Worth a second read.",
      "This one makes people hesitate.",
      "Your call. I'm just here for the commentary."
    ],
    happy: [
      "Nice one.",
      "That's it.",
      "Got it.",
      "Clean.",
      "Yes. Straight to the point.",
      "Textbook.",
      "You've done this before.",
      "Banked."
    ],
    encourage: [
      "Not yet. Here's why.",
      "Close. Have a look.",
      "Worth remembering.",
      "That one catches people.",
      "No harm done. It comes back tomorrow.",
      "Wrong today, known tomorrow. That's the job.",
      "The reason matters more than the guess."
    ],
    celebrate: [
      "Round done. Good work.",
      "That's a solid round.",
      "Finished. Go and get a coffee.",
      "Another round banked.",
      "Good session. Same time tomorrow?"
    ]
  };

  /* Short second lines. They run underneath the main line, so Pip can react and
     mutter at the same time. */
  var ASIDES = {
    idle: ["No pressure.", "Whenever you're ready.", "I'll be here."],
    thinking: ["(I checked. Twice.)", "Just saying.", "Back to it.", "No pressure."],
    happy: ["(That never gets old.)", "On to the next.", "Keep going."],
    encourage: [
      "(That's from Inland Revenue, not from me.)",
      "You'll get it next time.",
      "That's why we practise."
    ],
    celebrate: ["(I'm not tired. You might be.)", "Same time tomorrow?"]
  };

  /* Things Pip says on its own while you work. Dry, short, and never pretending
     to know more than the material does. */
  var COMMENTARY = [
    "Still here. Still not giving hints.",
    "This is the bit where people guess. Don't guess.",
    "Some of these rules are older than me.",
    "No marks for speed.",
    "Every answer here has a source. I like that about this place.",
    "If it feels obvious, check it anyway.",
    "The wrong answers are the ones people actually give.",
    "I once read the whole Income Tax Act. It is long.",
    "Being wrong is cheap here. That is the point.",
    "You are allowed to think.",
    "Quieter than a lecture theatre, this.",
    "Nothing you do here is sent anywhere. Relax."
  ];

  var POKES = [
    "Hello.",
    "That tickles.",
    "I'm a bird of few words. Mostly.",
    "Careful, I'm load-bearing.",
    "Still here.",
    "You found the poke button.",
    "I don't do tax advice. I do morale.",
    "Someone's avoiding question four.",
    "Poke received. Morale unchanged, but appreciated."
  ];

  var MARKUP = [
    '<svg viewBox="0 0 120 120" class="pet-svg" aria-hidden="true">',
    '<ellipse class="pet-shadow" cx="60" cy="105" rx="24" ry="5.5"/>',
    '<g class="pet-body">',
    '<line class="pet-antenna" x1="60" y1="28" x2="60" y2="16"/>',
    '<circle class="pet-tip" cx="60" cy="13" r="4.6"/>',
    '<path class="pet-shape" d="M60 25c20 0 32 14 32 33 0 20-14 33-32 33S28 78 28 58c0-19 12-33 32-33z"/>',
    '<ellipse class="pet-belly" cx="60" cy="71" rx="19" ry="17"/>',
    '<g class="pet-eyes">',
    '<ellipse class="pet-eye" cx="49" cy="53" rx="7" ry="7.4"/>',
    '<ellipse class="pet-eye" cx="71" cy="53" rx="7" ry="7.4"/>',
    '<circle class="pet-pupil" cx="50.5" cy="54" r="3.1"/>',
    '<circle class="pet-pupil" cx="72.5" cy="54" r="3.1"/>',
    "</g>",
    '<path class="pet-happy-eyes" d="M44 54q5-6 10 0M66 54q5-6 10 0"/>',
    '<path class="pet-beak" d="M60 61l-4.6 5 4.6 3.6 4.6-3.6z"/>',
    '<ellipse class="pet-cheek" cx="40" cy="65" rx="4" ry="2.5"/>',
    '<ellipse class="pet-cheek" cx="80" cy="65" rx="4" ry="2.5"/>',
    '<path class="pet-arm pet-arm-left" d="M28 61q-8 5-7 13"/>',
    '<path class="pet-arm pet-arm-right" d="M92 61q8 5 7 13"/>',
    '<ellipse class="pet-foot" cx="50" cy="99" rx="7" ry="3.3"/>',
    '<ellipse class="pet-foot" cx="70" cy="99" rx="7" ry="3.3"/>',
    "</g>",
    "</svg>"
  ].join("");

  var reduceMotion = window.matchMedia
    ? window.matchMedia("(prefers-reduced-motion: reduce)")
    : { matches: false };

  function pick(list, avoid) {
    if (!list.length) { return ""; }
    var fresh = list.filter(function (item) { return item !== avoid; });
    var pool = fresh.length ? fresh : list;
    return pool[Math.floor(Math.random() * pool.length)];
  }

  var Pet = {
    root: null,
    bubble: null,
    mood: "idle",
    level: 1,
    timer: null,
    ambient: null,
    lastLine: "",
    recentFacts: [],
    factSource: null,
    /** How often Pip speaks unprompted, in milliseconds. */
    ambientEvery: 26000,

    mount: function (container) {
      var wrapper = document.createElement("button");
      wrapper.type = "button";
      wrapper.setAttribute("aria-label", "Say hello to Pip");
      wrapper.className = "pet pet-idle";
      wrapper.setAttribute("data-level", "1");
      wrapper.innerHTML = MARKUP;

      var bubble = document.createElement("p");
      bubble.className = "pet-bubble";
      bubble.setAttribute("aria-live", "polite");

      container.appendChild(wrapper);
      container.appendChild(bubble);
      this.root = wrapper;
      this.bubble = bubble;
      wrapper.addEventListener("click", function () { Pet.poke(); });
      return wrapper;
    },

    /** Give Pip something true to say: a function returning a short sentence. */
    setFactSource: function (source) {
      this.factSource = source;
    },

    /** The bubble: a main line, and optionally a second line under it. */
    say: function (text, aside) {
      if (!this.bubble) { return; }
      var translate = window.bytetaxT || function (value) { return value; };
      this.bubble.textContent = "";
      if (text) {
        var line = document.createElement("span");
        line.className = "pet-line";
        line.textContent = translate(text);
        this.bubble.appendChild(line);
      }
      if (aside) {
        var second = document.createElement("span");
        second.className = "pet-aside";
        second.textContent = translate(aside);
        this.bubble.appendChild(second);
      }
      this.bubble.classList.toggle("is-on", Boolean(text || aside));
    },

    /** One of idle, thinking, happy, encourage, celebrate. */
    setMood: function (mood, line) {
      if (!this.root) { return; }
      this.root.className = "pet pet-" + mood;
      this.mood = mood;
      if (line === false) { return; }
      var says = line || pick(LINES[mood] || [], this.lastLine);
      this.lastLine = says;
      this.say(says, pick(ASIDES[mood] || [], ""));
      if (this.timer) { window.clearTimeout(this.timer); }
      if (mood === "happy" || mood === "encourage") {
        var self = this;
        this.timer = window.setTimeout(function () { self.setMood("idle", ""); }, 2400);
      }
    },

    setLevel: function (level) {
      if (!this.root) { return; }
      var grew = level > this.level;
      this.level = level;
      this.root.setAttribute("data-level", String(level));
      if (grew) { this.setMood("happy", "I grew a ring. That is you, not me."); }
    },

    /** A short reaction when the player clicks the companion. */
    poke: function () {
      if (!this.root) { return; }
      this.setMood("happy", pick(POKES, this.lastLine));
      this.burst(6);
    },

    /** A true sentence from the knowledge base, never the same one twice running. */
    factLine: function () {
      if (!this.factSource) { return ""; }
      var line = "";
      for (var attempt = 0; attempt < 6; attempt += 1) {
        line = this.factSource() || "";
        if (line && this.recentFacts.indexOf(line) === -1) { break; }
      }
      if (!line) { return ""; }
      this.recentFacts.push(line);
      if (this.recentFacts.length > 8) { this.recentFacts.shift(); }
      return line;
    },

    /** Pip's running commentary. It stays quiet unless the bubble is free. */
    startAmbient: function (every) {
      var self = this;
      this.stopAmbient();
      this.ambient = window.setInterval(function () {
        if (self.mood !== "idle") { return; }
        if (Math.random() < 0.34) {
          var fact = self.factLine();
          if (fact) { self.say(fact, "Did you know?"); return; }
        }
        self.say(pick(COMMENTARY, self.lastLine), "");
      }, every || this.ambientEvery);
      return this.ambient;
    },

    stopAmbient: function () {
      if (this.ambient) {
        window.clearInterval(this.ambient);
        this.ambient = null;
      }
    },

    /** A small burst of sparks, for a right answer. */
    burst: function (count) {
      if (!this.root || reduceMotion.matches) { return; }
      var sparks = count || 7;
      for (var i = 0; i < sparks; i += 1) {
        var spark = document.createElement("span");
        spark.className = "pet-spark";
        var angle = (i / sparks) * Math.PI * 2;
        spark.style.setProperty("--dx", Math.cos(angle).toFixed(2));
        spark.style.setProperty("--dy", Math.sin(angle).toFixed(2));
        spark.style.animationDelay = (i * 26) + "ms";
        this.root.appendChild(spark);
        window.setTimeout(function (node) {
          return function () { if (node.parentNode) { node.parentNode.removeChild(node); } };
        }(spark), 900);
      }
    }
  };

  window.ByteTaxPet = Pet;
})();
