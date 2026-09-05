/* Reading overlay — Folio kanban prototype.
   Vanilla, file:// safe. window.BOARD comes from board-data.js,
   window.READER from reader-data.js.

   Two native <dialog>s stack in the top layer: the card dialog (the mail)
   and the reader overlay above it. showModal() gives us the dimmed
   backdrop, the inert canvas behind, and one-level-at-a-time Esc for
   free; this file owns the bookkeeping — URL, focus return, band walking. */
(function () {
  "use strict";

  var BOARD = window.BOARD || { title: "Board", columns: [] };
  var READER = window.READER || {};

  /* ------------------------------------------------------------------ *
   * model
   * ------------------------------------------------------------------ */

  var cards = [];
  var byId = {};
  var columnOf = {};
  (BOARD.columns || []).forEach(function (col) {
    (col.cards || []).forEach(function (card) {
      cards.push(card);
      byId[card.id] = card;
      columnOf[card.id] = col;
    });
  });

  function basename(path) {
    var parts = String(path).split("/");
    return parts[parts.length - 1];
  }

  /* an artifact can open on the canvas only if the reader data holds a
     body for its target; everything else is a closed door */
  function readerEntry(art) {
    return READER[art.target] || null;
  }

  function openableIndices(card) {
    var out = [];
    (card.artifacts || []).forEach(function (art, i) {
      if (readerEntry(art)) out.push(i);
    });
    return out;
  }

  function artifactLabel(art) {
    var entry = readerEntry(art);
    return (
      art.label ||
      (entry && entry.title) ||
      basename(art.target) ||
      art.target
    );
  }

  /* ------------------------------------------------------------------ *
   * dom helpers
   * ------------------------------------------------------------------ */

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text != null) node.textContent = text;
    return node;
  }

  var $ = function (id) {
    return document.getElementById(id);
  };

  var columnsEl = $("columns");
  var cardDialog = $("card-dialog");
  var readerEl = $("reader");
  var rdMd = $("rd-md");
  var rdFrame = $("rd-frame");
  var rdBody = $("rd-body");

  /* ------------------------------------------------------------------ *
   * state
   * ------------------------------------------------------------------ */

  var state = { cardId: null, artIdx: null };

  /* focus returns to the element that opened what you just closed */
  var cardOpener = null;
  var artOpener = null;

  /* ------------------------------------------------------------------ *
   * board
   * ------------------------------------------------------------------ */

  function renderBoard() {
    (BOARD.columns || []).forEach(function (col) {
      var count = (col.cards || []).length;
      var section = el("section", "col");
      section.setAttribute("aria-label", col.title);
      if (col.limit && count > col.limit) section.dataset.over = "1";

      var head = el("div", "col-head");
      var title = el("h2", "col-title", col.title);
      head.appendChild(title);
      var countEl = el("p", "col-count");
      var b = el("b", "", String(count));
      countEl.appendChild(b);
      if (col.limit) countEl.appendChild(document.createTextNode(" / " + col.limit));
      head.appendChild(countEl);
      section.appendChild(head);

      if (!count) {
        section.appendChild(el("p", "col-empty", "no cards"));
        columnsEl.appendChild(section);
        return;
      }

      var list = el("ul", "cards");
      (col.cards || []).forEach(function (card) {
        var li = document.createElement("li");
        var btn = el("button", "bcard");
        btn.type = "button";
        btn.dataset.card = card.id;
        if (card.priority) btn.dataset.priority = card.priority;
        btn.setAttribute("aria-haspopup", "dialog");

        btn.appendChild(el("span", "bcard-title", card.title));

        var meta = el("span", "bcard-meta");
        var idSpan = el("span", "bm", card.id);
        meta.appendChild(idSpan);
        var nArts = (card.artifacts || []).length;
        if (nArts) {
          meta.appendChild(
            el("span", "bm-art", nArts + (nArts === 1 ? " artifact" : " artifacts"))
          );
        }
        btn.appendChild(meta);

        btn.addEventListener("click", function () {
          openCard(card.id, btn);
        });
        li.appendChild(btn);
        list.appendChild(li);
      });
      section.appendChild(list);
      columnsEl.appendChild(section);
    });
  }

  /* ------------------------------------------------------------------ *
   * card dialog — the mail
   * ------------------------------------------------------------------ */

  function metaPair(dl, label, value) {
    if (!value) return;
    var wrap = document.createElement("div");
    wrap.appendChild(el("dt", "", label));
    wrap.appendChild(el("dd", "", value));
    dl.appendChild(wrap);
  }

  function renderCardDialog(card) {
    $("cd-status").textContent = columnOf[card.id]
      ? columnOf[card.id].title
      : "";
    $("cd-title").textContent = card.title;
    $("cd-title").setAttribute("tabindex", "-1");
    $("cd-file").textContent = card.file || card.id;

    var dl = $("cd-meta");
    dl.textContent = "";
    metaPair(dl, "type", card.type);
    metaPair(dl, "size", card.size);
    metaPair(dl, "priority", card.priority);
    metaPair(dl, "milestone", card.milestone);
    metaPair(dl, "created", card.created);
    metaPair(dl, "assignee", (card.assignee || []).join(", "));
    metaPair(dl, "tags", (card.tags || []).join(", "));

    /* description: paragraphs on blank lines, soft-wrapped source lines
       rejoined — plain text in, plain text out */
    var desc = $("cd-desc");
    desc.textContent = "";
    String(card.description || "")
      .split(/\n{2,}/)
      .forEach(function (para) {
        var text = para.replace(/\s*\n\s*/g, " ").trim();
        if (text) desc.appendChild(el("p", "", text));
      });

    var criteria = card.criteria || [];
    var critWrap = $("cd-criteria-wrap");
    critWrap.hidden = !criteria.length;
    if (criteria.length) {
      var done = criteria.filter(function (c) {
        return c.done;
      }).length;
      $("cd-criteria-label").textContent =
        "Criteria · " + done + " of " + criteria.length + " done";
      var ul = $("cd-criteria");
      ul.textContent = "";
      criteria.forEach(function (c) {
        var li = el("li", "", c.text);
        if (c.done) li.dataset.done = "1";
        ul.appendChild(li);
      });
    }

    renderBand(card);
  }

  function renderBand(card) {
    var arts = card.artifacts || [];
    var wrap = $("cd-band-wrap");
    wrap.hidden = !arts.length;
    var ul = $("cd-band");
    ul.textContent = "";
    arts.forEach(function (art, i) {
      var li = document.createElement("li");
      var entry = readerEntry(art);
      var tile = entry ? el("button", "art") : el("div", "art closed");
      tile.dataset.kind = art.kind;
      tile.dataset.idx = String(i);

      tile.appendChild(el("span", "art-kind", art.kind));
      var text = el("span", "art-text");
      text.appendChild(el("span", "art-label", artifactLabel(art)));
      text.appendChild(el("code", "art-target", art.target));
      tile.appendChild(text);

      if (entry) {
        tile.type = "button";
        tile.appendChild(el("span", "art-open", "read ›"));
        tile.addEventListener("click", function () {
          openArtifact(card, i, tile);
        });
      } else {
        tile.appendChild(el("span", "art-open", "not published"));
      }
      li.appendChild(tile);
      ul.appendChild(li);
    });
  }

  /* ------------------------------------------------------------------ *
   * open / close — every path funnels through these four
   * ------------------------------------------------------------------ */

  function openCard(id, opener) {
    var card = byId[id];
    if (!card) return;
    cardOpener =
      opener || columnsEl.querySelector('[data-card="' + id + '"]');
    state.cardId = id;
    renderCardDialog(card);
    if (!cardDialog.open) cardDialog.showModal();
    writeHash();
    $("cd-title").focus();
  }

  function closeCard() {
    state.cardId = null;
    state.artIdx = null;
    if (cardDialog.open) cardDialog.close();
    writeHash();
    if (cardOpener && document.contains(cardOpener)) cardOpener.focus();
  }

  function openArtifact(card, idx, opener) {
    var art = (card.artifacts || [])[idx];
    if (!art || !readerEntry(art)) return;
    /* walking the band moves the return point with you: closing after
       prev/next lands on the tile of the artifact you were reading,
       which is the tile that would have opened it */
    if (opener) artOpener = opener;
    else if (
      !artOpener ||
      !document.contains(artOpener) ||
      artOpener.dataset.idx !== String(idx)
    )
      artOpener = $("cd-band").querySelector('[data-idx="' + idx + '"]');
    state.artIdx = idx;
    renderReader(card, idx);
    var firstShow = !readerEl.open;
    if (firstShow) readerEl.showModal();
    writeHash();
    /* land the keyboard on the scroller when there is one */
    if (firstShow) (rdMd.hidden ? rdBody : rdMd).focus();
  }

  function closeReader() {
    state.artIdx = null;
    if (readerEl.open) readerEl.close();
    /* drop the live document so it stops running behind the board */
    rdFrame.textContent = "";
    writeHash();
    if (artOpener && document.contains(artOpener)) artOpener.focus();
  }

  /* Esc arrives as `cancel` on the topmost dialog only; take over the
     close so URL and focus bookkeeping always run */
  readerEl.addEventListener("cancel", function (e) {
    e.preventDefault();
    closeReader();
  });
  cardDialog.addEventListener("cancel", function (e) {
    e.preventDefault();
    if (readerEl.open) closeReader();
    else closeCard();
  });

  /* clicking the dimmed canvas closes the top layer, like Esc */
  readerEl.addEventListener("click", function (e) {
    if (e.target === readerEl) closeReader();
  });
  cardDialog.addEventListener("click", function (e) {
    if (e.target === cardDialog) closeCard();
  });

  $("cd-close").addEventListener("click", closeCard);
  $("rd-close").addEventListener("click", closeReader);

  /* ------------------------------------------------------------------ *
   * the reader
   * ------------------------------------------------------------------ */

  function renderReader(card, idx) {
    var art = card.artifacts[idx];
    var entry = readerEntry(art);
    var open = openableIndices(card);
    var pos = open.indexOf(idx);

    $("rd-crumb-board").textContent = BOARD.title;
    $("rd-crumb-card").textContent = card.title;
    $("rd-crumb-art").textContent = artifactLabel(art);

    var posEl = $("rd-pos");
    posEl.textContent = "";
    posEl.appendChild(el("b", "", String(pos + 1)));
    posEl.appendChild(document.createTextNode(" of " + open.length));

    $("rd-prev").disabled = pos <= 0;
    $("rd-next").disabled = pos >= open.length - 1;

    var full = $("rd-full");
    if (entry.type === "html") {
      full.href = entry.src;
      full.textContent = "open full ↗";
    } else {
      /* the raw source file, repo-relative from this directory */
      full.href = "../../../" + art.target;
      full.textContent = "source ↗";
    }

    if (entry.type === "markdown") {
      rdFrame.hidden = true;
      rdFrame.textContent = "";
      rdMd.hidden = false;
      rdMd.setAttribute("tabindex", "0");
      /* trusted, pre-rendered in the repo — never re-escaped here */
      rdMd.innerHTML = '<div class="md-col">' + entry.html + "</div>";
      rdMd.scrollTop = 0;
    } else {
      rdMd.hidden = true;
      rdMd.innerHTML = "";
      rdFrame.hidden = false;
      /* a fresh iframe each time: setting src on a live one pollutes
         session history */
      rdFrame.textContent = "";
      var frame = document.createElement("iframe");
      frame.src = entry.src;
      frame.title = artifactLabel(art);
      rdFrame.appendChild(frame);
    }
  }

  function step(delta) {
    var card = byId[state.cardId];
    if (!card || state.artIdx == null) return;
    var open = openableIndices(card);
    var pos = open.indexOf(state.artIdx) + delta;
    if (pos < 0 || pos >= open.length) return;
    openArtifact(card, open[pos]);
    /* a pager button that just went disabled drops focus on the body;
       catch it and keep the keyboard in the chrome */
    var active = document.activeElement;
    if (active && active.disabled)
      (delta > 0 ? $("rd-prev") : $("rd-next")).focus();
  }

  $("rd-prev").addEventListener("click", function () {
    step(-1);
  });
  $("rd-next").addEventListener("click", function () {
    step(1);
  });

  readerEl.addEventListener("keydown", function (e) {
    if (e.altKey || e.ctrlKey || e.metaKey || e.shiftKey) return;
    if (e.key === "ArrowRight") {
      e.preventDefault();
      step(1);
    } else if (e.key === "ArrowLeft") {
      e.preventDefault();
      step(-1);
    }
  });

  /* ------------------------------------------------------------------ *
   * the reading position is a URL
   * ------------------------------------------------------------------ */

  function desiredHash() {
    if (!state.cardId) return "";
    var h = "#card=" + encodeURIComponent(state.cardId);
    if (state.artIdx != null) {
      var art = byId[state.cardId].artifacts[state.artIdx];
      h += "&artifact=" + encodeURIComponent(basename(art.target));
    }
    return h;
  }

  var syncing = false;

  function writeHash() {
    if (syncing) return;
    var want = desiredHash();
    if (location.hash === want) return;
    try {
      history.replaceState(
        null,
        "",
        location.pathname + location.search + want
      );
    } catch (err) {
      location.hash = want;
    }
  }

  function parseHash() {
    var out = {};
    location.hash
      .replace(/^#/, "")
      .split("&")
      .forEach(function (pair) {
        var i = pair.indexOf("=");
        if (i < 1) return;
        try {
          out[pair.slice(0, i)] = decodeURIComponent(pair.slice(i + 1));
        } catch (err) {
          /* malformed escape: ignore the pair */
        }
      });
    return out;
  }

  function resolveArtifact(card, key) {
    if (!key) return null;
    var arts = card.artifacts || [];
    for (var i = 0; i < arts.length; i++) {
      if (!readerEntry(arts[i])) continue;
      if (basename(arts[i].target) === key || arts[i].target === key)
        return i;
    }
    return null;
  }

  /* rebuild board / card / reader to match the location bar */
  function applyHash() {
    var h = parseHash();
    var cardId = h.card && byId[h.card] ? h.card : null;

    syncing = true;
    if (!cardId) {
      state.artIdx = null;
      state.cardId = null;
      if (readerEl.open) readerEl.close();
      if (cardDialog.open) cardDialog.close();
    } else {
      if (state.cardId !== cardId) {
        if (readerEl.open) readerEl.close();
        var btn = columnsEl.querySelector('[data-card="' + cardId + '"]');
        if (btn) btn.scrollIntoView({ block: "center" });
        openCard(cardId, btn);
      }
      var card = byId[cardId];
      var idx = resolveArtifact(card, h.artifact);
      if (idx == null) {
        state.artIdx = null;
        if (readerEl.open) readerEl.close();
      } else if (idx !== state.artIdx || !readerEl.open) {
        openArtifact(card, idx);
      }
    }
    syncing = false;
    writeHash();
  }

  window.addEventListener("hashchange", applyHash);

  /* ------------------------------------------------------------------ *
   * theme + boot
   * ------------------------------------------------------------------ */

  var THEME_KEY = "reading-overlay-theme";

  function setTheme(v) {
    document.documentElement.setAttribute("data-theme", v);
    Array.prototype.forEach.call(
      document.querySelectorAll("[data-theme-set]"),
      function (b) {
        b.setAttribute(
          "aria-pressed",
          b.getAttribute("data-theme-set") === v ? "true" : "false"
        );
      }
    );
  }

  Array.prototype.forEach.call(
    document.querySelectorAll("[data-theme-set]"),
    function (b) {
      b.addEventListener("click", function () {
        var v = b.getAttribute("data-theme-set");
        setTheme(v);
        try {
          localStorage.setItem(THEME_KEY, v);
        } catch (err) {
          /* private mode: theme just does not persist */
        }
      });
    }
  );

  var saved = null;
  try {
    saved = localStorage.getItem(THEME_KEY);
  } catch (err) {
    /* ignore */
  }
  if (saved === "light" || saved === "dark" || saved === "auto")
    setTheme(saved);

  renderBoard();
  if (location.hash) applyHash();
})();
