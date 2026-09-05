/* Document outline — the board set as one specification.
   Vanilla JS, no build step. window.BOARD comes from board-data.js. */

(function () {
  "use strict";

  var BOARD = window.BOARD || { title: "Board", columns: [] };
  var COLUMNS = BOARD.columns || [];
  var LAST = COLUMNS.length - 1;

  var COLPOS = {};
  COLUMNS.forEach(function (c, i) { COLPOS[c.id] = i; });

  var CARDS = [];
  var BY = {};
  COLUMNS.forEach(function (col) {
    (col.cards || []).forEach(function (card) { CARDS.push(card); BY[card.id] = card; });
  });

  /* ---- the forest, built so no walk can ever loop -------------------------
     `parent:` is validated at build time only against "exists" and "not self",
     so a -> b -> a is legal data. Every ancestor walk below is bounded and
     carries a seen-set; a card caught in a loop is lifted to the top level and
     footnoted rather than dropped or spun on. */

  var childrenOf = {};
  var detached = {};          /* id -> reason: parent missing, or a loop */
  var roots = [];

  CARDS.forEach(function (c) { childrenOf[c.id] = []; });

  function parentOf(card) {
    if (!card || !card.parent) return null;
    var p = BY[card.parent];
    if (!p || p.id === card.id) return null;
    return p;
  }

  CARDS.forEach(function (c) {
    var p = parentOf(c);
    if (!p) {
      if (c.parent === c.id) detached[c.id] = "names itself as its parent";
      else if (c.parent) detached[c.id] = "no card with the id “" + c.parent + "”";
      roots.push(c);
      return;
    }
    var seen = Object.create(null);
    seen[c.id] = true;
    var cur = p;
    var guard = 0;
    var looped = false;
    while (cur) {
      if (seen[cur.id] || guard++ > CARDS.length + 1) { looped = true; break; }
      seen[cur.id] = true;
      cur = parentOf(cur);
    }
    if (looped) {
      detached[c.id] = "parent chain loops";
      roots.push(c);
      return;
    }
    childrenOf[p.id].push(c);
  });

  /* descendants, memoised, still guarded */
  var descCache = {};
  function descendants(id) {
    if (descCache[id]) return descCache[id];
    var out = [];
    var seen = Object.create(null);
    var stack = (childrenOf[id] || []).slice();
    while (stack.length) {
      var n = stack.shift();
      if (!n || seen[n.id]) continue;
      seen[n.id] = true;
      out.push(n);
      (childrenOf[n.id] || []).forEach(function (k) { if (!seen[k.id]) stack.push(k); });
    }
    descCache[id] = out;
    return out;
  }

  /* ---- state ----------------------------------------------------------- */

  var state = {
    view: "outline",
    summaries: "head",
    q: "",
    cols: {},
    collapsed: {},
    opened: {},
    staged: {},
    focus: null
  };
  COLUMNS.forEach(function (c) { state.cols[c.id] = true; });

  /* the column a card is in *right now*, staged moves included, so the
     measure, the chapters and the WIP counts all answer the pending edit */
  function colOf(card) {
    var s = state.staged[card.id];
    if (s && COLPOS[s] !== undefined) return s;
    return COLPOS[card.status] !== undefined ? card.status : COLUMNS[0] && COLUMNS[0].id;
  }
  function colTitle(id) {
    var i = COLPOS[id];
    return i === undefined ? id : COLUMNS[i].title;
  }
  function isStaged(card) {
    var s = state.staged[card.id];
    return !!s && s !== card.status;
  }

  /* ---- small DOM helpers ----------------------------------------------- */

  function el(tag, attrs) {
    var n = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function (k) {
        var v = attrs[k];
        if (v === null || v === undefined || v === false) return;
        if (k === "class") n.className = v;
        else if (k === "text") n.textContent = v;
        else n.setAttribute(k, v === true ? "" : String(v));
      });
    }
    for (var i = 2; i < arguments.length; i++) {
      var c = arguments[i];
      if (c === null || c === undefined || c === false) continue;
      n.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
    }
    return n;
  }

  function marked(text, q) {
    var frag = document.createDocumentFragment();
    if (!q) { frag.appendChild(document.createTextNode(text)); return frag; }
    var hay = text.toLowerCase();
    var needle = q.toLowerCase();
    var at = 0;
    var i = hay.indexOf(needle);
    while (i !== -1) {
      if (i > at) frag.appendChild(document.createTextNode(text.slice(at, i)));
      frag.appendChild(el("mark", { text: text.slice(i, i + needle.length) }));
      at = i + needle.length;
      i = hay.indexOf(needle, at);
    }
    if (at < text.length) frag.appendChild(document.createTextNode(text.slice(at)));
    return frag;
  }

  window.__DOC_OUTLINE__ = {
    BOARD: BOARD, CARDS: CARDS, BY: BY, roots: roots, childrenOf: childrenOf,
    detached: detached, state: state, descendants: descendants
  };

  /* ---- what the query keeps -------------------------------------------- */

  function effParent(card) {
    if (detached[card.id]) return null;
    return parentOf(card);
  }

  function inScope(card) { return !!state.cols[colOf(card)]; }

  function hitsQuery(card) {
    if (!state.q) return true;
    var needle = state.q.toLowerCase();
    return card.title.toLowerCase().indexOf(needle) >= 0 ||
           card.id.toLowerCase().indexOf(needle) >= 0;
  }

  function matches(card) { return inScope(card) && hitsQuery(card); }

  function liveAnywhere(card) {
    if (matches(card)) return true;
    var d = descendants(card.id);
    for (var i = 0; i < d.length; i++) if (matches(d[i])) return true;
    return false;
  }

  function subtreeStats(card) {
    var d = descendants(card.id);
    var counts = COLUMNS.map(function () { return 0; });
    d.forEach(function (k) {
      var i = COLPOS[colOf(k)];
      if (i !== undefined) counts[i]++;
    });
    return { counts: counts, total: d.length, done: LAST >= 0 ? counts[LAST] : 0 };
  }

  /* ---- the plan: what gets set, and in what order ----------------------- */

  var numOf = {};        /* id -> "2.3.1" for the current reading */

  function planNode(card, guard) {
    if (guard > 24) return { type: "node", card: card, kids: [] };
    return {
      type: "node",
      card: card,
      kids: (childrenOf[card.id] || []).map(function (k) { return planNode(k, guard + 1); })
    };
  }

  function buildOutlinePlan() {
    return [{ col: null, entries: roots.map(function (c) { return planNode(c, 0); }) }];
  }

  function buildChaptersPlan() {
    return COLUMNS.map(function (col) {
      var local = CARDS.filter(function (c) { return colOf(c) === col.id; });
      var has = Object.create(null);
      local.forEach(function (c) { has[c.id] = true; });

      function localNode(card, guard) {
        var kids = [];
        if (guard <= 24) {
          (childrenOf[card.id] || []).forEach(function (k) {
            kids.push(has[k.id] ? localNode(k, guard + 1) : { type: "stub", card: k });
          });
        }
        return { type: "node", card: card, kids: kids };
      }

      var entries = local
        .filter(function (c) { var p = effParent(c); return !p || !has[p.id]; })
        .map(function (c) { return localNode(c, 0); });

      return { col: col, entries: entries };
    });
  }

  /* Tree filtering, decided: a match never leaves its place in the document.
     A line is set if it matched, if it sits under a match (a matched section
     keeps its plan intact), or if it is holding up a match from below. The
     third case is context, and reads in the margin voice. */
  function markKeep(entry, underQuery) {
    if (entry.type === "stub") {
      entry.keep = inScope(entry.card) && (!!underQuery || liveAnywhere(entry.card));
      return entry.keep;
    }
    var card = entry.card;
    var hit = hitsQuery(card);
    var kept = false;
    entry.kids.forEach(function (k) { if (markKeep(k, underQuery || hit)) kept = true; });
    entry.match = hit && inScope(card);
    entry.keep = entry.match || kept || (!!underQuery && inScope(card));
    entry.ctx = (!hit && !underQuery) || !inScope(card);
    return entry.keep;
  }

  function number(entries, prefix) {
    var n = 0;
    entries.forEach(function (e) {
      if (!e.keep || e.type === "stub") return;
      n++;
      var num = prefix ? prefix + "." + n : String(n);
      e.num = num;
      numOf[e.card.id] = num;
      number(e.kids, num);
    });
  }

  function buildPlan() {
    numOf = {};
    var chapters = state.view === "chapters" ? buildChaptersPlan() : buildOutlinePlan();
    chapters.forEach(function (ch, i) {
      ch.entries.forEach(function (e) { markKeep(e, false); });
      ch.visible = !ch.col || state.cols[ch.col.id];
      ch.index = i + 1;
      number(ch.entries, state.view === "chapters" ? String(ch.index) : "");
    });
    return chapters;
  }

  /* ---- setting a line --------------------------------------------------- */

  var doc = document.getElementById("doc");

  function statusMark(card) {
    var wrap = el("span", { class: "status" });
    if (isStaged(card)) {
      wrap.appendChild(el("s", { text: colTitle(card.status) }));
      wrap.appendChild(el("span", { class: "arrow", text: "→" }));
      wrap.appendChild(el("span", { class: "to", text: colTitle(state.staged[card.id]) }));
      wrap.appendChild(el("a", {
        class: "fn-mark", href: "#fn-staged", title: "staged move, not written to the repository"
      }, "Δ"));
    } else {
      wrap.appendChild(document.createTextNode(colTitle(colOf(card))));
    }
    var p = effParent(card);
    if (p && colOf(p) === colOf(card) && !isStaged(card)) wrap.setAttribute("data-echo", "true");
    if (p && colOf(p) !== colOf(card)) {
      wrap.appendChild(el("a", {
        class: "fn-mark", href: "#fn-diverge",
        title: "parent “" + p.title + "” is in " + colTitle(colOf(p))
      }, "†"));
    }
    if (detached[card.id]) {
      wrap.appendChild(el("a", {
        class: "fn-mark", href: "#fn-orphan", title: detached[card.id]
      }, "‡"));
    }
    return wrap;
  }

  function metaLine(card) {
    var bits = [];
    if (card.priority === "high") bits.push(el("span", { class: "hi", text: "high" }));
    if (card.type) bits.push(el("span", { text: card.type }));
    if (card.milestone) bits.push(el("span", { title: "milestone", text: "v" + card.milestone }));
    if (card.size) bits.push(el("span", { title: "size", text: card.size }));
    (card.assignee || []).forEach(function (a) {
      bits.push(el("span", { class: "who", text: "@" + a }));
    });
    var crit = card.criteria || [];
    if (crit.length) {
      var done = crit.filter(function (c) { return c.done; }).length;
      var c = el("span", { class: "crit", title: "acceptance criteria met" });
      c.appendChild(el("b", { text: String(done) }));
      c.appendChild(document.createTextNode("/" + crit.length));
      bits.push(c);
    }
    if (state.q && card.id.toLowerCase().indexOf(state.q.toLowerCase()) >= 0) {
      var idm = el("span", { class: "idm" });
      idm.appendChild(marked(card.id, state.q));
      bits.push(idm);
    }
    if (!bits.length) return null;
    var p = el("p", { class: "meta sub" });
    bits.forEach(function (b, i) {
      if (i) p.appendChild(el("span", { class: "sep", text: "·" }));
      p.appendChild(b);
    });
    return p;
  }

  function measure(card) {
    var s = subtreeStats(card);
    if (!s.total) return null;
    var bar = el("div", { class: "bar", role: "img",
      "aria-label": s.total + (s.total === 1 ? " sub-task, " : " sub-tasks, ") + s.done + " in " + colTitle(COLUMNS[LAST].id) });
    COLUMNS.forEach(function (col, i) {
      if (!s.counts[i]) return;
      bar.appendChild(el("span", {
        "data-i": i,
        style: "flex: " + s.counts[i] + " 0 0%",
        title: s.counts[i] + " in " + col.title
      }));
    });
    var read = el("span", { class: "read" });
    read.appendChild(el("b", { text: String(s.total) }));
    read.appendChild(document.createTextNode(s.total === 1 ? " sub-task · " : " sub-tasks · "));
    read.appendChild(el("b", { text: String(s.done) }));
    read.appendChild(document.createTextNode(" done"));
    return el("div", { class: "measure sub" }, bar, read);
  }

  function bodyOf(card) {
    var b = el("div", { class: "body sub" });
    if (card.description) {
      b.appendChild(el("h3", { text: "Description" }));
      b.appendChild(el("p", {}, marked(card.description, state.q)));
    }
    var crit = card.criteria || [];
    if (crit.length) {
      b.appendChild(el("h3", { text: "Acceptance criteria" }));
      var ul = el("ul");
      crit.forEach(function (c) {
        ul.appendChild(el("li", { "data-done": c.done ? "true" : "false", "data-mark": c.done ? "[x]" : "[ ]" }, c.text));
      });
      b.appendChild(ul);
    }
    var arts = card.artifacts || [];
    if (arts.length) {
      b.appendChild(el("h3", { text: "Artifacts" }));
      var ua = el("ul");
      arts.forEach(function (a) {
        Object.keys(a).forEach(function (k) {
          if (k === "label" || k === "href") return;
          var li = el("li", { "data-mark": "·" });
          li.appendChild(el("code", { text: k + " " + a[k] }));
          if (a.label) li.appendChild(document.createTextNode("  " + a.label));
          ua.appendChild(li);
        });
      });
      b.appendChild(ua);
    }
    if ((card.comments || []).length) {
      b.appendChild(el("h3", { text: "Comments" }));
      var uc = el("ul", { class: "cmts" });
      card.comments.forEach(function (c) {
        uc.appendChild(el("li", { "data-mark": "·" }, el("b", { text: c.actor + " " + c.date }), c.text));
      });
      b.appendChild(uc);
    }
    if ((card.trail || []).length) {
      b.appendChild(el("h3", { text: "Trail" }));
      var ut = el("ul", { class: "trail" });
      card.trail.forEach(function (t) {
        ut.appendChild(el("li", { "data-mark": "·" }, el("b", { text: t.date }), t.note || t.ref || ""));
      });
      b.appendChild(ut);
    }
    return b;
  }

  function renderStub(entry, depth) {
    var card = entry.card;
    var wrap = el("div", { class: "stub-node", role: "none", "data-depth": depth });
    wrap.appendChild(el("span", { class: "sec", text: numOf[card.id] || "" }));
    var s = el("span", { class: "stub" });
    s.appendChild(document.createTextNode(card.title));
    s.appendChild(el("span", { class: "xref", text: "filed under " + colTitle(colOf(card)) }));
    if (numOf[card.id]) {
      s.appendChild(el("button", {
        type: "button", class: "goto", tabindex: "-1", "data-goto": card.id
      }, "go to §" + numOf[card.id]));
    }
    wrap.appendChild(s);
    return wrap;
  }

  function renderNode(entry, depth, xrefParent) {
    var card = entry.card;
    var kids = entry.kids.filter(function (k) { return k.keep; });
    var hasKids = kids.length > 0;
    var expanded = state.q ? true : !state.collapsed[card.id];
    if (!hasKids) expanded = true;

    var node = el("div", {
      class: "node",
      role: "treeitem",
      tabindex: "-1",
      "data-id": card.id,
      "data-depth": depth,
      "data-kind": hasKids ? "head" : "leaf",
      "data-ctx": entry.ctx ? "true" : "false",
      "data-staged": isStaged(card) ? "true" : "false",
      "aria-level": depth + 1,
      "aria-label": card.title + ", " + colTitle(colOf(card)) +
        (hasKids ? ", " + kids.length + (kids.length === 1 ? " sub-task" : " sub-tasks") : "")
    });
    if (hasKids) node.setAttribute("aria-expanded", expanded ? "true" : "false");

    var disc = el("span", { class: "disc" });
    if (hasKids) {
      disc.appendChild(el("button", {
        type: "button", class: "caret", tabindex: "-1",
        "aria-hidden": "true", "data-toggle": card.id,
        title: expanded ? "collapse" : "expand"
      }));
    }
    node.appendChild(disc);
    node.appendChild(el("span", { class: "sec", text: entry.num || "" }));

    var line = el("div", { class: "line" });
    var ttl = el("button", { type: "button", class: "ttl", tabindex: "-1", "data-open": card.id });
    ttl.appendChild(marked(card.title, state.q));
    line.appendChild(ttl);
    line.appendChild(el("span", { class: "leader", "aria-hidden": "true" }));
    var marks = el("span", { class: "marks" });
    marks.appendChild(statusMark(card));
    marks.appendChild(el("button", {
      type: "button", class: "movebtn", tabindex: "-1", "data-move": card.id,
      "aria-label": "Move " + card.title + " to another column"
    }, "Move"));
    line.appendChild(marks);
    node.appendChild(line);

    if (xrefParent) {
      var x = el("p", { class: "xref sub" });
      x.appendChild(document.createTextNode("continues §" + (numOf[xrefParent.id] || "?") + " · "));
      x.appendChild(el("b", { text: xrefParent.title }));
      x.appendChild(document.createTextNode(" · " + colTitle(colOf(xrefParent))));
      node.appendChild(x);
    }

    if (!entry.ctx) {
      var m = metaLine(card);
      if (m) node.appendChild(m);
      var mm = measure(card);
      if (mm) node.appendChild(mm);
      var wantSummary = state.summaries === "all" || (state.summaries === "head" && hasKids);
      if (state.opened[card.id]) {
        node.appendChild(bodyOf(card));
      } else if (wantSummary && card.description) {
        node.appendChild(el("p", { class: "summary sub clamp" }, marked(card.description, state.q)));
      }
    }

    if (hasKids) {
      var group = el("div", { class: "kids", role: "group" });
      kids.forEach(function (k) {
        group.appendChild(k.type === "stub" ? renderStub(k, depth + 1) : renderNode(k, depth + 1, null));
      });
      node.appendChild(group);
    }
    return node;
  }

  function render() {
    var chapters = buildPlan();
    doc.textContent = "";
    doc.setAttribute("data-view", state.view);

    if (state.view === "chapters") {
      doc.setAttribute("role", "presentation");
      doc.removeAttribute("aria-multiselectable");
      chapters.forEach(function (ch) {
        if (!ch.visible) return;
        var sec = el("section", { class: "chapter" });
        var head = el("div", { class: "chapter-head" });
        head.appendChild(el("span", { class: "cnum", text: "§" + ch.index }));
        head.appendChild(el("h2", { text: ch.col.title }));
        var n = CARDS.filter(function (c) { return colOf(c) === ch.col.id; }).length;
        var over = ch.col.limit !== null && ch.col.limit !== undefined && n > ch.col.limit;
        head.appendChild(el("span", {
          class: "wip", "data-over": over ? "true" : "false",
          text: ch.col.limit === null || ch.col.limit === undefined
            ? n + (n === 1 ? " card" : " cards") : n + "/" + ch.col.limit
        }));
        sec.appendChild(head);
        var kept = ch.entries.filter(function (e) { return e.keep; });
        if (!kept.length) {
          sec.appendChild(el("p", { class: "chapter-empty", text: "Nothing in this column." }));
        } else {
          var tree = el("div", { role: "tree", "aria-label": ch.col.title });
          kept.forEach(function (e) {
            var p = effParent(e.card);
            tree.appendChild(renderNode(e, 0, p && colOf(p) !== colOf(e.card) ? p : null));
          });
          sec.appendChild(tree);
        }
        doc.appendChild(sec);
      });
    } else {
      doc.setAttribute("role", "tree");
      doc.setAttribute("aria-multiselectable", "false");
      chapters[0].entries.filter(function (e) { return e.keep; })
        .forEach(function (e) { doc.appendChild(renderNode(e, 0, null)); });
    }

    var hits = CARDS.filter(matches).length;
    var hitsEl = document.getElementById("hits");
    hitsEl.textContent = state.q ? hits + " of " + CARDS.length : "";
    document.getElementById("empty").hidden = doc.querySelectorAll(".node").length > 0;

    paintChrome();
    restoreFocus();
  }

  /* ---- the chrome around the document ---------------------------------- */

  var chipsEl = document.getElementById("chips");
  var stagedCountEl = document.getElementById("staged-count");
  var stagedBtn = document.getElementById("open-moves");
  var live = document.getElementById("live");

  function stagedList() {
    return Object.keys(state.staged).filter(function (id) {
      return BY[id] && state.staged[id] !== BY[id].status;
    });
  }

  function buildChips() {
    chipsEl.textContent = "";
    COLUMNS.forEach(function (col) {
      var b = el("button", {
        type: "button", class: "chip", "data-col": col.id,
        "aria-pressed": state.cols[col.id] ? "true" : "false"
      });
      b.appendChild(document.createTextNode(col.title));
      b.appendChild(el("span", { class: "n" }));
      chipsEl.appendChild(b);
    });
  }

  function paintChrome() {
    COLUMNS.forEach(function (col) {
      var b = chipsEl.querySelector('[data-col="' + col.id + '"]');
      if (!b) return;
      var n = CARDS.filter(function (c) { return colOf(c) === col.id; }).length;
      var lim = col.limit;
      var over = lim !== null && lim !== undefined && n > lim;
      b.setAttribute("aria-pressed", state.cols[col.id] ? "true" : "false");
      b.setAttribute("data-over", over ? "true" : "false");
      b.querySelector(".n").textContent = (lim === null || lim === undefined) ? String(n) : n + "/" + lim;
    });

    var n = stagedList().length;
    stagedCountEl.textContent = String(n);
    stagedBtn.setAttribute("data-any", n ? "true" : "false");

    var byline = document.getElementById("byline");
    byline.textContent = "";
    var withKids = CARDS.filter(function (c) { return (childrenOf[c.id] || []).length; }).length;
    var deepest = 0;
    CARDS.forEach(function (c) {
      var d = 0, cur = effParent(c), guard = 0, seen = Object.create(null);
      seen[c.id] = true;
      while (cur && !seen[cur.id] && guard++ < CARDS.length) { seen[cur.id] = true; d++; cur = effParent(cur); }
      if (d > deepest) deepest = d;
    });
    byline.appendChild(document.createTextNode(CARDS.length + " cards · "));
    byline.appendChild(el("b", { text: String(withKids) }));
    byline.appendChild(document.createTextNode(" decompose · " + roots.length + " at the top level · depth " + (deepest + 1)));
    var overCol = COLUMNS.filter(function (col) {
      var c = CARDS.filter(function (k) { return colOf(k) === col.id; }).length;
      return col.limit !== null && col.limit !== undefined && c > col.limit;
    });
    if (overCol.length) {
      byline.appendChild(document.createTextNode(" · "));
      byline.appendChild(el("span", { class: "over", text: overCol.map(function (c) {
        return c.title + " " + CARDS.filter(function (k) { return colOf(k) === c.id; }).length + "/" + c.limit;
      }).join(", ") + " over limit" }));
    }
  }

  function say(msg) { live.textContent = msg; }

  /* ---- focus, kept across every re-render ------------------------------ */

  function rows() { return Array.prototype.slice.call(doc.querySelectorAll(".node")); }

  function onPage(node) { return !!node && node.offsetParent !== null; }

  /* a collapse can hide the line that held focus, and a hidden element with
     tabindex=0 takes the whole outline out of the tab order — climb to the
     nearest section that is actually set on the page */
  function nearestOnPage(node) {
    var n = node;
    while (n && !onPage(n)) n = n.parentElement && n.parentElement.closest(".node");
    return n;
  }

  function restoreFocus() {
    var all = rows();
    var target = null;
    if (state.focus) target = doc.querySelector('.node[data-id="' + cssEscape(state.focus) + '"]');
    if (target && !onPage(target)) target = nearestOnPage(target);
    if (!target) {
      for (var i = 0; i < all.length && !target; i++) if (onPage(all[i])) target = all[i];
    }
    if (!target) target = all[0];
    all.forEach(function (r) {
      r.setAttribute("tabindex", r === target ? "0" : "-1");
      r.setAttribute("data-focused", "false");
    });
    if (target && state.refocus) {
      state.focus = target.getAttribute("data-id");
      target.setAttribute("data-focused", "true");
      /* re-rendering must not throw the reader's place: focus without the
         browser's own scroll, then bring only the line back if it has gone
         under the sticky toolbar. Opening a long card body used to scroll its
         own heading off the top of the window. */
      target.focus({ preventScroll: true });
      var line = target.querySelector(".line");
      (line && line.parentElement === target ? line : target)
        .scrollIntoView({ block: "nearest", inline: "nearest" });
      state.refocus = false;
    }
  }

  function cssEscape(s) { return String(s).replace(/["\\]/g, "\\$&"); }

  function focusRow(node) {
    if (!node) return;
    state.focus = node.getAttribute("data-id");
    rows().forEach(function (r) {
      r.setAttribute("tabindex", r === node ? "0" : "-1");
      r.setAttribute("data-focused", r === node ? "true" : "false");
    });
    node.focus();
  }

  function visibleRows() {
    return rows().filter(function (r) { return r.offsetParent !== null; });
  }
  function rowFor(id) { return doc.querySelector('.node[data-id="' + cssEscape(id) + '"]'); }

  function setCollapsed(id, v) {
    if (v) state.collapsed[id] = true; else delete state.collapsed[id];
    state.focus = id;
    state.refocus = true;
    render();
  }

  /* ---- the move menu ---------------------------------------------------- */

  var menu = document.getElementById("movemenu");
  var menuFor = null;

  function closeMenu(refocus) {
    if (menu.hidden) return;
    menu.hidden = true;
    menu.textContent = "";
    var id = menuFor;
    menuFor = null;
    if (refocus && id) { var r = rowFor(id); if (r) focusRow(r); }
  }

  function openMenu(id, anchor) {
    closeMenu(false);
    var card = BY[id];
    if (!card) return;
    menuFor = id;
    menu.textContent = "";
    menu.appendChild(el("span", { class: "mm-head", text: "Move to" }));
    COLUMNS.forEach(function (col) {
      var current = col.id === card.status;
      var staged = state.staged[id] === col.id && !current;
      menu.appendChild(el("button", {
        type: "button", role: "menuitem", "data-to": col.id,
        "data-current": current ? "true" : "false",
        "data-staged": staged ? "true" : "false"
      }, col.title));
    });
    if (isStaged(card)) {
      menu.appendChild(el("button", { type: "button", role: "menuitem", class: "mm-clear", "data-to": "__clear" }, "Discard staged move"));
    }
    menu.hidden = false;
    var r = anchor.getBoundingClientRect();
    var top = r.bottom + window.scrollY + 4;
    var left = Math.min(r.left + window.scrollX, window.scrollX + document.documentElement.clientWidth - menu.offsetWidth - 12);
    menu.style.top = top + "px";
    menu.style.left = Math.max(8, left) + "px";
    var first = menu.querySelector("button");
    if (first) first.focus();
  }

  menu.addEventListener("click", function (e) {
    var b = e.target.closest("button[data-to]");
    if (!b || !menuFor) return;
    var id = menuFor;
    var to = b.getAttribute("data-to");
    if (to === "__clear" || to === BY[id].status) delete state.staged[id];
    else state.staged[id] = to;
    closeMenu(false);
    state.focus = id;
    state.refocus = true;
    render();
    say(to === "__clear" ? "staged move discarded" : BY[id].title + " staged for " + colTitle(to));
  });

  menu.addEventListener("keydown", function (e) {
    var items = Array.prototype.slice.call(menu.querySelectorAll("button"));
    var i = items.indexOf(document.activeElement);
    if (e.key === "Escape") { e.preventDefault(); closeMenu(true); }
    else if (e.key === "ArrowDown") { e.preventDefault(); items[(i + 1) % items.length].focus(); }
    else if (e.key === "ArrowUp") { e.preventDefault(); items[(i - 1 + items.length) % items.length].focus(); }
  });

  document.addEventListener("mousedown", function (e) {
    if (menu.hidden) return;
    if (menu.contains(e.target) || (e.target.closest && e.target.closest("[data-move]"))) return;
    closeMenu(false);
  });

  /* ---- clicks in the document ------------------------------------------ */

  doc.addEventListener("click", function (e) {
    var t = e.target;
    var caret = t.closest("[data-toggle]");
    if (caret) {
      var id = caret.getAttribute("data-toggle");
      setCollapsed(id, !state.collapsed[id]);
      return;
    }
    var goTo = t.closest("[data-goto]");
    if (goTo) {
      var gid = goTo.getAttribute("data-goto");
      var target = rowFor(gid);
      if (target) { target.scrollIntoView({ block: "center" }); focusRow(target); }
      return;
    }
    var mv = t.closest("[data-move]");
    if (mv) { openMenu(mv.getAttribute("data-move"), mv); return; }
    var open = t.closest("[data-open]");
    if (open) {
      var oid = open.getAttribute("data-open");
      if (state.opened[oid]) delete state.opened[oid]; else state.opened[oid] = true;
      state.focus = oid;
      state.refocus = true;
      render();
      return;
    }
    var node = t.closest(".node");
    if (node && !t.closest("a")) focusRow(node);
  });

  doc.addEventListener("focusout", function () {
    setTimeout(function () {
      var a = document.activeElement;
      if (doc.contains(a) || menu.contains(a)) return;
      rows().forEach(function (r) { r.setAttribute("data-focused", "false"); });
    }, 0);
  });

  doc.addEventListener("focusin", function (e) {
    var node = e.target.closest ? e.target.closest(".node") : null;
    if (node && e.target === node) {
      state.focus = node.getAttribute("data-id");
      rows().forEach(function (r) { r.setAttribute("data-focused", r === node ? "true" : "false"); });
    }
  });

  /* ---- keyboard: the outline is a tree, so it behaves like one ---------- */

  doc.addEventListener("keydown", function (e) {
    var node = e.target.closest ? e.target.closest(".node") : null;
    if (!node || e.target !== node) return;
    var list = visibleRows();
    var i = list.indexOf(node);
    var id = node.getAttribute("data-id");
    var expandable = node.hasAttribute("aria-expanded");
    var expanded = node.getAttribute("aria-expanded") === "true";
    var key = e.key;

    if (key === "ArrowDown") { e.preventDefault(); focusRow(list[Math.min(i + 1, list.length - 1)]); }
    else if (key === "ArrowUp") { e.preventDefault(); focusRow(list[Math.max(i - 1, 0)]); }
    else if (key === "Home") { e.preventDefault(); focusRow(list[0]); }
    else if (key === "End") { e.preventDefault(); focusRow(list[list.length - 1]); }
    else if (key === "ArrowRight") {
      e.preventDefault();
      if (expandable && !expanded) setCollapsed(id, false);
      else {
        var kid = node.querySelector(".kids > .node");
        if (kid) focusRow(kid);
      }
    } else if (key === "ArrowLeft") {
      e.preventDefault();
      if (expandable && expanded) setCollapsed(id, true);
      else {
        var up = node.parentElement && node.parentElement.closest(".node");
        if (up) focusRow(up);
      }
    } else if (key === "Enter" || key === " ") {
      e.preventDefault();
      if (state.opened[id]) delete state.opened[id]; else state.opened[id] = true;
      state.focus = id; state.refocus = true; render();
    } else if (key === "m" || key === "M") {
      e.preventDefault();
      var btn = node.querySelector(".line [data-move]");
      if (btn) openMenu(id, btn);
    }
  });

  /* ---- toolbar ---------------------------------------------------------- */

  var qInput = document.getElementById("q");
  var qTimer = null;
  qInput.addEventListener("input", function () {
    clearTimeout(qTimer);
    qTimer = setTimeout(function () {
      state.q = qInput.value.trim();
      render();
    }, 60);
  });

  document.getElementById("seg-view").addEventListener("click", function (e) {
    var b = e.target.closest("button[data-v]");
    if (!b) return;
    state.view = b.getAttribute("data-v");
    Array.prototype.forEach.call(this.querySelectorAll("button"), function (x) {
      x.setAttribute("aria-checked", x === b ? "true" : "false");
    });
    render();
    say(state.view === "chapters" ? "grouped by column" : "one outline");
  });

  document.getElementById("seg-sum").addEventListener("click", function (e) {
    var b = e.target.closest("button[data-s]");
    if (!b) return;
    state.summaries = b.getAttribute("data-s");
    Array.prototype.forEach.call(this.querySelectorAll("button"), function (x) {
      x.setAttribute("aria-checked", x === b ? "true" : "false");
    });
    render();
  });

  chipsEl.addEventListener("click", function (e) {
    var b = e.target.closest("[data-col]");
    if (!b) return;
    var id = b.getAttribute("data-col");
    state.cols[id] = !state.cols[id];
    render();
  });

  document.getElementById("expand-all").addEventListener("click", function () {
    state.collapsed = {};
    state.refocus = doc.contains(document.activeElement);
    render();
    say("all sections open");
  });

  document.getElementById("collapse-all").addEventListener("click", function () {
    state.collapsed = {};
    CARDS.forEach(function (c) { if ((childrenOf[c.id] || []).length) state.collapsed[c.id] = true; });
    /* closing everything can swallow the line the keyboard was on; keep the
       reader inside the document by moving up to the section that ate it */
    state.refocus = doc.contains(document.activeElement);
    render();
    say("all sections closed");
  });

  /* ---- staged moves ----------------------------------------------------- */

  var dlg = document.getElementById("moves-dialog");
  var movesText = document.getElementById("moves-text");
  var dlgNote = document.getElementById("dlg-note");

  function moveCommands() {
    return stagedList().map(function (id) {
      return "folio kanban move " + id + " " + state.staged[id];
    });
  }

  stagedBtn.addEventListener("click", function () {
    var cmds = moveCommands();
    movesText.value = cmds.length ? cmds.join("\n") : "# nothing staged yet";
    movesText.rows = Math.max(3, Math.min(14, cmds.length || 1));
    dlgNote.textContent = cmds.length
      ? cmds.length + " move" + (cmds.length === 1 ? "" : "s") + " staged. The site is static and never writes to the repository — run these, or edit the cardfiles."
      : "No moves staged. Use Move on any line, or press m with a line focused.";
    if (typeof dlg.showModal === "function") dlg.showModal(); else dlg.setAttribute("open", "");
  });

  document.getElementById("copy-moves").addEventListener("click", function () {
    movesText.select();
    var ok = false;
    try { ok = document.execCommand("copy"); } catch (err) { ok = false; }
    if (!ok && navigator.clipboard) navigator.clipboard.writeText(movesText.value).catch(function () {});
    this.textContent = "Copied";
    var self = this;
    setTimeout(function () { self.textContent = "Copy"; }, 1400);
  });

  document.getElementById("clear-moves").addEventListener("click", function () {
    state.staged = {};
    movesText.value = "# nothing staged yet";
    dlgNote.textContent = "All staged moves discarded.";
    render();
  });

  /* ---- colour scheme ---------------------------------------------------- */

  var themeBtn = document.getElementById("theme");
  var THEMES = ["auto", "light", "dark"];
  themeBtn.addEventListener("click", function () {
    var cur = document.documentElement.getAttribute("data-theme") || "auto";
    var next = THEMES[(THEMES.indexOf(cur) + 1) % THEMES.length];
    document.documentElement.setAttribute("data-theme", next);
    themeBtn.textContent = next.charAt(0).toUpperCase() + next.slice(1);
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && !menu.hidden) { closeMenu(true); return; }
    var a = document.activeElement;
    var typing = a && (a.tagName === "INPUT" || a.tagName === "TEXTAREA" || a.isContentEditable);
    if (e.key === "/" && !typing && !dlg.open && !e.metaKey && !e.ctrlKey) {
      e.preventDefault();
      qInput.focus();
      qInput.select();
    }
  });

  /* ---- go ---------------------------------------------------------------- */

  document.getElementById("board-title").textContent = BOARD.title || "Board";
  document.title = (BOARD.title || "Board") + " — document outline";

  var keys = el("p", { class: "keys" });
  keys.appendChild(document.createTextNode("Keys "));
  [["↑ ↓", "line"], ["→ ←", "open / close a section"], ["Enter", "read the card"], ["m", "move"], ["/", "find"]]
    .forEach(function (pair, i) {
      if (i) keys.appendChild(document.createTextNode(" · "));
      keys.appendChild(el("kbd", { text: pair[0] }));
      keys.appendChild(document.createTextNode(" " + pair[1]));
    });
  doc.parentNode.insertBefore(keys, doc);

  buildChips();

  /* the deepest branch opens by default so the depth-3 case is visible on
     arrival; everything else that decomposes starts open too — this is a
     document, and a document is read open. */
  render();

  var first = rows()[0];
  if (first) first.setAttribute("tabindex", "0");
})();
