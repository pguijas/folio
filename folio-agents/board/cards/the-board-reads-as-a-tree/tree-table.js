/* Tree table — one table for the whole board.
   Every card is a row; the hierarchy lives in the first column. */
(function () {
  "use strict";

  var BOARD = window.BOARD || { title: "", columns: [] };
  var COLS = BOARD.columns || [];
  var LAST_COL = COLS.length ? COLS.length - 1 : 0;

  /* ------------------------------------------------------------- model -- */

  var cards = []; // board order
  var byId = Object.create(null);
  var colIndexOf = Object.create(null);

  COLS.forEach(function (col, ci) {
    colIndexOf[col.id] = ci;
    (col.cards || []).forEach(function (card) {
      card._order = cards.length;
      card._col = ci;
      cards.push(card);
      byId[card.id] = card;
    });
  });

  /* A parent link is honoured only when it is real, is not the card itself,
     and does not close a loop. `a.parent = b, b.parent = a` passes the
     build, so every link is checked against the chain above it before it is
     used; a link that would close a loop is dropped and the card becomes a
     root, flagged so the row can say so. */
  function closesLoop(card, parentId) {
    var seen = Object.create(null);
    var at = parentId;
    var guard = 0;
    while (at && guard++ < 500) {
      if (at === card.id) return true;
      if (seen[at]) return true; // already-looping chain above us
      seen[at] = true;
      var next = byId[at];
      at = next ? next.parent : null;
    }
    return false;
  }

  cards.forEach(function (card) {
    card._kids = [];
    card._parent = null;
    card._broken = "";
    var p = card.parent;
    if (!p) return;
    if (!byId[p]) {
      card._broken = "parent " + p + " is not on this board";
      return;
    }
    if (p === card.id) {
      card._broken = "card is its own parent";
      return;
    }
    if (closesLoop(card, p)) {
      card._broken = "parent " + p + " would close a loop";
      return;
    }
    card._parent = byId[p];
  });

  cards.forEach(function (card) {
    if (card._parent) card._parent._kids.push(card);
  });

  var roots = cards.filter(function (c) {
    return !c._parent;
  });

  // depth + subtree membership, computed once over the now-acyclic forest
  var subtree = Object.create(null); // id -> array of descendant cards
  (function walk(list, depth) {
    list.forEach(function (card) {
      card._depth = depth;
      walk(card._kids, depth + 1);
      var out = [];
      card._kids.forEach(function (kid) {
        out.push(kid);
        var deeper = subtree[kid.id] || [];
        for (var i = 0; i < deeper.length; i++) out.push(deeper[i]);
      });
      subtree[card.id] = out;
    });
  })(roots, 0);

  var ancestorsOf = Object.create(null); // id -> array of ancestor ids
  cards.forEach(function (card) {
    var out = [];
    var at = card._parent;
    var guard = 0;
    while (at && guard++ < 500) {
      out.push(at.id);
      at = at._parent;
    }
    ancestorsOf[card.id] = out;
  });

  /* ------------------------------------------------------------- state -- */

  var state = {
    collapsed: Object.create(null), // id -> true
    staged: Object.create(null), // id -> column id
    query: "",
    divergedOnly: false,
    sortKey: "",
    sortDir: 0, // 1 asc, -1 desc, 0 board order
    activeId: roots.length ? roots[0].id : "",
  };

  function statusOf(card) {
    var s = state.staged[card.id];
    return s ? colIndexOf[s] : card._col;
  }
  function stagedCount() {
    return Object.keys(state.staged).length;
  }

  /* -------------------------------------------------------- comparators -- */

  var SIZE_RANK = { XS: 1, S: 2, M: 3, L: 4, XL: 5 };

  function milestoneRank(v) {
    if (!v) return null;
    var parts = String(v).split(".");
    var n = 0;
    for (var i = 0; i < 3; i++) n = n * 1000 + (parseInt(parts[i], 10) || 0);
    return n;
  }

  function sortValue(card, key) {
    switch (key) {
      case "title":
        return card.title ? card.title.toLowerCase() : "";
      case "status":
        return statusOf(card);
      case "milestone":
        return milestoneRank(card.milestone);
      case "type":
        return card.type || "";
      case "size":
        return SIZE_RANK[String(card.size || "").toUpperCase()] || null;
      case "assignee":
        return (card.assignee || []).join(", ").toLowerCase();
      default:
        return null;
    }
  }

  function isBlank(v) {
    return v === null || v === undefined || v === "";
  }

  /* Sorting reorders siblings inside their parent and nothing else, so the
     tree survives every sort. Blanks always sink, in both directions. */
  function sortSiblings(list) {
    var key = state.sortKey;
    var dir = state.sortDir;
    var out = list.slice();
    if (!key || !dir) {
      out.sort(function (a, b) {
        return a._order - b._order;
      });
      return out;
    }
    out.sort(function (a, b) {
      var av = sortValue(a, key);
      var bv = sortValue(b, key);
      var ab = isBlank(av);
      var bb = isBlank(bv);
      if (ab && bb) return a._order - b._order;
      if (ab) return 1;
      if (bb) return -1;
      if (av < bv) return -1 * dir;
      if (av > bv) return 1 * dir;
      return a._order - b._order;
    });
    return out;
  }

  /* ----------------------------------------------------------- filtering -- */

  /* The decision: a matching child never re-roots. Its ancestors stay in
     place as dimmed context so depth never changes under you — the filter
     only ever removes rows, it never moves one. */

  function isDiverged(card) {
    return !!card._parent && statusOf(card) !== statusOf(card._parent);
  }

  var view = { rows: [], match: null, ctx: null, matches: 0, context: 0 };

  function computeFilter() {
    var q = state.query.trim().toLowerCase();
    if (!q && !state.divergedOnly) {
      view.match = null;
      view.ctx = null;
      view.matches = 0;
      view.context = 0;
      return false;
    }
    var match = Object.create(null);
    var ctx = Object.create(null);
    cards.forEach(function (card) {
      var ok = true;
      if (q) {
        ok =
          card.title.toLowerCase().indexOf(q) !== -1 ||
          card.id.toLowerCase().indexOf(q) !== -1;
      }
      if (ok && state.divergedOnly) ok = isDiverged(card);
      if (ok) match[card.id] = true;
    });
    cards.forEach(function (card) {
      if (!match[card.id]) return;
      ancestorsOf[card.id].forEach(function (id) {
        if (!match[id]) ctx[id] = true;
      });
    });
    view.match = match;
    view.ctx = ctx;
    view.matches = Object.keys(match).length;
    view.context = Object.keys(ctx).length;
    return true;
  }

  function visible(card) {
    if (!view.match) return true;
    return !!view.match[card.id] || !!view.ctx[card.id];
  }

  /* --------------------------------------------------------- subtree stats -- */

  function subStats(card) {
    var kids = subtree[card.id] || [];
    var counts = COLS.map(function () {
      return 0;
    });
    kids.forEach(function (k) {
      counts[statusOf(k)]++;
    });
    return { counts: counts, total: kids.length, done: counts[LAST_COL] || 0 };
  }

  /* What a collapsed row says about the children it is hiding: one value if
     parent and hidden children agree, a range or `mixed` if they do not.
     A value the card does not carry itself is never printed in the plain
     register, even when every hidden row agrees on it — otherwise collapsing
     a row invents a size or an assignee the card has not got. */
  function rollup(card, hidden, field) {
    var vals = [];
    var push = function (v) {
      if (v && vals.indexOf(v) === -1) vals.push(v);
    };
    var take = function (c) {
      if (field === "assignee") (c.assignee || []).forEach(push);
      else push(c[field]);
    };
    take(card);
    var own = vals.length > 0; // everything so far came from the card itself
    hidden.forEach(take);
    if (!vals.length) return null;
    if (vals.length === 1) {
      return {
        text: field === "assignee" ? "@" + vals[0] : vals[0],
        agreed: own,
        derived: !own,
        all: vals,
      };
    }
    if (field === "milestone") {
      var sorted = vals.slice().sort(function (a, b) {
        return milestoneRank(a) - milestoneRank(b);
      });
      return {
        text: sorted[0] + "–" + sorted[sorted.length - 1],
        agreed: false,
        derived: !own,
        all: sorted,
      };
    }
    if (field === "size") {
      var s = vals.slice().sort(function (a, b) {
        return (SIZE_RANK[a.toUpperCase()] || 0) - (SIZE_RANK[b.toUpperCase()] || 0);
      });
      return {
        text: s[0] + "–" + s[s.length - 1],
        agreed: false,
        derived: !own,
        all: s,
      };
    }
    if (field === "assignee") {
      return {
        text: "@" + vals[0] + " +" + (vals.length - 1),
        agreed: false,
        derived: !own,
        all: vals,
      };
    }
    return { text: "mixed", agreed: false, derived: !own, mixed: true, all: vals };
  }

  /* ---------------------------------------------------------- flatten -- */

  function buildRows() {
    computeFilter();
    var rows = [];

    function walkList(list, depth, lines) {
      var vis = list.filter(visible);
      var ordered = sortSiblings(vis);
      ordered.forEach(function (card, i) {
        var last = i === ordered.length - 1;
        var kids = card._kids.filter(visible);
        var open = !state.collapsed[card.id];
        var hiddenKids =
          kids.length && !open ? (subtree[card.id] || []).filter(visible) : [];
        rows.push({
          card: card,
          depth: depth,
          lines: lines,
          last: last,
          pos: i + 1,
          setsize: ordered.length,
          kids: kids.length,
          open: open,
          hidden: hiddenKids,
          context: !!(view.ctx && view.ctx[card.id] && !view.match[card.id]),
        });
        if (kids.length && open) {
          walkList(card._kids, depth + 1, lines.concat([!last]));
        }
      });
    }

    walkList(roots, 0, []);
    // a root and everything under it is one group; the rule below it is darker
    rows.forEach(function (r, i) {
      r.endsGroup = i === rows.length - 1 || rows[i + 1].depth === 0;
    });
    view.rows = rows;
    return rows;
  }

  /* ------------------------------------------------------------ render -- */

  var $ = function (sel) {
    return document.querySelector(sel);
  };
  var tbody = $("#rows");

  function esc(s) {
    return String(s === null || s === undefined ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function hl(text) {
    var q = state.query.trim();
    if (!q) return esc(text);
    var i = String(text).toLowerCase().indexOf(q.toLowerCase());
    if (i === -1) return esc(text);
    return (
      esc(String(text).slice(0, i)) +
      "<mark>" +
      esc(String(text).slice(i, i + q.length)) +
      "</mark>" +
      esc(String(text).slice(i + q.length))
    );
  }

  function railHTML(row) {
    if (!row.depth) return "";
    var out = '<span class="rail" aria-hidden="true">';
    for (var j = 0; j < row.depth; j++) {
      if (j === row.depth - 1) {
        out += '<i class="elbow' + (row.last ? " end" : "") + '"></i>';
      } else {
        out += row.lines[j + 1] ? '<i class="line"></i>' : "<i></i>";
      }
    }
    return out + "</span>";
  }

  function meterHTML(card) {
    var st = subStats(card);
    if (!st.total) return "";
    var bars = "";
    var breakdown = [];
    for (var i = 0; i < st.counts.length; i++) {
      var n = st.counts[i];
      if (!n) continue;
      bars +=
        '<i data-i="' + i + '" style="flex:' + n + '"></i>';
      breakdown.push(n + " " + COLS[i].title.toLowerCase());
    }
    var title =
      st.done +
      " of " +
      st.total +
      " subtasks in " +
      COLS[LAST_COL].title +
      " · " +
      breakdown.join(", ");
    return (
      '<span class="prog" title="' +
      esc(title) +
      '"><span class="meter">' +
      bars +
      '</span><span class="frac"><b>' +
      st.done +
      "</b>/" +
      st.total +
      "</span></span>"
    );
  }

  function metaHTML(row, field) {
    var card = row.card;
    var cls = field === "milestone" ? "meta num" : "meta";
    var text = "";
    var extra = "";
    if (row.hidden && row.hidden.length) {
      var r = rollup(card, row.hidden, field);
      if (r) {
        if (r.agreed) {
          text = esc(r.text);
        } else {
          var count = row.hidden.length;
          var hidden = count + (count === 1 ? " row" : " rows");
          extra =
            ' title="' +
            esc(
              r.derived
                ? r.all.join(", ") +
                    " on the " +
                    hidden +
                    " this one hides; not set on this card"
                : r.all.join(", ") + " across this row and the " + hidden + " it hides"
            ) +
            '"';
          text =
            '<span class="roll' +
            (r.mixed ? " mixed" : "") +
            (r.derived ? " derived" : "") +
            '">' +
            esc(r.text) +
            "</span>";
        }
      }
    } else if (field === "assignee") {
      var names = card.assignee || [];
      text = names
        .map(function (n) {
          return "@" + esc(n);
        })
        .join(" ");
    } else {
      text = esc(card[field] || "");
    }
    if (!text) return '<span class="' + cls + '"></span>';
    return "<span class=\"" + cls + '"' + extra + ">" + text + "</span>";
  }

  function statusHTML(row) {
    var card = row.card;
    var here = statusOf(card);
    var out = '<div class="stwrap">';
    if (isDiverged(card)) {
      out +=
        '<span class="dv" title="Sits in ' +
        esc(COLS[here].title) +
        ", under a parent in " +
        esc(COLS[statusOf(card._parent)].title) +
        '" aria-hidden="true">≠</span>';
    }
    if (state.staged[card.id]) {
      out += '<span class="from" title="was ' + esc(COLS[card._col].title) + '">' +
        esc(COLS[card._col].title) + "</span>";
    }
    out +=
      '<span class="stbox"><select class="st" tabindex="-1" aria-label="Column for ' +
      esc(card.title) +
      (isDiverged(card)
        ? ", which differs from its parent in " +
          esc(COLS[statusOf(card._parent)].title)
        : "") +
      (state.staged[card.id] ? ", staged, was " + esc(COLS[card._col].title) : "") +
      '">';
    COLS.forEach(function (col, ci) {
      out +=
        '<option value="' +
        esc(col.id) +
        '"' +
        (ci === here ? " selected" : "") +
        ">" +
        esc(col.title) +
        "</option>";
    });
    return out + "</select></span></div>";
  }

  function rowHTML(row) {
    var card = row.card;
    var attrs =
      '<tr role="row" data-id="' +
      esc(card.id) +
      '" data-depth="' +
      row.depth +
      '" data-kids="' +
      (row.kids ? 1 : 0) +
      '" data-open="' +
      (row.open ? 1 : 0) +
      '" aria-level="' +
      (row.depth + 1) +
      '" aria-posinset="' +
      row.pos +
      '" aria-setsize="' +
      row.setsize +
      '"' +
      (row.kids ? ' aria-expanded="' + (row.open ? "true" : "false") + '"' : "") +
      (state.staged[card.id] ? ' data-staged="1"' : "") +
      (isDiverged(card) ? ' data-diverged="1"' : "") +
      (row.context ? ' data-context="1"' : "") +
      (row.endsGroup ? ' data-ends-group="1"' : "") +
      (card.priority === "high" ? ' data-priority="high"' : "") +
      (card.id === state.activeId ? ' data-active="1"' : "") +
      ' tabindex="' + (card.id === state.activeId ? "0" : "-1") + '">';

    var tri = row.kids
      ? '<button type="button" class="tri" tabindex="-1" aria-hidden="true" data-toggle="' +
        esc(card.id) +
        '"></button>'
      : '<span class="tri-none" aria-hidden="true"></span>';

    var label =
      '<span class="label"><span class="title">' + hl(card.title) + "</span>";
    if (card._broken) {
      label +=
        '<span class="dv" title="' + esc(card._broken) + '">!</span>';
    }
    if (row.kids) label += meterHTML(card);
    if (row.hidden && row.hidden.length) {
      label +=
        '<span class="hidden-n" title="' +
        row.hidden.length +
        ' rows hidden under this one">+' +
        row.hidden.length +
        "</span>";
    }
    if (row.context) label += '<span class="ctx-tag">context</span>';
    label += '<span class="cid">' + hl(card.id) + "</span></span>";

    return (
      attrs +
      '<td role="gridcell"><div class="tw">' +
      railHTML(row) +
      tri +
      label +
      "</div></td>" +
      '<td role="gridcell">' +
      statusHTML(row) +
      "</td>" +
      '<td role="gridcell">' +
      metaHTML(row, "milestone") +
      "</td>" +
      '<td role="gridcell">' +
      metaHTML(row, "type") +
      "</td>" +
      '<td role="gridcell">' +
      metaHTML(row, "size") +
      "</td>" +
      '<td role="gridcell">' +
      metaHTML(row, "assignee") +
      "</td></tr>"
    );
  }

  /* ------------------------------------------------------------- paint -- */

  var elCount = $("#matchcount");
  var elLegend = $("#legend");
  var elCmds = $("#cmds");
  var elList = $("#staged-list");
  var elStagedN = $("#staged-n");
  var elStagedBtn = $("#staged-toggle");
  var elLive = $("#live");

  function renderLegend() {
    var base = COLS.map(function () {
      return 0;
    });
    var eff = COLS.map(function () {
      return 0;
    });
    cards.forEach(function (c) {
      base[c._col]++;
      eff[statusOf(c)]++;
    });
    elLegend.innerHTML = COLS.map(function (col, i) {
      var n = eff[i];
      var over = col.limit && n > col.limit;
      var delta = n - base[i];
      return (
        '<li class="' +
        (over ? "over" : "") +
        '"><span>' +
        esc(col.title) +
        '</span><span class="n">' +
        n +
        (col.limit ? "/" + col.limit : "") +
        "</span>" +
        (delta
          ? '<span class="delta">' + (delta > 0 ? "+" : "") + delta + "</span>"
          : "") +
        "</li>"
      );
    }).join("");
  }

  function renderCount() {
    if (!view.match) {
      elCount.innerHTML =
        "<b>" +
        cards.length +
        "</b> cards · <b>" +
        view.rows.length +
        "</b> rows shown";
      return;
    }
    elCount.innerHTML =
      "<b>" +
      view.matches +
      "</b> match · " +
      view.context +
      " kept as context · " +
      cards.length +
      " total";
  }

  function renderStaged() {
    var ids = cards
      .filter(function (c) {
        return state.staged[c.id];
      })
      .map(function (c) {
        return c.id;
      });
    elStagedN.textContent = String(ids.length);
    elStagedBtn.setAttribute("data-any", ids.length ? "1" : "0");
    elCmds.textContent = ids
      .map(function (id) {
        return "folio kanban move " + id + " " + state.staged[id];
      })
      .join("\n");
    elList.innerHTML = ids
      .map(function (id) {
        var col = COLS[colIndexOf[state.staged[id]]];
        return (
          "<li><span>" +
          esc(byId[id].title) +
          " <b>→ " +
          esc(col.title) +
          "</b></span><button type=\"button\" data-unstage=\"" +
          esc(id) +
          '" aria-label="Discard the move of ' +
          esc(byId[id].title) +
          '">×</button></li>'
        );
      })
      .join("");
    $("#copy-cmds").disabled = !ids.length;
    $("#clear-staged").disabled = !ids.length;
  }

  /* When the active row stops being on screen — you collapsed above it, or
     filtered it away — the place to land is the nearest ancestor still
     rendered, not the top of the board. Losing your position in a 35-row
     tree because you pressed Collapse all is the whole reason people stop
     trusting a keyboard. */
  function nextActive(rows, present) {
    var chain = ancestorsOf[state.activeId] || [];
    for (var i = 0; i < chain.length; i++) {
      if (present[chain[i]]) return chain[i];
    }
    for (var j = 0; j < rows.length; j++) {
      if (!rows[j].context) return rows[j].card.id;
    }
    return rows.length ? rows[0].card.id : "";
  }

  function render() {
    var rows = buildRows();
    var present = Object.create(null);
    rows.forEach(function (r) {
      present[r.card.id] = true;
    });
    if (!present[state.activeId]) {
      state.activeId = nextActive(rows, present);
    }
    tbody.innerHTML = rows.map(rowHTML).join("");
    $("#empty").hidden = rows.length > 0;
    $("#diverged-n").textContent = String(cards.filter(isDiverged).length);
    renderLegend();
    renderCount();
    renderStaged();
  }

  function rowEl(id) {
    return tbody.querySelector('tr[data-id="' + (window.CSS && CSS.escape ? CSS.escape(id) : id) + '"]');
  }

  function setActive(id, focus) {
    if (!id) return;
    var prev = tbody.querySelector('tr[data-active="1"]');
    if (prev) {
      prev.removeAttribute("data-active");
      prev.tabIndex = -1;
    }
    state.activeId = id;
    var tr = rowEl(id);
    if (!tr) return;
    tr.setAttribute("data-active", "1");
    tr.tabIndex = 0;
    if (focus) tr.focus();
  }

  function say(msg) {
    elLive.textContent = msg;
  }

  /* -------------------------------------------------------- behaviours -- */

  function toggle(id, force) {
    var card = byId[id];
    if (!card || !card._kids.length) return;
    var open = !state.collapsed[id];
    var next = force === undefined ? !open : force;
    if (next) delete state.collapsed[id];
    else state.collapsed[id] = true;
    render();
    setActive(id, true);
    say(
      card.title +
        (next ? " expanded" : " collapsed, hiding " + (subtree[id] || []).length + " rows")
    );
  }

  function stage(id, colId) {
    var card = byId[id];
    if (!card) return;
    if (colId === card.status) delete state.staged[id];
    else state.staged[id] = colId;
    render();
    setActive(id, false);
    var tr = rowEl(id);
    var sel = tr && tr.querySelector(".st");
    if (sel) sel.focus();
    say(
      card.title +
        (state.staged[id]
          ? " staged for " + COLS[colIndexOf[colId]].title
          : " move discarded")
    );
  }

  var savedCollapsed = null;

  function filtering() {
    return !!(state.query.trim() || state.divergedOnly);
  }

  function refilter(changer) {
    var was = filtering();
    changer();
    var now = filtering();
    if (now && !was) {
      savedCollapsed = state.collapsed;
      state.collapsed = Object.create(null);
      Object.keys(savedCollapsed).forEach(function (k) {
        state.collapsed[k] = true;
      });
    }
    if (now) {
      computeFilter();
      // every ancestor of a match opens so the match is actually on screen
      Object.keys(view.match || {}).forEach(function (id) {
        (ancestorsOf[id] || []).forEach(function (a) {
          delete state.collapsed[a];
        });
      });
    }
    if (!now && was && savedCollapsed) {
      state.collapsed = savedCollapsed;
      savedCollapsed = null;
    }
    render();
  }

  /* clicks */

  tbody.addEventListener("click", function (e) {
    var tri = e.target.closest(".tri");
    if (tri) {
      toggle(tri.getAttribute("data-toggle"));
      return;
    }
    var tr = e.target.closest("tr");
    if (!tr) return;
    var id = tr.getAttribute("data-id");
    if (e.target.closest("select")) {
      setActive(id, false);
      return;
    }
    setActive(id, true);
  });

  tbody.addEventListener("change", function (e) {
    var sel = e.target.closest(".st");
    if (!sel) return;
    var tr = sel.closest("tr");
    stage(tr.getAttribute("data-id"), sel.value);
  });

  tbody.addEventListener("dblclick", function (e) {
    var tr = e.target.closest("tr");
    if (!tr || e.target.closest("select")) return;
    toggle(tr.getAttribute("data-id"));
  });

  /* keyboard: a treegrid, driven from the row */

  function visibleRows() {
    return Array.prototype.slice.call(tbody.querySelectorAll("tr"));
  }

  tbody.addEventListener("keydown", function (e) {
    var tr = e.target.closest("tr");
    if (!tr) return;
    var id = tr.getAttribute("data-id");
    var card = byId[id];
    var inSelect = e.target.tagName === "SELECT";

    if (inSelect) {
      if (e.key === "ArrowLeft" || e.key === "Escape") {
        e.preventDefault();
        setActive(id, true);
      } else if (e.key === "ArrowRight") {
        e.preventDefault();
      }
      return;
    }

    var rows = visibleRows();
    var i = rows.indexOf(tr);
    var go = function (n) {
      e.preventDefault();
      if (rows[n]) setActive(rows[n].getAttribute("data-id"), true);
    };

    switch (e.key) {
      case "ArrowDown":
        go(i + 1);
        break;
      case "ArrowUp":
        go(i - 1);
        break;
      case "Home":
        go(0);
        break;
      case "End":
        go(rows.length - 1);
        break;
      case "ArrowRight":
        e.preventDefault();
        if (card && card._kids.length && state.collapsed[id]) toggle(id, true);
        else {
          var sel = tr.querySelector(".st");
          if (sel) sel.focus();
        }
        break;
      case "ArrowLeft":
        e.preventDefault();
        if (card && card._kids.length && !state.collapsed[id]) toggle(id, false);
        else if (card && card._parent && rowEl(card._parent.id)) {
          setActive(card._parent.id, true);
        }
        break;
      case "Enter":
      case " ":
        if (card && card._kids.length) {
          e.preventDefault();
          toggle(id);
        }
        break;
      case "*":
        e.preventDefault();
        expandAll();
        break;
      default:
        break;
    }
  });

  /* toolbar */

  function expandAll() {
    state.collapsed = Object.create(null);
    render();
    setActive(state.activeId, false);
    say("Everything expanded");
  }

  function collapseAll() {
    state.collapsed = Object.create(null);
    cards.forEach(function (c) {
      if (c._kids.length) state.collapsed[c.id] = true;
    });
    render();
    setActive(state.activeId, false);
    say("Everything collapsed to " + view.rows.length + " rows");
  }

  var elQ = $("#q");
  elQ.addEventListener("input", function () {
    refilter(function () {
      state.query = elQ.value;
    });
  });
  elQ.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      elQ.value = "";
      refilter(function () {
        state.query = "";
      });
    }
  });

  $("#expand-all").addEventListener("click", expandAll);
  $("#collapse-all").addEventListener("click", collapseAll);

  var elDiv = $("#diverged");
  elDiv.addEventListener("click", function () {
    refilter(function () {
      state.divergedOnly = !state.divergedOnly;
    });
    elDiv.setAttribute("aria-pressed", state.divergedOnly ? "true" : "false");
  });

  var elPanel = $("#staged-panel");
  elStagedBtn.addEventListener("click", function () {
    var open = elPanel.hidden;
    elPanel.hidden = !open;
    elStagedBtn.setAttribute("aria-expanded", open ? "true" : "false");
  });

  elList.addEventListener("click", function (e) {
    var b = e.target.closest("[data-unstage]");
    if (!b) return;
    var id = b.getAttribute("data-unstage");
    delete state.staged[id];
    render();
  });

  $("#clear-staged").addEventListener("click", function () {
    state.staged = Object.create(null);
    render();
    say("Staged moves discarded");
  });

  $("#copy-cmds").addEventListener("click", function () {
    var text = elCmds.textContent;
    if (!text) return;
    var done = function () {
      say("Commands copied");
      var b = $("#copy-cmds");
      b.textContent = "Copied";
      setTimeout(function () {
        b.textContent = "Copy";
      }, 1200);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done, function () {
        selectCmds();
      });
    } else selectCmds();
    function selectCmds() {
      var r = document.createRange();
      r.selectNodeContents(elCmds);
      var s = window.getSelection();
      s.removeAllRanges();
      s.addRange(r);
      try {
        if (document.execCommand("copy")) done();
      } catch (err) {
        say("Select the commands and copy them");
      }
    }
  });

  /* sorting: siblings only, so the tree never breaks */

  Array.prototype.slice
    .call(document.querySelectorAll("th[data-sort]"))
    .forEach(function (th) {
      th.querySelector("button").addEventListener("click", function () {
        var key = th.getAttribute("data-sort");
        if (state.sortKey !== key) {
          state.sortKey = key;
          state.sortDir = 1;
        } else if (state.sortDir === 1) {
          state.sortDir = -1;
        } else {
          state.sortKey = "";
          state.sortDir = 0;
        }
        Array.prototype.slice
          .call(document.querySelectorAll("th[data-sort]"))
          .forEach(function (other) {
            var on = other.getAttribute("data-sort") === state.sortKey;
            other.setAttribute(
              "aria-sort",
              on ? (state.sortDir === 1 ? "ascending" : "descending") : "none"
            );
          });
        render();
        say(
          state.sortKey
            ? "Sorted by " + state.sortKey + ", siblings only"
            : "Back to board order"
        );
      });
    });

  /* theme + chrome */

  Array.prototype.slice
    .call(document.querySelectorAll("[data-theme-set]"))
    .forEach(function (b) {
      b.addEventListener("click", function () {
        var v = b.getAttribute("data-theme-set");
        document.documentElement.setAttribute("data-theme", v);
        Array.prototype.slice
          .call(document.querySelectorAll("[data-theme-set]"))
          .forEach(function (o) {
            o.setAttribute(
              "aria-pressed",
              o.getAttribute("data-theme-set") === v ? "true" : "false"
            );
          });
        try {
          localStorage.setItem("tree-table-theme", v);
        } catch (err) {
          /* file:// can refuse storage; the toggle still works this session */
        }
      });
    });

  (function restoreTheme() {
    var v = null;
    try {
      v = localStorage.getItem("tree-table-theme");
    } catch (err) {
      v = null;
    }
    if (!v) return;
    document.documentElement.setAttribute("data-theme", v);
    Array.prototype.slice
      .call(document.querySelectorAll("[data-theme-set]"))
      .forEach(function (o) {
        o.setAttribute(
          "aria-pressed",
          o.getAttribute("data-theme-set") === v ? "true" : "false"
        );
      });
  })();

  function setToolbarHeight() {
    var tb = document.querySelector(".toolbar");
    if (tb) {
      document.documentElement.style.setProperty(
        "--tb-h",
        tb.offsetHeight + "px"
      );
    }
  }
  window.addEventListener("resize", setToolbarHeight);

  document.addEventListener("keydown", function (e) {
    var t = e.target;
    var typing =
      t &&
      (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.tagName === "SELECT");
    if (e.key === "/" && !typing) {
      e.preventDefault();
      elQ.focus();
      elQ.select();
    }
    if (e.key === "*" && !typing) {
      e.preventDefault();
      expandAll();
    }
  });

  /* ---------------------------------------------------------------- go -- */

  render();
  setToolbarHeight();

  window.__TREE = { cards: cards, roots: roots, state: state, subtree: subtree };
})();
