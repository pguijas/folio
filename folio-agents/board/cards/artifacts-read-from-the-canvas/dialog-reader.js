/* Dialog reader — Folio kanban prototype.
   Vanilla, file:// safe. window.BOARD comes from board-data.js,
   window.READER from reader-data.js. The card dialog is a mail; the
   attachment opens inside the mail: the dialog widens into letter and
   reading surface, Esc unwinds one level at a time. */
(function () {
  "use strict";

  var BOARD = window.BOARD || { title: "Board", columns: [] };
  var READER = window.READER || {};

  /* ------------------------------------------------------------------ *
   * model
   * ------------------------------------------------------------------ */

  var byId = {};
  var colOfCard = {};
  (BOARD.columns || []).forEach(function (col) {
    (col.cards || []).forEach(function (card) {
      byId[card.id] = card;
      colOfCard[card.id] = col;
    });
  });

  function readerEntry(art) {
    return art && art.target ? READER[art.target] || null : null;
  }

  /* ------------------------------------------------------------------ *
   * small helpers
   * ------------------------------------------------------------------ */

  function el(sel) {
    return document.querySelector(sel);
  }

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  /* markdown-lite for card bodies: paragraphs, lists, **bold**, `code`.
     Code spans are held aside so a `**literal**` inside one stays literal —
     these cards talk about markdown, so mangling their own examples reads
     badly. Artifact bodies do NOT come through here; READER carries
     pre-rendered HTML from trusted repo markdown. */
  function inlineMd(s) {
    var held = [];
    function hold(inner) {
      held.push(inner);
      /* the placeholder is an escape sequence, never a raw byte in source —
         see the NUL-byte story in the comparison doc */
      return "\u0000" + (held.length - 1) + "\u0000";
    }
    var t = esc(s)
      .replace(/``([\s\S]+?)``/g, function (m, inner) {
        return hold(inner.replace(/^ | $/g, ""));
      })
      .replace(/`([^`]+)`/g, function (m, inner) {
        return hold(inner);
      })
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    return t.replace(/\u0000(\d+)\u0000/g, function (m, i) {
      return "<code>" + held[Number(i)] + "</code>";
    });
  }

  function renderMd(src) {
    if (!src) return "";
    /* fenced blocks come out whole before anything splits on blank lines;
       one card carries an ASCII diagram that must survive verbatim */
    var fences = [];
    var held = String(src).replace(
      /```[^\n]*\n?([\s\S]*?)```/g,
      function (m, inner) {
        fences.push(inner.replace(/\n$/, ""));
        return "\u0001" + (fences.length - 1) + "\u0001";
      }
    );
    var blocks = held.split(/\n{2,}/);
    var out = [];
    blocks.forEach(function (b) {
      var lines = b.split("\n");
      var isList =
        lines.every(function (l) {
          return /^\s*[-*]\s+/.test(l) || /^\s*$/.test(l);
        }) &&
        lines.some(function (l) {
          return /^\s*[-*]\s+/.test(l);
        });
      if (isList) {
        out.push(
          "<ul>" +
            lines
              .filter(function (l) {
                return /\S/.test(l);
              })
              .map(function (l) {
                return "<li>" + inlineMd(l.replace(/^\s*[-*]\s+/, "")) + "</li>";
              })
              .join("") +
            "</ul>"
        );
      } else {
        out.push("<p>" + inlineMd(b.replace(/\n/g, " ")) + "</p>");
      }
    });
    return out.join("").replace(
      /(?:<p>)?\u0001(\d+)\u0001(?:<\/p>)?/g,
      function (m, i) {
        return "<pre><code>" + esc(fences[Number(i)]) + "</code></pre>";
      }
    );
  }

  function firstSentences(s, max) {
    var t = String(s || "").replace(/\s+/g, " ").trim();
    if (t.length <= max) return t;
    var cut = t.slice(0, max);
    var stop = cut.lastIndexOf(". ");
    return stop > 60 ? cut.slice(0, stop + 1) : cut + "…";
  }

  function announce(msg) {
    var live = el("#live");
    if (live) live.textContent = msg;
  }

  /* ------------------------------------------------------------------ *
   * theme — same convention as the sibling prototypes
   * ------------------------------------------------------------------ */

  Array.prototype.slice
    .call(document.querySelectorAll("[data-theme-set]"))
    .forEach(function (b) {
      b.addEventListener("click", function () {
        var v = b.getAttribute("data-theme-set");
        applyTheme(v);
        try {
          localStorage.setItem("dialog-reader-theme", v);
        } catch (err) {
          /* file:// can refuse storage; the toggle still works this session */
        }
      });
    });

  function applyTheme(v) {
    document.documentElement.setAttribute("data-theme", v);
    Array.prototype.slice
      .call(document.querySelectorAll("[data-theme-set]"))
      .forEach(function (o) {
        o.setAttribute(
          "aria-pressed",
          o.getAttribute("data-theme-set") === v ? "true" : "false"
        );
      });
  }

  (function restoreTheme() {
    var v = null;
    try {
      v = localStorage.getItem("dialog-reader-theme");
    } catch (err) {
      v = null;
    }
    if (v) applyTheme(v);
  })();

  /* ------------------------------------------------------------------ *
   * board render — all columns, all cards
   * ------------------------------------------------------------------ */

  function cardFace(card) {
    var meta = [card.type, card.size, card.milestone]
      .filter(Boolean)
      .join(" · ");
    var n = (card.artifacts || []).length;
    var foot = "";
    if (meta || n) {
      foot =
        '<span class="card-foot">' +
        '<span class="card-meta">' +
        esc(meta) +
        "</span>" +
        (n
          ? '<span class="card-att">' +
            n +
            (n === 1 ? " attachment" : " attachments") +
            "</span>"
          : "") +
        "</span>";
    }
    return (
      '<button type="button" class="card-btn" data-id="' +
      esc(card.id) +
      '" data-priority="' +
      esc(card.priority || "") +
      '">' +
      '<span class="card-title">' +
      esc(card.title) +
      "</span>" +
      foot +
      "</button>"
    );
  }

  function renderBoard() {
    var html = (BOARD.columns || [])
      .map(function (col) {
        var cards = col.cards || [];
        var body = cards.length
          ? '<ul class="col-cards">' +
            cards
              .map(function (c) {
                return "<li>" + cardFace(c) + "</li>";
              })
              .join("") +
            "</ul>"
          : '<p class="col-empty">no cards</p>';
        return (
          '<section class="col" aria-label="' +
          esc(col.title) +
          '">' +
          '<header class="col-head"><h2 class="col-title">' +
          esc(col.title) +
          '</h2><span class="col-n">' +
          cards.length +
          "</span></header>" +
          body +
          "</section>"
        );
      })
      .join("");
    el("#columns").innerHTML = html;
  }

  renderBoard();

  el("#columns").addEventListener("click", function (e) {
    var btn = e.target.closest(".card-btn");
    if (!btn) return;
    openCard(btn.getAttribute("data-id"), btn);
  });

  /* ------------------------------------------------------------------ *
   * the dialog: a mail, and the reading surface inside it
   * ------------------------------------------------------------------ */

  var dialog = el("#card-dialog");

  var state = {
    cardId: null,
    reading: null, // artifact index, or null when the letter is full-width
    cardOpener: null, // board button to refocus when the dialog closes
    readerOpener: null // band row to refocus when the reader closes
  };

  function metaRows(card) {
    var col = colOfCard[card.id];
    var mono = function (v) {
      return '<span class="mono">' + esc(v) + "</span>";
    };
    /* status and priority first: the compressed letter keeps only the
       first two rows */
    var rows = [["status", esc(col ? col.title : "")]];
    if (card.priority) rows.push(["priority", esc(card.priority)]);
    if (card.type) rows.push(["type", esc(card.type)]);
    if (card.size) rows.push(["size", esc(card.size)]);
    if (card.milestone) rows.push(["milestone", esc(card.milestone)]);
    if (card.created) rows.push(["created", mono(card.created)]);
    if ((card.assignee || []).length)
      rows.push(["assignee", esc(card.assignee.join(", "))]);
    if ((card.tags || []).length)
      rows.push(["tags", mono(card.tags.join(" · "))]);
    if (card.parent) rows.push(["parent", mono(card.parent)]);
    if ((card.blocked_by || []).length)
      rows.push(["blocked by", mono(card.blocked_by.join(", "))]);
    if (card.source) rows.push(["source", mono(card.source)]);
    return rows
      .map(function (r) {
        return "<dt>" + r[0] + "</dt><dd>" + r[1] + "</dd>";
      })
      .join("");
  }

  function bandRow(art, i) {
    var entry = readerEntry(art);
    var kind = esc(art.kind || "file");
    var inner =
      '<span class="kind kind-' + kind + '">' + kind + "</span>" +
      '<span class="art-main">' +
      '<span class="art-label">' + esc(art.label || art.target) + "</span>" +
      '<span class="art-path">' + esc(art.target) + "</span>" +
      "</span>";
    if (entry) {
      return (
        '<li data-i="' + i + '"><button type="button" class="art" data-i="' +
        i + '">' + inner + "</button></li>"
      );
    }
    /* a closed door: kind, label, mono path — visibly not a link */
    return (
      '<li data-i="' + i + '"><div class="art art-closed">' + inner +
      '<span class="art-note">not readable here</span></div></li>'
    );
  }

  function renderLetter(card) {
    var col = colOfCard[card.id];
    el("#letter-eyebrow").textContent =
      (col ? col.title : "") + " · " + card.id;
    el("#dlg-title").textContent = card.title;
    el("#mailmeta").innerHTML = metaRows(card);
    el("#letter-summary").textContent = firstSentences(card.description, 260);

    var body = "";
    if (card.description) {
      body += '<div class="desc">' + renderMd(card.description) + "</div>";
    }

    var crit = card.criteria || [];
    if (crit.length) {
      var done = crit.filter(function (c) {
        return c.done;
      }).length;
      body +=
        '<section><h3 class="sect-h">acceptance · <b>' + done + " of " +
        crit.length + "</b></h3>" +
        '<ul class="crit">' +
        crit
          .map(function (c) {
            return (
              '<li data-done="' + (c.done ? 1 : 0) + '">' +
              '<span class="box" aria-hidden="true"></span>' +
              '<span><span class="sr-only">' +
              (c.done ? "done · " : "open · ") + "</span>" +
              inlineMd(c.text) + "</span></li>"
            );
          })
          .join("") +
        "</ul></section>";
    }

    var cmts = card.comments || [];
    if (cmts.length) {
      body +=
        '<section><h3 class="sect-h">comments · <b>' + cmts.length +
        "</b></h3>" +
        '<ul class="cmt">' +
        cmts
          .map(function (c) {
            return (
              '<li><p class="cmt-head"><b>' + esc(c.actor) + "</b> · " +
              esc(c.date) + "</p>" +
              '<div class="cmt-text">' + renderMd(c.text) + "</div></li>"
            );
          })
          .join("") +
        "</ul></section>";
    }

    var trail = card.trail || [];
    if (trail.length) {
      body +=
        '<section><h3 class="sect-h">trail · <b>' + trail.length +
        "</b></h3>" +
        '<ul class="trail">' +
        trail
          .map(function (t) {
            var ref = "";
            if (t.ref) {
              ref = t.href
                ? ' · <a href="' + esc(t.href) + '" target="_blank" rel="noopener"><code>' +
                  esc(t.ref) + "</code></a>"
                : " · <code>" + esc(t.ref) + "</code>";
            }
            return (
              '<li><span class="t-date">' + esc(t.date) + "</span>" +
              '<span class="t-note"><b>' + esc(t.actor) + "</b>" + ref +
              " · " + inlineMd(t.note) + "</span></li>"
            );
          })
          .join("") +
        "</ul></section>";
    }

    el("#letter-body").innerHTML = body;

    var arts = card.artifacts || [];
    el("#band-h").innerHTML = "attachments · <b>" + arts.length + "</b>";
    el("#band-list").innerHTML = arts.length
      ? arts
          .map(function (a, i) {
            return bandRow(a, i);
          })
          .join("")
      : '<li class="band-empty">nothing attached</li>';
  }

  /* ------------------------------------------------------------------ *
   * open / close, one level at a time
   * ------------------------------------------------------------------ */

  function openCard(id, opener, opts) {
    var card = byId[id];
    if (!card) return false;
    state.cardId = id;
    state.cardOpener =
      opener || document.querySelector('.card-btn[data-id="' + id + '"]');
    resetReaderPane();
    renderLetter(card);
    if (!dialog.open) dialog.showModal();
    var letter = el("#letter");
    letter.scrollTop = 0;
    letter.focus();
    if (!(opts && opts.silent)) writeHash();
    return true;
  }

  /* tear the reading pane down without deciding where focus goes */
  function resetReaderPane() {
    state.reading = null;
    dialog.removeAttribute("data-reading");
    el("#reader").hidden = true;
    el("#reader-body").innerHTML = ""; // drops any live iframe
    markActiveBand();
  }

  function prevReadable(arts, i) {
    for (var k = i - 1; k >= 0; k--) if (readerEntry(arts[k])) return k;
    return null;
  }
  function nextReadable(arts, i) {
    for (var k = i + 1; k < arts.length; k++) if (readerEntry(arts[k])) return k;
    return null;
  }

  function markActiveBand() {
    Array.prototype.slice
      .call(document.querySelectorAll("#band-list > li"))
      .forEach(function (li) {
        var active =
          state.reading != null &&
          li.hasAttribute("data-i") &&
          Number(li.getAttribute("data-i")) === state.reading;
        if (active) li.setAttribute("data-active", "1");
        else li.removeAttribute("data-active");
      });
  }

  function openArtifact(i, focusMode) {
    var card = byId[state.cardId];
    if (!card) return false;
    var arts = card.artifacts || [];
    var art = arts[i];
    var entry = readerEntry(art);
    if (!entry) return false;

    state.reading = i;
    /* Esc from the reader lands on the band row of what was being read */
    state.readerOpener = document.querySelector(
      '#band-list button.art[data-i="' + i + '"]'
    );
    dialog.setAttribute("data-reading", "1");
    var reader = el("#reader");
    reader.hidden = false;

    el("#reader-pos").textContent =
      "attachment " + (i + 1) + " of " + arts.length + " · " +
      (art.kind || "file");
    var title = entry.title || art.label || art.target;
    el("#reader-title").textContent = title;
    el("#reader-path").textContent = art.target;

    var body = el("#reader-body");
    var full = el("#open-full");
    if (entry.type === "markdown") {
      body.classList.add("is-doc");
      body.setAttribute("tabindex", "0"); // scroll container, keyboard-scrollable
      /* trusted pre-rendered repo markdown, inserted as-is by design */
      body.innerHTML = '<article class="prose">' + entry.html + "</article>";
      body.scrollTop = 0;
      full.hidden = true;
      full.removeAttribute("href");
    } else {
      body.classList.remove("is-doc");
      body.removeAttribute("tabindex");
      body.innerHTML = "";
      var f = document.createElement("iframe");
      f.src = entry.src;
      f.title = title;
      body.appendChild(f);
      full.hidden = false;
      full.href = entry.src;
    }

    var prevBtn = el("#art-prev");
    var nextBtn = el("#art-next");
    prevBtn.disabled = prevReadable(arts, i) == null;
    nextBtn.disabled = nextReadable(arts, i) == null;

    markActiveBand();
    writeHash();
    announce(
      "Reading attachment " + (i + 1) + " of " + arts.length + ": " + title
    );

    if (focusMode === "keep") {
      /* walking with prev/next keeps focus on the walker; if the button
         just went disabled under it, hand focus to its sibling */
      var ae = document.activeElement;
      if (ae === prevBtn && prevBtn.disabled) nextBtn.focus();
      else if (ae === nextBtn && nextBtn.disabled) prevBtn.focus();
    } else {
      reader.focus();
    }
    return true;
  }

  function closeReader() {
    var t = state.readerOpener;
    resetReaderPane();
    writeHash();
    if (t && document.contains(t)) t.focus();
    else el("#letter").focus();
  }

  function step(dir) {
    var card = byId[state.cardId];
    if (!card || state.reading == null) return;
    var arts = card.artifacts || [];
    var t =
      dir < 0
        ? prevReadable(arts, state.reading)
        : nextReadable(arts, state.reading);
    if (t != null) openArtifact(t, "keep");
  }

  /* ------------------------------------------------------------------ *
   * wiring
   * ------------------------------------------------------------------ */

  el("#band-list").addEventListener("click", function (e) {
    var btn = e.target.closest("button.art");
    if (!btn) return;
    openArtifact(Number(btn.getAttribute("data-i")));
  });

  el("#dlg-close").addEventListener("click", function () {
    dialog.close();
  });
  el("#reader-close").addEventListener("click", closeReader);
  el("#reader-back").addEventListener("click", closeReader);
  el("#art-prev").addEventListener("click", function () {
    step(-1);
  });
  el("#art-next").addEventListener("click", function () {
    step(1);
  });

  /* Esc unwinds one level at a time: reader → letter, letter → board */
  dialog.addEventListener("cancel", function (e) {
    if (state.reading != null) {
      e.preventDefault();
      closeReader();
    }
    /* otherwise the default close runs and the close handler restores focus */
  });

  dialog.addEventListener("close", function () {
    resetReaderPane();
    state.cardId = null;
    writeHash();
    var t = state.cardOpener;
    if (t && document.contains(t)) t.focus();
    state.cardOpener = null;
    state.readerOpener = null;
  });

  /* clicking the backdrop unwinds one level, same as Esc */
  dialog.addEventListener("click", function (e) {
    if (e.target !== dialog) return;
    if (state.reading != null) closeReader();
    else dialog.close();
  });

  /* arrows walk the band while reading */
  dialog.addEventListener("keydown", function (e) {
    if (state.reading == null) return;
    if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
    if (e.altKey || e.metaKey || e.ctrlKey) return;
    var t = e.target;
    if (t && t.closest && t.closest("input, textarea, select")) return;
    e.preventDefault();
    step(e.key === "ArrowLeft" ? -1 : 1);
  });

  /* ------------------------------------------------------------------ *
   * the reading position is a URL
   * ------------------------------------------------------------------ */

  function writeHash() {
    var h = "";
    if (dialog.open && state.cardId) {
      h = "#card=" + encodeURIComponent(state.cardId);
      if (state.reading != null) h += "&a=" + state.reading;
    }
    try {
      history.replaceState(null, "", location.pathname + location.search + h);
    } catch (err) {
      location.hash = h; // some file:// engines refuse replaceState
    }
  }

  (function restoreFromHash() {
    var m = /[#&]card=([^&]+)/.exec(location.hash);
    if (!m) return;
    var id = decodeURIComponent(m[1]);
    if (!openCard(id, null, { silent: true })) return;
    var a = /[#&]a=(\d+)/.exec(location.hash);
    if (a) openArtifact(Number(a[1]));
    writeHash(); // normalise whatever the hash asked for into what opened
  })();
})();
