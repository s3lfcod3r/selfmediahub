/* Cover-Layout-Editor (Phase 6). Nur auf der Einstellungsseite (#leGrid).
   Mitte = 4x9-Raster (Cover-Vorschau), rechts = Badge-Palette. Drag-and-Drop
   aus der Palette aufs Raster platziert ein Badge; platzierte Badges lassen sich
   verschieben (ziehen) oder mit x entfernen. Speichert display.card_layout -
   dasselbe Format, das das Cover-Overlay (app.js) rendert. */
(function () {
  "use strict";
  var T = window.t || function (k) { return k; };
  var $ = function (id) { return document.getElementById(id); };
  var grid = $("leGrid");
  if (!grid) { return; }   // nicht auf der Einstellungsseite

  var COLS = 4, ROWS = 9;

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function ic(n) { return (window.smhIcon && window.smhIcon(n)) || ""; }
  function fl() {
    var p = window.__PRIMARY_LANG__ || "ger";
    return (window.smhFlag && window.smhFlag(p)) || '<span class="fl-code">DE</span>';
  }

  // Badge-Typen: Sockel-Breite (span) + Beispiel-Darstellung (wie das echte Cover).
  var PALETTE = [
    { id: "rating",       span: 2, cls: "b-rating locked", sample: function () { return "FSK 16"; } },
    { id: "resolution",   span: 2, cls: "b-res",           sample: function () { return "1080p"; } },
    { id: "completeness", span: 1, cls: "b-comp ok",       sample: function () { return "&#10003;"; } },
    { id: "audio",        span: 2, cls: "b-audio",         sample: function () { return ic("audio") + fl(); } },
    { id: "sub",          span: 2, cls: "b-sub",           sample: function () { return ic("cc") + fl(); } },
  ];
  var SPEC = {}; PALETTE.forEach(function (p) { SPEC[p.id] = p; });

  var DEFAULT_LAYOUT = [
    { badge: "rating", col: 0, row: 0 },
    { badge: "resolution", col: 0, row: 6 },
    { badge: "completeness", col: 2, row: 6 },
    { badge: "audio", col: 0, row: 8 },
    { badge: "sub", col: 2, row: 8 },
  ];

  // Zustand: badge-id -> {col,row}. Jedes Badge hoechstens einmal.
  var placed = {};
  function loadInitial() {
    placed = {};
    var src = (Array.isArray(window.__CARD_LAYOUT__) && window.__CARD_LAYOUT__.length)
      ? window.__CARD_LAYOUT__ : DEFAULT_LAYOUT;
    src.forEach(function (p) {
      if (SPEC[p.badge]) { placed[p.badge] = { col: p.col | 0, row: p.row | 0 }; }
    });
  }
  loadInitial();

  var dragId = null;

  function badgeHtml(id) {
    var p = SPEC[id];
    return '<span class="ov-badge ' + p.cls + '">' + p.sample() + "</span>";
  }

  function renderGrid() {
    var html = "";
    for (var r = 0; r < ROWS; r++) {
      for (var col = 0; col < COLS; col++) {
        html += '<div class="le-cell" data-col="' + col + '" data-row="' + r + '"></div>';
      }
    }
    Object.keys(placed).forEach(function (id) {
      var pos = placed[id], p = SPEC[id];
      var col = Math.max(0, Math.min(pos.col, COLS - p.span));   // span nicht ueber den Rand
      var style = "grid-column:" + (col + 1) + "/span " + p.span + ";grid-row:" + (pos.row + 1) + ";";
      html += '<div class="le-placed" draggable="true" data-id="' + id + '" style="' + style + '">' +
        badgeHtml(id) +
        '<button class="le-del" type="button" data-id="' + id + '" aria-label="x">&times;</button></div>';
    });
    grid.innerHTML = html;
  }

  function renderPalette() {
    $("lePalette").innerHTML = PALETTE.map(function (p) {
      var isPlaced = !!placed[p.id];
      return '<div class="le-pal-item' + (isPlaced ? " placed" : "") + '" draggable="true" data-id="' + p.id + '">' +
        '<span class="le-pal-name">' + esc(T("badge." + p.id)) + "</span>" +
        badgeHtml(p.id) +
        (isPlaced ? '<span class="le-pal-tag">' + esc(T("settings.display.placed_hint")) + "</span>" : "") +
        "</div>";
    }).join("");
  }

  function render() { renderGrid(); renderPalette(); }

  // -- Drag & Drop -----------------------------------------------------------
  document.addEventListener("dragstart", function (e) {
    var el = e.target.closest && e.target.closest(".le-pal-item, .le-placed");
    if (!el) { return; }
    dragId = el.getAttribute("data-id");
    grid.classList.add("dragging");
    try { e.dataTransfer.setData("text/plain", dragId); e.dataTransfer.effectAllowed = "move"; } catch (x) { /* IE */ }
  });
  document.addEventListener("dragend", function () {
    dragId = null;
    grid.classList.remove("dragging");
    Array.prototype.forEach.call(grid.querySelectorAll(".le-cell.over"), function (c) { c.classList.remove("over"); });
  });

  grid.addEventListener("dragover", function (e) {
    var cell = e.target.closest(".le-cell");
    if (!cell || !dragId) { return; }
    e.preventDefault();
    Array.prototype.forEach.call(grid.querySelectorAll(".le-cell.over"), function (c) { c.classList.remove("over"); });
    cell.classList.add("over");
  });
  grid.addEventListener("drop", function (e) {
    var cell = e.target.closest(".le-cell");
    if (!cell || !dragId) { return; }
    e.preventDefault();
    var col = +cell.getAttribute("data-col"), row = +cell.getAttribute("data-row");
    var span = SPEC[dragId].span;
    if (col + span > COLS) { col = COLS - span; }
    placed[dragId] = { col: col, row: row };
    render();
  });

  grid.addEventListener("click", function (e) {
    var del = e.target.closest(".le-del");
    if (!del) { return; }
    delete placed[del.getAttribute("data-id")];
    render();
  });

  function currentLayout() {
    return Object.keys(placed).map(function (id) {
      return { badge: id, col: placed[id].col, row: placed[id].row };
    });
  }

  $("leSave").onclick = function () {
    var btn = this; btn.disabled = true;
    fetch("/api/settings", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ "display.card_layout": currentLayout() }),
    })
      .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
      .then(function (res) {
        if (!res.ok) { throw new Error(res.j.detail || "?"); }
        window.smhToast(T("msg.layout_saved"), "ok");
      })
      .catch(function (e) { window.smhToast(T("msg.failed_prefix") + e.message, "err"); })
      .then(function () { btn.disabled = false; });
  };
  $("leReset").onclick = function () {
    if (!window.confirm(T("settings.display.reset_confirm"))) { return; }
    placed = {};
    DEFAULT_LAYOUT.forEach(function (p) { placed[p.badge] = { col: p.col, row: p.row }; });
    render();
  };

  render();
})();
