/* Einstellungsseite: Kategorie-Umschaltung (Sidebar <-> Panels) + Speichern.
   Theme/Toast liegen in common.js. Strings via window.t (i18n, base.html). */
(function () {
  "use strict";

  var $ = function (id) { return document.getElementById(id); };
  var T = window.t || function (k) { return k; };

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
        if (!res.ok) { throw new Error(res.j.detail || "?"); }
        window.smhToast(okMsg || T("msg.saved"), "ok");
      })
      .catch(function (e) { window.smhToast(T("msg.failed_prefix") + e.message, "err"); })
      .then(function () { if (btn) { btn.disabled = false; } });
  }

  // ======================================================================
  //  Datenquellen - Liste + Modal (anlegen/bearbeiten) + Datei-Browser
  // ======================================================================
  var KIND_LABEL = { emby: "Emby", jellyfin: "Jellyfin", plex: "Plex", local: T("sources.kind.local") };
  var SERVER_KINDS = ["emby", "jellyfin", "plex"];
  var srcState = { id: null, src: null, libsLoaded: false };
  var fsCurrent = "/";

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function isServerKind(k) { return SERVER_KINDS.indexOf(k) !== -1; }
  function showModal(id) { $(id).classList.add("open"); }
  function hideModal(id) { $(id).classList.remove("open"); }

  function modalStatus(msg, type) {
    var s = $("srcModalStatus");
    if (!s) { return; }
    s.textContent = msg || "";
    s.className = "src-modal-status set-desc" + (type ? " s-" + type : "");
  }

  // -- Liste laden + rendern --------------------------------------------
  function loadSources() {
    var list = $("sourcesList");
    if (!list) { return; }
    fetch("/api/sources")
      .then(function (r) { return r.json(); })
      .then(function (data) { renderList(list, data.sources || []); })
      .catch(function () {
        list.innerHTML = '<p class="set-desc">' + esc(T("sources.load_failed")) + "</p>";
      });
  }

  function subLine(s) {
    return isServerKind(s.kind) ? (s.base_url || "") : (s.local_paths || []).join(", ");
  }

  function renderList(list, sources) {
    if (!sources.length) {
      list.innerHTML = '<div class="src-empty">' + esc(T("sources.empty")) + "</div>";
      return;
    }
    list.innerHTML = sources.map(function (s) {
      var label = KIND_LABEL[s.kind] || s.kind;
      return '<div class="src-row' + (s.enabled ? "" : " src-off") + '" data-id="' + s.id + '">' +
        '<div class="src-row-main">' +
          '<div class="src-row-name">' + esc(s.name || label) +
            '<span class="src-kind-badge">' + esc(label) + "</span>" +
            (s.enabled ? "" : '<span class="src-off-badge">' + esc(T("sources.disabled")) + "</span>") +
          "</div>" +
          '<div class="src-row-sub mono">' + esc(subLine(s) || "-") + "</div>" +
        "</div>" +
        '<div class="src-row-actions">' +
          '<button class="btn btn-icon src-edit" title="' + esc(T("sources.edit")) +
            '" aria-label="' + esc(T("sources.edit")) + '">&#9998;</button>' +
          '<button class="btn btn-icon btn-danger src-del" title="' + esc(T("sources.delete")) +
            '" aria-label="' + esc(T("sources.delete")) + '">&#128465;</button>' +
        "</div></div>";
    }).join("");
    Array.prototype.forEach.call(list.querySelectorAll(".src-row"), function (row) {
      var id = row.getAttribute("data-id");
      row.querySelector(".src-edit").onclick = function () { openEdit(id); };
      row.querySelector(".src-del").onclick = function () { delSource(id); };
    });
  }

  // -- Modal: Felder je Typ ein-/ausblenden -----------------------------
  function applyKindFields(kind) {
    var server = isServerKind(kind);
    $("srcServerFields").hidden = !server;
    $("srcLocalFields").hidden = server;
  }

  function openAdd() {
    srcState = { id: null, src: null, libsLoaded: false };
    $("srcModalTitle").textContent = T("sources.add_title");
    $("srcKind").value = "emby";
    $("srcKind").disabled = false;
    $("srcName").value = "";
    $("srcUrl").value = "";
    $("srcSecret").value = "";
    $("srcSecret").placeholder = T("sources.secret_enter");
    $("srcPath").value = "";
    $("srcEnabled").checked = true;
    $("srcLibsWrap").hidden = true;
    $("srcLibsList").innerHTML = "";
    $("srcTestBtn").hidden = true;
    $("srcLibsBtn").hidden = true;
    $("srcSaveBtn").textContent = T("sources.add");
    applyKindFields("emby");
    modalStatus("", "");
    showModal("srcModal");
    $("srcName").focus();
  }

  function openEdit(id) {
    fetch("/api/sources").then(function (r) { return r.json(); }).then(function (data) {
      var src = (data.sources || []).filter(function (s) { return String(s.id) === String(id); })[0];
      if (!src) { return; }
      srcState = { id: src.id, src: src, libsLoaded: false };
      $("srcModalTitle").textContent = T("sources.edit_title");
      $("srcKind").value = src.kind;
      $("srcKind").disabled = true;   // Typ einer bestehenden Quelle nicht aenderbar
      $("srcName").value = src.name || "";
      $("srcUrl").value = src.base_url || "";
      $("srcSecret").value = "";
      $("srcSecret").placeholder = src.has_secret ? T("sources.secret_keep") : T("sources.secret_enter");
      $("srcPath").value = (src.local_paths || [])[0] || "";
      $("srcEnabled").checked = !!src.enabled;
      $("srcLibsWrap").hidden = true;
      $("srcLibsList").innerHTML = "";
      var server = isServerKind(src.kind);
      $("srcTestBtn").hidden = !server;
      $("srcLibsBtn").hidden = !server;
      $("srcSaveBtn").textContent = T("common.save");
      applyKindFields(src.kind);
      modalStatus("", "");
      showModal("srcModal");
    });
  }

  function saveModal() {
    var kind = $("srcKind").value;
    var server = isServerKind(kind);
    var body = { kind: kind, name: $("srcName").value.trim(), enabled: $("srcEnabled").checked };
    if (server) {
      body.base_url = $("srcUrl").value.trim();
      var secret = $("srcSecret").value;
      if (secret) { body.secret = secret; }
      if (srcState.libsLoaded) {
        var ids = [];
        Array.prototype.forEach.call($("srcLibsList").querySelectorAll(".src-lib-cb"), function (cb) {
          if (cb.checked) { ids.push(cb.value); }
        });
        body.libraries = ids;
      }
      if (!body.base_url) { modalStatus(T("sources.err_no_url"), "err"); return; }
      if (!srcState.id && !secret) { modalStatus(T("sources.err_no_key"), "err"); return; }
    } else {
      var p = $("srcPath").value.trim();
      body.local_paths = p ? [p] : [];
      if (!body.local_paths.length) { modalStatus(T("sources.err_no_path"), "err"); return; }
    }
    var btn = $("srcSaveBtn");
    btn.disabled = true;
    modalStatus(T("sources.saving"), "");
    var id = srcState.id;
    fetch(id ? "/api/sources/" + id : "/api/sources", {
      method: id ? "PUT" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    })
      .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
      .then(function (res) {
        if (!res.ok) { throw new Error(res.j.detail || "?"); }
        window.smhToast(T("sources.saved"), "ok");
        hideModal("srcModal");
        loadSources();
      })
      .catch(function (e) { modalStatus(T("msg.failed_prefix") + e.message, "err"); })
      .then(function () { btn.disabled = false; });
  }

  function delSource(id) {
    if (!window.confirm(T("sources.delete_confirm"))) { return; }
    fetch("/api/sources/" + id, { method: "DELETE" })
      .then(function () { window.smhToast(T("sources.deleted"), "ok"); loadSources(); })
      .catch(function () { window.smhToast(T("sources.delete_failed"), "err"); });
  }

  function testSource() {
    if (!srcState.id) { return; }
    var btn = $("srcTestBtn");
    btn.disabled = true;
    modalStatus(T("sources.testing"), "");
    fetch("/api/sources/" + srcState.id + "/test", { method: "POST" })
      .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
      .then(function (res) {
        if (res.ok) { modalStatus(T("sources.test_ok"), "ok"); }
        else { modalStatus(T("sources.error_prefix") + (res.j.detail || "?"), "err"); }
      })
      .catch(function () { modalStatus(T("sources.test_failed"), "err"); })
      .then(function () { btn.disabled = false; });
  }

  function loadLibs() {
    if (!srcState.id) { return; }
    var btn = $("srcLibsBtn");
    btn.disabled = true;
    modalStatus(T("sources.loading_libs"), "");
    fetch("/api/sources/" + srcState.id + "/libraries")
      .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
      .then(function (res) {
        if (!res.ok) { modalStatus(T("sources.error_prefix") + (res.j.detail || "?"), "err"); return; }
        renderLibs(res.j.libraries || [], (srcState.src && srcState.src.libraries) || []);
        modalStatus("", "");
      })
      .catch(function () { modalStatus(T("sources.libs_failed"), "err"); })
      .then(function () { btn.disabled = false; });
  }

  function renderLibs(available, selected) {
    var selSet = {};
    selected.forEach(function (x) { selSet[String(x)] = true; });
    $("srcLibsList").innerHTML = available.map(function (lib) {
      var id = String(lib.id);
      return '<label class="src-lib"><input type="checkbox" class="src-lib-cb" value="' + esc(id) +
        '"' + (selSet[id] ? " checked" : "") + "><span>" + esc(lib.name || id) + "</span></label>";
    }).join("") || '<p class="set-desc">' + esc(T("sources.no_libs")) + "</p>";
    $("srcLibsWrap").hidden = false;
    srcState.libsLoaded = true;
  }

  // -- Datei-Browser (lokale Pfade) -------------------------------------
  function openBrowser() {
    fsBrowse($("srcPath").value.trim() || "/");
    showModal("fsModal");
  }

  function fsBrowse(path) {
    fetch("/api/fs?path=" + encodeURIComponent(path))
      .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
      .then(function (res) {
        if (!res.ok) { if (path !== "/") { fsBrowse("/"); } return; }
        fsCurrent = res.j.path;
        $("fsCurrent").textContent = res.j.path;
        renderFs(res.j);
      })
      .catch(function () {
        $("fsList").innerHTML = '<p class="set-desc">' + esc(T("fs.load_failed")) + "</p>";
      });
  }

  function renderFs(data) {
    var html = "";
    if (data.parent !== null && data.parent !== undefined) {
      html += '<button class="fs-item fs-up" data-path="' + esc(data.parent) + '">&#8598; ' +
        esc(T("fs.up")) + "</button>";
    }
    html += (data.dirs || []).map(function (d) {
      return '<button class="fs-item" data-path="' + esc(d.path) + '">&#128193; ' + esc(d.name) + "</button>";
    }).join("");
    if (!(data.dirs || []).length) {
      html += '<p class="set-desc fs-empty">' + esc(T("fs.empty")) + "</p>";
    }
    $("fsList").innerHTML = html;
    Array.prototype.forEach.call($("fsList").querySelectorAll(".fs-item"), function (b) {
      b.onclick = function () { fsBrowse(b.getAttribute("data-path")); };
    });
  }

  function pickFs() {
    $("srcPath").value = fsCurrent;
    hideModal("fsModal");
  }

  function initSources() {
    var addBtn = $("srcAddBtn");
    if (!addBtn) { return; }   // nur auf der Einstellungsseite vorhanden
    addBtn.onclick = openAdd;
    $("srcKind").onchange = function () { applyKindFields($("srcKind").value); };
    $("srcModalClose").onclick = function () { hideModal("srcModal"); };
    $("srcSaveBtn").onclick = saveModal;
    $("srcTestBtn").onclick = testSource;
    $("srcLibsBtn").onclick = loadLibs;
    $("srcBrowse").onclick = openBrowser;
    $("fsModalClose").onclick = function () { hideModal("fsModal"); };
    $("fsPickBtn").onclick = pickFs;
    $("srcModal").addEventListener("click", function (e) {
      if (e.target === $("srcModal")) { hideModal("srcModal"); }
    });
    $("fsModal").addEventListener("click", function (e) {
      if (e.target === $("fsModal")) { hideModal("fsModal"); }
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") { hideModal("fsModal"); hideModal("srcModal"); }
    });
    loadSources();
  }

  // ======================================================================
  //  Metadaten-Dienste - zwei feste Dienste (TMDb + TheTVDB), Phase 5c
  // ======================================================================
  var MP_FIELDS = {
    tmdb: { toggle: "mpTmdbEnabled", key: "mpTmdbKey", save: "mpTmdbSave" },
    tvdb: { toggle: "mpTvdbEnabled", key: "mpTvdbKey", save: "mpTvdbSave" },
  };

  function mpStatus(msg, type) {
    var s = $("mpStatus");
    if (!s) { return; }
    s.textContent = msg || "";
    s.className = "src-modal-status set-desc" + (type ? " s-" + type : "");
  }

  function loadProviders() {
    if (!$("mpTmdbEnabled")) { return; }   // nur auf der Einstellungsseite
    fetch("/api/providers")
      .then(function (r) { return r.json(); })
      .then(function (data) {
        (data.providers || []).forEach(function (p) {
          var f = MP_FIELDS[p.kind];
          if (!f) { return; }
          $(f.toggle).checked = !!p.enabled;
          $(f.key).value = "";
          $(f.key).placeholder = p.has_key ? T("providers.key_keep") : T("providers.key_enter");
        });
      })
      .catch(function () { mpStatus(T("providers.load_failed"), "err"); });
  }

  function setProvider(kind, body, okMsg) {
    return fetch("/api/providers/" + kind, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    })
      .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
      .then(function (res) {
        if (!res.ok) { throw new Error(res.j.detail || "?"); }
        if (okMsg) { window.smhToast(okMsg, "ok"); }
      });
  }

  function initProviders() {
    if (!$("mpTmdbEnabled")) { return; }   // nur auf der Einstellungsseite
    Object.keys(MP_FIELDS).forEach(function (kind) {
      var f = MP_FIELDS[kind];
      $(f.toggle).onchange = function () {
        var on = $(f.toggle).checked;
        setProvider(kind, { enabled: on }, T(on ? "providers.enabled_on" : "providers.enabled_off"))
          .catch(function (e) {
            $(f.toggle).checked = !on;   // bei Fehler zuruecksetzen
            mpStatus(T("msg.failed_prefix") + e.message, "err");
          });
      };
      $(f.save).onclick = function () {
        var key = $(f.key).value;
        if (!key) { mpStatus(T("providers.err_no_key"), "err"); return; }
        var btn = $(f.save);
        btn.disabled = true;
        setProvider(kind, { api_key: key }, T("providers.saved"))
          .then(function () {
            $(f.key).value = "";
            $(f.key).placeholder = T("providers.key_keep");
            mpStatus("", "");
          })
          .catch(function (e) { mpStatus(T("msg.failed_prefix") + e.message, "err"); })
          .then(function () { btn.disabled = false; });
      };
    });
    loadProviders();
  }

  document.addEventListener("DOMContentLoaded", function () {
    initNav();
    initSources();
    initProviders();

    var allgBtn = $("saveAllgemein");
    if (allgBtn) {
      allgBtn.onclick = function () {
        saveSettings({ "general.instance_name": $("instanceName").value.trim() }, T("msg.saved"), allgBtn);
      };
    }

    var fsk = $("fskEnabled");
    if (fsk) {
      fsk.onchange = function () {
        saveSettings({ "fsk.enabled": fsk.checked }, T(fsk.checked ? "msg.fsk_on" : "msg.fsk_off"));
      };
    }

    // Auto-Uebersetzen-Schalter (Phase 5d, Fix 3): steuert, ob Freigaben in die
    // gewaehlte Rating-Art umgerechnet werden. Bei AUS zeigt die App die rohen
    // Quellwerte; das Rating-Art-Dropdown ist dann irrelevant und ausgeblendet.
    var ratingTranslate = $("ratingTranslate");
    var ratingArtField = $("ratingArtField");
    if (ratingTranslate) {
      ratingTranslate.onchange = function () {
        var on = ratingTranslate.checked;
        if (ratingArtField) { ratingArtField.hidden = !on; }
        saveSettings({ "display.rating_translate": on }, T("msg.saved"));
      };
    }

    var ratingArt = $("ratingArt");
    if (ratingArt) {
      ratingArt.onchange = function () {
        saveSettings({ "display.rating_art": ratingArt.value }, T("msg.saved"));
      };
    }

    var lang = $("primaryLang");
    if (lang) {
      lang.onchange = function () {
        saveSettings({ "display.primary_language": lang.value }, T("msg.primary_lang_saved"));
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
          if (!res.ok) { throw new Error(res.j.detail || "?"); }
          window.smhToast(okMsg, "ok");
          return res.j;
        })
        .catch(function (e) { window.smhToast(T("msg.failed_prefix") + e.message, "err"); throw e; })
        .then(function (v) { if (btn) { btn.disabled = false; } return v; },
              function () { if (btn) { btn.disabled = false; } });
    }

    var uBtn = $("saveUsername");
    if (uBtn) {
      uBtn.onclick = function () {
        postJson("/api/account/username", { username: $("accUsername").value.trim() },
          T("msg.username_saved"), uBtn);
      };
    }
    var eBtn = $("saveEmail");
    if (eBtn) {
      eBtn.onclick = function () {
        postJson("/api/account/email", { email: $("accEmail").value.trim() }, T("msg.email_saved"), eBtn);
      };
    }
    var pBtn = $("savePassword");
    if (pBtn) {
      pBtn.onclick = function () {
        postJson("/api/account/password",
          { current: $("accPwCurrent").value, new: $("accPwNew").value },
          T("msg.password_changed"), pBtn)
          .then(function () { $("accPwCurrent").value = ""; $("accPwNew").value = ""; })
          .catch(function () { /* Toast schon gezeigt */ });
      };
    }
    var authCb = $("authEnabled");
    if (authCb) {
      authCb.onchange = function () {
        if (!authCb.checked) {
          if (!window.confirm(T("msg.auth_confirm"))) { authCb.checked = true; return; }
        }
        postJson("/api/account/auth", { enabled: authCb.checked },
          T(authCb.checked ? "msg.auth_on" : "msg.auth_off"));
      };
    }

    var upd = $("updateCheck");
    if (upd) {
      upd.onclick = function () {
        upd.disabled = true;
        window.smhToast(T("msg.checking_updates"));
        fetch("/api/update/check", { method: "POST" })
          .then(function (r) { return r.json(); })
          .then(function (s) {
            var el = $("updateStatus");
            if (el) {
              el.textContent = s.available
                ? T("settings.about.status_available").replace("{latest}", s.latest)
                : (s.latest ? T("settings.about.status_current").replace("{current}", s.current)
                            : T("settings.about.status_error"));
            }
            window.smhToast(
              s.available ? T("msg.update_available").replace("{latest}", s.latest) : T("msg.up_to_date"),
              "ok");
          })
          .catch(function () { window.smhToast(T("msg.check_failed"), "err"); })
          .then(function () { upd.disabled = false; });
      };
    }
  });
})();
