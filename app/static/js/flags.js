/* Eingebettete SVG-Flaggen (CSP-sicher, ohne externe Abhaengigkeiten).
   window.smhFlag(code) -> SVG-String oder null. Windows/Edge zeigt Emoji-
   Flaggen nur als Buchstaben - SVG loest das ueberall. */
(function () {
  "use strict";

  var SVG = {
    de: '<svg class="fl" viewBox="0 0 20 15"><rect width="20" height="15" fill="#FFCE00"/><rect width="20" height="10" fill="#DD0000"/><rect width="20" height="5" fill="#000"/></svg>',
    gb: '<svg class="fl" viewBox="0 0 20 15"><rect width="20" height="15" fill="#012169"/><path d="M0,0L20,15M20,0L0,15" stroke="#fff" stroke-width="3"/><path d="M0,0L20,15M20,0L0,15" stroke="#C8102E" stroke-width="1.5"/><rect x="8" width="4" height="15" fill="#fff"/><rect y="5.5" width="20" height="4" fill="#fff"/><rect x="8.5" width="3" height="15" fill="#C8102E"/><rect y="6" width="20" height="3" fill="#C8102E"/></svg>',
    jp: '<svg class="fl" viewBox="0 0 20 15"><rect width="20" height="15" fill="#fff"/><circle cx="10" cy="7.5" r="4" fill="#BC002D"/></svg>',
    fr: '<svg class="fl" viewBox="0 0 20 15"><rect width="20" height="15" fill="#fff"/><rect width="6.7" height="15" fill="#0055A4"/><rect x="13.3" width="6.7" height="15" fill="#EF4135"/></svg>',
    es: '<svg class="fl" viewBox="0 0 20 15"><rect width="20" height="15" fill="#AA151B"/><rect y="3.75" width="20" height="7.5" fill="#F1BF00"/></svg>',
    it: '<svg class="fl" viewBox="0 0 20 15"><rect width="20" height="15" fill="#fff"/><rect width="6.7" height="15" fill="#009246"/><rect x="13.3" width="6.7" height="15" fill="#CE2B37"/></svg>',
    kr: '<svg class="fl" viewBox="0 0 20 15"><rect width="20" height="15" fill="#fff"/><circle cx="10" cy="7.5" r="4" fill="#0047A0"/><path d="M10,3.5a4,4 0 0,1 0,8a2,2 0 0,0 0,-4a2,2 0 0,1 0,-4z" fill="#CD2E3A"/></svg>',
    ru: '<svg class="fl" viewBox="0 0 20 15"><rect width="20" height="15" fill="#fff"/><rect y="5" width="20" height="5" fill="#0039A6"/><rect y="10" width="20" height="5" fill="#D52B1E"/></svg>',
    tr: '<svg class="fl" viewBox="0 0 20 15"><rect width="20" height="15" fill="#E30A17"/><circle cx="8" cy="7.5" r="3.2" fill="#fff"/><circle cx="9.1" cy="7.5" r="2.5" fill="#E30A17"/><path d="M12.2,7.5l2,0.65-1.24,-1.7v2.1l1.24,-1.7z" fill="#fff"/></svg>',
    pl: '<svg class="fl" viewBox="0 0 20 15"><rect width="20" height="15" fill="#fff"/><rect y="7.5" width="20" height="7.5" fill="#DC143C"/></svg>',
    nl: '<svg class="fl" viewBox="0 0 20 15"><rect width="20" height="15" fill="#fff"/><rect width="20" height="5" fill="#AE1C28"/><rect y="10" width="20" height="5" fill="#21468B"/></svg>',
    pt: '<svg class="fl" viewBox="0 0 20 15"><rect width="20" height="15" fill="#DA291C"/><rect width="8" height="15" fill="#046A38"/><circle cx="8" cy="7.5" r="1.8" fill="#FFE900"/></svg>',
    cn: '<svg class="fl" viewBox="0 0 20 15"><rect width="20" height="15" fill="#DE2910"/><path d="M5,2.5l1.05,3.23-2.75,-2h3.4l-2.75,2z" fill="#FFDE00"/></svg>',
    sa: '<svg class="fl" viewBox="0 0 20 15"><rect width="20" height="15" fill="#006C35"/></svg>'
  };
  var MAP = { ger: "de", deu: "de", de: "de", eng: "gb", en: "gb", jpn: "jp", ja: "jp",
    fre: "fr", fra: "fr", fr: "fr", spa: "es", es: "es", ita: "it", it: "it",
    kor: "kr", ko: "kr", rus: "ru", ru: "ru", tur: "tr", tr: "tr", pol: "pl", pl: "pl",
    nld: "nl", dut: "nl", nl: "nl", por: "pt", pt: "pt", chi: "cn", zho: "cn", zh: "cn",
    ara: "sa", ar: "sa" };

  window.smhFlag = function (code) {
    var c = MAP[String(code || "").toLowerCase()];
    return c ? SVG[c] : null;
  };

  // Teilweise-Variante: obere Haelfte farbig, untere diagonal ausgegraut.
  // Alles in EINEM SVG: die Flagge zweimal, entlang der Diagonale (oben-rechts
  // -> unten-links) in zwei Dreiecke geclippt. Oben: farbig. Unten: rein
  // entsaettigt (saturate 0) bei opacity 0.42 - dieselbe Graustufe wie die
  // "keine"-Flagge (.cbadge.off .fl in app.css). Weil die farbige Kopie nur ins
  // obere Dreieck geclippt ist, scheint unten KEINE Farbe mehr durch.
  // Keine CSS-Overlays -> keine Extralinie, keine krumme Kante.
  var _pid = 0;
  window.smhFlagPartial = function (code) {
    var c = MAP[String(code || "").toLowerCase()];
    if (!c) { return null; }
    var inner = SVG[c].replace(/^<svg[^>]*>/, "").replace(/<\/svg>\s*$/, "");
    var id = "smhp" + (++_pid);
    return '<svg class="fl" viewBox="0 0 20 15">' +
      "<defs>" +
        '<clipPath id="' + id + 'u"><polygon points="0,0 20,0 0,15"/></clipPath>' +
        '<clipPath id="' + id + 'c"><polygon points="20,0 20,15 0,15"/></clipPath>' +
        '<filter id="' + id + 'g"><feColorMatrix type="saturate" values="0"/></filter>' +
      "</defs>" +
      '<g clip-path="url(#' + id + 'u)">' + inner + "</g>" +
      '<g clip-path="url(#' + id + 'c)" filter="url(#' + id + 'g)" opacity="0.42">' +
        inner + "</g>" +
      "</svg>";
  };
})();
