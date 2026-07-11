/* Hidden staff access: press Ctrl+Shift+A to reveal the staff login modal.
   The password is verified server-side; nothing here checks credentials. */
(function () {
  "use strict";

  function getModal() {
    return document.getElementById("admin-access-modal");
  }

  function openAdminModal() {
    var modal = getModal();
    if (!modal) return;
    modal.hidden = false;
    var username = modal.querySelector("input[name=username]");
    if (username) username.focus();
  }

  function closeAdminModal() {
    var modal = getModal();
    if (!modal) return;
    modal.hidden = true;
    var err = modal.querySelector(".admin-access-error");
    if (err) err.hidden = true;
  }

  // Ctrl+Shift+A reveals the modal.
  document.addEventListener("keydown", function (e) {
    if (e.ctrlKey && e.shiftKey && e.code === "KeyA") {
      e.preventDefault();
      openAdminModal();
    }
    if (e.key === "Escape") {
      closeAdminModal();
    }
  });

  document.addEventListener("DOMContentLoaded", function () {
    var modal = getModal();
    if (!modal) return;

    var closeBtn = modal.querySelector(".admin-access-close");
    if (closeBtn) closeBtn.addEventListener("click", closeAdminModal);

    var backdrop = modal.querySelector(".admin-access-backdrop");
    if (backdrop) backdrop.addEventListener("click", closeAdminModal);
  });
})();
