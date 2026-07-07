/* SelfMediaHub - Uebersicht: Ansichten, Filter, Sortierung, Tags.
   Theme/Sync/Toast liegen in common.js. */
(function () {
  "use strict";

  var ALL = window.__DATA__ || [];
  var state = { view: "cover", q: "", library: "", type: "", rating: "", tag: "",
                sortKey: "sort_name", sortDir: 1 };

  var COLUMNS = [
    { key: "name",             label: "Titel",         on: true,  cls: "name" },
    { key: "item_type",        label: "Typ",           on: true },
    { key: "year",             label: "Jahr",          on: true,  num: true },
    { key: "library_name",     label: "Bibliothek",    on: false },
    { key: "official_rating",  label: "Freigabe",      on: true,  rating: true },
    { key: "resolution",       label: "Aufloesung",    on: true },
    { key: "hdr",              label: "HDR",           on: false },
    { key: "video_codec",      label: "Codec",         on: false },
    { key: "audio_langs",      label: "Sprachen",      on: false, list: true },
    { key: "completeness",     label: "Vollstaendig",  on: true,  comp: true },
    { key: "community_rating", label: "Bewertung",     on: false, num: true },
    { key: "tags",             label: "Tags",          on: true,  tags: true }
  ];

  var $ = function (id) { return document.getElementById(id); };
  var esc = function (s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  };

  function tagChip(t) {
    var ic = t.icon ? esc(t.icon) + " " : "";
    return '<span class="chip" style="border-color:' + esc(t.color) +
      ';color:' + esc(t.color) + '">' + ic + esc(t.name) + "</span>";
  }
  function compCell(i) {
    var c = i.completeness;
    if (c === "complete") { return '<span class="pill ok">komplett</span>'; }
    if (c === "incomplete") {
      var m = i.missing_episodes;
      return '<span class="pill bad">fehlt' + (m ? " " + m : "") + "</span>";
    }
    if (c === "unknown") { return '<span class="pill">unbekannt</span>'; }
    return '<span style="color:var(--self-text-3)">-</span>';
  }

  function fillFilters() {
    var ratings = {}, tagNames = {};
    ALL.forEach(function (i) {
      if (i.official_rating) { ratings[i.official_rating] = 1; }
      (i.tags || []).forEach(function (t) { tagNames[t.name] = 1; });
    });
    Object.keys(ratings).sort().forEach(function (r) {
      var o = document.createElement("option"); o.value = r; o.textContent = r; $("fRating").appendChild(o);
    });
    Object.keys(tagNames).sort().forEach(function (n) {
      var o = document.createElement("option"); o.value = n; o.textContent = n; $("fTag").appendChild(o);
    });
  }

  function filtered() {
    var q = state.q.toLowerCase();
    var rows = ALL.filter(function (i) {
      if (state.library && i.library_name !== state.library) { return false; }
      if (state.type && i.item_type !== state.type) { return false; }
      if (state.rating === "__none__" && i.official_rating) { return false; }
      if (state.rating && state.rating !== "__none__" && i.official_rating !== state.rating) { return false; }
      if (state.tag && !(i.tags || []).some(function (t) { return t.name === state.tag; })) { return false; }
      if (q && i.name.toLowerCase().indexOf(q) === -1) { return false; }
      return true;
    });
    var k = state.sortKey, dir = state.sortDir;
    rows.sort(function (a, b) {
      var va = a[k], vb = b[k];
      if (k === "sort_name" || k === "name") {
        va = (a.sort_name || a.name || "").toLowerCase(); vb = (b.sort_name || b.name || "").toLowerCase();
      }
      if (va == null) { return 1; } if (vb == null) { return -1; }
      if (typeof va === "number" && typeof vb === "number") { return (va - vb) * dir; }
      return String(va).localeCompare(String(vb), "de") * dir;
    });
    return rows;
  }

  function renderGrid(rows) {
    $("grid").innerHTML = rows.map(function (i) {
      var rating = i.official_rating
        ? '<span class="rating">' + esc(i.official_rating) + "</span>"
        : '<span class="rating none">o. FSK</span>';
      var res = i.resolution ? '<span class="qbadge">' + esc(i.resolution) + "</span>" : "";
      var comp = i.completeness === "incomplete"
        ? '<span class="qbadge bad">unvollst.</span>' : "";
      var img = i.image_url
        ? '<img loading="lazy" src="' + esc(i.image_url) + '" alt="" ' +
          'onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'grid\'">' +
          '<div class="noimg" style="display:none">' + esc(i.name) + "</div>"
        : '<div class="noimg">' + esc(i.name) + "</div>";
      var chips = (i.tags || []).slice(0, 3).map(tagChip).join("");
      return '<article class="card">' +
        '<div class="poster">' + rating + '<span class="type">' + esc(i.item_type) + "</span>" +
        '<div class="qrow">' + res + comp + "</div>" + img + "</div>" +
        '<div class="meta"><div class="t">' + esc(i.name) + "</div>" +
        '<div class="y">' + (i.year || "") + "</div>" +
        (chips ? '<div class="chips">' + chips + "</div>" : "") + "</div></article>";
    }).join("");
  }

  function cellValue(i, col) {
    if (col.tags) { return (i.tags || []).map(tagChip).join(" ") || '<span style="color:var(--self-text-3)">-</span>'; }
    if (col.comp) { return compCell(i); }
    if (col.list) { return esc((i[col.key] || []).join(", ")) || '<span style="color:var(--self-text-3)">-</span>'; }
    if (col.rating) {
      return i.official_rating ? '<span class="pill">' + esc(i.official_rating) + "</span>"
                               : '<span class="pill bad">ohne</span>';
    }
    if (col.key === "community_rating" && i.community_rating != null) { return Number(i.community_rating).toFixed(1); }
    var v = i[col.key];
    return (v == null || v === "") ? '<span style="color:var(--self-text-3)">-</span>' : esc(v);
  }

  function renderTable(rows) {
    var cols = COLUMNS.filter(function (c) { return c.on; });
    $("thead").innerHTML = "<tr>" + cols.map(function (c) {
      var arrow = state.sortKey === c.key
        ? ' <span class="arrow">' + (state.sortDir === 1 ? "▲" : "▼") + "</span>" : "";
      return '<th data-key="' + c.key + '">' + esc(c.label) + arrow + "</th>";
    }).join("") + "</tr>";
    $("tbody").innerHTML = rows.map(function (i) {
      return "<tr>" + cols.map(function (c) {
        return '<td class="' + (c.cls || "") + '">' + cellValue(i, c) + "</td>";
      }).join("") + "</tr>";
    }).join("");
    $("thead").querySelectorAll("th").forEach(function (th) {
      th.onclick = function () {
        var k = th.getAttribute("data-key");
        if (state.sortKey === k) { state.sortDir *= -1; } else { state.sortKey = k; state.sortDir = 1; }
        render();
      };
    });
  }

  function buildColMenu() {
    $("colPanel").innerHTML = COLUMNS.map(function (c, idx) {
      return '<label><input type="checkbox" data-idx="' + idx + '"' + (c.on ? " checked" : "") +
        "> " + esc(c.label) + "</label>";
    }).join("");
    $("colPanel").querySelectorAll("input").forEach(function (cb) {
      cb.onchange = function () { COLUMNS[+cb.getAttribute("data-idx")].on = cb.checked; render(); };
    });
  }

  function render() {
    var rows = filtered();
    $("count").textContent = rows.length;
    $("empty").classList.toggle("hidden", rows.length > 0);
    if (state.view === "cover") { renderGrid(rows); } else { renderTable(rows); }
  }

  function setView(v) {
    state.view = v;
    $("coverView").classList.toggle("hidden", v !== "cover");
    $("listView").classList.toggle("hidden", v !== "list");
    $("colmenu").hidden = v !== "list";
    $("viewToggle").querySelectorAll("button").forEach(function (b) {
      b.classList.toggle("active", b.getAttribute("data-view") === v);
    });
    render();
  }

  function wire() {
    $("q").oninput = function () { state.q = this.value; render(); };
    $("fLibrary").onchange = function () { state.library = this.value; render(); };
    $("fType").onchange = function () { state.type = this.value; render(); };
    $("fRating").onchange = function () { state.rating = this.value; render(); };
    $("fTag").onchange = function () { state.tag = this.value; render(); };
    $("viewToggle").querySelectorAll("button").forEach(function (b) {
      b.onclick = function () { setView(b.getAttribute("data-view")); };
    });
    $("colBtn").onclick = function (e) { e.stopPropagation(); $("colPanel").classList.toggle("open"); };
    document.addEventListener("click", function () { $("colPanel").classList.remove("open"); });
    $("colPanel").onclick = function (e) { e.stopPropagation(); };
  }

  fillFilters();
  buildColMenu();
  wire();
  render();
})();
