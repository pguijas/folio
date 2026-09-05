/* Tree rail and detail — Folio kanban prototype.
   Vanilla, file:// safe. window.BOARD comes from board-data.js. */
(function () {
  "use strict";

  var BOARD = window.BOARD || { title: "Board", columns: [] };
  var BOARD_NODE = "__board__";

  /* ------------------------------------------------------------------ *
   * model
   * ------------------------------------------------------------------ */

  var columns = (BOARD.columns || []).map(function (c, i) {
    return { id: c.id, title: c.title, limit: c.limit, index: i };
  });
  var colById = {};
  columns.forEach(function (c) { colById[c.id] = c; });

  var cards = [];
  (BOARD.columns || []).forEach(function (c) {
    (c.cards || []).forEach(function (card) { cards.push(card); });
  });

  var byId = {};
  cards.forEach(function (c) { byId[c.id] = c; });

  /* Cycle-safe parent resolution. A card keeps its parent only if the chain
     above it terminates. a.parent=b, b.parent=a leaves both as roots. */
  var brokenCycle = {};
  var parentOf = {};

  cards.forEach(function (card) {
    var p = card.parent;
    if (!p || p === card.id || !byId[p]) return;
    var seen = {};
    seen[card.id] = true;
    var cur = p;
    var steps = 0;
    var ok = true;
    while (cur && steps <= cards.length + 1) {
      if (seen[cur]) { ok = false; break; }
      seen[cur] = true;
      cur = byId[cur] ? byId[cur].parent : null;
      if (cur && !byId[cur]) cur = null;
      steps++;
    }
    if (steps > cards.length + 1) ok = false;
    if (ok) parentOf[card.id] = p;
    else brokenCycle[card.id] = true;
  });

  var childrenOf = {};
  cards.forEach(function (card) {
    var p = parentOf[card.id];
    if (!p) return;
    (childrenOf[p] = childrenOf[p] || []).push(card.id);
  });

  var roots = cards.filter(function (c) { return !parentOf[c.id]; }).map(function (c) { return c.id; });

  function kids(id) { return childrenOf[id] || []; }
  function hasKids(id) { return kids(id).length > 0; }

  /* depth, cycle-safe by construction */
  var depthOf = {};
  (function () {
    function walk(id, d, guard) {
      if (guard[id]) return;
      guard[id] = true;
      depthOf[id] = d;
      kids(id).forEach(function (k) { walk(k, d + 1, guard); });
    }
    var guard = {};
    roots.forEach(function (r) { walk(r, 0, guard); });
    cards.forEach(function (c) { if (depthOf[c.id] == null) depthOf[c.id] = 0; });
  })();

  /* descendants, cycle-safe */
  function subtree(id) {
    var out = [];
    var seen = {};
    var stack = kids(id).slice();
    seen[id] = true;
    while (stack.length) {
      var cur = stack.shift();
      if (seen[cur]) continue;
      seen[cur] = true;
      out.push(cur);
      kids(cur).forEach(function (k) { if (!seen[k]) stack.push(k); });
    }
    return out;
  }

  function ancestors(id) {
    var out = [];
    var seen = {};
    var cur = parentOf[id];
    while (cur && !seen[cur]) {
      seen[cur] = true;
      out.push(cur);
      cur = parentOf[cur];
    }
    return out;
  }

  /* ------------------------------------------------------------------ *
   * state
   * ------------------------------------------------------------------ */

  var state = {
    selected: BOARD_NODE,
    collapsed: {},
    moves: {},
    movesOrder: [],
    query: "",
    focusId: BOARD_NODE
  };

  function statusOf(id) {
    if (Object.prototype.hasOwnProperty.call(state.moves, id)) return state.moves[id];
    var c = byId[id];
    return c ? c.status : "";
  }
  function isStaged(id) { return Object.prototype.hasOwnProperty.call(state.moves, id); }

  function colTitle(cid) { return colById[cid] ? colById[cid].title : cid; }
  function colIndex(cid) { return colById[cid] ? colById[cid].index : -1; }

  /* a child diverges when its column is not its parent's column */
  function diverges(id) {
    var p = parentOf[id];
    if (!p) return false;
    return statusOf(id) !== statusOf(p);
  }

  function setMove(id, target) {
    var card = byId[id];
    if (!card) return;
    if (!target || target === card.status) {
      delete state.moves[id];
      state.movesOrder = state.movesOrder.filter(function (x) { return x !== id; });
    } else {
      if (!isStaged(id)) state.movesOrder.push(id);
      state.moves[id] = target;
    }
  }

  function moveCommands() {
    return state.movesOrder.map(function (id) {
      return "folio kanban move " + id + " " + state.moves[id];
    }).join("\n");
  }

  /* ------------------------------------------------------------------ *
   * small helpers
   * ------------------------------------------------------------------ */

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function el(sel) { return document.querySelector(sel); }

  function matches(id) {
    var q = state.query;
    if (!q) return false;
    var c = byId[id];
    if (!c) return false;
    return (c.title || "").toLowerCase().indexOf(q) >= 0 || c.id.toLowerCase().indexOf(q) >= 0;
  }

  function markQuery(text) {
    var q = state.query;
    var safe = esc(text);
    if (!q) return safe;
    var needle = esc(q);
    var lower = safe.toLowerCase();
    var i = lower.indexOf(needle.toLowerCase());
    if (i < 0) return safe;
    return safe.slice(0, i) + "<mark>" + safe.slice(i, i + needle.length) + "</mark>" + safe.slice(i + needle.length);
  }

  /* markdown-lite: paragraphs, lists, **bold**, `code` */
  /* code spans are held aside so a `**literal**` inside one stays literal —
     these cards talk about markdown, so mangling their own examples reads badly */
  function inlineMd(s) {
    var held = [];
    function hold(inner) {
      held.push(inner);
      return "\u0000" + (held.length - 1) + "\u0000";
    }
    var t = esc(s)
      .replace(/``([\s\S]+?)``/g, function (m, inner) { return hold(inner.replace(/^ | $/g, "")); })
      .replace(/`([^`]+)`/g, function (m, inner) { return hold(inner); })
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    return t.replace(/\u0000(\d+)\u0000/g, function (m, i) {
      return "<code>" + held[Number(i)] + "</code>";
    });
  }

  function renderMd(src) {
    if (!src) return "";
    var blocks = String(src).split(/\n{2,}/);
    var out = [];
    blocks.forEach(function (b) {
      var lines = b.split("\n");
      var isList = lines.every(function (l) { return /^\s*[-*]\s+/.test(l) || /^\s*$/.test(l); }) &&
        lines.some(function (l) { return /^\s*[-*]\s+/.test(l); });
      if (isList) {
        out.push("<ul>" + lines.filter(function (l) { return /\S/.test(l); }).map(function (l) {
          return "<li>" + inlineMd(l.replace(/^\s*[-*]\s+/, "")) + "</li>";
        }).join("") + "</ul>");
      } else {
        out.push("<p>" + inlineMd(b.replace(/\n/g, " ")) + "</p>");
      }
    });
    return out.join("");
  }

  /* ------------------------------------------------------------------ *
   * filtering — matches keep their ancestors as context
   * ------------------------------------------------------------------ */

  var filter = { active: false, match: {}, path: {}, open: {}, visible: {}, nMatch: 0 };

  function computeFilter() {
    filter = { active: false, match: {}, path: {}, open: {}, visible: {}, nMatch: 0 };
    if (!state.query) return;
    filter.active = true;
    cards.forEach(function (c) {
      if (matches(c.id)) { filter.match[c.id] = true; filter.visible[c.id] = true; }
    });
    Object.keys(filter.match).forEach(function (id) {
      /* every ancestor of a match opens, whether or not it is itself a match,
         otherwise a match nested under a collapsed match is silently dropped */
      ancestors(id).forEach(function (a) {
        filter.visible[a] = true;
        filter.open[a] = true;
        if (!filter.match[a]) filter.path[a] = true;
      });
      subtree(id).forEach(function (d) { filter.visible[d] = true; });
    });
    filter.nMatch = Object.keys(filter.match).length;
  }

  function isVisible(id) { return !filter.active || !!filter.visible[id]; }

  function isOpen(id) {
    if (!hasKids(id)) return false;
    if (filter.active && filter.open[id]) return true;   /* paths to matches auto-expand */
    return !state.collapsed[id];
  }

  /* ------------------------------------------------------------------ *
   * rail
   * ------------------------------------------------------------------ */

  var order = [];   /* ids in visual order, for the keyboard */

  function rowHtml(id, level) {
    var card = byId[id];
    var st = statusOf(id);
    var open = isOpen(id);
    var hiddenBelow = open ? 0 : subtree(id).filter(isVisible).length;
    var cls = ["row"];
    if (state.selected === id) cls.push("is-selected");
    if (level === 2) cls.push("is-root");
    if (filter.path[id]) cls.push("is-context");
    if (diverges(id)) cls.push("is-divergent");
    if (isStaged(id)) cls.push("is-moved");

    var tags = "";
    if (hasKids(id) && !open) tags += '<span class="rtag count">' + hiddenBelow + "</span>";
    if (isStaged(id)) tags += '<span class="rtag staged">&rarr; ' + esc(colTitle(st)) + "</span>";
    if (filter.path[id]) tags += '<span class="rtag">path</span>';

    var title = card.title + "  ·  " + id + "  ·  " + colTitle(st) +
      (diverges(id) ? "  ·  column differs from parent" : "");

    return '<div class="' + cls.join(" ") + '" role="treeitem" data-id="' + esc(id) + '"' +
      ' aria-level="' + level + '" aria-selected="' + (state.selected === id) + '"' +
      (hasKids(id) ? ' aria-expanded="' + open + '"' : "") +
      ' tabindex="' + (state.focusId === id ? "0" : "-1") + '"' +
      ' style="--depth:' + (level - 1) + '" title="' + esc(title) + '">' +
      '<span class="twisty' + (hasKids(id) ? "" : " is-leaf") + '" data-act="twisty" aria-hidden="true"></span>' +
      '<span class="dot" style="--dot: var(--col-' + esc(st || "backlog") + ')"></span>' +
      '<span class="rname">' + markQuery(card.title) + "</span>" +
      tags +
      "</div>";
  }

  function branchHtml(id, level, guard) {
    if (guard[id]) return "";
    guard[id] = true;
    if (!isVisible(id)) return "";
    order.push(id);
    var html = rowHtml(id, level);
    if (hasKids(id) && isOpen(id)) {
      var inner = kids(id).map(function (k) { return branchHtml(k, level + 1, guard); }).join("");
      if (inner) html += '<div role="group">' + inner + "</div>";
    }
    return html;
  }

  function renderRail() {
    var tree = el("#tree");
    order = [];
    var guard = {};

    var boardOpen = !state.collapsed[BOARD_NODE];
    var boardCls = "row tree-board-row" + (state.selected === BOARD_NODE ? " is-selected" : "");
    order.push(BOARD_NODE);

    var html = '<div class="' + boardCls + '" role="treeitem" data-id="' + BOARD_NODE + '"' +
      ' aria-level="1" aria-selected="' + (state.selected === BOARD_NODE) + '"' +
      ' aria-expanded="' + boardOpen + '" tabindex="' + (state.focusId === BOARD_NODE ? "0" : "-1") + '"' +
      ' style="--depth:0" title="The whole board">' +
      '<span class="twisty" data-act="twisty" aria-hidden="true"></span>' +
      '<span class="dot" style="--dot: var(--border)"></span>' +
      '<span class="rname">' + esc(BOARD.title || "Board") + "</span></div>";

    var rootHtml = "";
    if (boardOpen) {
      rootHtml = roots.map(function (r) { return branchHtml(r, 2, guard); }).join("");
      if (rootHtml) rootHtml = '<div role="group">' + rootHtml + "</div>";
    }

    tree.innerHTML = html + rootHtml;

    var nothing = filter.active && filter.nMatch === 0;
    el("#rail-empty").hidden = !nothing;

    var shown = order.length - 1;
    el("#rail-count").textContent = filter.active
      ? shown + "/" + cards.length
      : cards.length + " cards";

    /* make sure exactly one row is tabbable */
    if (order.indexOf(state.focusId) < 0) {
      state.focusId = order.length ? order[0] : BOARD_NODE;
      var first = tree.querySelector('[data-id="' + cssId(state.focusId) + '"]');
      if (first) first.setAttribute("tabindex", "0");
    }
  }

  function cssId(id) { return String(id).replace(/"/g, '\\"'); }

  function renderSearchNote() {
    var note = el("#query-note");
    if (!filter.active) {
      note.textContent = "";
      note.classList.remove("is-empty-result");
      return;
    }
    /* counted off the rows actually on screen, so the toolbar never promises
       rows the rail is not showing */
    var extra = 0;
    order.forEach(function (id) {
      if (id !== BOARD_NODE && !filter.match[id]) extra++;
    });
    note.classList.toggle("is-empty-result", filter.nMatch === 0);
    note.textContent = filter.nMatch + " match" + (filter.nMatch === 1 ? "" : "es") +
      (extra ? " · +" + extra + " row" + (extra === 1 ? "" : "s") + " kept for context" : "");
  }

  function renderLegend() {
    el("#rail-legend").innerHTML = columns.map(function (c) {
      return '<span class="legend-item"><span class="dot" style="--dot: var(--col-' + esc(c.id) + ')"></span>' +
        esc(c.title) + "</span>";
    }).join("");
  }

  /* ------------------------------------------------------------------ *
   * detail — rollup
   * ------------------------------------------------------------------ */

  function tally(ids) {
    var counts = {};
    columns.forEach(function (c) { counts[c.id] = 0; });
    var crit = { done: 0, total: 0 };
    ids.forEach(function (id) {
      var st = statusOf(id);
      if (counts[st] == null) counts[st] = 0;
      counts[st]++;
      var c = byId[id];
      (c && c.criteria ? c.criteria : []).forEach(function (k) {
        crit.total++;
        if (k.done) crit.done++;
      });
    });
    return { counts: counts, crit: crit, total: ids.length };
  }

  function barHtml(counts, total) {
    if (!total) return "";
    return '<div class="bar" role="img" aria-label="' + esc(columns.map(function (c) {
      return counts[c.id] + " " + c.title;
    }).join(", ")) + '">' + columns.map(function (c) {
      var n = counts[c.id] || 0;
      if (!n) return "";
      return '<span class="bar-seg" style="flex:' + n + ';background:var(--col-' + esc(c.id) + ')"></span>';
    }).join("") + "</div>";
  }

  function keyHtml(counts) {
    return '<ul class="bar-key">' + columns.map(function (c) {
      var n = counts[c.id] || 0;
      return '<li class="' + (n ? "" : "is-zero") + '"><span class="dot" style="--dot: var(--col-' +
        esc(c.id) + ')"></span><b>' + n + "</b> " + esc(c.title) + "</li>";
    }).join("") + "</ul>";
  }

  var DONE_COL = columns.length ? columns[columns.length - 1].id : "";
  var REVIEW_IDX = (function () {
    var i = colIndex("in-review");
    return i >= 0 ? i : Math.max(0, columns.length - 2);
  })();

  function rollupHtml(id) {
    var isBoard = id === BOARD_NODE;
    var ids = isBoard ? cards.map(function (c) { return c.id; }) : subtree(id);
    var direct = isBoard ? roots.length : kids(id).length;
    var t = tally(ids);

    if (!ids.length) {
      /* a leaf: the only progress it carries is its own criteria */
      var self = tally([id]);
      var pct = self.crit.total ? Math.round((self.crit.done / self.crit.total) * 100) : 0;
      return '<div class="rollup">' +
        '<div class="rollup-top">' +
        '<p class="rollup-headline">Leaf. Nothing decomposes from here, so its progress is its own acceptance criteria: <b>' +
        self.crit.done + "</b> of <b>" + self.crit.total + "</b> met.</p>" +
        '<span class="rollup-sub">' + pct + "% · depth " + (depthOf[id] || 0) + "</span></div>" +
        '<div class="bar"><span class="bar-seg" style="flex:' + Math.max(self.crit.done, 0) +
        ';background:var(--foreground)"></span><span class="bar-seg" style="flex:' +
        Math.max(self.crit.total - self.crit.done, 0) + ';background:var(--muted)"></span></div>' +
        "</div>";
    }

    var reached = ids.filter(function (x) { return colIndex(statusOf(x)) >= REVIEW_IDX; }).length;
    var released = t.counts[DONE_COL] || 0;
    var divergent = ids.filter(diverges).length;

    return '<div class="rollup">' +
      '<div class="rollup-top">' +
      '<p class="rollup-headline"><b>' + released + "</b> of <b>" + ids.length +
      "</b> cards below this node are " + esc(colTitle(DONE_COL)) + ", <b>" + reached +
      "</b> have reached " + esc(colTitle(columns[REVIEW_IDX] ? columns[REVIEW_IDX].id : "")) + ".</p>" +
      '<span class="rollup-sub">' + direct + " direct · " + ids.length + " in subtree" +
      (divergent ? " · " + divergent + " off-column" : "") + "</span>" +
      "</div>" +
      barHtml(t.counts, ids.length) +
      keyHtml(t.counts) +
      '<p class="crit-line">Acceptance criteria across the subtree: ' + t.crit.done + " / " +
      t.crit.total + " met</p>" +
      "</div>";
  }

  /* ------------------------------------------------------------------ *
   * detail — the children table
   * ------------------------------------------------------------------ */

  function moveSelect(id) {
    var card = byId[id];
    var st = statusOf(id);
    return '<div class="movebox' + (isStaged(id) ? " is-staged" : "") + '">' +
      '<span class="mlabel">' + (isStaged(id) ? "staged" : "move") + "</span>" +
      '<select data-move="' + esc(id) + '" aria-label="Move ' + esc(card.title) + ' to another column">' +
      columns.map(function (c) {
        return '<option value="' + esc(c.id) + '"' + (c.id === st ? " selected" : "") + ">" +
          esc(c.title) + "</option>";
      }).join("") + "</select></div>";
  }

  function statusCell(id) {
    var st = statusOf(id);
    var card = byId[id];
    var p = parentOf[id];
    var out = '<div class="statuscell"><span class="name"><span class="dot" style="--dot: var(--col-' +
      esc(st) + ')"></span>' + esc(colTitle(st)) + "</span>";
    if (isStaged(id)) out += '<span class="was">was ' + esc(colTitle(card.status)) + "</span>";
    if (p && diverges(id)) {
      out += '<span class="diverge" title="This child sits in a different column from its parent">&ne; ' +
        esc(colTitle(statusOf(p))) + "</span>";
    }
    return out + "</div>";
  }

  function metaCell(value) {
    if (!value) return '<td class="cell-mono cell-blank"></td>';
    return '<td class="cell-mono">' + esc(value) + "</td>";
  }

  function childrenTable(parentId, childIds, label) {
    var show = { type: false, milestone: false, size: false, owner: false };
    childIds.forEach(function (id) {
      var c = byId[id];
      if (c.type) show.type = true;
      if (c.milestone) show.milestone = true;
      if (c.size) show.size = true;
      if (c.assignee && c.assignee.length) show.owner = true;
    });
    var anyKids = childIds.some(hasKids);

    var head = "<tr><th>Card</th><th>Status</th>" +
      (show.type ? "<th>Type</th>" : "") +
      (show.milestone ? "<th>Milestone</th>" : "") +
      (show.size ? "<th>Size</th>" : "") +
      (show.owner ? "<th>Owner</th>" : "") +
      (anyKids ? "<th>Below</th>" : "") +
      "<th>Move to</th></tr>";

    var body = childIds.map(function (id) {
      var c = byId[id];
      var sub = [];
      if (c.priority) sub.push('<span class="prio">' + esc(c.priority) + " priority</span>");
      (c.tags || []).slice(0, 3).forEach(function (tg) {
        sub.push('<span class="tag">' + esc(tg) + "</span>");
      });
      if ((c.tags || []).length > 3) sub.push('<span class="tag">+' + ((c.tags.length) - 3) + "</span>");

      var below = "";
      if (anyKids) {
        if (hasKids(id)) {
          var ids = subtree(id);
          var t = tally(ids);
          below = '<td><div class="kid-progress"><span>' + ids.length + " card" +
            (ids.length === 1 ? "" : "s") + "</span>" +
            '<span class="minibar">' + columns.map(function (col) {
              var n = t.counts[col.id] || 0;
              return n ? '<span class="bar-seg" style="flex:' + n + ';background:var(--col-' +
                esc(col.id) + ')"></span>' : "";
            }).join("") + "</span></div></td>";
        } else {
          below = '<td class="cell-mono cell-blank"></td>';
        }
      }

      return '<tr class="' + (isStaged(id) ? "is-staged" : "") + '" data-row="' + esc(id) + '">' +
        '<td><button type="button" class="kid-title" data-open="' + esc(id) + '">' +
        '<span class="t">' + markQuery(c.title) + "</span></button>" +
        '<span class="kid-id">' + esc(id) + "</span>" +
        (sub.length ? '<div class="kid-sub tags">' + sub.join("") + "</div>" : "") + "</td>" +
        "<td>" + statusCell(id) + "</td>" +
        (show.type ? metaCell(c.type) : "") +
        (show.milestone ? metaCell(c.milestone) : "") +
        (show.size ? metaCell(c.size) : "") +
        (show.owner ? metaCell((c.assignee || []).join(", ")) : "") +
        below +
        "<td>" + moveSelect(id) + "</td>" +
        "</tr>";
    }).join("");

    var divergent = childIds.filter(diverges).length;
    var note = childIds.length + " direct child" + (childIds.length === 1 ? "" : "ren") +
      (divergent ? ' · <span class="warn">' + divergent + " in another column than this parent</span>" : "");

    return '<section class="sec"><div class="sec-head"><span class="label">' +
      esc(label || "Decomposes into") + "</span>" +
      '<span class="sec-note">' + note + "</span></div>" +
      '<div class="tablewrap"><table class="kids"><thead>' + head + "</thead><tbody>" +
      body + "</tbody></table></div></section>";
  }

  /* ------------------------------------------------------------------ *
   * detail — the card itself
   * ------------------------------------------------------------------ */

  function sectionHtml(label, note, inner) {
    return '<section class="sec"><div class="sec-head"><span class="label">' + esc(label) + "</span>" +
      (note ? '<span class="sec-note">' + note + "</span>" : "") + "</div>" + inner + "</section>";
  }

  function criteriaHtml(card) {
    var list = card.criteria || [];
    if (!list.length) return "";
    var done = list.filter(function (k) { return k.done; }).length;
    return sectionHtml("Acceptance criteria", done + " / " + list.length + " met",
      '<ul class="crit">' + list.map(function (k) {
        return '<li class="' + (k.done ? "done" : "") + '"><span class="box"></span><span>' +
          inlineMd(k.text) + "</span></li>";
      }).join("") + "</ul>");
  }

  function artifactsHtml(card) {
    var list = card.artifacts || [];
    if (!list.length) return "";
    return sectionHtml("Artifacts", String(list.length),
      '<ul class="arts">' + list.map(function (a) {
        var kind = Object.keys(a).filter(function (k) { return k !== "label"; })[0] || "file";
        var target = a[kind];
        if (kind === "pr") target = "#" + target;
        return "<li>" + '<span class="art-kind">' + esc(kind) + "</span>" +
          '<span class="art-target">' + esc(target) + "</span>" +
          (a.label ? '<span class="art-label">' + esc(a.label) + "</span>" : "") + "</li>";
      }).join("") + "</ul>");
  }

  function commentsHtml(card) {
    var list = card.comments || [];
    if (!list.length) return "";
    return sectionHtml("Comments", String(list.length),
      '<ul class="trail">' + list.map(function (c) {
        return '<li><span class="when">' + esc(c.date) + '</span><span class="who">' +
          esc(c.actor) + '</span><span class="what">' + inlineMd(c.text) + "</span></li>";
      }).join("") + "</ul>");
  }

  function trailHtml(card) {
    var list = card.trail || [];
    if (!list.length) return "";
    return sectionHtml("Trail", String(list.length),
      '<ul class="trail">' + list.map(function (t) {
        return '<li><span class="when">' + esc(t.date) + '</span><span class="who">' +
          esc(t.actor) + '</span><span class="what">' + inlineMd(t.note || "") +
          (t.ref ? ' <code class="inline-code">' + esc(t.ref) + "</code>" : "") + "</span></li>";
      }).join("") + "</ul>");
  }

  function crumbsHtml(id) {
    var parts = ['<button type="button" data-open="' + BOARD_NODE + '">' +
      esc(BOARD.title || "Board") + "</button>"];
    if (id !== BOARD_NODE) {
      ancestors(id).reverse().forEach(function (a) {
        parts.push('<span class="sep">/</span><button type="button" data-open="' + esc(a) + '">' +
          esc(byId[a].title) + "</button>");
      });
      parts.push('<span class="sep">/</span><span class="here">' + esc(byId[id].title) + "</span>");
    }
    return '<nav class="crumbs" aria-label="Path">' + parts.join("") + "</nav>";
  }

  function metaLine(card) {
    var st = statusOf(card.id);
    var bits = [];
    if (card.type) bits.push(esc(card.type));
    if (card.milestone) bits.push(esc(card.milestone));
    if (card.size) bits.push(esc(card.size));
    if (card.priority) bits.push(esc(card.priority) + " priority");
    if ((card.assignee || []).length) bits.push(esc(card.assignee.join(", ")));
    if (card.created) bits.push(esc(card.created));
    var head = '<span class="status"><span class="dot" style="--dot: var(--col-' + esc(st) +
      ')"></span>' + esc(colTitle(st)) + "</span>";
    return '<p class="dmeta">' + head + bits.map(function (b) {
      return '<span class="sep">·</span>' + b;
    }).join("") + "</p>";
  }

  function renderDetail() {
    var id = state.selected;
    if (id !== BOARD_NODE && !byId[id]) id = state.selected = BOARD_NODE;
    var host = el("#detail");

    if (id === BOARD_NODE) {
      var nested = cards.length - roots.length;
      var maxDepth = Math.max.apply(null, cards.map(function (c) { return depthOf[c.id] || 0; }));
      var leaves = roots.filter(function (r) { return !hasKids(r); }).length;
      host.innerHTML = '<div class="detail-inner">' + crumbsHtml(BOARD_NODE) +
        '<header class="dhead"><div class="dhead-main">' +
        '<h2 class="dtitle">' + esc(BOARD.title || "Board") + "</h2>" +
        '<p class="dmeta"><span class="status">' + cards.length + " cards</span>" +
        '<span class="sep">·</span>' + roots.length + " top level" +
        '<span class="sep">·</span>' + nested + " nested" +
        '<span class="sep">·</span>' + (maxDepth + 1) + " levels deep</p>" +
        '</div><div class="dhead-side"><span class="idchip">select a row in the rail</span></div></header>' +
        rollupHtml(BOARD_NODE) +
        childrenTable(BOARD_NODE, roots, "Top level") +
        '<p class="empty-note">' + leaves + " of the " + roots.length +
        " top-level cards decompose into nothing. They are ordinary cards, not empty parents, so " +
        "selecting one shows the card and no table.</p>" +
        "</div>";
      return;
    }

    var card = byId[id];
    var childIds = kids(id);
    var html = '<div class="detail-inner">' + crumbsHtml(id) +
      '<header class="dhead"><div class="dhead-main">' +
      '<h2 class="dtitle">' + esc(card.title) + "</h2>" + metaLine(card) +
      '</div><div class="dhead-side"><span class="idchip">' + esc(card.id) + "</span>" +
      moveSelect(card.id) + "</div></header>";

    if (brokenCycle[id]) {
      html += '<p class="empty-note">Its <code class="inline-code">parent: ' + esc(card.parent) +
        "</code> closes a loop, so this prototype treats the card as a root rather than hanging.</p>";
    }

    html += rollupHtml(id);
    if (childIds.length) html += childrenTable(id, childIds, "Decomposes into");
    if (card.description) html += sectionHtml("Description", "", '<div class="prose">' + renderMd(card.description) + "</div>");
    html += criteriaHtml(card);
    html += artifactsHtml(card);
    html += commentsHtml(card);
    html += trailHtml(card);

    host.innerHTML = html + "</div>";
  }

  /* ------------------------------------------------------------------ *
   * staged moves
   * ------------------------------------------------------------------ */

  function renderMoves() {
    var n = state.movesOrder.length;
    var pill = el("#moves-count");
    pill.textContent = n;
    pill.classList.toggle("is-live", n > 0);
    el("#moves-out").value = n ? moveCommands() : "# no moves staged yet";
    el("#moves-list").innerHTML = state.movesOrder.map(function (id) {
      return '<li><button type="button" class="move-chip" data-unstage="' + esc(id) +
        '" title="Discard this staged move">' + esc(id) + " &rarr; " + esc(colTitle(state.moves[id])) +
        '<span class="x">&times;</span></button></li>';
    }).join("");
  }

  /* ------------------------------------------------------------------ *
   * render + navigation
   * ------------------------------------------------------------------ */

  function render() {
    computeFilter();
    renderRail();
    renderSearchNote();
    renderDetail();
    renderMoves();
  }

  function rowEl(id) {
    return document.querySelector('#tree [data-id="' + cssId(id) + '"]');
  }

  function scrollRowIntoView(row) {
    var tree = el("#tree");
    var r = row.getBoundingClientRect();
    var t = tree.getBoundingClientRect();
    if (r.top < t.top) tree.scrollTop += r.top - t.top - 4;
    else if (r.bottom > t.bottom) tree.scrollTop += r.bottom - t.bottom + 4;
  }

  function focusRow(id, refocus) {
    var row = rowEl(id);
    if (!row) return;
    if (refocus) {
      try { row.focus({ preventScroll: true }); } catch (e) { row.focus(); }
    }
    scrollRowIntoView(row);
  }

  function select(id, refocus) {
    state.selected = id;
    state.focusId = id;
    computeFilter();
    renderRail();
    renderSearchNote();
    renderDetail();
    focusRow(id, refocus);
    /* the detail is a page, not a pane: start it at its heading */
    if (window.scrollY > 0) window.scrollTo(0, 0);
  }

  function inTree() {
    var a = document.activeElement;
    return !!(a && a.closest && a.closest("#tree"));
  }

  function toggle(id, force) {
    if (id !== BOARD_NODE && !hasKids(id)) return;
    /* read focus before the rail is rebuilt: replacing innerHTML sends focus
       back to the body, so asking afterwards always answers "no" */
    var hadFocus = inTree();
    var open = id === BOARD_NODE ? !state.collapsed[id] : isOpen(id);
    var next = typeof force === "boolean" ? force : !open;
    if (next) delete state.collapsed[id];
    else state.collapsed[id] = true;
    renderRail();
    renderSearchNote();
    focusRow(state.focusId, hadFocus);
  }

  function step(delta) {
    var i = order.indexOf(state.focusId);
    if (i < 0) i = 0;
    var next = order[Math.min(order.length - 1, Math.max(0, i + delta))];
    if (next) select(next, true);
  }

  /* ------------------------------------------------------------------ *
   * events
   * ------------------------------------------------------------------ */

  function wire() {
    var tree = el("#tree");

    tree.addEventListener("click", function (e) {
      var row = e.target.closest(".row");
      if (!row) return;
      var id = row.getAttribute("data-id");
      if (e.target.closest('[data-act="twisty"]')) {
        state.focusId = id;
        toggle(id);
        return;
      }
      select(id, true);
    });

    tree.addEventListener("keydown", function (e) {
      var row = e.target.closest(".row");
      if (!row) return;
      var id = row.getAttribute("data-id");
      var kidIds = id === BOARD_NODE ? roots.filter(isVisible) : kids(id).filter(isVisible);
      var open = id === BOARD_NODE ? !state.collapsed[id] : isOpen(id);

      switch (e.key) {
        case "ArrowDown": e.preventDefault(); step(1); break;
        case "ArrowUp": e.preventDefault(); step(-1); break;
        case "Home": e.preventDefault(); if (order.length) select(order[0], true); break;
        case "End": e.preventDefault(); if (order.length) select(order[order.length - 1], true); break;
        case "ArrowRight":
          e.preventDefault();
          if (kidIds.length && !open) toggle(id, true);
          else if (kidIds.length && open) select(kidIds[0], true);
          break;
        case "ArrowLeft":
          e.preventDefault();
          if (kidIds.length && open) toggle(id, false);
          else {
            var p = id === BOARD_NODE ? null : (parentOf[id] || BOARD_NODE);
            if (p) select(p, true);
          }
          break;
        case "Enter":
        case " ":
          e.preventDefault();
          select(id, true);
          break;
        case "*":
          e.preventDefault();
          state.collapsed = {};
          render();
          focusRow(state.focusId, true);
          break;
        default: break;
      }
    });

    el("#detail").addEventListener("click", function (e) {
      var open = e.target.closest("[data-open]");
      if (open) select(open.getAttribute("data-open"), false);
    });

    document.addEventListener("change", function (e) {
      var sel = e.target.closest && e.target.closest("select[data-move]");
      if (!sel) return;
      var id = sel.getAttribute("data-move");
      setMove(id, sel.value);
      render();
      var again = document.querySelector('select[data-move="' + cssId(id) + '"]');
      if (again) { try { again.focus({ preventScroll: true }); } catch (err) { again.focus(); } }
    });

    el("#query").addEventListener("input", function (e) {
      state.query = e.target.value.trim().toLowerCase();
      render();
    });
    el("#query").addEventListener("keydown", function (e) {
      if (e.key === "Escape") { e.target.value = ""; state.query = ""; render(); }
    });

    el("#expand-all").addEventListener("click", function () {
      state.collapsed = {};
      render();
    });

    el("#collapse-all").addEventListener("click", function () {
      state.collapsed = {};
      cards.forEach(function (c) { if (hasKids(c.id)) state.collapsed[c.id] = true; });
      render();
    });

    var panel = el("#moves-panel");
    el("#moves-toggle").addEventListener("click", function (e) {
      var open = panel.hidden;
      panel.hidden = !open;
      e.currentTarget.setAttribute("aria-expanded", String(open));
    });

    el("#moves-clear").addEventListener("click", function () {
      state.moves = {};
      state.movesOrder = [];
      render();
    });

    el("#moves-copy").addEventListener("click", function (e) {
      var out = el("#moves-out");
      var btn = e.currentTarget;
      var done = function () {
        btn.textContent = "Copied";
        setTimeout(function () { btn.textContent = "Copy commands"; }, 1400);
      };
      out.select();
      var ok = false;
      try { ok = document.execCommand("copy"); } catch (err) { ok = false; }
      if (ok) { done(); return; }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(out.value).then(done, function () {
          btn.textContent = "Select and copy";
          setTimeout(function () { btn.textContent = "Copy commands"; }, 1800);
        });
      }
    });

    document.addEventListener("click", function (e) {
      var chip = e.target.closest && e.target.closest("[data-unstage]");
      if (!chip) return;
      setMove(chip.getAttribute("data-unstage"), null);
      render();
    });

    var themeBtn = el("#theme-toggle");
    var prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
    var dark = prefersDark;
    function paintTheme() {
      document.documentElement.setAttribute("data-theme", dark ? "dark" : "light");
      themeBtn.textContent = dark ? "Light" : "Dark";
      themeBtn.setAttribute("aria-pressed", String(dark));
    }
    themeBtn.textContent = dark ? "Light" : "Dark";
    themeBtn.setAttribute("aria-pressed", String(dark));
    themeBtn.addEventListener("click", function () { dark = !dark; paintTheme(); });
  }

  /* ------------------------------------------------------------------ *
   * boot
   * ------------------------------------------------------------------ */

  function boot() {
    el("#board-title").textContent = BOARD.title || "Board";
    document.title = "Tree rail and detail — " + (BOARD.title || "Board");
    renderLegend();
    render();
    wire();
    window.__tree = { state: state, select: select, render: render, setMove: setMove };
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
