/* Inline-SVG-Icons fuer die Cover-Badges. Skalieren verlustfrei (currentColor
   erbt die Badge-Farbe), CSP-sicher, keine externen Requests.
   window.smhIcon(name) -> SVG-String oder "". */
(function () {
  "use strict";
  var ICONS = {
    // Lautsprecher mit Schallwellen (Audiospur)
    audio:
      '<svg class="smh-ic" viewBox="0 0 16 16" aria-hidden="true">' +
      '<path fill="currentColor" d="M7 3 3.8 5.6H1.6v4.8h2.2L7 13z"/>' +
      '<path fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" ' +
      'd="M10 5.6a3.3 3.3 0 0 1 0 4.8M11.9 3.7a6 6 0 0 1 0 8.6"/></svg>',
    // "CC" (Closed Captions) - abgerundetes Rechteck mit zwei C-Boegen (wie Emby)
    cc:
      '<svg class="smh-ic smh-ic-cc" viewBox="0 0 20 14" aria-hidden="true">' +
      '<rect x="0.7" y="0.7" width="18.6" height="12.6" rx="3" fill="none" ' +
      'stroke="currentColor" stroke-width="1.2"/>' +
      '<path fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" ' +
      'd="M8.4 5.7a2.3 2.3 0 1 0 0 2.6M15.6 5.7a2.3 2.3 0 1 0 0 2.6"/></svg>',
  };
  window.smhIcon = function (name) { return ICONS[name] || ""; };
})();
