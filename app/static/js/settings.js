/* Einstellungsseite: Kategorie-Umschaltung (Sidebar <-> Panels) + Speichern.
   Theme/Toast liegen in common.js. */
(function () {
  "use strict";

  var $ = function (id) { return document.getElementById(id); };

  // -- Kategorie-Umschaltung (per Klick + URL-Hash, damit Links teilbar sind) --
  function showCat(cat) {
    var tabs = document.querySelectorAll(".set-tab");
    var panels = document.querySelectorAll(".set-panel");
    var found = false;
    Array.prototype.forEach.call(tabs, function (t) {
      var on = t.getAttribute("data-cat") === cat;
      t.classList.toggle("active", on);
      if (on) { found = true; }
    });
    Array.prototype.forEach.call(panels, function (p) {
      p.classList.toggle("active", p.getAttribute("data-cat") === cat);
    });
    return found;
  }

  function initNav() {
    var nav = $("setNav");
    if (!nav) { return; }
    nav.addEventListener("click", function (e) {
      var btn = e.target.closest(".set-tab");
      if (!btn) { return; }
      var cat = btn.getAttribute("data-cat");
      if (showCat(cat)) {
        try { history.replaceState(null, "", "#" + cat); } catch (err) { /* ignore */ }
      }
    });
    var hash = (location.hash || "").replace("#", "");
    if (hash) { showCat(hash); }
  }

  // -- Speichern: an /api/settings schicken (Teil-Objekt aus key/value) --
  function saveSettings(payload, okMsg, btn) {
    if (btn) { btn.disabled = true; }
    return fetch("/api/settings", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
      .then(function (res) {
        if (!res.ok) { throw new Error(res.j.detail || "Fehler"); }
        window.smhToast(okMsg || "Gespeichert", "ok");
      })
      .catch(function (e) { window.smhToast("Fehlgeschlagen: " + e.message, "err"); })
      .then(function () { if (btn) { btn.disabled = false; } });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initNav();

    var allgBtn = $("saveAllgemein");
    if (allgBtn) {
      allgBtn.onclick = function () {
        saveSettings({ "general.instance_name": $("instanceName").value.trim() }, "Gespeichert", allgBtn);
      };
    }

    var fsk = $("fskEnabled");
    if (fsk) {
      fsk.onchange = function () {
        saveSettings({ "fsk.enabled": fsk.checked },
          fsk.checked ? "FSK-Prüfung aktiviert" : "FSK-Prüfung deaktiviert");
      };
    }

    var upd = $("updateCheck");
    if (upd) {
      upd.onclick = function () {
        upd.disabled = true;
        window.smhToast("Prüfe auf Updates ...");
        fetch("/api/update/check", { method: "POST" })
          .then(function (r) { return r.json(); })
          .then(function (s) {
            var el = $("updateStatus");
            if (el) {
              el.textContent = s.available
                ? ("Neue Version " + s.latest + " verfügbar.")
                : (s.latest ? ("Aktuell - v" + s.current + " ist die neueste Version.")
                            : "Konnte nicht geprüft werden (keine Verbindung/kein Release).");
            }
            window.smhToast(s.available ? ("Update verfügbar: " + s.latest) : "Alles aktuell", "ok");
          })
          .catch(function () { window.smhToast("Prüfung fehlgeschlagen", "err"); })
          .then(function () { upd.disabled = false; });
      };
    }
  });
})();
