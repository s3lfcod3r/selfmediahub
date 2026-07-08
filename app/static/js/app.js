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
    { key: "size_bytes",       label: "Groesse",       on: false, size: true },
    { key: "tags",             label: "Tags",          on: true,  tags: true }
  ];

  var LANG = { ger: "Deutsch", deu: "Deutsch", de: "Deutsch", eng: "Englisch", en: "Englisch",
    fre: "Franzoesisch", fra: "Franzoesisch", spa: "Spanisch", ita: "Italienisch",
    jpn: "Japanisch", rus: "Russisch", tur: "Tuerkisch", pol: "Polnisch",
    nld: "Niederlaendisch", dut: "Niederlaendisch", por: "Portugiesisch",
    kor: "Koreanisch", chi: "Chinesisch", zho: "Chinesisch", ara: "Arabisch", und: "unbekannt" };

  var $ = function (id) { return document.getElementById(id); };
  var esc = function (s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  };
  function fmtSize(b) {
    if (!b) { return null; }
    var gb = b / 1073741824;
    return gb >= 1 ? gb.toFixed(1) + " GB" : Math.round(b / 1048576) + " MB";
  }
  function langName(c) { return c ? (LANG[String(c).toLowerCase()] || c) : c; }
  function langList(arr) { return (arr || []).map(langName).join(", "); }

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
      return '<article class="card" data-id="' + i.id + '">' +
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
    if (col.size) { return fmtSize(i.size_bytes) || '<span style="color:var(--self-text-3)">-</span>'; }
    if (col.list) { return esc(langList(i[col.key])) || '<span style="color:var(--self-text-3)">-</span>'; }
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
      return '<tr data-id="' + i.id + '">' + cols.map(function (c) {
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

  // -- Detail-Fenster ------------------------------------------------------
  function metaItem(k, v) {
    if (v == null || v === "") { return ""; }
    return '<div><div class="k">' + esc(k) + '</div><div class="v">' + v + "</div></div>";
  }
  function epTech(e) {
    var parts = [];
    if (e.resolution) { parts.push('<span class="qbadge">' + esc(e.resolution) + "</span>"); }
    if (e.video_codec) { parts.push('<span class="pill">' + esc(e.video_codec) + "</span>"); }
    if (fmtSize(e.size_bytes)) { parts.push('<span class="pill">' + fmtSize(e.size_bytes) + "</span>"); }
    if ((e.subtitle_langs || []).length) { parts.push('<span class="pill">UT</span>'); }
    return parts.join("");
  }
  function renderDetail(d) {
    var i = d.item;
    var poster = i.image_url
      ? '<img class="modal-poster" src="' + esc(i.image_url) + '" alt="" onerror="this.style.visibility=\'hidden\'">'
      : '<div class="modal-poster"></div>';
    var badges = [];
    if (i.official_rating) { badges.push('<span class="pill">' + esc(i.official_rating) + "</span>"); }
    else { badges.push('<span class="pill bad">ohne FSK</span>'); }
    if (i.resolution) { badges.push('<span class="qbadge">' + esc(i.resolution) + "</span>"); }
    if (i.hdr && i.hdr !== "SDR") { badges.push('<span class="qbadge">' + esc(i.hdr) + "</span>"); }
    if (i.completeness === "incomplete") { badges.push('<span class="pill bad">fehlen ' + (i.missing_episodes || "?") + "</span>"); }
    if (i.completeness === "complete") { badges.push('<span class="pill ok">komplett</span>'); }
    (i.tags || []).forEach(function (t) { badges.push(tagChip(t)); });

    var meta = "";
    meta += metaItem("Laufzeit", i.runtime_min ? i.runtime_min + " min" : null);
    meta += metaItem("Groesse", fmtSize(i.size_bytes));
    meta += metaItem("Video-Codec", i.video_codec ? esc(i.video_codec) : null);
    meta += metaItem("Audiosprachen", langList(i.audio_langs) || null);
    meta += metaItem("Untertitel", (i.subtitle_langs || []).length ? esc(langList(i.subtitle_langs)) : "keine");
    meta += metaItem("Genres", (i.genres || []).length ? esc(i.genres.join(", ")) : null);
    meta += metaItem("Bibliothek", i.library_name ? esc(i.library_name) : null);
    meta += metaItem("Bewertung", i.community_rating != null ? Number(i.community_rating).toFixed(1) : null);
    if (i.item_type === "Serie") {
      meta += metaItem("Staffeln", (i.have_seasons != null ? i.have_seasons : "?") + (i.tmdb_seasons ? " / " + i.tmdb_seasons : ""));
      meta += metaItem("Episoden", (i.have_episodes != null ? i.have_episodes : "?") + (i.tmdb_episodes ? " / " + i.tmdb_episodes : ""));
      meta += metaItem("Status", i.status ? esc(i.status) : null);
    }
    meta += metaItem("FSK-Vorschlag", i.fsk_suggested ? esc(i.fsk_suggested) : null);

    var eps = "";
    if (d.episodes && d.episodes.length) {
      var curSeason = null;
      d.episodes.forEach(function (e) {
        if (e.season !== curSeason) {
          curSeason = e.season;
          eps += '<div class="season-h">Staffel ' + (curSeason == null ? "?" : curSeason) + "</div>";
        }
        var no = "S" + (e.season == null ? "?" : ("0" + e.season).slice(-2)) +
                 "E" + (e.episode == null ? "?" : ("0" + e.episode).slice(-2));
        if (e.missing) {
          eps += '<div class="ep missing"><span class="no">' + no + '</span>' +
            '<span class="en">nicht vorhanden</span>' +
            '<span class="et"><span class="pill bad">fehlt</span></span></div>';
        } else {
          var title = e.path ? ' title="' + esc(e.path) + '"' : "";
          eps += '<div class="ep"' + title + '><span class="no">' + no + '</span>' +
            '<span class="en">' + esc(e.name || "") + '</span>' +
            '<span class="et">' + epTech(e) + "</span></div>";
        }
      });
    }
    var note = d.note ? '<div class="modal-note">' + esc(d.note) + "</div>" : "";

    $("modalPanel").innerHTML =
      '<div class="modal-head">' + poster +
        '<div><div class="modal-title">' + esc(i.name) + "</div>" +
        '<div class="modal-sub">' + esc(i.item_type) + (i.year ? " &middot; " + i.year : "") +
          (i.library_name ? " &middot; " + esc(i.library_name) : "") + "</div>" +
        '<div class="modal-badges">' + badges.join("") + "</div></div></div>" +
      '<div class="modal-body">' +
        '<div class="meta-grid">' + meta + "</div>" +
        (i.path ? '<div class="pathline"><div class="k">Pfad im Verzeichnis</div>' +
                  '<div class="pv mono">' + esc(i.path) + "</div></div>" : "") +
        (i.overview ? '<div class="overview">' + esc(i.overview) + "</div>" : "") +
        note + eps + "</div>";
  }
  function openDetail(id) {
    if (!id) { return; }
    $("modalPanel").innerHTML = '<div class="modal-loading">Lade Details ...</div>';
    $("modal").classList.add("open");
    fetch("/api/items/" + id + "/detail")
      .then(function (r) { return r.json(); })
      .then(renderDetail)
      .catch(function () { $("modalPanel").innerHTML = '<div class="modal-loading">Details konnten nicht geladen werden.</div>'; });
  }
  function closeModal() { $("modal").classList.remove("open"); }

  function wire() {
    $("grid").onclick = function (e) {
      var c = e.target.closest(".card"); if (c) { openDetail(c.getAttribute("data-id")); }
    };
    $("tbody").onclick = function (e) {
      var tr = e.target.closest("tr"); if (tr && tr.getAttribute("data-id")) { openDetail(tr.getAttribute("data-id")); }
    };
    $("modalClose").onclick = closeModal;
    $("modal").onclick = function (e) { if (e.target === $("modal")) { closeModal(); } };
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") { closeModal(); } });

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
