/* Board with inline expansion — Folio kanban prototype.

   The board is unchanged: every card renders exactly once, in its own
   column. A card that decomposes grows one extra line, and opening that
   line lists what it breaks into as sub-rows that *point at* the real
   cards. Nothing is moved by nesting.

   `parent:` has no cycle check beyond self-parent, so every walk below
   carries a visited set. `a -> b -> a` renders a CYCLE stop, not a hang. */

(function () {
  "use strict";

  var BOARD = window.BOARD || { title: "Board", columns: [] };
  var COLUMNS = BOARD.columns || [];

  var CARD = Object.create(null); // id -> card
  var HOME = Object.create(null); // id -> committed column id
  var KIDS = Object.create(null); // id -> [child id]
  var ORDER = []; // every id, in board order
  var COLUMN_AT = Object.create(null); // column id -> index

  COLUMNS.forEach(function (column, index) {
    COLUMN_AT[column.id] = index;
    (column.cards || []).forEach(function (card) {
      if (!card.id || CARD[card.id]) return;
      CARD[card.id] = card;
      HOME[card.id] = column.id;
      ORDER.push(card.id);
    });
  });

  var LAST_COLUMN = COLUMNS.length ? COLUMNS[COLUMNS.length - 1].id : "";

  /* A parent link only counts when it names a card that exists and is not
     the card itself — the two things the build already guarantees. */
  function parentOf(id) {
    var card = CARD[id];
    if (!card) return "";
    var p = card.parent || "";
    if (!p || p === id || !CARD[p]) return "";
    return p;
  }

  ORDER.forEach(function (id) {
    KIDS[id] = KIDS[id] || [];
  });
  ORDER.forEach(function (id) {
    var p = parentOf(id);
    if (p) KIDS[p].push(id);
  });

  /* A card is a root when it has no parent, or when walking up from it
     comes back to something already seen — the cycle case. Without this,
     a -> b -> a would render nowhere and loop forever looking for a top. */
  function isRoot(id) {
    var p = parentOf(id);
    if (!p) return true;
    var seen = Object.create(null);
    seen[id] = true;
    while (p) {
      if (seen[p]) return true;
      seen[p] = true;
      p = parentOf(p);
    }
    return false;
  }

  var IN_CYCLE = Object.create(null);
  ORDER.forEach(function (id) {
    if (parentOf(id) && isRoot(id)) IN_CYCLE[id] = true;
  });

  /* Every descendant, once, cycle-safe. */
  function subtree(id) {
    var out = [];
    var seen = Object.create(null);
    seen[id] = true;
    var queue = (KIDS[id] || []).slice();
    while (queue.length) {
      var next = queue.shift();
      if (seen[next]) continue;
      seen[next] = true;
      out.push(next);
      (KIDS[next] || []).forEach(function (kid) {
        if (!seen[kid]) queue.push(kid);
      });
    }
    return out;
  }

  var SUBTREE = Object.create(null);
  ORDER.forEach(function (id) {
    SUBTREE[id] = subtree(id);
  });

  /* ------------------------------------------------------------ state */

  var state = {
    expanded: Object.create(null), // card id -> true
    staged: Object.create(null), // card id -> target column id
    query: "",
    rowMemory: Object.create(null), // column id -> row key
    focusKey: null,
  };

  function columnOf(id) {
    return state.staged[id] || HOME[id];
  }

  function columnTitle(colId) {
    var index = COLUMN_AT[colId];
    return index === undefined ? colId : COLUMNS[index].title;
  }

  /* ----------------------------------------------------------- filter */

  function matches(id) {
    if (!state.query) return true;
    var card = CARD[id];
    return (
      (card.title || "").toLowerCase().indexOf(state.query) >= 0 ||
      id.toLowerCase().indexOf(state.query) >= 0
    );
  }

  /* Context, not promotion: a card survives if it matches or if anything
     under it matches. A match never climbs out of its parent, because
     climbing would move a card, and this variant never moves a card. */
  function subtreeMatches(id) {
    if (!state.query) return true;
    if (matches(id)) return true;
    var list = SUBTREE[id] || [];
    for (var i = 0; i < list.length; i++) {
      if (matches(list[i])) return true;
    }
    return false;
  }

  function matchCount(id) {
    var list = SUBTREE[id] || [];
    var n = 0;
    for (var i = 0; i < list.length; i++) {
      if (matches(list[i])) n++;
    }
    return n;
  }

  /* -------------------------------------------------------- utilities */

  function esc(value) {
    return String(value === undefined || value === null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function el(html) {
    var host = document.createElement("div");
    host.innerHTML = html.trim();
    return host.firstElementChild;
  }

  var GLYPH = {
    chevronRight: "m6 4 4 4-4 4",
    chevronDown: "m4 6 4 4 4-4",
    priority: "m4 8.5 4-4 4 4M4 13l4-4 4 4",
    branch: "M4 3v6.5A2.5 2.5 0 0 0 6.5 12H12",
    arrow: "M3 8h9m-3.5-3.5L12 8l-3.5 3.5",
  };

  function glyph(d, cls) {
    return (
      '<svg viewBox="0 0 16 16" class="glyph ' +
      (cls || "") +
      '" aria-hidden="true"><path d="' +
      d +
      '" /></svg>'
    );
  }

  function say(message) {
    var live = document.getElementById("live");
    if (live) live.textContent = message;
  }

  /* ------------------------------------------------------ open / shut */

  /* While a filter is on, a parent holding a match opens itself, because a
     match you cannot see is not a match. An explicit toggle during a
     filter overrides that, and the override dies with the query. */
  var override = Object.create(null);

  function isOpen(id) {
    if (!(KIDS[id] || []).length) return false;
    if (state.query) {
      if (id in override) return override[id];
      return matchCount(id) > 0;
    }
    return !!state.expanded[id];
  }

  function setOpen(id, open) {
    if (state.query) override[id] = open;
    else if (open) state.expanded[id] = true;
    else delete state.expanded[id];
  }

  /* --------------------------------------------------------- markup */

  function progressHTML(id) {
    var list = SUBTREE[id] || [];
    var counts = COLUMNS.map(function () {
      return 0;
    });
    var done = 0;
    list.forEach(function (kid) {
      var index = COLUMN_AT[columnOf(kid)];
      if (index !== undefined) counts[index]++;
      if (columnOf(kid) === LAST_COLUMN) done++;
    });
    var total = list.length || 1;
    var bars = counts
      .map(function (n, index) {
        if (!n) return "";
        return (
          '<i data-stage="' +
          index +
          '" style="width:' +
          ((n / total) * 100).toFixed(3) +
          '%"></i>'
        );
      })
      .join("");
    return {
      bar: '<span class="bar" aria-hidden="true">' + bars + "</span>",
      done: done,
      total: list.length,
    };
  }

  function discloseHTML(id) {
    var kids = KIDS[id] || [];
    if (!kids.length) return "";
    var open = isOpen(id);
    var progress = progressHTML(id);
    var label;
    if (state.query) {
      label =
        '<span class="label"><span class="n">' +
        matchCount(id) +
        "</span> of " +
        progress.total +
        " subtask" +
        (progress.total === 1 ? "" : "s") +
        " match</span>";
    } else {
      label =
        '<span class="label"><span class="n">' +
        progress.total +
        "</span> subtask" +
        (progress.total === 1 ? "" : "s") +
        "</span>";
    }
    return (
      '<button type="button" class="disclose" data-toggle="' +
      esc(id) +
      '" aria-expanded="' +
      (open ? "true" : "false") +
      '" tabindex="-1">' +
      '<span class="tw">' +
      glyph(GLYPH.chevronRight) +
      "</span>" +
      label +
      '<span class="done">' +
      progress.done +
      "/" +
      progress.total +
      " done</span>" +
      progress.bar +
      "</button>"
    );
  }

  /* A sub-row is a reference to a card, never the card itself. It carries
     the column its card is in; when that is not the column you are
     reading, it is drawn as a ghost and says so in words. */
  function kidRows(parentId, colId, path, depth, out) {
    (KIDS[parentId] || []).forEach(function (kid) {
      if (!subtreeMatches(kid)) return;

      var key = colId + "|" + path.concat(kid).join(">");
      var here = columnOf(kid) === colId;
      var open = isOpen(kid);
      var hasKids = (KIDS[kid] || []).length > 0;
      var flags =
        (here ? " data-here" : " data-elsewhere") +
        (state.query && !matches(kid) ? " data-context" : "") +
        (state.staged[kid] ? " data-staged" : "");

      /* The cycle stop: a -> b -> a renders one marked row and ends. */
      if (path.indexOf(kid) >= 0) {
        out.push(
          '<li class="kid" style="--depth:' +
            depth +
            '"><div class="kid-row"><span class="kid-tw is-leaf"></span>' +
            '<span class="kid-open">' +
            esc(CARD[kid].title) +
            '</span><span class="kid-cycle">cycle</span></div></li>'
        );
        return;
      }

      out.push(
        '<li class="kid" style="--depth:' +
          depth +
          '" data-kid="' +
          esc(kid) +
          '"' +
          flags +
          ">" +
          '<div class="kid-row" tabindex="-1" data-row="' +
          esc(key) +
          '" data-card="' +
          esc(kid) +
          '"' +
          (hasKids ? ' aria-expanded="' + (open ? "true" : "false") + '"' : "") +
          ">" +
          (hasKids
            ? '<button type="button" class="kid-tw" data-toggle="' +
              esc(kid) +
              '" aria-expanded="' +
              (open ? "true" : "false") +
              '" aria-label="' +
              (open ? "Collapse " : "Expand ") +
              esc(CARD[kid].title) +
              '" tabindex="-1">' +
              glyph(GLYPH.chevronRight) +
              "</button>"
            : '<span class="kid-tw is-leaf"></span>') +
          '<button type="button" class="kid-open" data-goto="' +
          esc(kid) +
          '" tabindex="-1">' +
          esc(CARD[kid].title) +
          "</button>" +
          '<span class="kid-chip">' +
          (here ? "" : glyph(GLYPH.arrow)) +
          esc(columnTitle(columnOf(kid))) +
          (here ? "" : '<span class="sr-only">, in another column</span>') +
          "</span>" +
          "</div>" +
          "</li>"
      );

      if (open) kidRows(kid, colId, path.concat(kid), depth + 1, out);
    });
  }

  function cardHTML(id, colId) {
    var card = CARD[id];
    var key = colId + "|" + id;
    var parent = parentOf(id);
    var kids = KIDS[id] || [];
    var open = isOpen(id);

    var keyLine = [card.type, card.milestone].filter(Boolean).join(" · ");
    var meta = "";
    if (card.priority === "high" || (card.assignee || []).length || card.size) {
      meta =
        '<p class="card-meta">' +
        (card.priority === "high"
          ? glyph(GLYPH.priority, "prio") +
            '<span class="sr-only">High priority</span>'
          : "") +
        (card.assignee || [])
          .map(function (name) {
            return "<span>@" + esc(name) + "</span>";
          })
          .join("") +
        (card.size
          ? '<span class="size">' +
            esc(card.size) +
            '<span class="sr-only"> size</span></span>'
          : "") +
        "</p>";
    }

    var foot = "";
    if (parent || kids.length) {
      foot =
        '<div class="card-foot">' +
        (parent
          ? '<button type="button" class="card-under" data-goto="' +
            esc(parent) +
            '" tabindex="-1">' +
            glyph(GLYPH.branch) +
            "under <span class=\"name\">" +
            esc(CARD[parent].title) +
            "</span></button>"
          : "") +
        discloseHTML(id) +
        "</div>";
    }

    var kidsList = "";
    if (kids.length && open) {
      var rows = [];
      kidRows(id, colId, [id], 1, rows);
      kidsList = '<ul class="kids">' + rows.join("") + "</ul>";
    }

    var staged = state.staged[id];

    return (
      '<article class="card" role="listitem" data-card="' +
      esc(id) +
      '" data-row="' +
      esc(key) +
      '" tabindex="-1"' +
      (kids.length ? ' aria-expanded="' + (open ? "true" : "false") + '"' : "") +
      (staged ? " data-staged" : "") +
      (state.query && !matches(id) ? " data-context" : "") +
      (IN_CYCLE[id] ? " data-cycle" : "") +
      ">" +
      (card.priority === "high" || staged
        ? '<span class="card-edge" aria-hidden="true"></span>'
        : "") +
      '<button type="button" class="card-move" data-move="' +
      esc(id) +
      '" aria-haspopup="listbox" aria-label="Move ' +
      esc(card.title) +
      ' to another column" tabindex="-1">' +
      glyph(GLYPH.chevronDown) +
      "</button>" +
      (keyLine ? '<span class="card-key">' + esc(keyLine) + "</span>" : "") +
      '<h3 class="card-title">' +
      esc(card.title) +
      "</h3>" +
      meta +
      (staged
        ? '<p class="card-staged">staged<span class="from"> · from ' +
          esc(columnTitle(HOME[id])) +
          "</span></p>"
        : "") +
      (IN_CYCLE[id]
        ? '<p class="card-loop">parent loop · read as a root</p>'
        : "") +
      foot +
      kidsList +
      "</article>"
    );
  }

  function columnHTML(column) {
    var ids = ORDER.filter(function (id) {
      return columnOf(id) === column.id && subtreeMatches(id);
    });
    var over = column.limit !== null && ids.length > column.limit;
    var count =
      state.query || column.limit === null
        ? String(ids.length)
        : ids.length + "/" + column.limit;

    return (
      '<section class="col" aria-labelledby="col-' +
      esc(column.id) +
      '">' +
      '<div class="col-head">' +
      '<h2 id="col-' +
      esc(column.id) +
      '" aria-label="' +
      esc(column.title) +
      '">' +
      esc(column.title) +
      "</h2>" +
      '<span class="col-count"' +
      (over && !state.query ? " data-over" : "") +
      ">" +
      count +
      (over && !state.query
        ? '<span class="sr-only"> cards, over the limit</span>'
        : "") +
      "</span>" +
      "</div>" +
      (ids.length
        ? '<div class="col-list" role="list" data-column="' +
          esc(column.id) +
          '">' +
          ids
            .map(function (id) {
              return cardHTML(id, column.id);
            })
            .join("") +
          "</div>"
        : '<p class="col-empty">' +
          (state.query ? "no matches" : "no cards") +
          "</p>") +
      "</section>"
    );
  }

  var boardEl = document.getElementById("board");

  function render() {
    boardEl.innerHTML = COLUMNS.map(columnHTML).join("");
    rovingTabindex();
    restoreFocus();
    paintCounts();
  }

  /* ------------------------------------------------- focus and re-render */

  function columnEls() {
    return Array.prototype.slice.call(boardEl.querySelectorAll(".col"));
  }

  function rowsIn(colEl) {
    return Array.prototype.slice.call(colEl.querySelectorAll("[data-row]"));
  }

  /* One tab stop per column: Tab crosses the board, the arrow keys walk a
     column. 35 cards plus their sub-rows is not a tab sequence anyone
     wants to sit through. */
  function rovingTabindex() {
    columnEls().forEach(function (colEl) {
      var rows = rowsIn(colEl);
      if (!rows.length) return;
      var list = colEl.querySelector(".col-list");
      var wanted = list && state.rowMemory[list.getAttribute("data-column")];
      var chosen =
        rows.filter(function (row) {
          return row.getAttribute("data-row") === wanted;
        })[0] || rows[0];
      rows.forEach(function (row) {
        row.tabIndex = row === chosen ? 0 : -1;
      });
    });
  }

  /* The single tab stop moves with you. Promoting a row without demoting
     the one that held the stop leaves both tabbable, and after a few
     arrow presses a column has as many tab stops as rows you visited —
     which is the sequence the roving index exists to avoid. */
  function promote(row) {
    var colEl = row.closest(".col");
    if (colEl) {
      rowsIn(colEl).forEach(function (other) {
        other.tabIndex = other === row ? 0 : -1;
      });
    } else {
      row.tabIndex = 0;
    }
  }

  function restoreFocus() {
    if (!state.wantFocus || !state.focusKey) return;
    var row = boardEl.querySelector('[data-row="' + state.focusKey + '"]');
    if (!row) {
      state.wantFocus = false;
      return;
    }
    var target = row;
    if (state.focusInner) {
      var inner = row.querySelector("." + state.focusInner);
      if (inner) target = inner;
    }
    promote(row);
    target.focus({ preventScroll: true });
    state.wantFocus = false;
  }

  function rerender() {
    var active = document.activeElement;
    var inside = active && boardEl.contains(active);
    state.wantFocus = !!inside;
    state.focusInner = null;
    state.focusKey = null;
    if (inside) {
      var row = active.closest("[data-row]");
      if (row) {
        state.focusKey = row.getAttribute("data-row");
        ["kid-tw", "disclose", "card-move", "kid-open", "card-under"].forEach(
          function (cls) {
            if (active.classList.contains(cls)) state.focusInner = cls;
          }
        );
      }
    }
    render();
  }

  function remember(row) {
    var colEl = row.closest(".col");
    var list = colEl && colEl.querySelector(".col-list");
    if (list) state.rowMemory[list.getAttribute("data-column")] =
      row.getAttribute("data-row");
  }

  /* ------------------------------------------------------------ counts */

  function paintCounts() {
    var total = ORDER.length;
    var shown = ORDER.filter(subtreeMatches).length;
    var qCount = document.getElementById("q-count");
    qCount.textContent = state.query ? shown + "/" + total : "";
    /* The bare fraction counts survivors, matches plus the parents kept
       as context. Say so rather than leave it to be inferred. */
    if (state.query) {
      qCount.title =
        shown + " of " + total + " cards shown: matches and their parents";
    } else {
      qCount.removeAttribute("title");
    }

    var staged = Object.keys(state.staged);
    var button = document.getElementById("staged");
    document.getElementById("staged-n").textContent = String(staged.length);
    button.disabled = staged.length === 0;
    if (staged.length) button.setAttribute("data-live", "");
    else button.removeAttribute("data-live");
  }

  /* ------------------------------------------------- going to a card */

  var flashTimer = null;

  function goTo(id) {
    var card = boardEl.querySelector('article.card[data-card="' + id + '"]');
    if (!card) {
      say(CARD[id] ? CARD[id].title + " is filtered out." : "Card not found.");
      return;
    }
    card.scrollIntoView({ behavior: "smooth", block: "center" });
    promote(card);
    card.focus({ preventScroll: true });
    remember(card);
    card.removeAttribute("data-hit");
    void card.offsetWidth;
    card.setAttribute("data-hit", "");
    if (flashTimer) clearTimeout(flashTimer);
    flashTimer = setTimeout(function () {
      card.removeAttribute("data-hit");
    }, 1200);
    say(CARD[id].title + ", in " + columnTitle(columnOf(id)) + ".");
  }

  /* --------------------------------------------------------- staging */

  function stage(id, colId) {
    if (colId === HOME[id]) delete state.staged[id];
    else state.staged[id] = colId;
    rerender();
    /* The card just changed column, so the row that had focus is gone from
       where it was. Following it is also the answer to "where did it go". */
    var card = boardEl.querySelector('article.card[data-card="' + id + '"]');
    if (card) {
      promote(card);
      card.focus();
      remember(card);
    }
    say(
      CARD[id].title +
        (state.staged[id]
          ? " staged for " + columnTitle(colId) + "."
          : " returned to " + columnTitle(colId) + ", no longer staged.")
    );
  }

  function stagedCommands() {
    return ORDER.filter(function (id) {
      return state.staged[id];
    })
      .map(function (id) {
        return "folio kanban move " + id + " " + state.staged[id];
      })
      .join("\n");
  }

  /* ------------------------------------------------------- move menu */

  var menu = null;

  function closeMenu(refocus) {
    if (!menu) return;
    var owner = menu.owner;
    menu.el.remove();
    menu = null;
    document.removeEventListener("mousedown", onDocDown, true);
    if (refocus && owner && document.contains(owner)) owner.focus();
  }

  function onDocDown(event) {
    if (menu && !menu.el.contains(event.target)) closeMenu(false);
  }

  function openMenu(id, anchor) {
    closeMenu(false);
    var current = columnOf(id);
    var active = COLUMN_AT[current] || 0;

    var html =
      '<div class="menu" role="dialog" aria-label="Move to">' +
      '<p class="menu-label">Move to</p>' +
      '<ul role="listbox" tabindex="-1" aria-label="Move to">' +
      COLUMNS.map(function (column, index) {
        var count = ORDER.filter(function (other) {
          return columnOf(other) === column.id;
        }).length;
        var over = column.limit !== null && count > column.limit;
        return (
          '<li role="option" data-pick="' +
          esc(column.id) +
          '" aria-selected="' +
          (column.id === current ? "true" : "false") +
          '"' +
          (index === active ? " data-active" : "") +
          '><span class="left"><span class="mark"></span>' +
          esc(column.title) +
          "</span>" +
          '<span class="n"' +
          (over ? " data-over" : "") +
          ">" +
          (column.limit === null ? count : count + "/" + column.limit) +
          "</span></li>"
        );
      }).join("") +
      "</ul></div>";

    var node = el(html);
    document.body.appendChild(node);
    var rect = anchor.getBoundingClientRect();
    var width = node.offsetWidth;
    var left = Math.min(
      rect.right + window.scrollX - width,
      window.scrollX + document.documentElement.clientWidth - width - 8
    );
    node.style.left = Math.max(8, left) + "px";
    node.style.top = rect.bottom + window.scrollY + 4 + "px";

    menu = { el: node, owner: anchor, id: id, active: active };
    document.addEventListener("mousedown", onDocDown, true);
    node.querySelector("ul").focus();
  }

  function menuMove(delta) {
    if (!menu) return;
    var items = menu.el.querySelectorAll("li");
    menu.active = (menu.active + delta + items.length) % items.length;
    Array.prototype.forEach.call(items, function (item, index) {
      if (index === menu.active) item.setAttribute("data-active", "");
      else item.removeAttribute("data-active");
    });
  }

  document.addEventListener("keydown", function (event) {
    if (!menu) return;
    if (event.key === "Escape") {
      event.preventDefault();
      closeMenu(true);
    } else if (event.key === "ArrowDown") {
      event.preventDefault();
      menuMove(1);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      menuMove(-1);
    } else if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      var pick = menu.el.querySelectorAll("li")[menu.active];
      var id = menu.id;
      closeMenu(false);
      stage(id, pick.getAttribute("data-pick"));
    }
  });

  document.addEventListener("click", function (event) {
    if (!menu) return;
    var option = event.target.closest("li[data-pick]");
    if (!option || !menu.el.contains(option)) return;
    var id = menu.id;
    closeMenu(false);
    stage(id, option.getAttribute("data-pick"));
  });

  document.addEventListener("mouseover", function (event) {
    if (!menu) return;
    var option = event.target.closest("li[data-pick]");
    if (!option || !menu.el.contains(option)) return;
    var items = Array.prototype.slice.call(menu.el.querySelectorAll("li"));
    menu.active = items.indexOf(option);
    menuMove(0);
  });

  /* ---------------------------------------------------- board events */

  boardEl.addEventListener("click", function (event) {
    var toggle = event.target.closest("[data-toggle]");
    if (toggle && boardEl.contains(toggle)) {
      var id = toggle.getAttribute("data-toggle");
      var open = !isOpen(id);
      setOpen(id, open);
      rerender();
      say(
        (open ? "Expanded " : "Collapsed ") +
          CARD[id].title +
          ", " +
          (SUBTREE[id] || []).length +
          " subtasks."
      );
      return;
    }
    var link = event.target.closest("[data-goto]");
    if (link && boardEl.contains(link)) {
      goTo(link.getAttribute("data-goto"));
      return;
    }
    var move = event.target.closest("[data-move]");
    if (move && boardEl.contains(move)) {
      openMenu(move.getAttribute("data-move"), move);
    }
  });

  boardEl.addEventListener("focusin", function (event) {
    var row = event.target.closest("[data-row]");
    if (row) remember(row);
  });

  function focusRow(row) {
    if (!row) return;
    promote(row);
    row.focus();
    remember(row);
  }

  function step(row, delta) {
    var colEl = row.closest(".col");
    var rows = rowsIn(colEl);
    var index = rows.indexOf(row);
    var next = rows[index + delta];
    if (next) focusRow(next);
  }

  function crossColumn(row, delta) {
    var cols = columnEls();
    var colEl = row.closest(".col");
    var from = cols.indexOf(colEl);
    var offset = rowsIn(colEl).indexOf(row);
    for (var i = from + delta; i >= 0 && i < cols.length; i += delta) {
      var rows = rowsIn(cols[i]);
      if (rows.length) {
        focusRow(rows[Math.min(offset, rows.length - 1)]);
        return;
      }
    }
  }

  function expandable(row) {
    var id = row.getAttribute("data-card");
    return id && (KIDS[id] || []).length > 0;
  }

  boardEl.addEventListener("keydown", function (event) {
    var row = event.target.closest("[data-row]");
    if (!row) return;
    var id = row.getAttribute("data-card");
    var key = event.key;

    if (key === "ArrowDown") {
      event.preventDefault();
      step(row, 1);
    } else if (key === "ArrowUp") {
      event.preventDefault();
      step(row, -1);
    } else if (key === "Home") {
      event.preventDefault();
      focusRow(rowsIn(row.closest(".col"))[0]);
    } else if (key === "End") {
      event.preventDefault();
      var all = rowsIn(row.closest(".col"));
      focusRow(all[all.length - 1]);
    } else if (key === "ArrowRight") {
      event.preventDefault();
      if (expandable(row) && !isOpen(id)) {
        setOpen(id, true);
        rerender();
        say("Expanded " + CARD[id].title + ".");
      } else if (expandable(row)) {
        step(row, 1);
      } else {
        crossColumn(row, 1);
      }
    } else if (key === "ArrowLeft") {
      event.preventDefault();
      if (expandable(row) && isOpen(id)) {
        setOpen(id, false);
        rerender();
        say("Collapsed " + CARD[id].title + ".");
      } else if (row.classList.contains("kid-row")) {
        /* Out of a sub-row is up to the row that owns it: one segment off
           the row key, which is the path that got us here. */
        var path = row.getAttribute("data-row").split("|");
        var chain = path[1].split(">");
        chain.pop();
        var up = boardEl.querySelector(
          '[data-row="' + path[0] + "|" + chain.join(">") + '"]'
        );
        if (up) focusRow(up);
      } else {
        crossColumn(row, -1);
      }
    } else if (key === "Enter" || key === " ") {
      if (event.target !== row) return;
      event.preventDefault();
      if (row.classList.contains("kid-row")) {
        goTo(id);
      } else if (expandable(row)) {
        setOpen(id, !isOpen(id));
        rerender();
      }
    } else if (key === "m" || key === "M") {
      if (!id) return;
      event.preventDefault();
      var anchor = row.querySelector(".card-move") || row;
      openMenu(id, anchor);
    } else if (key === "u" || key === "U") {
      /* The `under <parent>` line is the mirror half of the expansion, so
         it needs a key: every other way to it is a mouse. */
      if (!id) return;
      event.preventDefault();
      var up = parentOf(id);
      if (up) goTo(up);
      else say(CARD[id].title + " has no parent.");
    }
  });

  /* -------------------------------------------------------- toolbar */

  var input = document.getElementById("q");

  input.addEventListener("input", function () {
    var next = input.value.trim().toLowerCase();
    if (next === state.query) return;
    state.query = next;
    override = Object.create(null);
    render();
  });

  input.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && input.value) {
      event.preventDefault();
      input.value = "";
      state.query = "";
      override = Object.create(null);
      render();
    }
  });

  document.getElementById("expand-all").addEventListener("click", function () {
    ORDER.forEach(function (id) {
      if ((KIDS[id] || []).length) setOpen(id, true);
    });
    rerender();
    say("All parents expanded.");
  });

  document
    .getElementById("collapse-all")
    .addEventListener("click", function () {
      ORDER.forEach(function (id) {
        if ((KIDS[id] || []).length) setOpen(id, false);
      });
      rerender();
      say("All parents collapsed.");
    });

  /* ---------------------------------------------------------- sheet */

  var sheet = document.getElementById("sheet");
  var sheetCode = document.getElementById("sheet-code");
  var sheetOpener = null;

  function openSheet() {
    sheetCode.textContent = stagedCommands() || "# nothing staged";
    sheet.hidden = false;
    sheetOpener = document.activeElement;
    document.getElementById("sheet-close").focus();
  }

  function closeSheet() {
    sheet.hidden = true;
    if (sheetOpener && document.contains(sheetOpener)) sheetOpener.focus();
  }

  document.getElementById("staged").addEventListener("click", openSheet);
  document.getElementById("sheet-close").addEventListener("click", closeSheet);
  sheet.addEventListener("click", function (event) {
    if (event.target === sheet) closeSheet();
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && !sheet.hidden) closeSheet();
  });

  document.getElementById("sheet-copy").addEventListener("click", function () {
    var text = stagedCommands();
    var button = document.getElementById("sheet-copy");
    var done = function () {
      button.textContent = "Copied";
      setTimeout(function () {
        button.textContent = "Copy";
      }, 1400);
    };
    /* file:// blocks the async clipboard in some browsers, so the old
       selection path is the fallback, not an afterthought. */
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done, function () {
        legacyCopy(text, done);
      });
    } else {
      legacyCopy(text, done);
    }
  });

  function legacyCopy(text, done) {
    var area = document.createElement("textarea");
    area.value = text;
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    try {
      document.execCommand("copy");
      done();
    } catch (error) {
      /* nothing to do: the text is on screen and selectable. */
    }
    area.remove();
  }

  document.getElementById("sheet-clear").addEventListener("click", function () {
    state.staged = Object.create(null);
    closeSheet();
    render();
    say("Staged moves cleared.");
  });

  /* ---------------------------------------------------------- theme */

  var themeButton = document.getElementById("theme");

  function effectiveTheme() {
    var set = document.documentElement.getAttribute("data-theme");
    if (set === "dark" || set === "light") return set;
    return window.matchMedia &&
      window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  }

  function paintTheme() {
    themeButton.textContent = effectiveTheme() === "dark" ? "Light" : "Dark";
  }

  themeButton.addEventListener("click", function () {
    document.documentElement.setAttribute(
      "data-theme",
      effectiveTheme() === "dark" ? "light" : "dark"
    );
    paintTheme();
  });

  /* ----------------------------------------------------------- boot */

  /* A handle for poking at the prototype from a console — it is a
     prototype, and the tree walks above are the part worth interrogating. */
  window.__inline = {
    state: state,
    kids: KIDS,
    subtree: SUBTREE,
    columnOf: columnOf,
    isOpen: isOpen,
    setOpen: setOpen,
    render: render,
    stage: stage,
    commands: stagedCommands,
    setQuery: function (value) {
      state.query = String(value || "")
        .trim()
        .toLowerCase();
      override = Object.create(null);
      render();
    },
  };

  document.getElementById("board-title").textContent =
    BOARD.title || "Development board";
  paintTheme();
  render();
})();
