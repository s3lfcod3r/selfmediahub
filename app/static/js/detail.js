/* Gemeinsames Detail-Fenster (Modal). Auf allen Seiten nutzbar:
   window.smhOpenDetail(id). Braucht #modal / #modalPanel / #modalClose.
   Strings via window.t (i18n, base.html). */
(function () {
  "use strict";

  var T = window.t || function (k) { return k; };

  // Sprach-Codes (inkl. Aliase) auf einen kanonischen Katalog-Key abbilden.
  var LANG_CANON = { ger: "ger", deu: "ger", de: "ger", eng: "eng", en: "eng",
    fre: "fre", fra: "fre", fr: "fre", spa: "spa", es: "spa", ita: "ita", it: "ita",
    jpn: "jpn", ja: "jpn", rus: "rus", ru: "rus", tur: "tur", tr: "tur", pol: "pol", pl: "pol",
    nld: "nld", dut: "nld", nl: "nld", por: "por", pt: "por", kor: "kor", ko: "kor",
    chi: "chi", zho: "chi", zh: "chi", ara: "ara", ar: "ara", und: "und" };

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
  function langName(c) {
    if (!c) { return c; }
    var canon = LANG_CANON[String(c).toLowerCase()];
    return canon ? T("langname." + canon) : c;
  }
  function langList(a) { return (a || []).map(langName).join(", "); }

  var SHORTLANG = { ger: "DE", deu: "DE", de: "DE", eng: "EN", en: "EN", fre: "FR", fra: "FR", fr: "FR",
    spa: "ES", es: "ES", ita: "IT", it: "IT", jpn: "JP", ja: "JP", rus: "RU", ru: "RU", tur: "TR", tr: "TR",
    pol: "PL", pl: "PL", nld: "NL", dut: "NL", nl: "NL", por: "PT", pt: "PT", kor: "KO", ko: "KO",
    chi: "ZH", zho: "ZH", zh: "ZH", ara: "AR", ar: "AR", und: "?" };
  function shortLang(c) { if (!c) { return "?"; } var k = String(c).toLowerCase(); return SHORTLANG[k] || k.slice(0, 2).toUpperCase(); }

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
    var aTitle = T("detail.ep_audio_title").replace("{lang}", name)
      .replace("{state}", audioOk ? T("detail.present") : T("detail.absent"));
    var sTitle = T("detail.ep_sub_title").replace("{lang}", name)
      .replace("{state}", subOk ? T("detail.present") : T("detail.absent"));
    return (
      '<span class="qbadge et-badge et-res' + (e.resolution ? "" : " et-empty") + '">' +
        (e.resolution ? esc(e.resolution) : "–") + "</span>" +
      '<span class="pill et-badge et-codec' + (e.video_codec ? "" : " et-empty") + '">' +
        (e.video_codec ? esc(e.video_codec) : "–") + "</span>" +
      '<span class="pill et-badge et-size' + (fmtSize(e.size_bytes) ? "" : " et-empty") + '">' +
        (fmtSize(e.size_bytes) || "–") + "</span>" +
      '<span class="lbadge et-badge et-lang' + (audioOk ? "" : " et-off") + '" title="' + aTitle + '">' +
        pflag + "</span>" +
      '<span class="pill et-badge et-ut' + (subOk ? "" : " et-off") + '" title="' + sTitle + '">' +
        pflag + " " + esc(T("cover.sub_abbr")) + "</span>"
    );
  }
  function epDetailRow(k, v) {
    if (v == null || v === "") { return ""; }
    return '<div class="epd-row"><span class="epd-k">' + esc(k) + '</span><span class="epd-v">' + v + "</span></div>";
  }
  function epDetail(e) {
    var h = "";
    h += epDetailRow(T("detail.resolution"), (e.width && e.height) ? (e.width + " × " + e.height) :
                     (e.resolution ? esc(e.resolution) : null));
    h += epDetailRow(T("detail.hdr"), (e.hdr && e.hdr !== "SDR") ? esc(e.hdr) : null);
    h += epDetailRow(T("detail.video_codec"), e.video_codec ? esc(e.video_codec) : null);
    h += epDetailRow(T("detail.audio_langs"), langList(e.audio_langs) || null);
    h += epDetailRow(T("detail.subtitles"), (e.subtitle_langs || []).length ? esc(langList(e.subtitle_langs)) : T("detail.none_f"));
    h += epDetailRow(T("detail.size"), fmtSize(e.size_bytes));
    h += epDetailRow(T("detail.runtime"), e.runtime_min ? e.runtime_min + " " + T("detail.min") : null);
    h += e.path ? '<div class="epd-path mono">' + esc(e.path) + "</div>" : "";
    return h || '<div class="epd-row"><span class="epd-v" style="color:var(--self-text-3)">' +
      esc(T("detail.no_more")) + "</span></div>";
  }

  function seasonSummary(s, item) {
    if (!s || !s.total_tmdb) { return ""; }
    var miss = Math.max(0, s.total_tmdb - s.total_have);
    var missWord = function (n) { return n + " " + (n === 1 ? T("detail.missing_one") : T("detail.missing_many")); };
    var head = T("detail.ss_head") + " &middot; " + s.total_have + " / " + s.total_tmdb + " " +
      T("detail.ss_available") + (miss > 0 ? " &middot; " + missWord(miss) : " &middot; " + T("comp.complete"));
    // Verlaessliche Staffel-Zuordnung -> Pro-Staffel-Aufschluesselung
    if (s.reliable && s.seasons && s.seasons.length) {
      var rows = s.seasons.map(function (r) {
        var m = Math.max(0, r.tmdb_total - r.have);
        var cls = m > 0 ? " miss" : " full";
        var right = m > 0 ? missWord(m) : T("comp.complete");
        return '<div class="ssum-row' + cls + '">' +
          '<span class="ssum-s">' + esc(T("detail.season")) + " " + r.season + "</span>" +
          '<span class="ssum-c">' + r.have + " / " + r.tmdb_total + "</span>" +
          '<span class="ssum-b">' + right + "</span></div>";
      }).join("");
      return '<div class="ssum"><div class="ssum-h">' + head + "</div>" + rows +
        '<div class="ssum-foot">' + esc(T("detail.ss_foot_reliable")) + "</div></div>";
    }
    // Nummerierung passt gar nicht -> wenigstens die Gesamtzahl ehrlich nennen
    var hs = (item && item.have_seasons != null) ? item.have_seasons : "?";
    var ts = (item && item.tmdb_seasons != null) ? item.tmdb_seasons : "?";
    return '<div class="ssum"><div class="ssum-h">' + head + "</div>" +
      '<div class="ssum-foot">' +
      esc(T("detail.ss_foot_unreliable").replace("{hs}", hs).replace("{ts}", ts)) + "</div></div>";
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
      else { badges.push('<span class="pill bad">' + esc(T("detail.no_rating")) + "</span>"); }
    }
    if (i.resolution) { badges.push('<span class="qbadge">' + esc(i.resolution) + "</span>"); }
    if (i.hdr && i.hdr !== "SDR") { badges.push('<span class="qbadge">' + esc(i.hdr) + "</span>"); }
    if (i.completeness === "incomplete") {
      badges.push('<span class="pill bad">' + esc(T("detail.missing_count").replace("{n}", i.missing_episodes || "?")) + "</span>");
    }
    if (i.completeness === "complete") { badges.push('<span class="pill ok">' + esc(T("comp.complete")) + "</span>"); }
    (i.tags || []).forEach(function (t) { badges.push(tagChip(t)); });

    var meta = "";
    meta += metaItem(T("detail.runtime"), i.runtime_min ? i.runtime_min + " " + T("detail.min") : null);
    meta += metaItem(T("detail.size"), fmtSize(i.size_bytes));
    meta += metaItem(T("detail.resolution"), (i.width && i.height) ? (i.width + " × " + i.height) :
                     (i.resolution ? esc(i.resolution) : null));
    meta += metaItem(T("detail.video_codec"), i.video_codec ? esc(i.video_codec) : null);
    meta += metaItem(T("detail.audio_langs"), langList(i.audio_langs) || null);
    meta += metaItem(T("detail.subtitles"), (i.subtitle_langs || []).length ? esc(langList(i.subtitle_langs)) : T("detail.none_f"));
    meta += metaItem(T("detail.genres"), (i.genres || []).length ? esc(i.genres.join(", ")) : null);
    meta += metaItem(T("detail.library"), i.library_name ? esc(i.library_name) : null);
    meta += metaItem(T("detail.score"), i.community_rating != null ? Number(i.community_rating).toFixed(1) : null);
    if (i.item_type === "Serie") {
      meta += metaItem(T("detail.seasons"), (i.have_seasons != null ? i.have_seasons : "?") + (i.tmdb_seasons ? " / " + i.tmdb_seasons : ""));
      meta += metaItem(T("detail.episodes"), (i.have_episodes != null ? i.have_episodes : "?") + (i.tmdb_episodes ? " / " + i.tmdb_episodes : ""));
      meta += metaItem(T("detail.status"), i.status ? esc(i.status) : null);
    }
    if (fskOn) { meta += metaItem(T("detail.fsk_suggestion"), i.fsk_suggested ? esc(i.fsk_suggested) : null); }

    var eps = "";
    if (d.episodes && d.episodes.length) {
      var curSeason = null;
      d.episodes.forEach(function (e, idx) {
        if (e.season !== curSeason) {
          curSeason = e.season;
          eps += '<div class="season-h">' + esc(T("detail.season")) + " " + (curSeason == null ? "?" : curSeason) + "</div>";
        }
        var no = "S" + (e.season == null ? "?" : ("0" + e.season).slice(-2)) +
                 "E" + (e.episode == null ? "?" : ("0" + e.episode).slice(-2));
        if (e.missing) {
          eps += '<div class="ep missing"><span class="no">' + no + '</span>' +
            '<span class="en">' + esc(T("detail.ep_absent")) + '</span>' +
            '<span class="et"><span class="pill bad">' + esc(T("comp.missing")) + '</span></span></div>';
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
        '<div class="fsk-editor"><div class="k">' + esc(T("detail.fsk_set_title")) + "</div>" +
        '<div class="fsk-row">' +
          '<select class="field" id="fskSel"' + dis + ">" + opts +
            '<option value="">' + esc(T("fsk.none_option")) + "</option></select>" +
          '<button class="btn btn-primary" id="fskSave" data-id="' + i.id + '"' + dis +
            ">" + esc(T("detail.fsk_save_btn")) + "</button>" +
        "</div>" +
        (d.allow_write ? "" : '<div class="modal-note">' + T("detail.fsk_write_note") + "</div>") +
        "</div>";
    }

    var ackBox = "";
    if (fskOn && i.fsk_suspicious && !i.fsk_acked) {
      ackBox = '<div class="fsk-ack-box"><span>' + esc(T("detail.fsk_implausible")) +
        (i.fsk_reason ? ": " + esc(i.fsk_reason) : "") + "</span>" +
        '<button class="btn btn-small" id="ackBtn" data-id="' + i.id + '">' + esc(T("detail.fsk_ack_btn")) + "</button></div>";
    }

    document.getElementById("modalPanel").innerHTML =
      '<div class="modal-head">' + poster +
        '<div><div class="modal-title">' + esc(i.name) + "</div>" +
        '<div class="modal-sub">' + esc(T("type." + i.item_type)) + (i.year ? " &middot; " + i.year : "") +
          (i.library_name ? " &middot; " + esc(i.library_name) : "") + "</div>" +
        '<div class="modal-badges">' + badges.join("") + "</div></div></div>" +
      '<div class="modal-body">' +
        '<div class="meta-grid">' + meta + "</div>" +
        fskEditor + ackBox +
        (i.path ? '<div class="pathline"><div class="k">' + esc(T("detail.path")) + "</div>" +
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
            if (!res.ok) { throw new Error(res.j.detail || "?"); }
            window.smhToast(T("detail.fsk_saved").replace("{rating}", res.j.rating), "ok");
            setTimeout(function () { location.reload(); }, 900);
          })
          .catch(function (e) { window.smhToast(T("msg.failed_prefix") + e.message, "err"); saveBtn.disabled = false; });
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
            window.smhToast(T("detail.acked"), "ok");
            var box = ackB.closest(".fsk-ack-box"); if (box) { box.remove(); }
          })
          .catch(function () { window.smhToast(T("common.failed"), "err"); ackB.disabled = false; });
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
    document.getElementById("modalPanel").innerHTML = '<div class="modal-loading">' + esc(T("detail.loading")) + "</div>";
    document.getElementById("modal").classList.add("open");
    fetch("/api/items/" + id + "/detail")
      .then(function (r) { return r.json(); })
      .then(renderDetail)
      .catch(function () {
        document.getElementById("modalPanel").innerHTML = '<div class="modal-loading">' + esc(T("detail.load_failed")) + "</div>";
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
