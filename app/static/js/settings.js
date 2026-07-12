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
  //  Datenquellen (Phase 4a) - Quellen-Editor im "Datenquellen"-Panel
  // ======================================================================
  var KIND_LABEL = { emby: "Emby", jellyfin: "Jellyfin", plex: "Plex", local: T("sources.kind.local") };

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
        root.innerHTML = '<p class="set-desc">' + esc(T("sources.load_failed")) + "</p>";
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
    var label = KIND_LABEL[kind] || kind;
    var name = src ? src.name : "";
    var enabled = src ? src.enabled : true;
    var head =
      '<div class="src-head"><h3>' + esc(label) + "</h3>" +
        '<label class="set-toggle"><input type="checkbox" class="src-enabled"' +
        (enabled ? " checked" : "") + "><span>" + esc(T("sources.active")) + "</span></label></div>" +
      '<div class="set-field"><label>' + esc(T("sources.name")) + "</label>" +
        '<input class="field src-name" maxlength="60" value="' + esc(name) +
        '" placeholder="' + esc(label) + '"></div>';

    var mid, actions;
    if (isServer) {
      var secretPh = src && src.has_secret ? T("sources.secret_keep") : T("sources.secret_enter");
      mid =
        '<div class="set-field"><label>' + esc(T("sources.server_url")) + "</label>" +
          '<input class="field src-url" value="' + esc(src ? src.base_url : "") +
          '" placeholder="http://192.168.1.19:8096"></div>' +
        '<div class="set-field"><label>' + esc(T("sources.api_key")) + "</label>" +
          '<input class="field src-secret" type="password" autocomplete="new-password" placeholder="' +
          esc(secretPh) + '"></div>' +
        '<div class="set-field src-libs" hidden><label>' + esc(T("sources.libraries")) + " " +
          '<span class="set-hint">' + esc(T("sources.libraries_hint")) + "</span></label>" +
          '<div class="src-libs-list"></div></div>';
      actions =
        '<button class="btn btn-primary src-save">' + esc(T("common.save")) + "</button>" +
        '<button class="btn src-test"' + (src ? "" : " disabled") + ">" + esc(T("sources.test")) + "</button>" +
        '<button class="btn src-libsbtn"' + (src ? "" : " disabled") + ">" + esc(T("sources.libraries_btn")) + "</button>" +
        '<button class="btn src-del"' + (src ? "" : " disabled") + ">" + esc(T("sources.delete")) + "</button>";
    } else {
      var paths = src && src.local_paths ? src.local_paths.join("\n") : "";
      mid =
        '<div class="set-field"><label>' + esc(T("sources.paths")) + " " +
          '<span class="set-hint">' + esc(T("sources.paths_hint")) + "</span></label>" +
          '<textarea class="field src-paths" rows="3" placeholder="/media/filme">' +
          esc(paths) + "</textarea></div>";
      actions =
        '<button class="btn btn-primary src-save">' + esc(T("common.save")) + "</button>" +
        '<button class="btn src-del"' + (src ? "" : " disabled") + ">" + esc(T("sources.delete")) + "</button>";
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
        if (!window.confirm(T("sources.delete_confirm"))) { return; }
        fetch("/api/sources/" + id, { method: "DELETE" })
          .then(function () { window.smhToast(T("sources.deleted"), "ok"); reloadSources(); })
          .catch(function () { window.smhToast(T("sources.delete_failed"), "err"); });
      };
    }

    var testBtn = el.querySelector(".src-test");
    if (testBtn) {
      testBtn.onclick = function () {
        var id = idOf();
        if (!id) { return; }
        testBtn.disabled = true;
        setStatus(el, T("sources.testing"), "");
        fetch("/api/sources/" + id + "/test", { method: "POST" })
          .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
          .then(function (res) {
            if (res.ok) { setStatus(el, T("sources.test_ok"), "ok"); }
            else { setStatus(el, T("sources.error_prefix") + (res.j.detail || "?"), "err"); }
          })
          .catch(function () { setStatus(el, T("sources.test_failed"), "err"); })
          .then(function () { testBtn.disabled = false; });
      };
    }

    var libsBtn = el.querySelector(".src-libsbtn");
    if (libsBtn) {
      libsBtn.onclick = function () {
        var id = idOf();
        if (!id) { return; }
        libsBtn.disabled = true;
        setStatus(el, T("sources.loading_libs"), "");
        fetch("/api/sources/" + id + "/libraries")
          .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
          .then(function (res) {
            if (!res.ok) { setStatus(el, T("sources.error_prefix") + (res.j.detail || "?"), "err"); return; }
            renderLibs(el, res.j.libraries || [], (src && src.libraries) || []);
            setStatus(el, "", "");
          })
          .catch(function () { setStatus(el, T("sources.libs_failed"), "err"); })
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
    }).join("") || '<p class="set-desc">' + esc(T("sources.no_libs")) + "</p>";
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
      if (!body.base_url) { setStatus(el, T("sources.err_no_url"), "err"); return; }
      if (!id && !secret) { setStatus(el, T("sources.err_no_key"), "err"); return; }
    } else {
      body.local_paths = el.querySelector(".src-paths").value.split("\n")
        .map(function (p) { return p.trim(); }).filter(Boolean);
      if (!body.local_paths.length) { setStatus(el, T("sources.err_no_path"), "err"); return; }
    }
    var save = el.querySelector(".src-save");
    save.disabled = true;
    setStatus(el, T("sources.saving"), "");
    fetch(id ? "/api/sources/" + id : "/api/sources", {
      method: id ? "PUT" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    })
      .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
      .then(function (res) {
        if (!res.ok) { throw new Error(res.j.detail || "?"); }
        window.smhToast(T("sources.saved"), "ok");
        reloadSources();
      })
      .catch(function (e) {
        setStatus(el, T("msg.failed_prefix") + e.message, "err");
        window.smhToast(T("sources.save_failed"), "err");
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
        saveSettings({ "general.instance_name": $("instanceName").value.trim() }, T("msg.saved"), allgBtn);
      };
    }

    var fsk = $("fskEnabled");
    if (fsk) {
      fsk.onchange = function () {
        saveSettings({ "fsk.enabled": fsk.checked }, T(fsk.checked ? "msg.fsk_on" : "msg.fsk_off"));
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
