/* Interactive route line: clicking a city stop loads its info via AJAX
   and reveals it in the detail panel — no page reload. */
(function () {
  "use strict";

  function escapeHtml(value) {
    var div = document.createElement("div");
    div.textContent = value == null ? "" : String(value);
    return div.innerHTML;
  }

  function renderPanel(panel, data) {
    var gallery = (data.gallery || []).slice(0, 3);
    var galleryHtml = gallery
      .map(function (url) {
        return '<img src="' + encodeURI(url) + '" alt="' + escapeHtml(data.name) + '">';
      })
      .join("");

    var attractionsHtml = (data.attractions || [])
      .map(function (a) {
        return '<span class="attraction-chip">' + escapeHtml(a.name) + "</span>";
      })
      .join("");

    panel.innerHTML =
      (galleryHtml ? '<div class="city-gallery">' + galleryHtml + "</div>" : "") +
      '<div class="city-info">' +
      "<h3>" + escapeHtml(data.name) + "</h3>" +
      "<p>" + escapeHtml(data.description) + "</p>" +
      (attractionsHtml
        ? '<div class="city-attractions">' + attractionsHtml + "</div>"
        : "") +
      "</div>";
  }

  async function loadCity(btn) {
    var stops = document.querySelectorAll(".route-stop");
    stops.forEach(function (b) {
      b.classList.remove("active");
    });
    btn.classList.add("active");

    var slug = btn.dataset.citySlug;
    var panel = document.getElementById("city-detail-panel");
    if (!panel) return;

    panel.hidden = false;
    panel.innerHTML = '<div class="city-loading">Yuklanmoqda...</div>';

    try {
      var res = await fetch("/api/cities/" + encodeURIComponent(slug) + "/info/");
      if (!res.ok) throw new Error("HTTP " + res.status);
      var data = await res.json();
      renderPanel(panel, data);
    } catch (err) {
      panel.innerHTML =
        '<div class="city-loading">Ma\'lumotni yuklab bo\'lmadi.</div>';
    }

    panel.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  document.addEventListener("DOMContentLoaded", function () {
    var stops = document.querySelectorAll(".route-stop");
    if (!stops.length) return;

    stops.forEach(function (btn) {
      btn.addEventListener("click", function () {
        loadCity(btn);
      });
    });

    // Auto-open the first stop so the panel isn't empty on page load.
    loadCity(stops[0]);
  });
})();
