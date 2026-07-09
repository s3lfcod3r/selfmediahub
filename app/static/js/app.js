/* SelfMediaHub - Übersicht: Ansichten, Filter, Sortierung, Tags.
   Theme/Sync/Toast liegen in common.js. */
(function () {
  "use strict";

  var ALL = window.__DATA__ || [];
  var state = { view: "cover", q: "", library: "", type: "", rating: "", tag: "", complete: "",
                res: "", sortKey: "sort_name", sortDir: 1 };

  var COLUMNS = [
    { key: "name",             label: "Titel",         on: true,  cls: "name" },
    { key: "item_type",        label: "Typ",           on: true },
    { key: "year",             label: "Jahr",          on: true,  num: true },
    { key: "library_name",     label: "Bibliothek",    on: false },
    { key: "official_rating",  label: "Freigabe",      on: true,  rating: true },
    { key: "resolution",       label: "Auflösung",    on: true },
    { key: "hdr",              label: "HDR",           on: false },
    { key: "video_codec",      label: "Codec",         on: false },
    { key: "audio_langs",      label: "Sprachen",      on: false, list: true },
    { key: "completeness",     label: "Vollständig",  on: true,  comp: true },
    { key: "community_rating", label: "Bewertung",     on: false, num: true },
    { key: "size_bytes",       label: "Größe",       on: false, size: true },
    { key: "tags",             label: "Tags",          on: true,  tags: true }
  ];

  var LANG = { ger: "Deutsch", deu: "Deutsch", de: "Deutsch", eng: "Englisch", en: "Englisch",
    fre: "Franzoesisch", fra: "Franzoesisch", spa: "Spanisch", ita: "Italienisch",
    jpn: "Japanisch", rus: "Russisch", tur: "Tuerkisch", pol: "Polnisch",
    nld: "Niederlaendisch", dut: "Niederlaendisch", por: "Portugiesisch",
    kor: "Koreanisch", chi: "Chinesisch", zho: "Chinesisch", ara: "Arabisch", und: "unbekannt" };

  var SHORTLANG = { ger: "DE", deu: "DE", de: "DE", eng: "EN", en: "EN", fre: "FR", fra: "FR", fr: "FR",
    spa: "ES", es: "ES", ita: "IT", it: "IT", jpn: "JP", ja: "JP", rus: "RU", tur: "TR", pol: "PL",
    nld: "NL", dut: "NL", por: "PT", kor: "KO", chi: "ZH", zho: "ZH", ara: "AR", und: "?" };
  function shortLang(c) {
    if (!c) { return "?"; }
    var k = String(c).toLowerCase();
    return SHORTLANG[k] || k.slice(0, 2).toUpperCase();
  }

  var FLAG = { ger: "🇩🇪", deu: "🇩🇪", de: "🇩🇪", eng: "🇬🇧", en: "🇬🇧",
    fre: "🇫🇷", fra: "🇫🇷", fr: "🇫🇷", spa: "🇪🇸", es: "🇪🇸", ita: "🇮🇹", it: "🇮🇹",
    jpn: "🇯🇵", ja: "🇯🇵", rus: "🇷🇺", ru: "🇷🇺", tur: "🇹🇷", tr: "🇹🇷", pol: "🇵🇱", pl: "🇵🇱",
    nld: "🇳🇱", dut: "🇳🇱", nl: "🇳🇱", por: "🇵🇹", pt: "🇵🇹", kor: "🇰🇷", ko: "🇰🇷",
    chi: "🇨🇳", zho: "🇨🇳", zh: "🇨🇳", ara: "🇸🇦", ar: "🇸🇦" };
  function flag(c) { return FLAG[String(c || "").toLowerCase()] || null; }

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
    var ratings = {}, tagNames = {}, resHeight = {};
    ALL.forEach(function (i) {
      if (i.official_rating) { ratings[i.official_rating] = 1; }
      (i.tags || []).forEach(function (t) { tagNames[t.name] = 1; });
      if (i.resolution) { resHeight[i.resolution] = i.resolution === "4K" ? 100000 : (parseInt(i.resolution, 10) || 0); }
    });
    Object.keys(ratings).sort().forEach(function (r) {
      var o = document.createElement("option"); o.value = r; o.textContent = r; $("fRating").appendChild(o);
    });
    // Auflösungen nach Bildhöhe absteigend (hoechste zuerst)
    Object.keys(resHeight).sort(function (a, b) { return resHeight[b] - resHeight[a]; }).forEach(function (r) {
      var o = document.createElement("option"); o.value = r; o.textContent = r; $("fRes").appendChild(o);
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
      if (state.rating === "__suspicious__" && !(i.fsk_suspicious && !i.fsk_acked)) { return false; }
      if (state.rating && state.rating !== "__none__" && state.rating !== "__suspicious__" && i.official_rating !== state.rating) { return false; }
      if (state.res === "__lt720__" && !(i.height && i.height < 720)) { return false; }
      if (state.res && state.res !== "__lt720__" && i.resolution !== state.res) { return false; }
      if (state.tag && !(i.tags || []).some(function (t) { return t.name === state.tag; })) { return false; }
      if (state.complete && i.completeness !== state.complete) { return false; }
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

  var FSK_STD = ["DE-0", "DE-6", "DE-12", "DE-16", "DE-18"];

  function renderGrid(rows) {
    $("grid").innerHTML = rows.map(function (i) {
      var editable = window.__ALLOW_WRITE__ && i.source_kind === "emby";
      var cls = "rating" + (i.official_rating ? "" : " none") + (editable ? " editable" : "");
      var did = editable ? ' data-id="' + i.id + '"' : "";
      var rating = '<span class="' + cls + '"' + did +
        (editable ? ' title="FSK ändern"' : "") + ">" +
        (i.official_rating ? esc(i.official_rating) : "o. FSK") + "</span>";
      var res = i.resolution ? '<span class="qbadge res">' + esc(i.resolution) + "</span>" : "";
      var comp = i.completeness === "incomplete"
        ? '<span class="qbadge bad">unvollst.</span>' : "";
      var lang = "";
      if (i.item_type === "Film") {
        var flags = (i.audio_langs || []).slice(0, 4).map(function (l) {
          var f = flag(l);
          return '<span class="lbadge flag" title="' + esc(langName(l)) + '">' +
            (f || esc(shortLang(l))) + "</span>";
        }).join("");
        var subs = (i.subtitle_langs || []).length > 0;
        var ut = '<span class="lbadge ut' + (subs ? "" : " none") + '" title="' +
          (subs ? esc(langList(i.subtitle_langs)) : "keine Untertitel") + '">UT</span>';
        lang = '<div class="langrow">' + flags + ut + "</div>";
      }
      var img = i.image_url
        ? '<img loading="lazy" src="' + esc(i.image_url) + '" alt="" ' +
          'onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'grid\'">' +
          '<div class="noimg" style="display:none">' + esc(i.name) + "</div>"
        : '<div class="noimg">' + esc(i.name) + "</div>";
      var chips = (i.tags || []).slice(0, 3).map(tagChip).join("");
      return '<article class="card" data-id="' + i.id + '">' +
        '<div class="poster">' + rating + '<span class="type">' + esc(i.item_type) + "</span>" +
        '<div class="qrow">' + res + comp + "</div>" + lang + img + "</div>" +
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

  // Cover-Anzeige-Optionen (FSK-Ecke / Auflösung / Sprache) merken in localStorage
  function initDisp() {
    var saved = {};
    try { saved = JSON.parse(localStorage.getItem("smh-disp") || "{}"); } catch (e) { saved = {}; }
    ["fsk", "res", "lang"].forEach(function (key) {
      var on = saved[key] !== false;
      $("grid").classList.toggle("hide-" + key, !on);
      var cb = $("dispPanel").querySelector('[data-disp="' + key + '"]');
      if (cb) { cb.checked = on; }
    });
    $("dispPanel").querySelectorAll("input").forEach(function (cb) {
      cb.onchange = function () {
        var key = cb.getAttribute("data-disp");
        $("grid").classList.toggle("hide-" + key, !cb.checked);
        saved[key] = cb.checked;
        try { localStorage.setItem("smh-disp", JSON.stringify(saved)); } catch (e) { /* ignore */ }
      };
    });
  }

  function fmtDate(iso) {
    try {
      var d = new Date(iso);
      if (isNaN(d.getTime())) { return iso; }
      return d.toLocaleString("de-DE", { day: "2-digit", month: "2-digit", year: "numeric",
        hour: "2-digit", minute: "2-digit" });
    } catch (e) { return iso; }
  }
  function initSyncTooltip() {
    var btn = $("syncBtn");
    if (!btn) { return; }
    var ls = window.__LASTSYNC__;
    var text = ls ? ("Zuletzt eingelesen: " + fmtDate(ls)) : "Noch nie eingelesen";
    btn.title = text;
    var tip = document.createElement("div");
    tip.className = "smh-tip hidden";
    tip.textContent = text;
    document.body.appendChild(tip);
    btn.addEventListener("mouseenter", function () {
      var r = btn.getBoundingClientRect();
      tip.style.top = Math.round(r.bottom + 8) + "px";
      tip.style.right = Math.round(window.innerWidth - r.right) + "px";
      tip.classList.remove("hidden");
    });
    btn.addEventListener("mouseleave", function () { tip.classList.add("hidden"); });
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

  var fskMenu = null;
  function buildFskMenu() {
    if (fskMenu) { return fskMenu; }
    fskMenu = document.createElement("div");
    fskMenu.className = "fsk-menu hidden";
    fskMenu.innerHTML = FSK_STD.concat([""]).map(function (v) {
      return '<button class="fsk-menu-item" data-val="' + v + '">' + (v || "— keine —") + "</button>";
    }).join("");
    document.body.appendChild(fskMenu);
    fskMenu.addEventListener("click", function (e) {
      var b = e.target.closest(".fsk-menu-item"); if (!b) { return; }
      saveFsk(fskMenu.getAttribute("data-id"), b.getAttribute("data-val"), fskMenu._badge);
      hideFskMenu();
    });
    return fskMenu;
  }
  function hideFskMenu() { if (fskMenu) { fskMenu.classList.add("hidden"); } }
  function openFskMenu(badge) {
    var m = buildFskMenu();
    var id = badge.getAttribute("data-id");
    m.setAttribute("data-id", id);
    m._badge = badge;
    var item = ALL.filter(function (x) { return String(x.id) === String(id); })[0] || {};
    var cur = item.official_rating || "";
    Array.prototype.forEach.call(m.querySelectorAll(".fsk-menu-item"), function (b) {
      b.classList.toggle("active", b.getAttribute("data-val") === cur);
    });
    var r = badge.getBoundingClientRect();
    m.style.left = Math.round(r.left) + "px";
    m.style.top = Math.round(r.bottom + 6) + "px";
    m.classList.remove("hidden");
  }
  function saveFsk(id, rating, badge) {
    fetch("/api/fsk/write", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ item_id: +id, rating: rating }) })
      .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
      .then(function (res) {
        if (!res.ok) { throw new Error(res.j.detail || "Fehler"); }
        var item = ALL.filter(function (x) { return String(x.id) === String(id); })[0];
        if (item) { item.official_rating = rating; }
        if (badge) {
          badge.className = (rating ? "rating" : "rating none") + " editable";
          badge.textContent = rating || "o. FSK";
        }
        window.smhToast("FSK " + (rating || "(entfernt)") + " gesetzt", "ok");
      })
      .catch(function (e) { window.smhToast("Fehlgeschlagen: " + e.message, "err"); });
  }

  function wire() {
    $("grid").onclick = function (e) {
      var badge = e.target.closest(".rating.editable");
      if (badge) { e.stopPropagation(); openFskMenu(badge); return; }
      var c = e.target.closest(".card"); if (c) { window.smhOpenDetail(c.getAttribute("data-id")); }
    };
    document.addEventListener("click", function (e) {
      if (fskMenu && !fskMenu.classList.contains("hidden") &&
          !e.target.closest(".fsk-menu") && !e.target.closest(".rating.editable")) {
        hideFskMenu();
      }
    });
    window.addEventListener("scroll", hideFskMenu, true);
    $("tbody").onclick = function (e) {
      var tr = e.target.closest("tr"); if (tr && tr.getAttribute("data-id")) { window.smhOpenDetail(tr.getAttribute("data-id")); }
    };

    $("q").oninput = function () { state.q = this.value; render(); };
    $("fLibrary").onchange = function () { state.library = this.value; render(); };
    $("fType").onchange = function () { state.type = this.value; render(); };
    $("fRating").onchange = function () { state.rating = this.value; render(); };
    $("fRes").onchange = function () { state.res = this.value; render(); };
    $("fTag").onchange = function () { state.tag = this.value; render(); };
    $("fComplete").onchange = function () { state.complete = this.value; render(); };
    $("viewToggle").querySelectorAll("button").forEach(function (b) {
      b.onclick = function () { setView(b.getAttribute("data-view")); };
    });
    $("colBtn").onclick = function (e) { e.stopPropagation(); $("colPanel").classList.toggle("open"); };
    $("dispBtn").onclick = function (e) { e.stopPropagation(); $("dispPanel").classList.toggle("open"); };
    document.addEventListener("click", function () {
      $("colPanel").classList.remove("open"); $("dispPanel").classList.remove("open");
    });
    $("colPanel").onclick = function (e) { e.stopPropagation(); };
    $("dispPanel").onclick = function (e) { e.stopPropagation(); };

    initSyncTooltip();
  }

  fillFilters();
  buildColMenu();
  initDisp();
  wire();
  render();
})();
