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

  // ======================================================================
  //  Datenquellen (Phase 4a) - Quellen-Editor im "Datenquellen"-Panel
  // ======================================================================
  var KIND_LABEL = { emby: "Emby", jellyfin: "Jellyfin", plex: "Plex", local: "Lokale Ordner" };

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function setStatus(el, msg, type) {
    var s = el.querySelector(".src-status");
    if (!s) { return; }
    s.textContent = msg || "";
    s.className = "src-status set-desc" + (type ? " s-" + type : "");
  }

  function reloadSources() {
    var root = $("sourcesRoot");
    if (root) { loadSources(root); }
  }

  function loadSources(root) {
    fetch("/api/sources")
      .then(function (r) { return r.json(); })
      .then(function (data) { renderSources(root, data); })
      .catch(function () {
        root.innerHTML = '<p class="set-desc">Quellen konnten nicht geladen werden.</p>';
      });
  }

  function renderSources(root, data) {
    var byKind = {};
    (data.sources || []).forEach(function (s) { byKind[s.kind] = s; });
    var serverKinds = data.server_kinds || ["emby", "jellyfin", "plex"];
    root.innerHTML = "";
    (data.kinds || ["emby", "jellyfin", "plex", "local"]).forEach(function (kind) {
      var isServer = serverKinds.indexOf(kind) !== -1;
      root.appendChild(buildCard(kind, byKind[kind] || null, isServer));
    });
  }

  function buildCard(kind, src, isServer) {
    var el = document.createElement("div");
    el.className = "src-card" + (src && !src.enabled ? " src-off" : "");
    el.setAttribute("data-kind", kind);
    if (src) { el.setAttribute("data-id", src.id); }
    var name = src ? src.name : "";
    var enabled = src ? src.enabled : true;
    var head =
      '<div class="src-head"><h3>' + esc(KIND_LABEL[kind] || kind) + "</h3>" +
        '<label class="set-toggle"><input type="checkbox" class="src-enabled"' +
        (enabled ? " checked" : "") + "><span>aktiv</span></label></div>" +
      '<div class="set-field"><label>Name</label>' +
        '<input class="field src-name" maxlength="60" value="' + esc(name) +
        '" placeholder="' + esc(KIND_LABEL[kind] || kind) + '"></div>';

    var mid, actions;
    if (isServer) {
      var secretPh = src && src.has_secret
        ? "•••••••• (leer lassen = unverändert)" : "API-Key / Token eingeben";
      mid =
        '<div class="set-field"><label>Server-URL</label>' +
          '<input class="field src-url" value="' + esc(src ? src.base_url : "") +
          '" placeholder="http://192.168.1.19:8096"></div>' +
        '<div class="set-field"><label>API-Key / Token</label>' +
          '<input class="field src-secret" type="password" autocomplete="new-password" placeholder="' +
          esc(secretPh) + '"></div>' +
        '<div class="set-field src-libs" hidden><label>Überwachte Bibliotheken ' +
          '<span class="set-hint">leer = alle</span></label>' +
          '<div class="src-libs-list"></div></div>';
      actions =
        '<button class="btn btn-primary src-save">Speichern</button>' +
        '<button class="btn src-test"' + (src ? "" : " disabled") + ">Testen</button>" +
        '<button class="btn src-libsbtn"' + (src ? "" : " disabled") + ">Bibliotheken</button>" +
        '<button class="btn src-del"' + (src ? "" : " disabled") + ">Löschen</button>";
    } else {
      var paths = src && src.local_paths ? src.local_paths.join("\n") : "";
      mid =
        '<div class="set-field"><label>Pfade ' +
          '<span class="set-hint">einer pro Zeile (im Container)</span></label>' +
          '<textarea class="field src-paths" rows="3" placeholder="/media/filme">' +
          esc(paths) + "</textarea></div>";
      actions =
        '<button class="btn btn-primary src-save">Speichern</button>' +
        '<button class="btn src-del"' + (src ? "" : " disabled") + ">Löschen</button>";
    }
    el.innerHTML = head + mid + '<div class="set-actions">' + actions + "</div>" +
      '<p class="src-status set-desc"></p>';
    bindCard(el, kind, src, isServer);
    return el;
  }

  function bindCard(el, kind, src, isServer) {
    var idOf = function () { return el.getAttribute("data-id"); };

    el.querySelector(".src-save").onclick = function () { saveCard(el, kind, isServer); };

    var delBtn = el.querySelector(".src-del");
    if (delBtn) {
      delBtn.onclick = function () {
        var id = idOf();
        if (!id) { return; }
        if (!window.confirm("Quelle wirklich löschen?\n\nDie eingelesenen Einträge dieser " +
          "Quelle werden beim nächsten Einlesen entfernt.")) { return; }
        fetch("/api/sources/" + id, { method: "DELETE" })
          .then(function () { window.smhToast("Quelle gelöscht", "ok"); reloadSources(); })
          .catch(function () { window.smhToast("Löschen fehlgeschlagen", "err"); });
      };
    }

    var testBtn = el.querySelector(".src-test");
    if (testBtn) {
      testBtn.onclick = function () {
        var id = idOf();
        if (!id) { return; }
        testBtn.disabled = true;
        setStatus(el, "Teste Verbindung …", "");
        fetch("/api/sources/" + id + "/test", { method: "POST" })
          .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
          .then(function (res) {
            if (res.ok) { setStatus(el, "Verbindung OK ✓", "ok"); }
            else { setStatus(el, "Fehler: " + (res.j.detail || "unbekannt"), "err"); }
          })
          .catch(function () { setStatus(el, "Verbindung fehlgeschlagen", "err"); })
          .then(function () { testBtn.disabled = false; });
      };
    }

    var libsBtn = el.querySelector(".src-libsbtn");
    if (libsBtn) {
      libsBtn.onclick = function () {
        var id = idOf();
        if (!id) { return; }
        libsBtn.disabled = true;
        setStatus(el, "Lade Bibliotheken …", "");
        fetch("/api/sources/" + id + "/libraries")
          .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
          .then(function (res) {
            if (!res.ok) { setStatus(el, "Fehler: " + (res.j.detail || "unbekannt"), "err"); return; }
            renderLibs(el, res.j.libraries || [], (src && src.libraries) || []);
            setStatus(el, "", "");
          })
          .catch(function () { setStatus(el, "Bibliotheken konnten nicht geladen werden", "err"); })
          .then(function () { libsBtn.disabled = false; });
      };
    }
  }

  function renderLibs(el, available, selected) {
    var wrap = el.querySelector(".src-libs");
    var list = el.querySelector(".src-libs-list");
    if (!wrap || !list) { return; }
    var selSet = {};
    selected.forEach(function (x) { selSet[String(x)] = true; });
    list.innerHTML = available.map(function (lib) {
      var id = String(lib.id);
      return '<label class="src-lib"><input type="checkbox" class="src-lib-cb" value="' + esc(id) +
        '"' + (selSet[id] ? " checked" : "") + "><span>" + esc(lib.name || id) + "</span></label>";
    }).join("") || '<p class="set-desc">Keine Bibliotheken gefunden.</p>';
    wrap.hidden = false;
    wrap.setAttribute("data-loaded", "1");
  }

  function saveCard(el, kind, isServer) {
    var id = el.getAttribute("data-id");
    var body = {
      kind: kind,
      name: el.querySelector(".src-name").value.trim(),
      enabled: el.querySelector(".src-enabled").checked,
    };
    if (isServer) {
      body.base_url = el.querySelector(".src-url").value.trim();
      var secret = el.querySelector(".src-secret").value;
      if (secret) { body.secret = secret; }
      var libsWrap = el.querySelector(".src-libs");
      if (libsWrap && libsWrap.getAttribute("data-loaded")) {
        var ids = [];
        Array.prototype.forEach.call(el.querySelectorAll(".src-lib-cb"), function (cb) {
          if (cb.checked) { ids.push(cb.value); }
        });
        body.libraries = ids;
      }
      if (!body.base_url) { setStatus(el, "Server-URL fehlt", "err"); return; }
      if (!id && !secret) { setStatus(el, "API-Key / Token fehlt", "err"); return; }
    } else {
      body.local_paths = el.querySelector(".src-paths").value.split("\n")
        .map(function (p) { return p.trim(); }).filter(Boolean);
      if (!body.local_paths.length) { setStatus(el, "Mindestens einen Pfad angeben", "err"); return; }
    }
    var save = el.querySelector(".src-save");
    save.disabled = true;
    setStatus(el, "Speichere …", "");
    fetch(id ? "/api/sources/" + id : "/api/sources", {
      method: id ? "PUT" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    })
      .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
      .then(function (res) {
        if (!res.ok) { throw new Error(res.j.detail || "Fehler"); }
        window.smhToast("Quelle gespeichert", "ok");
        reloadSources();
      })
      .catch(function (e) {
        setStatus(el, "Fehlgeschlagen: " + e.message, "err");
        window.smhToast("Speichern fehlgeschlagen", "err");
        save.disabled = false;
      });
  }

  function initSources() {
    var root = $("sourcesRoot");
    if (root) { loadSources(root); }
  }

  document.addEventListener("DOMContentLoaded", function () {
    initNav();
    initSources();

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

    var lang = $("primaryLang");
    if (lang) {
      lang.onchange = function () {
        saveSettings({ "display.primary_language": lang.value }, "Primäre Sprache gespeichert");
      };
    }

    // UI-Sprache: nach dem Speichern neu laden, damit die Oberflaeche umschaltet.
    var uiLang = $("uiLang");
    if (uiLang) {
      uiLang.onchange = function () {
        saveSettings({ "general.ui_language": uiLang.value }, "…")
          .then(function () { location.reload(); });
      };
    }

    // -- Account --
    function postJson(url, body, okMsg, btn) {
      if (btn) { btn.disabled = true; }
      return fetch(url, { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body) })
        .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
        .then(function (res) {
          if (!res.ok) { throw new Error(res.j.detail || "Fehler"); }
          window.smhToast(okMsg, "ok");
          return res.j;
        })
        .catch(function (e) { window.smhToast("Fehlgeschlagen: " + e.message, "err"); throw e; })
        .then(function (v) { if (btn) { btn.disabled = false; } return v; },
              function () { if (btn) { btn.disabled = false; } });
    }

    var uBtn = $("saveUsername");
    if (uBtn) {
      uBtn.onclick = function () {
        postJson("/api/account/username", { username: $("accUsername").value.trim() },
          "Benutzername gespeichert", uBtn);
      };
    }
    var eBtn = $("saveEmail");
    if (eBtn) {
      eBtn.onclick = function () {
        postJson("/api/account/email", { email: $("accEmail").value.trim() }, "E-Mail gespeichert", eBtn);
      };
    }
    var pBtn = $("savePassword");
    if (pBtn) {
      pBtn.onclick = function () {
        postJson("/api/account/password",
          { current: $("accPwCurrent").value, new: $("accPwNew").value },
          "Passwort geändert", pBtn)
          .then(function () { $("accPwCurrent").value = ""; $("accPwNew").value = ""; })
          .catch(function () { /* Toast schon gezeigt */ });
      };
    }
    var authCb = $("authEnabled");
    if (authCb) {
      authCb.onchange = function () {
        if (!authCb.checked) {
          var ok = window.confirm(
            "Anmeldung wirklich abschalten?\n\nOhne Anmeldung ist deine Medienverwaltung " +
            "ungeschützt für jeden erreichbar, der die Seite aufrufen kann.");
          if (!ok) { authCb.checked = true; return; }
        }
        postJson("/api/account/auth", { enabled: authCb.checked },
          authCb.checked ? "Anmeldung aktiviert" : "Anmeldung deaktiviert");
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
