/* Gemeinsames Detail-Fenster (Modal). Auf allen Seiten nutzbar:
   window.smhOpenDetail(id). Braucht #modal / #modalPanel / #modalClose. */
(function () {
  "use strict";

  var LANG = { ger: "Deutsch", deu: "Deutsch", de: "Deutsch", eng: "Englisch", en: "Englisch",
    fre: "Französisch", fra: "Französisch", spa: "Spanisch", ita: "Italienisch",
    jpn: "Japanisch", rus: "Russisch", tur: "Türkisch", pol: "Polnisch",
    nld: "Niederländisch", dut: "Niederländisch", por: "Portugiesisch",
    kor: "Koreanisch", chi: "Chinesisch", zho: "Chinesisch", ara: "Arabisch", und: "unbekannt" };

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function fmtSize(b) {
    if (!b) { return null; }
    var gb = b / 1073741824;
    return gb >= 1 ? gb.toFixed(1) + " GB" : Math.round(b / 1048576) + " MB";
  }
  function langName(c) { return c ? (LANG[String(c).toLowerCase()] || c) : c; }
  function langList(a) { return (a || []).map(langName).join(", "); }

  var SHORTLANG = { ger: "DE", deu: "DE", de: "DE", eng: "EN", en: "EN", fre: "FR", fra: "FR", fr: "FR",
    spa: "ES", es: "ES", ita: "IT", it: "IT", jpn: "JP", ja: "JP", rus: "RU", ru: "RU", tur: "TR", tr: "TR",
    pol: "PL", pl: "PL", nld: "NL", dut: "NL", nl: "NL", por: "PT", pt: "PT", kor: "KO", ko: "KO",
    chi: "ZH", zho: "ZH", zh: "ZH", ara: "AR", ar: "AR", und: "?" };
  function shortLang(c) { if (!c) { return "?"; } var k = String(c).toLowerCase(); return SHORTLANG[k] || k.slice(0, 2).toUpperCase(); }
  var FLAG = { ger: "🇩🇪", deu: "🇩🇪", de: "🇩🇪", eng: "🇬🇧", en: "🇬🇧", fre: "🇫🇷", fra: "🇫🇷", fr: "🇫🇷",
    spa: "🇪🇸", es: "🇪🇸", ita: "🇮🇹", it: "🇮🇹", jpn: "🇯🇵", ja: "🇯🇵", rus: "🇷🇺", ru: "🇷🇺", tur: "🇹🇷", tr: "🇹🇷",
    pol: "🇵🇱", pl: "🇵🇱", nld: "🇳🇱", dut: "🇳🇱", nl: "🇳🇱", por: "🇵🇹", pt: "🇵🇹", kor: "🇰🇷", ko: "🇰🇷",
    chi: "🇨🇳", zho: "🇨🇳", zh: "🇨🇳", ara: "🇸🇦", ar: "🇸🇦" };
  function flag(c) { return FLAG[String(c || "").toLowerCase()] || null; }
  function tagChip(t) {
    var ic = t.icon ? esc(t.icon) + " " : "";
    return '<span class="chip" style="border-color:' + esc(t.color) + ";color:" + esc(t.color) +
      '">' + ic + esc(t.name) + "</span>";
  }
  function metaItem(k, v) {
    if (v == null || v === "") { return ""; }
    return '<div><div class="k">' + esc(k) + '</div><div class="v">' + v + "</div></div>";
  }
  function prefLang() { return window.__PRIMARY_LANG__ || "ger"; }
  function hasLang(list, pref) {
    var p = shortLang(pref);
    return (list || []).some(function (l) { return shortLang(l) === p; });
  }
  function epTech(e) {
    var pref = prefLang();
    var svg = (window.smhFlag && window.smhFlag(pref)) || null;
    var pflag = svg || ('<span class="fl-code">' + esc(shortLang(pref)) + "</span>");
    var name = esc(langName(pref));
    var audioOk = hasLang(e.audio_langs, pref);
    var subOk = hasLang(e.subtitle_langs, pref);
    return (
      '<span class="qbadge et-badge et-res' + (e.resolution ? "" : " et-empty") + '">' +
        (e.resolution ? esc(e.resolution) : "–") + "</span>" +
      '<span class="pill et-badge et-codec' + (e.video_codec ? "" : " et-empty") + '">' +
        (e.video_codec ? esc(e.video_codec) : "–") + "</span>" +
      '<span class="pill et-badge et-size' + (fmtSize(e.size_bytes) ? "" : " et-empty") + '">' +
        (fmtSize(e.size_bytes) || "–") + "</span>" +
      '<span class="lbadge et-badge et-lang' + (audioOk ? "" : " et-off") + '" title="' +
        name + "-Tonspur " + (audioOk ? "vorhanden" : "fehlt") + '">' + pflag + "</span>" +
      '<span class="pill et-badge et-ut' + (subOk ? "" : " et-off") + '" title="' +
        name + "-Untertitel " + (subOk ? "vorhanden" : "fehlt") + '">' + pflag + " UT</span>"
    );
  }
  function epDetailRow(k, v) {
    if (v == null || v === "") { return ""; }
    return '<div class="epd-row"><span class="epd-k">' + esc(k) + '</span><span class="epd-v">' + v + "</span></div>";
  }
  function epDetail(e) {
    var h = "";
    h += epDetailRow("Auflösung", (e.width && e.height) ? (e.width + " × " + e.height) :
                     (e.resolution ? esc(e.resolution) : null));
    h += epDetailRow("HDR", (e.hdr && e.hdr !== "SDR") ? esc(e.hdr) : null);
    h += epDetailRow("Video-Codec", e.video_codec ? esc(e.video_codec) : null);
    h += epDetailRow("Audiosprachen", langList(e.audio_langs) || null);
    h += epDetailRow("Untertitel", (e.subtitle_langs || []).length ? esc(langList(e.subtitle_langs)) : "keine");
    h += epDetailRow("Größe", fmtSize(e.size_bytes));
    h += epDetailRow("Laufzeit", e.runtime_min ? e.runtime_min + " min" : null);
    h += e.path ? '<div class="epd-path mono">' + esc(e.path) + "</div>" : "";
    return h || '<div class="epd-row"><span class="epd-v" style="color:var(--self-text-3)">Keine weiteren Angaben</span></div>';
  }

  function seasonSummary(s, item) {
    if (!s || !s.total_tmdb) { return ""; }
    var miss = Math.max(0, s.total_tmdb - s.total_have);
    var head = "Folgen-Vollständigkeit &middot; " + s.total_have + " / " + s.total_tmdb +
      " vorhanden" + (miss > 0 ? " &middot; " + miss + (miss === 1 ? " fehlt" : " fehlen") : " &middot; komplett");
    // Verlaessliche Staffel-Zuordnung -> Pro-Staffel-Aufschluesselung
    if (s.reliable && s.seasons && s.seasons.length) {
      var rows = s.seasons.map(function (r) {
        var m = Math.max(0, r.tmdb_total - r.have);
        var cls = m > 0 ? " miss" : " full";
        var right = m > 0 ? (m + (m === 1 ? " fehlt" : " fehlen")) : "komplett";
        return '<div class="ssum-row' + cls + '">' +
          '<span class="ssum-s">Staffel ' + r.season + "</span>" +
          '<span class="ssum-c">' + r.have + " / " + r.tmdb_total + "</span>" +
          '<span class="ssum-b">' + right + "</span></div>";
      }).join("");
      return '<div class="ssum"><div class="ssum-h">' + head + "</div>" + rows +
        '<div class="ssum-foot">Einzelne Folgennummern lassen sich bei dieser Serie nicht ' +
        "sicher zuordnen (Emby-Nummerierung weicht von TMDb ab) - daher nur die Staffel-Summen.</div></div>";
    }
    // Nummerierung passt gar nicht -> wenigstens die Gesamtzahl ehrlich nennen
    var hs = (item && item.have_seasons != null) ? item.have_seasons : "?";
    var ts = (item && item.tmdb_seasons != null) ? item.tmdb_seasons : "?";
    return '<div class="ssum"><div class="ssum-h">' + head + "</div>" +
      '<div class="ssum-foot">Emby teilt die Serie in ' + esc(hs) + " Staffeln ein, TMDb in " +
      esc(ts) + " - deshalb lässt sich nur die Gesamtzahl bestimmen, nicht welche Folgen genau fehlen.</div></div>";
  }

  function renderDetail(d) {
    var i = d.item;
    var fskOn = window.__FSK_ENABLED__ !== false;   // FSK-Feature (nur UI); Standard an
    var poster = i.image_url
      ? '<img class="modal-poster" src="' + esc(i.image_url) + '" alt="" onerror="this.style.visibility=\'hidden\'">'
      : '<div class="modal-poster"></div>';
    var badges = [];
    if (fskOn) {
      if (i.official_rating) { badges.push('<span class="pill">' + esc(i.official_rating) + "</span>"); }
      else { badges.push('<span class="pill bad">ohne FSK</span>'); }
    }
    if (i.resolution) { badges.push('<span class="qbadge">' + esc(i.resolution) + "</span>"); }
    if (i.hdr && i.hdr !== "SDR") { badges.push('<span class="qbadge">' + esc(i.hdr) + "</span>"); }
    if (i.completeness === "incomplete") { badges.push('<span class="pill bad">fehlen ' + (i.missing_episodes || "?") + "</span>"); }
    if (i.completeness === "complete") { badges.push('<span class="pill ok">komplett</span>'); }
    (i.tags || []).forEach(function (t) { badges.push(tagChip(t)); });

    var meta = "";
    meta += metaItem("Laufzeit", i.runtime_min ? i.runtime_min + " min" : null);
    meta += metaItem("Größe", fmtSize(i.size_bytes));
    meta += metaItem("Auflösung", (i.width && i.height) ? (i.width + " × " + i.height) :
                     (i.resolution ? esc(i.resolution) : null));
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
    if (fskOn) { meta += metaItem("FSK-Vorschlag", i.fsk_suggested ? esc(i.fsk_suggested) : null); }

    var eps = "";
    if (d.episodes && d.episodes.length) {
      var curSeason = null;
      d.episodes.forEach(function (e, idx) {
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
          eps += '<div class="ep ep-clickable" data-epidx="' + idx + '"><span class="no">' + no + '</span>' +
            '<span class="en">' + esc(e.name || "") + '</span>' +
            '<span class="et">' + epTech(e) + '<span class="ep-chev">&rsaquo;</span></span></div>' +
            '<div class="ep-detail hidden" id="epd-' + idx + '">' + epDetail(e) + "</div>";
        }
      });
    }
    var note = d.note ? '<div class="modal-note">' + esc(d.note) + "</div>" : "";

    var fskEditor = "";
    if (fskOn && i.source_kind === "emby") {
      var opts = ["DE-0", "DE-6", "DE-12", "DE-16", "DE-18"].map(function (v) {
        return '<option value="' + v + '"' + (i.official_rating === v ? " selected" : "") + ">" + v + "</option>";
      }).join("");
      var dis = d.allow_write ? "" : " disabled";
      fskEditor =
        '<div class="fsk-editor"><div class="k">FSK-Freigabe selbst festlegen</div>' +
        '<div class="fsk-row">' +
          '<select class="field" id="fskSel"' + dis + ">" + opts +
            '<option value="">&mdash; keine &mdash;</option></select>' +
          '<button class="btn btn-primary" id="fskSave" data-id="' + i.id + '"' + dis +
            ">In Emby speichern</button>" +
        "</div>" +
        (d.allow_write ? "" :
          '<div class="modal-note">Zum Ändern am Container <code>ALLOW_EMBY_WRITE=1</code> setzen (Standard: read-only).</div>') +
        "</div>";
    }

    var ackBox = "";
    if (fskOn && i.fsk_suspicious && !i.fsk_acked) {
      ackBox = '<div class="fsk-ack-box"><span>Freigabe wirkt unplausibel' +
        (i.fsk_reason ? ": " + esc(i.fsk_reason) : "") + "</span>" +
        '<button class="btn btn-small" id="ackBtn" data-id="' + i.id + '">Passt so</button></div>';
    }

    document.getElementById("modalPanel").innerHTML =
      '<div class="modal-head">' + poster +
        '<div><div class="modal-title">' + esc(i.name) + "</div>" +
        '<div class="modal-sub">' + esc(i.item_type) + (i.year ? " &middot; " + i.year : "") +
          (i.library_name ? " &middot; " + esc(i.library_name) : "") + "</div>" +
        '<div class="modal-badges">' + badges.join("") + "</div></div></div>" +
      '<div class="modal-body">' +
        '<div class="meta-grid">' + meta + "</div>" +
        fskEditor + ackBox +
        (i.path ? '<div class="pathline"><div class="k">Pfad im Verzeichnis</div>' +
                  '<div class="pv mono">' + esc(i.path) + "</div></div>" : "") +
        (i.overview ? '<div class="overview">' + esc(i.overview) + "</div>" : "") +
        note + seasonSummary(d.season_summary, i) + eps + "</div>";

    var saveBtn = document.getElementById("fskSave");
    if (saveBtn) {
      saveBtn.onclick = function () {
        var rating = document.getElementById("fskSel").value;
        saveBtn.disabled = true;
        fetch("/api/fsk/write", { method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ item_id: +saveBtn.getAttribute("data-id"), rating: rating }) })
          .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
          .then(function (res) {
            if (!res.ok) { throw new Error(res.j.detail || "Fehler"); }
            window.smhToast("FSK " + res.j.rating + " gesetzt - Seite wird aktualisiert ...", "ok");
            setTimeout(function () { location.reload(); }, 900);
          })
          .catch(function (e) { window.smhToast("Fehlgeschlagen: " + e.message, "err"); saveBtn.disabled = false; });
      };
    }

    var ackB = document.getElementById("ackBtn");
    if (ackB) {
      ackB.onclick = function () {
        ackB.disabled = true;
        fetch("/api/fsk/ack", { method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ item_id: +ackB.getAttribute("data-id") }) })
          .then(function (r) { return r.json(); })
          .then(function () {
            window.smhToast("Als korrekt bestätigt", "ok");
            var box = ackB.closest(".fsk-ack-box"); if (box) { box.remove(); }
          })
          .catch(function () { window.smhToast("Fehlgeschlagen", "err"); ackB.disabled = false; });
      };
    }

    Array.prototype.forEach.call(document.querySelectorAll(".ep-clickable"), function (row) {
      row.onclick = function () {
        var det = document.getElementById("epd-" + row.getAttribute("data-epidx"));
        if (det) { det.classList.toggle("hidden"); row.classList.toggle("open"); }
      };
    });
  }

  function openDetail(id) {
    if (!id) { return; }
    document.getElementById("modalPanel").innerHTML = '<div class="modal-loading">Lade Details ...</div>';
    document.getElementById("modal").classList.add("open");
    fetch("/api/items/" + id + "/detail")
      .then(function (r) { return r.json(); })
      .then(renderDetail)
      .catch(function () {
        document.getElementById("modalPanel").innerHTML = '<div class="modal-loading">Details konnten nicht geladen werden.</div>';
      });
  }
  function closeModal() { document.getElementById("modal").classList.remove("open"); }

  window.smhOpenDetail = openDetail;

  document.addEventListener("DOMContentLoaded", function () {
    var mc = document.getElementById("modalClose");
    if (mc) { mc.onclick = closeModal; }
    var m = document.getElementById("modal");
    if (m) { m.onclick = function (e) { if (e.target === m) { closeModal(); } }; }
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") { closeModal(); } });
  });
})();
