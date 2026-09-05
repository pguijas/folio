/* Reading rail — Folio kanban prototype.
   Vanilla, file:// safe. window.BOARD comes from board-data.js,
   window.READER from reader-data.js. The reader is a right rail beside the
   live board; the card dialog collapses into the rail's crumb while a
   document is open. */
(function () {
  "use strict";

  var BOARD = window.BOARD || { title: "Board", columns: [] };
  var READER = window.READER || {};

  /* ------------------------------------------------------------------ *
   * model
   * ------------------------------------------------------------------ */

  var columns = BOARD.columns || [];
  var cards = [];
  var byId = {};
  var columnOf = {};

  columns.forEach(function (col) {
    (col.cards || []).forEach(function (card) {
      cards.push(card);
      byId[card.id] = card;
      columnOf[card.id] = col;
    });
  });

  /* owner card of a reader target, for restoring #art=… on load */
  var ownerOfTarget = {};
  cards.forEach(function (card) {
    (card.artifacts || []).forEach(function (art) {
      if (art.target && !ownerOfTarget[art.target]) {
        ownerOfTarget[art.target] = card.id;
      }
    });
  });

  function readable(art) {
    return !!(art && art.target && READER[art.target]);
  }

  function artLabel(art) {
    if (art.label) return art.label;
    var entry = READER[art.target];
    if (entry && entry.title) return entry.title;
    var bits = String(art.target || "").split("/");
    return bits[bits.length - 1] || art.target || art.kind;
  }

  /* ------------------------------------------------------------------ *
   * state
   * ------------------------------------------------------------------ */

  var state = {
    q: "",
    dialogCard: null,   /* card id whose dialog is open, or null */
    dialogOpener: null, /* element to refocus when the dialog closes */
    railCard: null,     /* card id being read on the rail, or null */
    railTarget: null    /* artifact target on the rail, or null */
  };

  /* ------------------------------------------------------------------ *
   * helpers
   * ------------------------------------------------------------------ */

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function el(sel) { return document.querySelector(sel); }

  function announce(msg) {
    var live = el("#live");
    if (live) live.textContent = msg;
  }

  function prefersReducedMotion() {
    return window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  /* ------------------------------------------------------------------ *
   * URL — the reading position is a hash
   * ------------------------------------------------------------------ */

  function writeHash() {
    var p = new URLSearchParams();
    if (state.q) p.set("q", state.q);
    if (state.dialogCard) p.set("card", state.dialogCard);
    if (state.railTarget) p.set("art", state.railTarget);
    var s = p.toString();
    var url = location.pathname + location.search + (s ? "#" + s : "");
    try {
      history.replaceState(null, "", url);
    } catch (e) {
      location.replace(url);
    }
  }

  function readHash() {
    return new URLSearchParams((location.hash || "").replace(/^#/, ""));
  }

  /* ------------------------------------------------------------------ *
   * board
   * ------------------------------------------------------------------ */

  var faceOf = {}; /* card id -> button element on the board */

  function cardFaceHtml(card) {
    var h = "";
    if (card.priority === "high") h += '<span class="card-edge" aria-hidden="true"></span>';
    h += '<span class="card-key">' + esc(card.id) + "</span>";
    h += '<span class="card-title">' + esc(card.title) + "</span>";

    var meta = [];
    if (card.type) meta.push("<span>" + esc(card.type) + "</span>");
    if (card.size) meta.push('<span class="size">' + esc(card.size) + "</span>");
    if (card.assignee && card.assignee.length) {
      meta.push("<span>" + esc(card.assignee.join(" · ")) + "</span>");
    }
    var n = (card.artifacts || []).length;
    if (n) {
      meta.push('<span class="arts">' + n + (n === 1 ? " artifact" : " artifacts") + "</span>");
    }
    if (meta.length) h += '<span class="card-meta">' + meta.join("") + "</span>";
    return h;
  }

  function renderBoard() {
    var root = el("#columns");
    var frag = document.createDocumentFragment();

    columns.forEach(function (col) {
      var sec = document.createElement("section");
      sec.className = "col";
      sec.setAttribute("aria-label", col.title);

      var head = document.createElement("header");
      head.className = "col-head";
      var count = (col.cards || []).length;
      var countHtml = col.limit != null ? count + " / " + col.limit : String(count);
      var over = col.limit != null && count > col.limit;
      head.innerHTML =
        "<h2>" + esc(col.title) + "</h2>" +
        '<span class="col-count"' + (over ? " data-over" : "") +
        (col.limit != null
          ? ' title="' + count + " of a limit of " + col.limit + '"'
          : "") +
        ">" + countHtml + "</span>";
      sec.appendChild(head);

      var list = document.createElement("ul");
      list.className = "col-list";

      if (!count) {
        var empty = document.createElement("p");
        empty.className = "col-empty";
        empty.textContent = "No cards";
        sec.appendChild(empty);
      }

      (col.cards || []).forEach(function (card) {
        var li = document.createElement("li");
        var btn = document.createElement("button");
        btn.type = "button";
        btn.className = "card";
        btn.setAttribute("aria-haspopup", "dialog");
        btn.dataset.id = card.id;
        btn.innerHTML = cardFaceHtml(card);
        btn.addEventListener("click", function () {
          openDialog(card.id, btn, null);
        });
        faceOf[card.id] = btn;
        li.appendChild(btn);
        list.appendChild(li);
      });

      sec.appendChild(list);
      frag.appendChild(sec);
    });

    root.appendChild(frag);
  }

  function markReadingFace() {
    Object.keys(faceOf).forEach(function (id) {
      if (id === state.railCard) faceOf[id].setAttribute("data-reading", "");
      else faceOf[id].removeAttribute("data-reading");
    });
  }

  /* ------------------------------------------------------------------ *
   * filter — hides card faces, never re-renders, writes q to the hash
   * ------------------------------------------------------------------ */

  function applyFilter() {
    var q = state.q.trim().toLowerCase();
    var hits = 0;
    cards.forEach(function (card) {
      var face = faceOf[card.id];
      if (!face) return;
      var hit = !q ||
        card.title.toLowerCase().indexOf(q) >= 0 ||
        card.id.toLowerCase().indexOf(q) >= 0;
      face.parentElement.hidden = !hit;
      if (hit) hits++;
    });
    var mc = el("#matchcount");
    if (!q) mc.textContent = cards.length + " cards";
    else mc.innerHTML = "<b>" + hits + "</b> of " + cards.length + " match";
  }

  /* ------------------------------------------------------------------ *
   * dialog — the mail. Its artifact band is the subject.
   * ------------------------------------------------------------------ */

  var dialogLayer, dialog;

  function metaRow(label, value, cls) {
    if (!value) return "";
    return "<div><dt>" + label + "</dt><dd" + (cls ? ' class="' + cls + '"' : "") +
      ">" + esc(value) + "</dd></div>";
  }

  function artTileHtml(card, art) {
    var isOpen = readable(art);
    var current = state.railCard === card.id && state.railTarget === art.target;
    var label = artLabel(art);
    var chip = '<span class="kind-chip" data-kind="' + esc(art.kind) + '">' +
      esc(art.kind) + "</span>";
    var pathLine = '<span class="art-path">' + esc(art.target) + "</span>";

    if (!isOpen) {
      /* A closed door: kind, label, path — flat, and not clickable. */
      return '<li><div class="art-tile" data-closed>' +
        '<span class="art-row">' + chip +
        '<span class="art-label">' + esc(label) + "</span>" +
        '<span class="art-open">not published</span></span>' +
        pathLine + "</div></li>";
    }

    return '<li><button type="button" class="art-tile" data-target="' +
      esc(art.target) + '"' + (current ? " data-current" : "") + ">" +
      '<span class="art-row">' + chip +
      '<span class="art-label">' + esc(label) + "</span>" +
      '<span class="art-open">' +
      (current ? "on the rail" : "read →") + "</span></span>" +
      pathLine + "</button></li>";
  }

  function dialogHtml(card) {
    var col = columnOf[card.id];
    var h = "";

    h += '<header class="dlg-head"><div>' +
      '<p class="eyebrow">' + esc(card.id) + "</p>" +
      '<h2 id="dlg-title">' + esc(card.title) + "</h2></div>" +
      '<button type="button" class="dlg-close" id="dlg-close">Close</button>' +
      "</header>";

    h += '<div class="dlg-body">';

    h += '<dl class="dlg-meta">' +
      metaRow("column", col ? col.title : "") +
      (card.priority
        ? '<div><dt>priority</dt><dd data-prio="' + esc(card.priority) + '">' +
          esc(card.priority) + "</dd></div>"
        : "") +
      metaRow("type", card.type) +
      metaRow("size", card.size) +
      metaRow("milestone", card.milestone) +
      metaRow("created", card.created, "mono") +
      metaRow("assignee", (card.assignee || []).join(", ")) +
      metaRow("tags", (card.tags || []).join(", "), "mono") +
      metaRow("parent", card.parent, "mono") +
      metaRow("blocked by", (card.blocked_by || []).join(", "), "mono") +
      "</dl>";

    if (card.description) {
      h += '<p class="dlg-desc">' + esc(card.description) + "</p>";
    }

    var crit = card.criteria || [];
    if (crit.length) {
      var done = crit.filter(function (c) { return c.done; }).length;
      h += '<h3 class="dlg-section-h">Acceptance criteria · ' + done +
        " of " + crit.length + "</h3>";
      h += '<ul class="criteria">' + crit.map(function (c) {
        return "<li" + (c.done ? " data-done" : "") +
          '><span class="box" aria-hidden="true"></span><span>' +
          (c.done
            ? '<span class="sr-only">done: </span>'
            : '<span class="sr-only">open: </span>') +
          esc(c.text) + "</span></li>";
      }).join("") + "</ul>";
    }

    var arts = card.artifacts || [];
    h += '<h3 class="dlg-section-h">Artifacts · ' + arts.length + "</h3>";
    if (arts.length) {
      h += '<ul class="art-band">' + arts.map(function (a) {
        return artTileHtml(card, a);
      }).join("") + "</ul>";
    } else {
      h += '<p class="dlg-desc">This card attached nothing.</p>';
    }

    h += "</div>";

    var foot = [];
    foot.push((card.comments || []).length + " comments");
    foot.push((card.trail || []).length + " trail entries");
    if (card.file) foot.push(card.file);
    h += '<footer class="dlg-foot">' + esc(foot.join(" · ")) + "</footer>";

    return h;
  }

  /* focusTarget: optional artifact target whose tile should take focus */
  function openDialog(cardId, opener, focusTarget) {
    var card = byId[cardId];
    if (!card) return;

    state.dialogCard = cardId;
    if (opener) state.dialogOpener = opener;

    dialog.innerHTML = dialogHtml(card);
    dialogLayer.hidden = false;

    el("#dlg-close").addEventListener("click", function () {
      closeDialog(true);
    });

    Array.prototype.forEach.call(
      dialog.querySelectorAll(".art-tile[data-target]"),
      function (tile) {
        tile.addEventListener("click", function () {
          openRail(cardId, tile.getAttribute("data-target"));
        });
      }
    );

    if (focusTarget) {
      var t = dialog.querySelector(
        '.art-tile[data-target="' + cssEscape(focusTarget) + '"]'
      );
      if (t) t.focus();
      else dialog.focus();
    } else {
      dialog.focus();
    }

    writeHash();
  }

  function closeDialog(refocus) {
    if (!state.dialogCard) return;
    state.dialogCard = null;
    dialogLayer.hidden = true;
    dialog.innerHTML = "";
    var opener = state.dialogOpener;
    state.dialogOpener = null;
    if (refocus && opener && document.contains(opener)) opener.focus();
    writeHash();
  }

  function cssEscape(s) {
    if (window.CSS && CSS.escape) return CSS.escape(s);
    return String(s).replace(/["\\\]]/g, "\\$&");
  }

  /* keep Tab inside the dialog while it is open */
  function trapTab(e) {
    if (!state.dialogCard || e.key !== "Tab") return;
    var focusables = dialog.querySelectorAll(
      "button, [href], input, [tabindex]:not([tabindex='-1'])"
    );
    if (!focusables.length) return;
    var first = focusables[0];
    var last = focusables[focusables.length - 1];
    var active = document.activeElement;
    if (!dialog.contains(active)) {
      e.preventDefault();
      first.focus();
    } else if (e.shiftKey && active === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && active === last) {
      e.preventDefault();
      first.focus();
    }
  }

  /* ------------------------------------------------------------------ *
   * rail — the reader beside the board
   * ------------------------------------------------------------------ */

  var rail, railMd, railFrame;

  function railIsOpen() { return !!state.railTarget; }

  function artifactsOf(cardId) {
    var card = byId[cardId];
    return card ? card.artifacts || [] : [];
  }

  function currentArtIndex() {
    var arts = artifactsOf(state.railCard);
    for (var i = 0; i < arts.length; i++) {
      if (arts[i].target === state.railTarget) return i;
    }
    return -1;
  }

  /* nearest readable artifact in a direction; -1 when there is none */
  function readableNeighbor(dir) {
    var arts = artifactsOf(state.railCard);
    var i = currentArtIndex();
    if (i < 0) return -1;
    for (var j = i + dir; j >= 0 && j < arts.length; j += dir) {
      if (readable(arts[j])) return j;
    }
    return -1;
  }

  function renderRailBand() {
    var arts = artifactsOf(state.railCard);
    var band = el("#rail-band");
    band.innerHTML = arts.map(function (a) {
      var chip = '<span class="kind-chip" data-kind="' + esc(a.kind) + '">' +
        esc(a.kind) + "</span>";
      var label = "<span>" + esc(artLabel(a)) + "</span>";
      if (!readable(a)) {
        return '<li><span class="band-tile" data-closed title="' +
          esc(a.target) + ' — not published">' + chip + label + "</span></li>";
      }
      var current = a.target === state.railTarget;
      return '<li><button type="button" class="band-tile" data-target="' +
        esc(a.target) + '" aria-current="' + (current ? "true" : "false") +
        '" title="' + esc(a.target) + '">' + chip + label + "</button></li>";
    }).join("");

    Array.prototype.forEach.call(
      band.querySelectorAll("button.band-tile"),
      function (tile) {
        tile.addEventListener("click", function () {
          openRail(state.railCard, tile.getAttribute("data-target"));
        });
      }
    );
  }

  function openRail(cardId, target) {
    var card = byId[cardId];
    var entry = READER[target];
    if (!card || !entry) return;

    var wasOpen = railIsOpen();
    var arts = artifactsOf(cardId);
    var art = null;
    for (var i = 0; i < arts.length; i++) {
      if (arts[i].target === target) { art = arts[i]; break; }
    }
    if (!art) return;

    state.railCard = cardId;
    state.railTarget = target;

    /* The dialog collapses into the crumb: one reading surface at a time. */
    if (state.dialogCard) closeDialog(false);

    document.body.setAttribute("data-rail", "");
    rail.removeAttribute("aria-hidden");
    rail.inert = false;

    el("#crumb-id").textContent = card.id;
    el("#crumb-title").textContent = card.title;

    var kindChip = el("#rail-kind");
    kindChip.textContent = art.kind;
    kindChip.setAttribute("data-kind", art.kind);
    el("#rail-label").textContent = artLabel(art);
    el("#rail-pos").textContent = (currentArtIndex() + 1) + " / " + arts.length;

    el("#rail-prev").disabled = readableNeighbor(-1) < 0;
    el("#rail-next").disabled = readableNeighbor(1) < 0;

    var full = el("#rail-full");
    if (entry.type === "html") {
      full.hidden = false;
      full.href = entry.src;
      full.title = "Open the artifact alone in a new tab";
    } else if (art.href) {
      full.hidden = false;
      full.href = art.href;
      full.title = "Compiled page — resolves on the served site";
    } else {
      full.hidden = true;
      full.removeAttribute("href");
    }

    renderRailBand();

    if (entry.type === "markdown") {
      railFrame.hidden = true;
      if (railFrame.getAttribute("src")) railFrame.src = "about:blank";
      railMd.hidden = false;
      railMd.innerHTML = entry.html; /* trusted, pre-rendered repo markdown */
      railMd.scrollTop = 0;
    } else {
      railMd.hidden = true;
      railMd.innerHTML = "";
      railFrame.hidden = false;
      railFrame.title = artLabel(art);
      if (railFrame.getAttribute("src") !== entry.src) railFrame.src = entry.src;
    }

    markReadingFace();

    var note = el("#reading-note");
    note.hidden = false;
    note.innerHTML = "reading <b>" + esc(artLabel(art)) + "</b>";

    el("#rail-art-title").focus({ preventScroll: true });

    if (!wasOpen) {
      el("#stage").scrollIntoView({
        block: "start",
        behavior: prefersReducedMotion() ? "auto" : "smooth"
      });
    }

    writeHash();
    announce("Reading " + artLabel(art) + " from " + card.title);
  }

  /* mode: "unwind" reopens the card dialog (Esc); "close" drops back to
     the board (the Close button). */
  function closeRail(mode) {
    if (!railIsOpen()) return;
    var cardId = state.railCard;
    var target = state.railTarget;

    state.railCard = null;
    state.railTarget = null;

    document.body.removeAttribute("data-rail");
    rail.setAttribute("aria-hidden", "true");
    rail.inert = true;
    railMd.innerHTML = "";
    railMd.hidden = true;
    if (railFrame.getAttribute("src")) railFrame.src = "about:blank";
    railFrame.hidden = true;

    markReadingFace();
    el("#reading-note").hidden = true;
    announce("Reader closed");

    if (mode === "unwind") {
      openDialog(cardId, faceOf[cardId] || null, target);
    } else {
      /* the face can be filtered out while reading; never drop focus */
      var face = faceOf[cardId];
      if (face && !face.parentElement.hidden) face.focus();
      else el("#q").focus();
      writeHash();
    }
  }

  function walkRail(dir) {
    var j = readableNeighbor(dir);
    if (j < 0) return;
    var arts = artifactsOf(state.railCard);
    openRail(state.railCard, arts[j].target);
  }

  /* ------------------------------------------------------------------ *
   * keyboard
   * ------------------------------------------------------------------ */

  function isTyping(e) {
    var t = e.target;
    return t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA");
  }

  function onKeydown(e) {
    if (e.key === "Escape") {
      /* a non-empty search field clears first — done here, not left to the
         browser: Firefox never clears search inputs on Escape */
      if (isTyping(e) && e.target.value) {
        e.preventDefault();
        e.target.value = "";
        state.q = "";
        applyFilter();
        writeHash();
        return;
      }
      if (state.dialogCard) {
        e.preventDefault();
        closeDialog(true);
      } else if (railIsOpen()) {
        e.preventDefault();
        closeRail("unwind");
      }
      return;
    }

    if (state.dialogCard && e.key === "Tab") {
      trapTab(e);
      return;
    }

    if (isTyping(e)) return;

    if (e.key === "/" && !state.dialogCard) {
      e.preventDefault();
      el("#q").focus();
      return;
    }

    if (railIsOpen() && !state.dialogCard) {
      if (e.key === "[") {
        e.preventDefault();
        walkRail(-1);
      } else if (e.key === "]") {
        e.preventDefault();
        walkRail(1);
      }
    }
  }

  /* ------------------------------------------------------------------ *
   * theme + init
   * ------------------------------------------------------------------ */

  function initTheme() {
    var buttons = document.querySelectorAll("[data-theme-set]");
    function set(v, persist) {
      document.documentElement.setAttribute("data-theme", v);
      Array.prototype.forEach.call(buttons, function (b) {
        b.setAttribute(
          "aria-pressed",
          b.getAttribute("data-theme-set") === v ? "true" : "false"
        );
      });
      if (persist) {
        try { localStorage.setItem("reading-rail-theme", v); } catch (err) {}
      }
    }
    Array.prototype.forEach.call(buttons, function (b) {
      b.addEventListener("click", function () {
        set(b.getAttribute("data-theme-set"), true);
      });
    });
    var saved = null;
    try { saved = localStorage.getItem("reading-rail-theme"); } catch (err) {}
    if (saved === "light" || saved === "dark" || saved === "auto") {
      set(saved, false);
    }
  }

  function restoreFromHash() {
    var p = readHash();

    var q = p.get("q") || "";
    if (q) {
      state.q = q;
      el("#q").value = q;
    }
    applyFilter();

    var art = p.get("art");
    if (art && READER[art] && ownerOfTarget[art]) {
      openRail(ownerOfTarget[art], art);
    }

    var cardId = p.get("card");
    if (cardId && byId[cardId]) {
      /* reopen the dialog on top of (or without) the rail */
      openDialog(cardId, faceOf[cardId] || null, null);
    }
  }

  function init() {
    dialogLayer = el("#dialog-layer");
    dialog = el("#dialog");
    rail = el("#rail");
    railMd = el("#rail-md");
    railFrame = el("#rail-frame");

    dialog.setAttribute("aria-modal", "true");
    rail.inert = true;

    renderBoard();
    applyFilter();
    initTheme();

    el("#q").addEventListener("input", function (e) {
      state.q = e.target.value;
      applyFilter();
      writeHash();
    });

    el("#scrim").addEventListener("click", function () { closeDialog(true); });
    el("#rail-close").addEventListener("click", function () { closeRail("close"); });
    el("#rail-crumb").addEventListener("click", function () {
      if (state.railCard) openDialog(state.railCard, el("#rail-crumb"), null);
    });
    el("#rail-prev").addEventListener("click", function () { walkRail(-1); });
    el("#rail-next").addEventListener("click", function () { walkRail(1); });

    document.addEventListener("keydown", onKeydown);

    restoreFromHash();
  }

  init();
})();
