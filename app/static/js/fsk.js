/* FSK-Bearbeitungs-Seite: Quelle (Emby) vs. Dienst-Vorschlag vs. Gewuenscht.
   Filter + editierbare "Gewuenscht"-Dropdowns; Anwenden schreibt via write-bulk.
   Werte werden in der bevorzugten Rating-Art angezeigt, aber als "DE-<Alter>"
   geschrieben (Konsistenz zum Grid-Editor). */
(function () {
  "use strict";
  var T = window.t || function (k) { return k; };
  var $ = function (id) { return document.getElementById(id); };
  var ITEMS = window.__ITEMS__ || [];
  var ART = window.__RATING_ART__ || "fsk";
  var CAN_WRITE = window.__ALLOW_WRITE__ === true;
  var SYSTEMS = { fsk: [0, 6, 12, 16, 18], usk: [0, 6, 12, 16, 18], pegi: [3, 7, 12, 16, 18], age: null };
  var BUCKETS = SYSTEMS[ART] || [0, 6, 12, 16, 18];
  var state = { q: "", filter: "todo" };

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function label(age) {
    if (age == null) { return ""; }
    if (!SYSTEMS[ART]) { return age + "+"; }
    return ({ fsk: "FSK", usk: "USK", pegi: "PEGI" }[ART] || "") + " " + age;
  }
  function bucketUp(age) {
    if (age == null) { return null; }
    for (var i = 0; i < BUCKETS.length; i++) { if (BUCKETS[i] >= age) { return BUCKETS[i]; } }
    return BUCKETS[BUCKETS.length - 1];
  }

  function isEmby(i) { return i.source_kind === "emby"; }
  function actionable(i) {
    if (!isEmby(i) || i.rating_locked) { return false; }
    if (!i.official_rating) { return true; }                            // fehlt
    return i.suggested_age != null && i.rating_age !== i.suggested_age;  // Abweichung
  }
  function matches(i) {
    if (state.q && i.name.toLowerCase().indexOf(state.q) === -1) { return false; }
    if (state.filter === "todo") { return actionable(i); }
    if (state.filter === "none") { return !i.official_rating; }
    if (state.filter === "locked") { return !!i.rating_locked; }
    return true;
  }
  function defaultSel(i) {
    if (!isEmby(i) || i.rating_locked) { return "keep"; }
    if (i.suggested_age != null) { return String(bucketUp(i.suggested_age)); }
    return "keep";
  }

  function optionsHtml(i) {
    var sel = defaultSel(i);
    var html = '<option value="keep"' + (sel === "keep" ? " selected" : "") + ">" + esc(T("fskpage.keep")) + "</option>";
    html += '<option value="none"' + (sel === "none" ? " selected" : "") + ">" + esc(T("fskpage.none")) + "</option>";
    BUCKETS.forEach(function (a) {
      html += '<option value="' + a + '"' + (sel === String(a) ? " selected" : "") + ">" + esc(label(a)) + "</option>";
    });
    return html;
  }

  function srcBadge(i) {
    if (!i.official_rating) { return '<span class="fsk-badge none">' + esc(T("fskpage.no_rating")) + "</span>"; }
    var lock = i.rating_locked ? '<span class="rlock" aria-hidden="true">&#128274;</span>' : "";
    return '<span class="fsk-badge' + (i.rating_locked ? " locked" : "") + '">' +
      lock + esc(i.rating_disp || i.official_rating) + "</span>";
  }
  function suggBadge(i) {
    if (!i.suggested_disp) { return '<span class="fsk-dash">&mdash;</span>'; }
    var x = i.suggested_xlated
      ? '<span class="xmark" title="' + esc(T("fskpage.legend_xlated")) + '">&#9650;</span>' : "";
    return '<span class="fsk-badge sugg">' + esc(i.suggested_disp) + x + "</span>";
  }

  function render() {
    var list = $("fskList");
    var rows = ITEMS.filter(matches);
    $("fskCount").textContent = rows.length;
    if (!rows.length) {
      list.innerHTML = '<p class="set-desc" style="padding:16px">' + esc(T("fskpage.empty")) + "</p>";
      return;
    }
    var head = '<div class="fsk-row fsk-head"><span></span><span>' + esc(T("fskpage.col.title")) +
      "</span><span>" + esc(T("fskpage.col.source")) + "</span><span>" + esc(T("fskpage.col.suggested")) +
      "</span><span>" + esc(T("fskpage.col.desired")) + "</span></div>";
    list.innerHTML = head + rows.map(function (i) {
      var img = i.image_url
        ? '<img class="fsk-cover" loading="lazy" src="' + esc(i.image_url) + '" alt="">'
        : '<span class="fsk-cover noimg"></span>';
      var year = i.year ? ' <span class="fsk-year">(' + i.year + ")</span>" : "";
      var dis = (!CAN_WRITE || !isEmby(i)) ? " disabled" : "";
      return '<div class="fsk-row" data-id="' + i.id + '">' + img +
        '<span class="fsk-title">' + esc(i.name) + year + "</span>" +
        '<span class="fsk-col">' + srcBadge(i) + "</span>" +
        '<span class="fsk-col">' + suggBadge(i) + "</span>" +
        '<span class="fsk-col"><select class="field fsk-sel" data-id="' + i.id + '"' + dis + ">" +
        optionsHtml(i) + "</select></span></div>";
    }).join("");
  }

  function apply() {
    var changes = [];
    Array.prototype.forEach.call(document.querySelectorAll(".fsk-sel"), function (sel) {
      var v = sel.value;
      if (v === "keep") { return; }
      changes.push({ item_id: +sel.getAttribute("data-id"), rating: v === "none" ? "" : "DE-" + v });
    });
    if (!changes.length) { window.smhToast(T("fskpage.nothing"), "err"); return; }
    if (!window.confirm(T("fskpage.confirm").replace("{n}", changes.length))) { return; }
    var btn = $("fskApply");
    btn.disabled = true;
    fetch("/api/fsk/write-bulk", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ changes: changes }),
    })
      .then(function (r) { return r.json(); })
      .then(function (res) {
        var bad = res.errors && res.errors.length;
        window.smhToast(T("fskpage.written").replace("{n}", res.saved), bad ? "err" : "ok");
        location.reload();
      })
      .catch(function (e) { window.smhToast(T("msg.failed_prefix") + e.message, "err"); btn.disabled = false; });
  }

  document.addEventListener("DOMContentLoaded", function () {
    $("fskQ").addEventListener("input", function () { state.q = this.value.toLowerCase(); render(); });
    $("fskFilter").addEventListener("change", function () { state.filter = this.value; render(); });
    if (CAN_WRITE) { $("fskApply").addEventListener("click", apply); }
    render();
  });
})();
