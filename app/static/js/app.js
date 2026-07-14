/* SelfMediaHub - Übersicht: Ansichten, Filter, Sortierung, Tags.
   Theme/Sync/Toast liegen in common.js. */
(function () {
  "use strict";

  var T = window.t || function (k) { return k; };
  var LOCALE = window.__LANG__ === "en" ? "en-GB" : "de-DE";
  var ALL = window.__DATA__ || [];
  var FSK_ON = window.__FSK_ENABLED__ !== false;   // FSK-Feature (nur UI); Standard an
  var state = { view: "cover", q: "", library: "", type: "", rating: "", tag: "", complete: "",
                res: "", codec: "", audioLang: "", subLang: "", sortKey: "sort_name", sortDir: 1 };

  // Erweiterte Filter im Aufklapp-Panel (Reihenfolge = Panel-Reihenfolge)
  var ADV_FILTERS = [
    { id: "fRating", key: "rating" }, { id: "fRes", key: "res" }, { id: "fCodec", key: "codec" },
    { id: "fAudioLang", key: "audioLang" }, { id: "fSubLang", key: "subLang" }, { id: "fTag", key: "tag" },
  ];

  var COLUMNS = [
    { key: "name",             label: T("col.name"),             on: true,  cls: "name" },
    { key: "item_type",        label: T("col.type"),             on: true,  type: true },
    { key: "year",             label: T("col.year"),             on: true,  num: true },
    { key: "library_name",     label: T("col.library"),          on: false },
    { key: "official_rating",  label: T("col.rating"),           on: true,  rating: true },
    { key: "resolution",       label: T("col.resolution"),       on: true },
    { key: "hdr",              label: T("col.hdr"),              on: false },
    { key: "video_codec",      label: T("col.codec"),            on: false },
    { key: "audio_langs",      label: T("col.languages"),        on: false, list: true },
    { key: "completeness",     label: T("col.complete"),         on: true,  comp: true },
    { key: "community_rating", label: T("col.community_rating"), on: false, num: true },
    { key: "size_bytes",       label: T("col.size"),             on: false, size: true },
    { key: "tags",             label: T("col.tags"),             on: true,  tags: true }
  ];

  // Sprach-Codes (inkl. Aliase) auf einen kanonischen Katalog-Key abbilden.
  var LANG_CANON = { ger: "ger", deu: "ger", de: "ger", eng: "eng", en: "eng",
    fre: "fre", fra: "fre", fr: "fre", spa: "spa", es: "spa", ita: "ita", it: "ita",
    jpn: "jpn", ja: "jpn", rus: "rus", ru: "rus", tur: "tur", tr: "tur", pol: "pol", pl: "pol",
    nld: "nld", dut: "nld", nl: "nld", por: "por", pt: "por", kor: "kor", ko: "kor",
    chi: "chi", zho: "chi", zh: "chi", ara: "ara", ar: "ara", und: "und" };

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

  function prefLang() { return window.__PRIMARY_LANG__ || "ger"; }

  // Abdeckung (Prozent) -> 3 Zustaende fuer die Flagge
  function covState(pct) {
    if (pct == null) { return "none"; }
    if (pct >= 100) { return "full"; }
    return pct > 0 ? "partial" : "none";
  }
  function covLabel(state) { return T("cov." + state); }
  function coverFlag(pref, state) {
    if (state === "partial" && window.smhFlagPartial) {
      var pf = window.smhFlagPartial(pref);
      if (pf) { return pf; }
    }
    return (window.smhFlag && window.smhFlag(pref)) ||
      ('<span class="fl-code">' + esc(shortLang(pref)) + "</span>");
  }

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
  function langName(c) {
    if (!c) { return c; }
    var canon = LANG_CANON[String(c).toLowerCase()];
    return canon ? T("langname." + canon) : c;
  }
  function langList(arr) { return (arr || []).map(langName).join(", "); }

  function tagChip(t) {
    var ic = t.icon ? esc(t.icon) + " " : "";
    return '<span class="chip" style="border-color:' + esc(t.color) +
      ';color:' + esc(t.color) + '">' + ic + esc(t.name) + "</span>";
  }
  function compCell(i) {
    var c = i.completeness;
    if (c === "complete") { return '<span class="pill ok">' + esc(T("comp.complete")) + "</span>"; }
    if (c === "incomplete") {
      var m = i.missing_episodes;
      return '<span class="pill bad">' + esc(T("comp.missing")) + (m ? " " + m : "") + "</span>";
    }
    if (c === "unknown") { return '<span class="pill">' + esc(T("comp.unknown")) + "</span>"; }
    return '<span style="color:var(--self-text-3)">-</span>';
  }

  function addOpts(selId, pairs) {
    var sel = $(selId);
    if (!sel) { return; }
    pairs.forEach(function (p) {
      var o = document.createElement("option"); o.value = p[0]; o.textContent = p[1];
      sel.appendChild(o);
    });
  }

  function fillFilters() {
    var ratings = {}, tagNames = {}, resHeight = {}, codecs = {}, audioLangs = {}, subLangs = {};
    ALL.forEach(function (i) {
      if (i.official_rating) { ratings[i.official_rating] = 1; }
      (i.tags || []).forEach(function (t) { tagNames[t.name] = 1; });
      if (i.resolution) { resHeight[i.resolution] = i.resolution === "4K" ? 100000 : (parseInt(i.resolution, 10) || 0); }
      if (i.video_codec) { codecs[i.video_codec] = 1; }
      (i.audio_langs || []).forEach(function (l) { audioLangs[shortLang(l)] = langName(l); });
      (i.subtitle_langs || []).forEach(function (l) { subLangs[shortLang(l)] = langName(l); });
    });
    addOpts("fRating", Object.keys(ratings).sort().map(function (r) { return [r, r]; }));
    // Auflösungen nach Bildhöhe absteigend (hoechste zuerst)
    addOpts("fRes", Object.keys(resHeight).sort(function (a, b) { return resHeight[b] - resHeight[a]; })
      .map(function (r) { return [r, r]; }));
    addOpts("fCodec", Object.keys(codecs).sort().map(function (c) { return [c, c]; }));
    // Sprachen nach Anzeigename sortiert (Wert = Kürzel wie 'DE', damit ger/deu/de zusammenfallen)
    var langSort = function (a, b) { return audioLangs[a].localeCompare(audioLangs[b], "de"); };
    addOpts("fAudioLang", Object.keys(audioLangs).sort(langSort).map(function (k) { return [k, audioLangs[k]]; }));
    addOpts("fSubLang", Object.keys(subLangs).sort(function (a, b) {
      return subLangs[a].localeCompare(subLangs[b], "de"); }).map(function (k) { return [k, subLangs[k]]; }));
    addOpts("fTag", Object.keys(tagNames).sort().map(function (n) { return [n, n]; }));
    // FSK deaktiviert -> Freigabe-Filter ausblenden
    if (!FSK_ON) { var fr = $("fRating"); if (fr) { fr.style.display = "none"; } }
  }

  // Zahl aktiver erweiterter Filter am "Filter"-Button anzeigen
  function updateFilterCount() {
    var n = ADV_FILTERS.filter(function (f) { return state[f.key]; }).length;
    var badge = $("filterCount");
    if (badge) { badge.textContent = n; badge.classList.toggle("hidden", n === 0); }
    var btn = $("filterBtn"); if (btn) { btn.classList.toggle("has-active", n > 0); }
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
      if (state.codec && i.video_codec !== state.codec) { return false; }
      if (state.audioLang && !(i.audio_langs || []).some(function (l) { return shortLang(l) === state.audioLang; })) { return false; }
      if (state.subLang && !(i.subtitle_langs || []).some(function (l) { return shortLang(l) === state.subLang; })) { return false; }
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
      var hasRating = !!i.official_rating;
      var rlabel = i.rating_disp || i.official_rating;   // in bevorzugter Rating-Art
      // Ampel: gruen = in Emby gesperrt/erledigt, neutral = Rating unbestaetigt,
      // .none = keine Freigabe (Warnung). Nur bei aktivem FSK-Feature.
      var cls = "rating" + (hasRating ? "" : " none") +
        (i.rating_locked ? " locked" : "") + (editable ? " editable" : "");
      var did = editable ? ' data-id="' + i.id + '"' : "";
      var lock = i.rating_locked ? '<span class="rlock" aria-hidden="true">&#128274;</span>' : "";
      var rating = FSK_ON
        ? '<span class="' + cls + '"' + did +
          (editable ? ' title="' + esc(T("grid.fsk_change_title")) + '"' : "") + ">" +
          lock + (hasRating ? esc(rlabel) : esc(T("grid.no_fsk"))) + "</span>"
        : "";
      var res = i.resolution ? '<span class="qbadge res">' + esc(i.resolution) + "</span>" : "";
      var comp = i.completeness === "incomplete"
        ? '<span class="qbadge bad">' + esc(T("grid.incomplete_badge")) + "</span>" : "";
      var img = i.image_url
        ? '<img loading="lazy" src="' + esc(i.image_url) + '" alt="" ' +
          'onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'grid\'">' +
          '<div class="noimg" style="display:none">' + esc(i.name) + "</div>"
        : '<div class="noimg">' + esc(i.name) + "</div>";
      var pref = prefLang();
      var pname = esc(langName(pref));
      var aState = covState(i.primary_audio_pct);
      var sState = covState(i.primary_sub_pct);
      var aTitle = T("cover.audio_title").replace("{lang}", pname).replace("{state}", covLabel(aState));
      var sTitle = T("cover.subtitle_title").replace("{lang}", pname).replace("{state}", covLabel(sState));
      var langrow = '<div class="langrow">' +
        '<span class="cbadge cb-lang' + (aState === "none" ? " off" : "") + '" title="' + aTitle + '">' +
          coverFlag(pref, aState) + "</span>" +
        '<span class="cbadge cb-ut' + (sState === "none" ? " off" : "") + '" title="' + sTitle + '">' +
          coverFlag(pref, sState) + " " + esc(T("cover.sub_abbr")) + "</span>" +
        "</div>";
      var chips = (i.tags || []).slice(0, 3).map(tagChip).join("");
      return '<article class="card" data-id="' + i.id + '">' +
        '<div class="poster">' + rating + '<span class="type">' + esc(T("type." + i.item_type)) + "</span>" +
        '<div class="qrow">' + res + comp + "</div>" + langrow + img + "</div>" +
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
    if (col.type) { return esc(T("type." + i.item_type)); }
    if (col.rating) {
      return i.official_rating ? '<span class="pill">' + esc(i.official_rating) + "</span>"
                               : '<span class="pill bad">' + esc(T("grid.rating_none_short")) + "</span>";
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

  function fmtDate(iso) {
    try {
      var d = new Date(iso);
      if (isNaN(d.getTime())) { return iso; }
      return d.toLocaleString(LOCALE, { day: "2-digit", month: "2-digit", year: "numeric",
        hour: "2-digit", minute: "2-digit" });
    } catch (e) { return iso; }
  }
  function initSyncTooltip() {
    var btn = $("syncBtn");
    if (!btn) { return; }
    var ls = window.__LASTSYNC__;
    var text = ls ? T("sync.last").replace("{date}", fmtDate(ls)) : T("sync.never");
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
      return '<button class="fsk-menu-item" data-val="' + v + '">' + (v || T("fsk.none_option")) + "</button>";
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
        if (!res.ok) { throw new Error(res.j.detail || "?"); }
        var item = ALL.filter(function (x) { return String(x.id) === String(id); })[0];
        if (item) { item.official_rating = rating; }
        if (badge) {
          badge.className = (rating ? "rating" : "rating none") + " editable";
          badge.textContent = rating || T("grid.no_fsk");
        }
        window.smhToast(T("msg.fsk_set").replace("{rating}", rating || T("common.removed")), "ok");
      })
      .catch(function (e) { window.smhToast(T("msg.failed_prefix") + e.message, "err"); });
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
    $("fComplete").onchange = function () { state.complete = this.value; render(); };
    // Erweiterte Filter (im Panel) - jeweils state setzen + Aktiv-Zähler aktualisieren
    ADV_FILTERS.forEach(function (f) {
      var el = $(f.id);
      if (el) { el.onchange = function () { state[f.key] = this.value; updateFilterCount(); render(); }; }
    });
    $("filterReset").onclick = function () {
      ADV_FILTERS.forEach(function (f) { state[f.key] = ""; var el = $(f.id); if (el) { el.value = ""; } });
      updateFilterCount(); render();
    };
    $("viewToggle").querySelectorAll("button").forEach(function (b) {
      b.onclick = function () { setView(b.getAttribute("data-view")); };
    });
    $("filterBtn").onclick = function (e) { e.stopPropagation(); $("filterPanel").classList.toggle("open"); };
    $("filterPanel").onclick = function (e) { e.stopPropagation(); };
    $("colBtn").onclick = function (e) { e.stopPropagation(); $("colPanel").classList.toggle("open"); };
    document.addEventListener("click", function () {
      $("colPanel").classList.remove("open");
      $("filterPanel").classList.remove("open");
    });
    $("colPanel").onclick = function (e) { e.stopPropagation(); };

    initSyncTooltip();
  }

  fillFilters();
  updateFilterCount();
  buildColMenu();
  wire();
  render();
})();
