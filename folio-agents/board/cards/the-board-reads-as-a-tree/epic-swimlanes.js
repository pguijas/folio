/* Epic swimlanes — columns are status, rows are decomposition.
   Everything below is driven by window.BOARD. No row is hardcoded. */

(function () {
  "use strict";

  var BOARD = window.BOARD || { title: "", columns: [] };
  var COLS = BOARD.columns || [];
  var NCOL = COLS.length;

  /* ---------- model ---------- */

  var cards = [];          // flat, in board order
  var byId = new Map();    // id -> card
  var homeCol = new Map(); // id -> column index it ships in

  COLS.forEach(function (col, i) {
    (col.cards || []).forEach(function (card) {
      cards.push(card);
      byId.set(card.id, card);
      homeCol.set(card.id, i);
    });
  });

  /* Effective parent edges. `parent` is validated at build only against
     "exists" and "not self", so a -> b -> a ships fine. Every edge that
     closes a loop is dropped here, once, in board order, so the forest
     below is a forest and no walk can hang. */
  var effParent = new Map();
  cards.forEach(function (c) {
    var p = c.parent || "";
    if (!p || p === c.id || !byId.has(p)) p = "";
    effParent.set(c.id, p);
  });

  var brokenCycles = [];
  cards.forEach(function (c) {
    var seen = new Set([c.id]);
    var cur = effParent.get(c.id);
    var guard = 0;
    while (cur && guard++ < 500) {
      if (seen.has(cur)) {
        brokenCycles.push(c.id);
        effParent.set(c.id, "");
        break;
      }
      seen.add(cur);
      cur = effParent.get(cur);
    }
  });

  var kids = new Map(); // id -> [card]
  cards.forEach(function (c) {
    var p = effParent.get(c.id);
    if (!p) return;
    if (!kids.has(p)) kids.set(p, []);
    kids.get(p).push(c);
  });

  function childrenOf(id) { return kids.get(id) || []; }

  /* Pre-order descendants, cycle-safe by construction and by seen set. */
  function descendants(id) {
    var out = [];
    var seen = new Set([id]);
    (function walk(pid, depth) {
      childrenOf(pid).forEach(function (c) {
        if (seen.has(c.id)) return;
        seen.add(c.id);
        out.push({ card: c, depth: depth });
        walk(c.id, depth + 1);
      });
    })(id, 1);
    return out;
  }

  var roots = cards.filter(function (c) { return !effParent.get(c.id); });

  /* A lane per root that decomposes; everything else falls into one
     unlabelled lane at the end so no card is orphaned. */
  var lanes = [];
  roots.forEach(function (r) {
    if (childrenOf(r.id).length) {
      lanes.push({ key: "lane:" + r.id, epic: r, rows: descendants(r.id) });
    }
  });
  var flatRoots = roots.filter(function (r) { return !childrenOf(r.id).length; });
  if (flatRoots.length) {
    lanes.push({
      key: "lane:__flat__",
      epic: null,
      rows: flatRoots.map(function (c) { return { card: c, depth: 1 }; })
    });
  }

  /* ---------- state ---------- */

  var collapsed = new Set();
  var staged = new Map(); // card id -> target column index
  var query = "";
  var NESTED = cards.length - roots.length;

  function colOf(id) {
    return staged.has(id) ? staged.get(id) : homeCol.get(id);
  }

  function stage(id, target) {
    if (target === homeCol.get(id)) staged.delete(id);
    else staged.set(id, target);
    render();
  }

  function matches(card) {
    if (!query) return true;
    return (card.title + " " + card.id).toLowerCase().indexOf(query) !== -1;
  }

  /* ---------- small dom helpers ---------- */

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }

  function mark(text, into) {
    // highlights the live query inside a text node, case-insensitively
    if (!query) { into.textContent = text; return into; }
    var low = text.toLowerCase();
    var at = 0, i;
    while ((i = low.indexOf(query, at)) !== -1) {
      if (i > at) into.appendChild(document.createTextNode(text.slice(at, i)));
      var m = document.createElement("mark");
      m.textContent = text.slice(i, i + query.length);
      into.appendChild(m);
      at = i + query.length;
    }
    into.appendChild(document.createTextNode(text.slice(at)));
    return into;
  }

  function eyebrowText(card) {
    var bits = [];
    if (card.type) bits.push(card.type);
    if (card.milestone) bits.push(card.milestone);
    return bits.join(" · ");
  }

  /* ---------- the card face ---------- */

  function posControl(card, withLabel) {
    var wrap = el("div", "pos");
    var home = homeCol.get(card.id);
    var now = colOf(card.id);
    for (var i = 0; i < NCOL; i++) {
      var b = el("button", "pos-seg");
      b.type = "button";
      b.tabIndex = -1;
      b.dataset.move = card.id;
      b.dataset.col = String(i);
      b.setAttribute("aria-pressed", i === now ? "true" : "false");
      b.title = (i === now ? "In " : "Move to ") + COLS[i].title;
      b.setAttribute("aria-label", (i === now ? "In " : "Move to ") + COLS[i].title);
      if (i === now && staged.has(card.id)) b.classList.add("target");
      if (i === home && staged.has(card.id)) b.classList.add("origin");
      wrap.appendChild(b);
    }
    /* The label is redundant on a card — the card is standing in the column
       it names. It earns its place only in the rail, where the epic has no
       cell of its own to be read from. */
    if (withLabel) wrap.appendChild(el("span", "pos-label", COLS[now].title));
    return wrap;
  }

  function cardEl(row, opts) {
    var card = row.card;
    var node = el("div", "card");
    node.tabIndex = 0;
    node.dataset.nav = "card";
    node.dataset.card = card.id;
    node.setAttribute("role", "group");
    node.setAttribute("aria-label",
      card.title + ", " + COLS[colOf(card.id)].title +
      (staged.has(card.id) ? ", staged move from " + COLS[homeCol.get(card.id)].title : ""));

    if (row.depth > 1) {
      node.classList.add("nested");
      /* indent by the real depth below the epic, so a level-four descendant
         does not sit at the same offset as a level-two one */
      node.style.setProperty("--d", String(row.depth - 1));
    }
    if (opts.detached) {
      node.classList.add("detached");
      var parent = byId.get(effParent.get(card.id));
      if (parent) {
        var crumb = el("span", "crumb");
        crumb.appendChild(document.createTextNode("under "));
        crumb.appendChild(el("b", null, parent.title));
        node.appendChild(crumb);
      }
    }

    if (staged.has(card.id)) {
      node.classList.add("staged");
      var tag = el("div", "staged-tag");
      tag.appendChild(el("span", "dot"));
      tag.appendChild(document.createTextNode(
        "staged · was " + COLS[homeCol.get(card.id)].title));
      var undo = el("button", "undo", "undo");
      undo.type = "button";
      undo.tabIndex = -1;
      undo.dataset.undo = card.id;
      tag.appendChild(undo);
      node.appendChild(tag);
    }

    var eb = eyebrowText(card);
    if (eb) node.appendChild(el("span", "card-eyebrow", eb));

    var title = el("div", "card-title");
    mark(card.title, title);
    node.appendChild(title);

    var id = el("span", "card-id");
    mark(card.id, id);
    node.appendChild(id);

    var meta = el("div", "card-meta");
    if (card.priority === "high") {
      var p = el("span", "pri");
      p.setAttribute("aria-hidden", "true");
      meta.appendChild(p);
      meta.appendChild(el("span", "sr", "high"));
      meta.lastChild.style.cssText =
        "position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%)";
    }
    (card.assignee || []).forEach(function (name) {
      meta.appendChild(el("span", null, "@" + name));
    });
    var crit = card.criteria || [];
    if (crit.length) {
      var done = crit.filter(function (c) { return c.done; }).length;
      var cn = el("span", null, done + "/" + crit.length);
      cn.title = done + " of " + crit.length + " acceptance criteria met";
      meta.appendChild(cn);
    }
    if (card.size) meta.appendChild(el("span", "size", card.size));
    /* absent milestone / type / size / assignee render as nothing at all —
       no dash column, the line just gets shorter */
    meta.appendChild(posControl(card, false));
    node.appendChild(meta);
    return node;
  }

  function ghostEl(row, isEpic) {
    var card = row.card;
    var g = el("div", "ghost" +
      (row.depth > 1 ? " nested" : "") + (isEpic ? " ghost-epic" : ""));
    if (row.depth > 1) g.style.setProperty("--d", String(row.depth - 1));
    var t = card.title.length > 40 ? card.title.slice(0, 39) + "…" : card.title;
    g.appendChild(document.createTextNode((isEpic ? "epic " : "") + t + " → "));
    g.appendChild(el("b", null, COLS[colOf(card.id)].title));
    g.title = card.title + " is staged into " + COLS[colOf(card.id)].title;
    return g;
  }

  /* ---------- the lane rail ---------- */

  function rollupEl(lane) {
    var counts = new Array(NCOL).fill(0);
    lane.rows.forEach(function (r) { counts[colOf(r.card.id)]++; });
    var total = lane.rows.length;
    var wrap = el("div", "rollup");
    var bar = el("div", "rollup-bar");
    for (var i = 0; i < NCOL; i++) {
      if (!counts[i]) continue;
      var seg = el("div", "rollup-seg");
      seg.dataset.i = String(i);
      seg.style.width = (counts[i] / total * 100) + "%";
      seg.title = counts[i] + " in " + COLS[i].title;
      bar.appendChild(seg);
    }
    wrap.appendChild(bar);

    var line = el("div", "rollup-line");
    line.appendChild(el("span", "rollup-num",
      counts[NCOL - 1] + "/" + total));
    line.appendChild(el("span", null, COLS[NCOL - 1].title.toLowerCase()));

    var spread = counts.filter(function (n) { return n > 0; }).length;
    if (lane.epic && counts[colOf(lane.epic.id)] === 0) spread++;
    if (spread > 1) {
      var d = el("span", "drift", "spans " + spread);
      d.title = "this lane's work sits in " + spread + " different columns";
      line.appendChild(d);
    }
    wrap.appendChild(line);
    return wrap;
  }

  function railEl(lane, isContext, shownCount) {
    var rail = el("div", "rail");
    rail.tabIndex = 0;
    rail.dataset.nav = "rail";
    rail.dataset.lane = lane.key;

    var open = !collapsed.has(lane.key);
    /* The rail, not the twisty, is the tab stop — Enter and the arrows toggle
       from here — so the expanded state has to be announced on the rail too. */
    rail.setAttribute("role", "group");
    rail.setAttribute("aria-expanded", open ? "true" : "false");

    var tw = el("button", "twisty");
    tw.type = "button";
    tw.tabIndex = -1;
    tw.setAttribute("aria-expanded", open ? "true" : "false");
    tw.dataset.toggle = lane.key;
    rail.appendChild(tw);

    var body = el("div", "rail-body");

    var eyebrow = el("div", "rail-eyebrow");
    if (lane.epic) {
      var bits = ["epic"];
      var eb = eyebrowText(lane.epic);
      if (eb) bits.push(eb);
      eyebrow.appendChild(el("span", null, bits.join(" · ")));
    } else {
      eyebrow.appendChild(el("span", null, "standalone"));
    }
    if (isContext) {
      var ctx = el("span", "tag-ctx", "context");
      ctx.title = "this lane did not match — it is here to hold its children";
      eyebrow.appendChild(ctx);
    }
    body.appendChild(eyebrow);

    var title = el("div", "rail-title");
    if (lane.epic) mark(lane.epic.title, title);
    else title.textContent = "No epic";
    body.appendChild(title);

    var sub = el("span", "rail-id");
    if (lane.epic) mark(lane.epic.id, sub);
    else {
      sub.classList.add("note");
      sub.textContent = lane.rows.length + " cards · no parent, no children";
    }
    body.appendChild(sub);

    if (lane.epic) {
      body.appendChild(rollupEl(lane));
      body.appendChild(posControl(lane.epic, true));
    }

    rail.setAttribute("aria-label",
      (lane.epic ? "Lane " + lane.epic.title : "Lane without an epic") +
      ", " + lane.rows.length + " children, " +
      (open ? "expanded" : "collapsed") +
      (shownCount != null && query ? ", " + shownCount + " matching" : ""));

    rail.appendChild(body);
    return rail;
  }

  /* ---------- the board ---------- */

  var boardEl = document.getElementById("board");
  var emptyEl = document.getElementById("empty-all");

  function headEl(laneCount) {
    var head = el("div", "head");
    var rh = el("div", "head-cell rail-head");
    rh.appendChild(el("span", "head-title", "Epic"));
    rh.appendChild(el("span", "head-count",
      laneCount + (laneCount === 1 ? " lane" : " lanes")));
    head.appendChild(rh);

    var live = new Array(NCOL).fill(0);
    cards.forEach(function (c) { live[colOf(c.id)]++; });

    COLS.forEach(function (col, i) {
      var h = el("div", "head-cell");
      h.appendChild(el("span", "head-title", col.title));
      var over = col.limit != null && live[i] > col.limit;
      var cnt = el("span", "head-count" + (over ? " over" : ""),
        col.limit != null ? live[i] + "/" + col.limit : String(live[i]));
      cnt.title = col.limit != null
        ? live[i] + " cards against a WIP limit of " + col.limit
        : live[i] + " cards";
      h.appendChild(cnt);
      head.appendChild(h);
    });
    return head;
  }

  function laneEl(lane) {
    var epicMatch = lane.epic ? matches(lane.epic) : false;
    var shown = query ? lane.rows.filter(function (r) { return matches(r.card); })
                      : lane.rows;
    if (query && !epicMatch && !shown.length) return null;

    var node = el("div", "lane");
    if (!lane.epic) node.classList.add("flat");
    if (query && lane.epic && !epicMatch) node.classList.add("is-context");
    var isCollapsed = collapsed.has(lane.key);
    if (isCollapsed) node.classList.add("collapsed");

    node.appendChild(railEl(lane, query && lane.epic && !epicMatch, shown.length));

    var inCell = new Map(); // id -> column index, for the cards actually drawn
    shown.forEach(function (r) { inCell.set(r.card.id, colOf(r.card.id)); });

    for (var i = 0; i < NCOL; i++) {
      (function (i) {
        var cell = el("div", "cell");
        cell.dataset.col = String(i);
        if (lane.epic && colOf(lane.epic.id) === i) {
          cell.classList.add("epic-here");
          var m = el("span", "cell-mark", "epic");
          m.title = (lane.epic.title) + " itself sits in " + COLS[i].title;
          cell.appendChild(m);
        }
        /* An epic staged out of its column leaves the same ghost line a card
           leaves, otherwise the accent rule teleports and nothing marks where
           the epic came from. */
        if (lane.epic && !isCollapsed && staged.has(lane.epic.id) &&
            homeCol.get(lane.epic.id) === i) {
          cell.appendChild(ghostEl({ card: lane.epic, depth: 1 }, true));
        }
        var here = 0;
        shown.forEach(function (r) {
          var id = r.card.id;
          if (colOf(id) === i) {
            here++;
            if (isCollapsed) return;
            var parentId = effParent.get(id);
            var detached = r.depth > 1 &&
              (!inCell.has(parentId) || inCell.get(parentId) !== i);
            cell.appendChild(cardEl(r, { detached: detached }));
          } else if (staged.has(id) && homeCol.get(id) === i && !isCollapsed) {
            cell.appendChild(ghostEl(r));
          }
        });
        if (isCollapsed && here) {
          cell.appendChild(el("div", "cell-collapsed",
            here + (here === 1 ? " card" : " cards")));
        }
        /* The lane survived on the epic's own title. Say so in the epic's cell
           rather than drawing four blank ones and letting it read as an epic
           that decomposes into nothing. */
        var hidden = lane.rows.length - shown.length;
        if (query && hidden && !isCollapsed &&
            lane.epic && colOf(lane.epic.id) === i) {
          cell.appendChild(el("div", "cell-empty",
            hidden + (hidden === 1 ? " child" : " children") +
            " hidden by the filter"));
        }
        node.appendChild(cell);
      })(i);
    }
    return node;
  }

  function render() {
    var focusKey = null;
    var active = document.activeElement;
    if (active && active.dataset && active.dataset.nav) {
      focusKey = active.dataset.nav + ":" + (active.dataset.card || active.dataset.lane);
    }

    boardEl.textContent = "";
    var drawn = [];
    lanes.forEach(function (lane) {
      var n = laneEl(lane);
      if (n) drawn.push(n);
    });

    boardEl.appendChild(headEl(drawn.length));
    drawn.forEach(function (n) { boardEl.appendChild(n); });
    emptyEl.hidden = drawn.length > 0;
    boardEl.hidden = drawn.length === 0;

    var shownCards = query ? cards.filter(matches).length : cards.length;
    document.getElementById("result-line").textContent = query
      ? shownCards + " of " + cards.length + " cards · " +
        drawn.length + " of " + lanes.length + " lanes"
      : cards.length + " cards · " + lanes.length + " lanes · " +
        NESTED + " with a parent";

    syncStaged();

    if (focusKey) {
      var sel = focusKey.indexOf("card:") === 0
        ? '[data-card="' + focusKey.slice(5) + '"]'
        : '[data-lane="' + focusKey.slice(5) + '"]';
      var again = boardEl.querySelector(sel);
      if (again) again.focus({ preventScroll: true });
    }
  }

  /* ---------- staging ---------- */

  var countEl = document.getElementById("staged-count");
  var showBtn = document.getElementById("show-commands");
  var clearBtn = document.getElementById("clear-staged");
  var panel = document.getElementById("cmd-panel");
  var scrim = document.getElementById("cmd-scrim");
  var cmdText = document.getElementById("cmd-text");
  var cmdStatus = document.getElementById("cmd-status");

  function commands() {
    var out = [];
    cards.forEach(function (c) {
      if (staged.has(c.id)) {
        out.push("folio kanban move " + c.id + " " + COLS[staged.get(c.id)].id);
      }
    });
    return out.join("\n");
  }

  function syncStaged() {
    var n = staged.size;
    countEl.textContent = String(n);
    countEl.dataset.live = n ? "1" : "0";
    showBtn.disabled = n === 0;
    clearBtn.disabled = n === 0;
    if (!panel.hidden) {
      if (!n) closePanel();
      else cmdText.value = commands();
    }
  }

  function openPanel() {
    cmdText.value = commands();
    cmdStatus.textContent = "";
    panel.hidden = false;
    scrim.hidden = false;
    cmdText.focus();
    cmdText.select();
  }

  function closePanel() {
    panel.hidden = true;
    scrim.hidden = true;
    (showBtn.disabled ? qInput : showBtn).focus();
  }

  showBtn.addEventListener("click", openPanel);
  scrim.addEventListener("click", closePanel);
  document.getElementById("cmd-close").addEventListener("click", closePanel);
  clearBtn.addEventListener("click", function () {
    staged.clear();
    render();
    closePanel();
  });

  document.getElementById("cmd-copy").addEventListener("click", function () {
    cmdText.focus();
    cmdText.select();
    var ok = false;
    try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
    if (!ok && navigator.clipboard) {
      navigator.clipboard.writeText(cmdText.value).then(function () {
        cmdStatus.textContent = "copied";
      }, function () {
        cmdStatus.textContent = "select and copy";
      });
      return;
    }
    cmdStatus.textContent = ok ? "copied" : "select and copy";
  });

  /* ---------- events ---------- */

  boardEl.addEventListener("click", function (ev) {
    var move = ev.target.closest("[data-move]");
    if (move) {
      stage(move.dataset.move, Number(move.dataset.col));
      return;
    }
    var undo = ev.target.closest("[data-undo]");
    if (undo) {
      staged.delete(undo.dataset.undo);
      render();
      return;
    }
    var rail = ev.target.closest(".rail");
    if (rail) toggleLane(rail.dataset.lane);
  });

  function toggleLane(key) {
    if (collapsed.has(key)) collapsed.delete(key);
    else collapsed.add(key);
    render();
  }

  document.getElementById("collapse-all").addEventListener("click", function () {
    lanes.forEach(function (l) { collapsed.add(l.key); });
    render();
  });

  document.getElementById("expand-all").addEventListener("click", function () {
    collapsed.clear();
    render();
  });

  var qInput = document.getElementById("q");
  qInput.addEventListener("input", function () {
    query = qInput.value.trim().toLowerCase();
    render();
  });

  /* ---------- keyboard ---------- */

  function navList() {
    return Array.prototype.slice.call(boardEl.querySelectorAll("[data-nav]"));
  }

  function step(node, dir) {
    var list = navList();
    var i = list.indexOf(node);
    var next = list[i + dir];
    if (next) next.focus();
  }

  function across(node, dir) {
    var lane = node.closest(".lane");
    var cell = node.closest(".cell");
    if (!lane || !cell) return;
    var cells = Array.prototype.slice.call(lane.querySelectorAll(".cell"));
    var at = cells.indexOf(cell);
    for (var i = at + dir; i >= 0 && i < cells.length; i += dir) {
      var target = cells[i].querySelector(".card");
      if (target) { target.focus(); return; }
    }
  }

  boardEl.addEventListener("keydown", function (ev) {
    var node = ev.target.closest ? ev.target.closest("[data-nav]") : null;
    if (!node) return;
    var k = ev.key;

    if (node.dataset.nav === "rail") {
      var key = node.dataset.lane;
      var isOpen = !collapsed.has(key);
      if (k === "Enter" || k === " ") { ev.preventDefault(); toggleLane(key); return; }
      if (k === "ArrowLeft" && isOpen) { ev.preventDefault(); toggleLane(key); return; }
      if (k === "ArrowRight" && !isOpen) { ev.preventDefault(); toggleLane(key); return; }
      if (k === "ArrowRight" && isOpen) {
        var first = node.closest(".lane").querySelector(".card");
        if (first) { ev.preventDefault(); first.focus(); }
      }
    }

    if (node.dataset.nav === "card") {
      var id = node.dataset.card;
      if (ev.altKey && (k === "ArrowLeft" || k === "ArrowRight")) {
        ev.preventDefault();
        var t = colOf(id) + (k === "ArrowRight" ? 1 : -1);
        if (t >= 0 && t < NCOL) stage(id, t);
        return;
      }
      if (k >= "1" && k <= "9" && !ev.altKey && !ev.metaKey && !ev.ctrlKey) {
        var n = Number(k) - 1;
        if (n < NCOL) { ev.preventDefault(); stage(id, n); }
        return;
      }
      if ((k === "Backspace" || k === "Delete") && staged.has(id)) {
        ev.preventDefault();
        staged.delete(id);
        render();
        return;
      }
      if (k === "ArrowLeft" || k === "ArrowRight") {
        ev.preventDefault();
        across(node, k === "ArrowRight" ? 1 : -1);
        return;
      }
    }

    if (k === "ArrowDown") { ev.preventDefault(); step(node, 1); }
    else if (k === "ArrowUp") { ev.preventDefault(); step(node, -1); }
    else if (k === "Home") { ev.preventDefault(); (navList()[0] || node).focus(); }
    else if (k === "End") {
      ev.preventDefault();
      var l = navList();
      (l[l.length - 1] || node).focus();
    }
  });

  document.addEventListener("keydown", function (ev) {
    if (ev.key === "Escape" && !panel.hidden) { ev.preventDefault(); closePanel(); }
    var tag = document.activeElement ? document.activeElement.tagName : "";
    if (ev.key === "/" && tag !== "INPUT" && tag !== "TEXTAREA" &&
        !ev.metaKey && !ev.ctrlKey && !ev.altKey) {
      ev.preventDefault();
      qInput.focus();
      qInput.select();
    }
  });

  /* ---------- chrome ---------- */

  var root = document.documentElement;
  var themeBtn = document.getElementById("theme-toggle");

  function setTheme(t) {
    root.dataset.theme = t;
    themeBtn.textContent = t === "dark" ? "Light" : "Dark";
    themeBtn.setAttribute("aria-pressed", t === "dark" ? "true" : "false");
  }

  setTheme(window.matchMedia &&
    window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");

  themeBtn.addEventListener("click", function () {
    setTheme(root.dataset.theme === "dark" ? "light" : "dark");
  });

  function measure() {
    var bar = document.querySelector(".toolbar");
    root.style.setProperty("--stick", (bar ? bar.offsetHeight : 62) + "px");
  }

  root.style.setProperty("--ncols", String(NCOL));
  window.addEventListener("resize", measure);

  render();
  measure();

  /* exposed for poking at in the console, nothing depends on it */
  window.__SWIM = {
    cards: cards, lanes: lanes, colOf: colOf, staged: staged,
    brokenCycles: brokenCycles, render: render
  };
})();
