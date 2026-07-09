/* Gemeinsame Logik für alle Seiten: Theme-Umschalter, Sync, Toast. */
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

  var pollTimer;
  function setLabel(txt) {
    var label = document.getElementById("syncLabel");
    if (label) { label.innerHTML = txt; }
  }
  function stopSync(resetText) {
    clearInterval(pollTimer);
    var btn = document.getElementById("syncBtn");
    if (btn) { btn.disabled = false; }
    setLabel(resetText || "Neu einlesen");
  }
  function phaseText(s) {
    var spin = '<span class="spin" style="display:inline-block">&#8635;</span> ';
    if (s.total && String(s.phase).indexOf("TMDb") !== -1) {
      return spin + "Abgleich " + s.processed + "/" + s.total;
    }
    return spin + (s.phase || "Lese ein");
  }
  function poll() {
    fetch("/api/sync/status").then(function (r) { return r.json(); }).then(function (s) {
      if (s.error) { stopSync(); toast("Sync fehlgeschlagen: " + s.error, "err"); return; }
      if (!s.running) {
        clearInterval(pollTimer);
        var n = s.result ? s.result.count : 0;
        toast(n + " Einträge - Seite wird aktualisiert ...", "ok");
        setTimeout(function () { location.reload(); }, 900);
        return;
      }
      setLabel(phaseText(s));
    }).catch(function () { /* transienter Fehler - weiter pollen */ });
  }
  function doSync() {
    var btn = document.getElementById("syncBtn");
    btn.disabled = true;
    setLabel('<span class="spin" style="display:inline-block">&#8635;</span> Starte ...');
    fetch("/api/sync", { method: "POST" })
      .then(function (r) { return r.json(); })
      .then(function () {
        clearInterval(pollTimer);
        pollTimer = setInterval(poll, 1500);
        poll();
      })
      .catch(function (e) { stopSync(); toast("Start fehlgeschlagen: " + e.message, "err"); });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initTheme();
    var s = document.getElementById("syncBtn");
    if (s) { s.onclick = doSync; }
  });
})();
