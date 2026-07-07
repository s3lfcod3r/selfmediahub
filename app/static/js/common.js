/* Gemeinsame Logik fuer alle Seiten: Theme-Umschalter, Sync, Toast. */
(function () {
  "use strict";

  var toastTimer;
  function toast(msg, kind) {
    var t = document.getElementById("toast");
    if (!t) { return; }
    t.textContent = msg;
    t.className = "toast show " + (kind || "");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { t.className = "toast"; }, 4500);
  }
  window.smhToast = toast;

  function initTheme() {
    var saved = localStorage.getItem("smh-theme") || "dark";
    document.documentElement.setAttribute("data-theme", saved);
    var btn = document.getElementById("themeBtn");
    if (!btn) { return; }
    btn.onclick = function () {
      var cur = document.documentElement.getAttribute("data-theme");
      var next = cur === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
      localStorage.setItem("smh-theme", next);
    };
  }

  function doSync() {
    var btn = document.getElementById("syncBtn");
    var label = document.getElementById("syncLabel");
    btn.disabled = true;
    if (label) { label.innerHTML = 'Lese ein <span class="spin" style="display:inline-block">&#8635;</span>'; }
    fetch("/api/sync", { method: "POST" })
      .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
      .then(function (res) {
        if (!res.ok) { throw new Error(res.j.detail || "Fehler beim Einlesen"); }
        toast(res.j.count + " Eintraege - Seite wird aktualisiert ...", "ok");
        setTimeout(function () { location.reload(); }, 900);
      })
      .catch(function (e) {
        toast("Sync fehlgeschlagen: " + e.message, "err");
        btn.disabled = false;
        if (label) { label.textContent = "Neu einlesen"; }
      });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initTheme();
    var s = document.getElementById("syncBtn");
    if (s) { s.onclick = doSync; }
  });
})();
