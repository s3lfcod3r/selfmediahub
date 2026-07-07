/* SelfMediaHub - Frontend-Logik: Ansichten, Filter, Sortierung, Sync.
   Daten kommen als window.__DATA__ (aus der lokalen DB gerendert). */
(function () {
  "use strict";

  var ALL = window.__DATA__ || [];
  var state = { view: "cover", q: "", library: "", type: "", rating: "",
                sortKey: "sort_name", sortDir: 1 };

  // Sichtbare Tabellen-Spalten (frei zuschaltbar).
  var COLUMNS = [
    { key: "name",             label: "Titel",       on: true,  cls: "name" },
    { key: "item_type",        label: "Typ",         on: true },
    { key: "year",             label: "Jahr",        on: true,  num: true },
    { key: "library_name",     label: "Bibliothek",  on: true },
    { key: "official_rating",  label: "Freigabe",    on: true,  rating: true },
    { key: "community_rating", label: "Bewertung",   on: true,  num: true },
    { key: "child_count",      label: "Staffeln",    on: false, num: true },
    { key: "genres",           label: "Genres",      on: false }
  ];

  var $ = function (id) { return document.getElementById(id); };
  var esc = function (s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  };

  // -- Freigabe-Filter aus den Daten befuellen -----------------------------
  function fillRatingOptions() {
    var seen = {};
    ALL.forEach(function (i) { if (i.official_rating) seen[i.official_rating] = 1; });
    var sel = $("fRating");
    Object.keys(seen).sort().forEach(function (r) {
      var o = document.createElement("option");
      o.value = r; o.textContent = r; sel.appendChild(o);
    });
  }

  // -- Filtern + Sortieren -------------------------------------------------
  function filtered() {
    var q = state.q.toLowerCase();
    var rows = ALL.filter(function (i) {
      if (state.library && i.library_name !== state.library) return false;
      if (state.type && i.item_type !== state.type) return false;
      if (state.rating === "__none__" && i.official_rating) return false;
      if (state.rating && state.rating !== "__none__" && i.official_rating !== state.rating) return false;
      if (q && i.name.toLowerCase().indexOf(q) === -1) return false;
      return true;
    });
    var k = state.sortKey, dir = state.sortDir;
    rows.sort(function (a, b) {
      var va = a[k], vb = b[k];
      if (k === "sort_name" || k === "name") { va = (a.sort_name || a.name || "").toLowerCase(); vb = (b.sort_name || b.name || "").toLowerCase(); }
      if (va == null) return 1; if (vb == null) return -1;
      if (typeof va === "number" && typeof vb === "number") return (va - vb) * dir;
      return String(va).localeCompare(String(vb), "de") * dir;
    });
    return rows;
  }

  // -- Cover-Grid ----------------------------------------------------------
  function renderGrid(rows) {
    var html = rows.map(function (i) {
      var rating = i.official_rating
        ? '<span class="rating">' + esc(i.official_rating) + "</span>"
        : '<span class="rating none">o. FSK</span>';
      var img = i.image_url
        ? '<img loading="lazy" src="' + esc(i.image_url) + '" alt="" ' +
          'onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'grid\'">' +
          '<div class="noimg" style="display:none">' + esc(i.name) + "</div>"
        : '<div class="noimg">' + esc(i.name) + "</div>";
      return '<article class="card">' +
        '<div class="poster">' + rating +
        '<span class="type">' + esc(i.item_type) + "</span>" + img + "</div>" +
        '<div class="meta"><div class="t">' + esc(i.name) + "</div>" +
        '<div class="y">' + (i.year || "") + "</div></div></article>";
    }).join("");
    $("grid").innerHTML = html;
  }

  // -- Tabelle -------------------------------------------------------------
  function cellValue(i, col) {
    if (col.key === "genres") return esc((i.genres || []).join(", "));
    if (col.rating) {
      return i.official_rating
        ? '<span class="pill">' + esc(i.official_rating) + "</span>"
        : '<span class="pill none">ohne</span>';
    }
    if (col.key === "community_rating" && i.community_rating != null)
      return Number(i.community_rating).toFixed(1);
    var v = i[col.key];
    return v == null || v === "" ? '<span style="color:var(--self-text-3)">-</span>' : esc(v);
  }

  function renderTable(rows) {
    var cols = COLUMNS.filter(function (c) { return c.on; });
    var head = "<tr>" + cols.map(function (c) {
      var arrow = state.sortKey === c.key
        ? ' <span class="arrow">' + (state.sortDir === 1 ? "▲" : "▼") + "</span>" : "";
      return '<th data-key="' + c.key + '">' + esc(c.label) + arrow + "</th>";
    }).join("") + "</tr>";
    $("thead").innerHTML = head;

    $("tbody").innerHTML = rows.map(function (i) {
      return "<tr>" + cols.map(function (c) {
        return '<td class="' + (c.cls || "") + '">' + cellValue(i, c) + "</td>";
      }).join("") + "</tr>";
    }).join("");

    $("thead").querySelectorAll("th").forEach(function (th) {
      th.onclick = function () {
        var k = th.getAttribute("data-key");
        if (state.sortKey === k) state.sortDir *= -1;
        else { state.sortKey = k; state.sortDir = 1; }
        render();
      };
    });
  }

  // -- Spaltenmenue --------------------------------------------------------
  function buildColMenu() {
    $("colPanel").innerHTML = COLUMNS.map(function (c, idx) {
      return '<label><input type="checkbox" data-idx="' + idx + '"' +
        (c.on ? " checked" : "") + "> " + esc(c.label) + "</label>";
    }).join("");
    $("colPanel").querySelectorAll("input").forEach(function (cb) {
      cb.onchange = function () {
        COLUMNS[+cb.getAttribute("data-idx")].on = cb.checked;
        render();
      };
    });
  }

  // -- Render-Dispatch -----------------------------------------------------
  function render() {
    var rows = filtered();
    $("count").textContent = rows.length;
    $("empty").classList.toggle("hidden", rows.length > 0);
    if (state.view === "cover") { renderGrid(rows); }
    else { renderTable(rows); }
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

  // -- Toast ---------------------------------------------------------------
  var toastTimer;
  function toast(msg, kind) {
    var t = $("toast");
    t.textContent = msg;
    t.className = "toast show " + (kind || "");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { t.className = "toast"; }, 4000);
  }

  // -- Sync ----------------------------------------------------------------
  function doSync() {
    var btn = $("syncBtn");
    btn.disabled = true;
    $("syncLabel").innerHTML = 'Lese ein <span class="spin" style="display:inline-block">↻</span>';
    fetch("/api/sync", { method: "POST" })
      .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
      .then(function (res) {
        if (!res.ok) throw new Error(res.j.detail || "Fehler beim Einlesen");
        toast(res.j.count + " Eintraege eingelesen - Seite wird aktualisiert ...", "ok");
        setTimeout(function () { location.reload(); }, 900);
      })
      .catch(function (e) {
        toast("Sync fehlgeschlagen: " + e.message, "err");
        btn.disabled = false;
        $("syncLabel").textContent = "Neu einlesen";
      });
  }

  // -- Theme ---------------------------------------------------------------
  function initTheme() {
    var saved = localStorage.getItem("smh-theme") || "dark";
    document.documentElement.setAttribute("data-theme", saved);
    $("themeBtn").onclick = function () {
      var cur = document.documentElement.getAttribute("data-theme");
      var next = cur === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
      localStorage.setItem("smh-theme", next);
    };
  }

  // -- Verdrahtung ---------------------------------------------------------
  function wire() {
    $("q").oninput = function () { state.q = this.value; render(); };
    $("fLibrary").onchange = function () { state.library = this.value; render(); };
    $("fType").onchange = function () { state.type = this.value; render(); };
    $("fRating").onchange = function () { state.rating = this.value; render(); };
    $("viewToggle").querySelectorAll("button").forEach(function (b) {
      b.onclick = function () { setView(b.getAttribute("data-view")); };
    });
    $("colBtn").onclick = function (e) {
      e.stopPropagation(); $("colPanel").classList.toggle("open");
    };
    document.addEventListener("click", function () { $("colPanel").classList.remove("open"); });
    $("colPanel").onclick = function (e) { e.stopPropagation(); };
    $("syncBtn").onclick = doSync;
  }

  fillRatingOptions();
  buildColMenu();
  initTheme();
  wire();
  render();
})();
