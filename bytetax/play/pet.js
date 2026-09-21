/* Pip, the ByteTax companion.

   Drawn as inline SVG rather than a picture so the character stays sharp at any
   size, adds no download, and can be animated from CSS. Pip has a mood for each
   moment in a round and grows a ring as the player masters items.

   Poses are driven by a class on the wrapper: idle, thinking, happy, encourage,
   celebrate. Everything here is switched off under prefers-reduced-motion by
   the stylesheet. */

(function () {
  "use strict";

  var LINES = {
    thinking: ["Take your time.", "No clock running.", "Read it twice if you like."],
    happy: ["Nice one.", "That's it.", "Got it.", "Well spotted."],
    encourage: ["Not yet. Here's why.", "Close. Have a look.", "Worth remembering."],
    celebrate: ["Round done. Good work.", "That's a solid round."],
    levelup: ["I grew a ring. Keep going."]
  };

  var HELLO = [
    "Hello.",
    "Ready when you are.",
    "No rush. It's only practice.",
    "Ask me anything. Well, the questions do the talking."
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

  var Pet = {
    root: null,
    bubble: null,
    mood: "idle",
    level: 1,
    timer: null,

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

    /** A small reaction when the player clicks the companion directly. */
    poke: function () {
      if (!this.root) { return; }
      this.setMood("happy", HELLO[Math.floor(Math.random() * HELLO.length)]);
      this.burst(6);
    },

    say: function (text) {
      if (!this.bubble) { return; }
      this.bubble.textContent = text || "";
      this.bubble.classList.toggle("is-on", Boolean(text));
    },

    /** One of idle, thinking, happy, encourage, celebrate. */
    setMood: function (mood, line) {
      if (!this.root) { return; }
      this.root.className = "pet pet-" + mood;
      this.mood = mood;
      if (line === false) { return; }
      var pool = LINES[mood] || [];
      this.say(line || pool[Math.floor(Math.random() * pool.length)] || "");
      if (this.timer) { window.clearTimeout(this.timer); }
      if (mood === "happy" || mood === "encourage" || mood === "levelup") {
        var self = this;
        this.timer = window.setTimeout(function () { self.setMood("idle", ""); }, 2200);
      }
    },

    setLevel: function (level) {
      if (!this.root) { return; }
      var grew = level > this.level;
      this.level = level;
      this.root.setAttribute("data-level", String(level));
      if (grew) { this.setMood("happy", LINES.levelup[0]); }
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
