/* Gemeinsames Detail-Fenster (Modal). Auf allen Seiten nutzbar:
   window.smhOpenDetail(id). Braucht #modal / #modalPanel / #modalClose. */
(function () {
  "use strict";

  var LANG = { ger: "Deutsch", deu: "Deutsch", de: "Deutsch", eng: "Englisch", en: "Englisch",
    fre: "Franzoesisch", fra: "Franzoesisch", spa: "Spanisch", ita: "Italienisch",
    jpn: "Japanisch", rus: "Russisch", tur: "Tuerkisch", pol: "Polnisch",
    nld: "Niederlaendisch", dut: "Niederlaendisch", por: "Portugiesisch",
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
  function tagChip(t) {
    var ic = t.icon ? esc(t.icon) + " " : "";
    return '<span class="chip" style="border-color:' + esc(t.color) + ";color:" + esc(t.color) +
      '">' + ic + esc(t.name) + "</span>";
  }
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

    document.getElementById("modalPanel").innerHTML =
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
