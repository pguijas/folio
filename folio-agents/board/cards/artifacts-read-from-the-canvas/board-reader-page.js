/* Board reader page — Folio kanban prototype.
   Vanilla, file:// safe. window.BOARD comes from board-data.js and
   window.READER from reader-data.js.

   The route model: the hash simulates /kanban/<card>/<artifact>.
     #/kanban              the board
     #/kanban/<card>       the board with the card dialog open
     #/kanban/<card>/<art> the artifact page (this variant's subject)
   ?q=<filter> rides along on every level. Opening a level is a pushState,
   walking the artifact band is a replaceState, so Back always unwinds one
   level and never replays a reading session. history.state.d counts in-app
   pushes: when it is 0 (deep link, manual hash edit) Esc navigates directly
   instead of calling history.back() out of the app. */
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
  var colOf = {};

  columns.forEach(function (col) {
    (col.cards || []).forEach(function (card) {
      cards.push(card);
      byId[card.id] = card;
      colOf[card.id] = col;
    });
  });

  function fileName(target) {
    return String(target || "").split("/").pop();
  }
  function stemOf(target) {
    return fileName(target).replace(/\.[^.]+$/, "");
  }

  /* per-card artifact list with a stable slug each — the last URL segment.
     Stems first; a collision falls back to the file name, then the index. */
  var artsOf = {};
  var artBySlug = {};

  cards.forEach(function (card) {
    var list = (card.artifacts || []).map(function (a, i) {
      var entry = READER[a.target] || null;
      return {
        index: i,
        kind: a.kind || "file",
        target: a.target,
        label: a.label || "",
        entry: entry,
        openable: !!entry,
        slug: ""
      };
    });
    var taken = {};
    list.forEach(function (a) {
      var candidates = [
        a.kind === "pr" ? "pr-" + a.target : stemOf(a.target),
        fileName(a.target),
        String(a.index)
      ];
      for (var i = 0; i < candidates.length; i++) {
        var c = candidates[i];
        if (c && !taken[c]) { a.slug = c; break; }
      }
      taken[a.slug] = true;
    });
    artsOf[card.id] = list;
    var map = {};
    list.forEach(function (a) { map[a.slug] = a; });
    artBySlug[card.id] = map;
  });

  /* ------------------------------------------------------------------ *
   * helpers
   * ------------------------------------------------------------------ */

  function el(sel) { return document.querySelector(sel); }
  function els(sel) { return Array.prototype.slice.call(document.querySelectorAll(sel)); }

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function announce(msg) {
    el("#live").textContent = msg;
  }

  function safeFocus(node) {
    if (!node) return;
    try { node.focus({ preventScroll: true }); } catch (e) { node.focus(); }
  }

  /* markdown-lite for card descriptions: paragraphs, lists, **bold**,
     `code`. Code spans are held aside so literal asterisks inside them
     survive — these cards talk about markdown. */
  function inlineMd(s) {
    var held = [];
    function hold(inner) {
      held.push(inner);
      return "\u0001" + (held.length - 1) + "\u0001";
    }
    var t = esc(s)
      .replace(/``([\s\S]+?)``/g, function (m, inner) { return hold(inner.replace(/^ | $/g, "")); })
      .replace(/`([^`]+)`/g, function (m, inner) { return hold(inner); })
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    return t.replace(/\u0001(\d+)\u0001/g, function (m, i) {
      return "<code>" + held[Number(i)] + "</code>";
    });
  }

  function renderMd(src) {
    if (!src) return "";
    return String(src).split(/\n{2,}/).map(function (b) {
      var lines = b.split("\n");
      var isList = lines.every(function (l) { return /^\s*[-*]\s+/.test(l) || /^\s*$/.test(l); }) &&
        lines.some(function (l) { return /^\s*[-*]\s+/.test(l); });
      if (isList) {
        return "<ul>" + lines.filter(function (l) { return /\S/.test(l); }).map(function (l) {
          return "<li>" + inlineMd(l.replace(/^\s*[-*]\s+/, "")) + "</li>";
        }).join("") + "</ul>";
      }
      return "<p>" + inlineMd(b.replace(/\n/g, " ")) + "</p>";
    }).join("");
  }

  function markQuery(text) {
    var safe = esc(text);
    if (!state.q) return safe;
    var lower = safe.toLowerCase();
    var needle = esc(state.q).toLowerCase();
    var i = lower.indexOf(needle);
    if (i < 0) return safe;
    return safe.slice(0, i) + "<mark>" + safe.slice(i, i + needle.length) + "</mark>" +
      safe.slice(i + needle.length);
  }

  function displayTarget(a) {
    return a.kind === "pr" ? "#" + a.target : a.target;
  }
  function displayLabel(a) {
    if (a.label) return a.label;
    if (a.kind === "pr") return "Pull request #" + a.target;
    return fileName(a.target) || a.target;
  }

  /* ------------------------------------------------------------------ *
   * route: state <-> hash
   * ------------------------------------------------------------------ */

  var state = { card: null, art: null, q: "" };
  var appliedHash = null;   /* last hash this script rendered, to dedupe events */

  function formatHash(s) {
    var h = "#/kanban";
    if (s.card) h += "/" + encodeURIComponent(s.card);
    if (s.card && s.art) h += "/" + encodeURIComponent(s.art);
    if (s.q) h += "?q=" + encodeURIComponent(s.q);
    return h;
  }

  function parseHash(hash) {
    var s = { card: null, art: null, q: "" };
    var h = String(hash || "").replace(/^#\/?/, "");
    var qi = h.indexOf("?");
    if (qi >= 0) {
      var query = h.slice(qi + 1);
      h = h.slice(0, qi);
      query.split("&").forEach(function (pair) {
        var kv = pair.split("=");
        if (kv[0] === "q") { try { s.q = decodeURIComponent(kv.slice(1).join("=") || ""); } catch (e) { s.q = ""; } }
      });
    }
    var segs = h.split("/").filter(Boolean).map(function (seg) {
      try { return decodeURIComponent(seg); } catch (e) { return seg; }
    });
    if (segs[0] === "kanban") segs.shift();
    if (segs[0]) s.card = segs[0];
    if (segs[1]) s.art = segs[1];
    return s;
  }

  /* an invalid card falls back to the board; a closed or unknown artifact
     falls back to the card dialog — never a dead page */
  function sanitize(s) {
    var out = { card: s.card, art: s.art, q: (s.q || "").trim() };
    if (out.card && !byId[out.card]) { out.card = null; out.art = null; }
    if (out.art) {
      var a = out.card ? artBySlug[out.card][out.art] : null;
      if (!a || !a.openable) out.art = null;
    }
    return out;
  }

  function levelOf(s) { return s.art ? 2 : (s.card ? 1 : 0); }

  function inAppDepth() {
    return (history.state && typeof history.state.d === "number") ? history.state.d : 0;
  }

  /* ------------------------------------------------------------------ *
   * theme — Auto / Light / Dark, two synced groups
   * ------------------------------------------------------------------ */

  function wireTheme() {
    function setTheme(v) {
      document.documentElement.setAttribute("data-theme", v);
      els(".theme button").forEach(function (b) {
        b.setAttribute("aria-pressed", String(b.getAttribute("data-theme-set") === v));
      });
    }
    document.addEventListener("click", function (e) {
      var btn = e.target.closest && e.target.closest("[data-theme-set]");
      if (btn) setTheme(btn.getAttribute("data-theme-set"));
    });
  }

  /* ------------------------------------------------------------------ *
   * the board: columns, faces, filter, roving tab stop
   * ------------------------------------------------------------------ */

  var visByCol = [];      /* [[cardId, …] per column] — the arrow-key grid */
  var activeCardId = null;  /* the single tab stop on the canvas */

  function cardMatches(card) {
    if (!state.q) return true;
    var q = state.q.toLowerCase();
    if (card.title.toLowerCase().indexOf(q) >= 0) return true;
    if (card.id.toLowerCase().indexOf(q) >= 0) return true;
    return (card.tags || []).some(function (t) { return t.toLowerCase().indexOf(q) >= 0; });
  }

  function faceHtml(card) {
    var arts = artsOf[card.id];
    var nOpen = arts.filter(function (a) { return a.openable; }).length;
    var tags = (card.tags || []).slice(0, 2).map(function (t) {
      return '<span class="face-tag">' + markQuery(t) + "</span>";
    }).join("");
    var chip = arts.length
      ? '<span class="face-arts" data-open="' + (nOpen ? "1" : "0") + '">' +
        arts.length + " artifact" + (arts.length === 1 ? "" : "s") + "</span>"
      : "";
    return '<li><button type="button" class="face" tabindex="-1" data-card="' + esc(card.id) + '"' +
      (card.priority === "high" ? ' data-priority="high"' : "") + ">" +
      '<span class="face-title">' + markQuery(card.title) + "</span>" +
      (tags || chip ? '<span class="face-foot">' + tags + chip + "</span>" : "") +
      "</button></li>";
  }

  function renderBoard() {
    visByCol = [];
    var shown = 0;
    var html = columns.map(function (col) {
      var vis = (col.cards || []).filter(cardMatches);
      visByCol.push(vis.map(function (c) { return c.id; }));
      shown += vis.length;
      var over = col.limit != null && (col.cards || []).length > col.limit;
      var n = state.q
        ? vis.length + "/" + (col.cards || []).length
        : String((col.cards || []).length);
      var lim = col.limit != null ? ' <span class="lim">· limit ' + col.limit + "</span>" : "";
      return '<li class="col"' + (over ? ' data-over="1"' : "") + ">" +
        '<div class="col-head"><h2>' + esc(col.title) + "</h2>" +
        '<span class="col-n">' + n + lim + "</span></div>" +
        (vis.length
          ? '<ol class="col-cards">' + vis.map(faceHtml).join("") + "</ol>"
          : '<p class="col-empty">' + (state.q ? "no match" : "empty") + "</p>") +
        "</li>";
    }).join("");
    el("#columns").innerHTML = html;

    el("#matchcount").innerHTML = state.q
      ? "<b>" + shown + "</b> of " + cards.length + " match"
      : cards.length + " cards";

    /* exactly one tab stop on the canvas, always on a visible face */
    var flat = [];
    visByCol.forEach(function (ids) { flat = flat.concat(ids); });
    if (flat.indexOf(activeCardId) < 0) activeCardId = flat[0] || null;
    if (activeCardId) {
      var btn = faceEl(activeCardId);
      if (btn) btn.setAttribute("tabindex", "0");
    }
  }

  function faceEl(id) {
    return document.querySelector('.face[data-card="' + String(id).replace(/"/g, '\\"') + '"]');
  }

  function setActiveFace(id, focus) {
    if (activeCardId && activeCardId !== id) {
      var prev = faceEl(activeCardId);
      if (prev) prev.setAttribute("tabindex", "-1");
    }
    activeCardId = id;
    var btn = faceEl(id);
    if (btn) {
      btn.setAttribute("tabindex", "0");
      if (focus) safeFocus(btn);
    }
  }

  function moveOnCanvas(dCol, dRow) {
    var c = 0, r = 0, found = false;
    for (var i = 0; i < visByCol.length && !found; i++) {
      var j = visByCol[i].indexOf(activeCardId);
      if (j >= 0) { c = i; r = j; found = true; }
    }
    if (!found) return;
    if (dCol) {
      var nc = c + dCol;
      while (nc >= 0 && nc < visByCol.length && !visByCol[nc].length) nc += dCol;
      if (nc < 0 || nc >= visByCol.length) return;
      c = nc;
      r = Math.min(r, visByCol[c].length - 1);
    } else {
      r = Math.max(0, Math.min(visByCol[c].length - 1, r + dRow));
    }
    setActiveFace(visByCol[c][r], true);
  }

  /* ------------------------------------------------------------------ *
   * the card dialog — level 1
   * ------------------------------------------------------------------ */

  var dlg = el("#card-dialog");

  function artRowHtml(a) {
    var kind = '<span class="art-kind" data-kind="' + esc(a.kind) + '">' + esc(a.kind) + "</span>";
    var main = '<span class="art-main">' +
      '<span class="art-label">' + esc(displayLabel(a)) + "</span>" +
      '<span class="art-target">' + esc(displayTarget(a)) + "</span></span>";
    if (a.openable) {
      return '<li><button type="button" class="art-row" data-art="' + esc(a.slug) + '">' +
        kind + main + '<span class="art-go">read &rarr;</span></button></li>';
    }
    /* a closed door: attached but unpublished — visibly not a link */
    return '<li class="art-closed"><div class="art-row">' +
      kind + main + '<span class="art-go">path only</span></div></li>';
  }

  function renderDialog(card) {
    var col = colOf[card.id];
    var meta = [
      '<span class="st">' + esc(col ? col.title : card.status || "") + "</span>"
    ];
    if (card.milestone) meta.push(esc(card.milestone));
    if (card.type) meta.push(esc(card.type));
    if (card.size) meta.push(esc(String(card.size).toUpperCase()));
    if (card.priority) meta.push(esc(card.priority));

    var crit = card.criteria || [];
    var nDone = crit.filter(function (c) { return c.done; }).length;
    var arts = artsOf[card.id];

    var html =
      '<div class="dlg-head">' +
        '<div class="dlg-head-main">' +
          "<h2 id=\"dlg-title\">" + esc(card.title) + "</h2>" +
          '<p class="dlg-meta">' + meta.join('<span class="sep">&middot;</span>') + "</p>" +
          (card.file ? '<p class="dlg-id">' + esc(card.file) + "</p>" : "") +
        "</div>" +
        '<button type="button" class="dlg-close" aria-label="Close">&#10005;</button>' +
      "</div>";

    if (card.description) {
      html += '<div class="dlg-sec"><p class="dlg-label">Description</p>' +
        '<div class="dlg-desc">' + renderMd(card.description) + "</div></div>";
    }
    if (crit.length) {
      html += '<div class="dlg-sec"><p class="dlg-label">Acceptance criteria ' +
        '<span class="n">' + nDone + "/" + crit.length + "</span></p>" +
        '<ul class="crit">' + crit.map(function (c) {
          return '<li class="' + (c.done ? "done" : "") + '"><span class="box"></span>' +
            "<span>" + inlineMd(c.text) + "</span></li>";
        }).join("") + "</ul></div>";
    }
    if (arts.length) {
      html += '<div class="dlg-sec"><p class="dlg-label">Artifacts ' +
        '<span class="n">' + arts.length + "</span></p>" +
        '<ul class="band">' + arts.map(artRowHtml).join("") + "</ul></div>";
    }
    el("#dlg-inner").innerHTML = html;
  }

  /* ------------------------------------------------------------------ *
   * the artifact page — level 2
   * ------------------------------------------------------------------ */

  function openableOf(cardId) {
    return artsOf[cardId].filter(function (a) { return a.openable; });
  }

  function railItemHtml(card, a, current) {
    var kind = '<span class="art-kind" data-kind="' + esc(a.kind) + '">' + esc(a.kind) + "</span>";
    var body = '<span class="rail-main">' +
      '<span class="rail-label">' + esc(displayLabel(a)) + "</span>" +
      '<span class="rail-target">' + esc(displayTarget(a)) + "</span>" +
      (a.openable ? "" : '<span class="rail-closed-tag">path only</span>') +
      "</span>";
    if (!a.openable) {
      return '<li class="rail-closed"><div class="rail-item">' + kind + body + "</div></li>";
    }
    var href = formatHash({ card: card.id, art: a.slug, q: state.q });
    return "<li><a class=\"rail-item\" data-art=\"" + esc(a.slug) + '" href="' + esc(href) + '"' +
      (current ? ' aria-current="page"' : "") + ">" + kind + body + "</a></li>";
  }

  function renderPage(card, art) {
    var col = colOf[card.id];
    el("#crumb-title").textContent = BOARD.title || "Board";
    el("#crumb-board").setAttribute("href", formatHash({ card: null, art: null, q: state.q }));
    el("#route").textContent = "/kanban/" + card.id + "/" + art.slug;
    el("#pg-title").textContent = displayLabel(art);
    el("#pg-meta").innerHTML =
      '<span class="st">' + esc(col ? col.title : "") + "</span>" +
      '<span class="sep">&middot;</span>' + esc(card.title) +
      '<span class="sep">&middot;</span>' + esc(displayTarget(art));

    /* the band bar: position among this card's openable artifacts */
    var open = openableOf(card.id);
    var at = open.indexOf(artBySlug[card.id][art.slug]);
    el("#band-label").innerHTML = "<b>" + (at + 1) + "</b> / " + open.length;
    el("#band-prev").disabled = at <= 0;
    el("#band-next").disabled = at >= open.length - 1;

    var prose = el("#prose");
    var embed = el("#embed");
    var full = el("#open-full");
    if (art.entry.type === "markdown") {
      prose.innerHTML = art.entry.html;
      prose.hidden = false;
      embed.hidden = true;
      embed.innerHTML = "";
      /* nothing full to open over file:// — the compiled page is the served
         site's business, so the link hides rather than pointing at a 404 */
      full.hidden = true;
      full.removeAttribute("href");
    } else {
      embed.innerHTML =
        '<iframe src="' + esc(art.entry.src) + '" title="' + esc(displayLabel(art)) + '"></iframe>' +
        '<p class="embed-note">' + esc(art.target) + " &middot; embedded live</p>";
      embed.hidden = false;
      prose.hidden = true;
      prose.innerHTML = "";
      full.hidden = false;
      full.setAttribute("href", art.entry.src);
    }

    var arts = artsOf[card.id];
    el("#rail-h").innerHTML = "Artifacts <span class=\"n\">" + arts.length + "</span>";
    el("#rail-list").innerHTML = arts.map(function (a) {
      return railItemHtml(card, a, a.slug === art.slug);
    }).join("");
    el("#rail-note").hidden = !arts.some(function (a) { return !a.openable; });
    el("#pg-foot-meta").textContent =
      "Simulates /kanban/" + card.id + "/" + art.slug + " — the hash stands in for the route because file:// has no server.";
  }

  /* ------------------------------------------------------------------ *
   * navigation — every render goes through applyState
   * ------------------------------------------------------------------ */

  function applyState(next, focusHint) {
    var prev = state;
    state = next;
    appliedHash = formatHash(next);

    var level = levelOf(next);
    var card = next.card ? byId[next.card] : null;
    var art = level === 2 ? artBySlug[next.card][next.art] : null;

    el("#view-page").hidden = level !== 2;
    el("#view-board").hidden = level === 2;

    if (level < 2) {
      var q = el("#q");
      if (q.value !== next.q) q.value = next.q;
      renderBoard();
    }

    if (level === 1) {
      renderDialog(card);
      if (!dlg.open) dlg.showModal();
    } else if (dlg.open) {
      dlg.close();
    }

    if (level === 2) {
      renderPage(card, art);
    } else {
      /* park the embed so a hidden iframe stops costing anything */
      el("#embed").innerHTML = "";
    }

    document.title =
      (level === 2 ? displayLabel(art) + " — " : level === 1 ? card.title + " — " : "") +
      "Board reader page — Folio kanban prototype";

    /* focus follows the direction of travel */
    if (focusHint === "page") {
      safeFocus(el("#pg-title"));
      announce("Reading " + displayLabel(art));
    } else if (focusHint === "dialog") {
      var row = prev.art
        ? dlg.querySelector('.art-row[data-art="' + String(prev.art).replace(/"/g, '\\"') + '"]')
        : null;
      safeFocus(row || dlg.querySelector(".dlg-close"));
    } else if (focusHint === "board" && prev.card) {
      if (faceEl(prev.card)) {
        setActiveFace(prev.card, true);
      } else if (activeCardId) {
        /* the card that owned the reading is filtered off the board;
           renderBoard already moved the tab stop to a visible face */
        setActiveFace(activeCardId, true);
      }
    }
  }

  function goTo(next, mode, focusHint) {
    var s = sanitize(next);
    var url = formatHash(s);
    if (mode === "push") {
      history.pushState({ d: inAppDepth() + 1 }, "", url);
    } else {
      history.replaceState({ d: inAppDepth() }, "", url);
    }
    applyState(s, focusHint);
  }

  /* Esc and the close affordances: one level, preferring real history so
     Back and Esc mean the same stairs. A deep link has no in-app history
     (state.d is 0), so the level above is written in place instead. */
  function escLevel() {
    var level = levelOf(state);
    if (!level) return;
    if (inAppDepth() > 0) {
      history.back();
      return;
    }
    var up = level === 2 ? { card: state.card, art: null, q: state.q }
                         : { card: null, art: null, q: state.q };
    goTo(up, "replace", level === 2 ? "dialog" : "board");
  }

  function jumpToBoard() {
    var level = levelOf(state);
    if (!level) return;
    if (inAppDepth() >= level) {
      history.go(-level);
      return;
    }
    goTo({ card: null, art: null, q: state.q }, "replace", "board");
  }

  /* the band, from the page: replaceState, so Back never replays reading */
  function stepArt(delta) {
    if (levelOf(state) !== 2) return;
    var open = openableOf(state.card);
    var at = open.indexOf(artBySlug[state.card][state.art]);
    var to = open[at + delta];
    if (!to) return;
    goTo({ card: state.card, art: to.slug, q: state.q }, "replace", "page");
  }

  function onLocationChange(focusHint) {
    /* only #/kanban… hashes belong to the router; a plain in-page anchor
       (the skip link's #board) must neither rewrite the URL nor reset the
       filter */
    if (!location.hash.startsWith("#/")) return;
    if (location.hash === appliedHash) return;
    var s = sanitize(parseHash(location.hash));
    var canonical = formatHash(s);
    if (canonical !== location.hash) {
      history.replaceState(history.state, "", canonical);
    }
    var going = levelOf(s) - levelOf(state);
    applyState(s, focusHint || (going > 0 ? (levelOf(s) === 2 ? "page" : "dialog")
                                          : (levelOf(s) === 1 ? "dialog" : "board")));
  }

  /* ------------------------------------------------------------------ *
   * events
   * ------------------------------------------------------------------ */

  function wireEvents() {
    el("#columns").addEventListener("click", function (e) {
      var face = e.target.closest && e.target.closest(".face");
      if (!face) return;
      setActiveFace(face.getAttribute("data-card"), false);
      goTo({ card: face.getAttribute("data-card"), art: null, q: state.q }, "push", "dialog");
    });

    dlg.addEventListener("click", function (e) {
      if (e.target === dlg) { escLevel(); return; }
      if (e.target.closest && e.target.closest(".dlg-close")) { escLevel(); return; }
      var row = e.target.closest && e.target.closest("button.art-row[data-art]");
      if (row) {
        goTo({ card: state.card, art: row.getAttribute("data-art"), q: state.q }, "push", "page");
      }
    });

    /* the dialog's own Esc arrives as cancel; route it through the stairs */
    dlg.addEventListener("cancel", function (e) {
      e.preventDefault();
      escLevel();
    });

    el("#crumb-board").addEventListener("click", function (e) {
      /* a modified click asked for a new tab; the href is real, let it be */
      if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      e.preventDefault();
      jumpToBoard();
    });

    el("#rail-list").addEventListener("click", function (e) {
      var item = e.target.closest && e.target.closest("a.rail-item[data-art]");
      if (!item) return;
      if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      e.preventDefault();
      var slug = item.getAttribute("data-art");
      if (slug !== state.art) {
        goTo({ card: state.card, art: slug, q: state.q }, "replace", "page");
      }
    });

    el("#band-prev").addEventListener("click", function () { stepArt(-1); });
    el("#band-next").addEventListener("click", function () { stepArt(1); });

    el("#q").addEventListener("input", function () {
      goTo({ card: state.card, art: state.art, q: el("#q").value }, "replace");
    });

    document.addEventListener("keydown", function (e) {
      var typing = /^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName);
      var level = levelOf(state);

      if (level === 2) {
        if (e.key === "Escape") { e.preventDefault(); escLevel(); return; }
        if (!typing && e.key === "[") { e.preventDefault(); stepArt(-1); return; }
        if (!typing && e.key === "]") { e.preventDefault(); stepArt(1); return; }
        return;
      }
      if (level !== 0 || typing) {
        if (typing && e.key === "Escape" && level === 0) e.target.blur();
        return;
      }
      if (e.key === "/") { e.preventDefault(); safeFocus(el("#q")); return; }
      /* arrows drive the face grid only from a face (or the page body);
         on the theme buttons, the notes summary or a scrolled footer they
         keep their native meaning */
      var onFace = e.target.closest && e.target.closest(".face");
      if (!onFace && e.target !== document.body) return;
      if (e.key === "ArrowLeft") { e.preventDefault(); moveOnCanvas(-1, 0); }
      else if (e.key === "ArrowRight") { e.preventDefault(); moveOnCanvas(1, 0); }
      else if (e.key === "ArrowUp") { e.preventDefault(); moveOnCanvas(0, -1); }
      else if (e.key === "ArrowDown") { e.preventDefault(); moveOnCanvas(0, 1); }
    });

    window.addEventListener("popstate", function () { onLocationChange(); });
    window.addEventListener("hashchange", function () { onLocationChange(); });
  }

  /* ------------------------------------------------------------------ *
   * init
   * ------------------------------------------------------------------ */

  wireTheme();
  wireEvents();

  var initial = sanitize(parseHash(location.hash));
  history.replaceState(
    { d: inAppDepth() }, "",
    location.pathname + location.search + formatHash(initial)
  );
  applyState(initial, levelOf(initial) === 2 ? "page" : null);
})();
