/* Brand-pattern page transition. Intercepts internal link clicks, plays a
   quick wipe, then navigates. Total animation budget < 500ms. Progressive
   enhancement: anything we don't handle just navigates normally. */
(function () {
  "use strict";

  var reduceMotion =
    window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function overlay() {
    return document.getElementById("page-transition-overlay");
  }

  document.addEventListener("click", function (e) {
    if (reduceMotion) return;
    // Ignore modified clicks (new tab/window, etc.).
    if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) {
      return;
    }

    var link = e.target.closest("a");
    if (!link) return;

    var href = link.getAttribute("href");
    if (!href || href.startsWith("#") || href.startsWith("mailto:") || href.startsWith("tel:")) return;
    if (link.target === "_blank" || link.hasAttribute("download")) return;
    if (link.origin !== window.location.origin) return;
    // Same page (just a hash/query change to the current path) — let it be.
    if (link.pathname === window.location.pathname && link.hash) return;

    var ov = overlay();
    if (!ov) return;

    e.preventDefault();
    ov.classList.add("active");
    setTimeout(function () {
      window.location.href = href;
    }, 380);
  });

  // Wipe out on each fresh page load.
  function playOut() {
    if (reduceMotion) return;
    var ov = overlay();
    if (!ov) return;
    ov.classList.add("active");
    requestAnimationFrame(function () {
      setTimeout(function () {
        ov.classList.add("leaving");
        setTimeout(function () {
          ov.classList.remove("active", "leaving");
        }, 400);
      }, 50);
    });
  }

  window.addEventListener("DOMContentLoaded", playOut);

  // When restored from the back/forward cache, clear any stuck overlay state.
  window.addEventListener("pageshow", function (e) {
    var ov = overlay();
    if (ov) ov.classList.remove("active", "leaving");
    if (e.persisted) playOut();
  });
})();
