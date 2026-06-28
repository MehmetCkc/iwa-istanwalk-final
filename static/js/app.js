"use strict";

document.addEventListener("DOMContentLoaded", function () {
  function showConfirmation(message, onConfirm) {
    var previousFocus = document.activeElement;
    var overlay = document.createElement("div");
    overlay.className = "confirm-overlay";
    overlay.innerHTML = [
      '<section class="confirm-box" role="alertdialog" aria-modal="true" aria-labelledby="confirm-title">',
      '<span class="confirm-kicker">ISTANWALK / CONFIRM</span>',
      '<h2 id="confirm-title">Are you sure?</h2>',
      '<p class="confirm-message"></p>',
      '<div class="confirm-actions">',
      '<button class="confirm-back" type="button">Go back</button>',
      '<button class="confirm-accept" type="button">Yes, continue</button>',
      "</div>",
      "</section>",
    ].join("");
    overlay.querySelector(".confirm-message").textContent = message;
    document.body.appendChild(overlay);
    document.body.classList.add("confirm-open");

    var back = overlay.querySelector(".confirm-back");
    var accept = overlay.querySelector(".confirm-accept");

    function close() {
      document.removeEventListener("keydown", onKeydown);
      document.body.classList.remove("confirm-open");
      overlay.remove();
      if (previousFocus && previousFocus.focus) previousFocus.focus();
    }

    function onKeydown(event) {
      if (event.key === "Escape") close();
    }

    back.addEventListener("click", close);
    overlay.addEventListener("click", function (event) {
      if (event.target === overlay) close();
    });
    accept.addEventListener("click", function () {
      close();
      onConfirm();
    });
    document.addEventListener("keydown", onKeydown);
    back.focus();
  }

  document.addEventListener("click", function (event) {
    var control = event.target.closest("a[data-confirm], button[data-confirm]");
    if (!control) return;
    event.preventDefault();
    showConfirmation(control.getAttribute("data-confirm"), function () {
      if (control.tagName === "A") {
        window.location.href = control.href;
        return;
      }
      control.removeAttribute("data-confirm");
      control.click();
    });
  });

  document.addEventListener("submit", function (event) {
    var form = event.target;
    var message = form.getAttribute("data-confirm");
    if (!message || form.dataset.confirmed === "true") {
      delete form.dataset.confirmed;
      return;
    }
    event.preventDefault();
    var submitter = event.submitter;
    showConfirmation(message, function () {
      form.dataset.confirmed = "true";
      if (form.requestSubmit) form.requestSubmit(submitter);
      else form.submit();
    });
  });

  var toggle = document.querySelector("[data-nav-toggle]");
  var nav = document.querySelector("[data-nav]");

  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      nav.classList.toggle("open");
    });
  }

  var uploadInput = document.querySelector("[data-upload-input]");
  var uploadName = document.querySelector("[data-upload-name]");
  var uploadPreview = document.querySelector("[data-upload-preview]");

  if (uploadInput && uploadName && uploadPreview) {
    uploadInput.addEventListener("change", function () {
      var file = uploadInput.files && uploadInput.files[0];
      if (!file) {
        return;
      }

      uploadName.textContent = file.name;

      if (file.type && file.type.indexOf("image/") === 0) {
        var reader = new FileReader();
        reader.addEventListener("load", function () {
          uploadPreview.innerHTML = "";
          var image = document.createElement("img");
          image.src = reader.result;
          image.alt = "Selected profile picture";
          uploadPreview.appendChild(image);
        });
        reader.readAsDataURL(file);
      }
    });
  }

  function fillTulips() {
    var stack = document.querySelector("[data-tulip-stack]");
    if (!stack) {
      return;
    }

    var src = stack.getAttribute("data-tulip-src");
    var main = document.querySelector(".main");
    var side = document.querySelector(".side");
    if (
      !src ||
      !main ||
      !side ||
      window.matchMedia("(max-width: 900px)").matches
    ) {
      stack.innerHTML = "";
      return;
    }

    // Fill the left rail with decorative tulips based on the current page height.
    var navHeight = Array.prototype.reduce.call(
      side.querySelectorAll(".navblock"),
      function (total, item) {
        return total + item.offsetHeight;
      },
      0,
    );
    var available = Math.max(0, main.offsetHeight - navHeight - 36);
    var count = Math.max(0, Math.floor((available + 16) / 126));
    var existing = stack.querySelectorAll("img").length;

    if (existing === count) {
      return;
    }

    stack.innerHTML = "";
    for (var index = 0; index < count; index += 1) {
      var image = document.createElement("img");
      image.src = src;
      image.alt = "";
      stack.appendChild(image);
    }
  }

  window.fillIstanwalkTulips = fillTulips;
  fillTulips();
  window.addEventListener("resize", fillTulips);
  window.addEventListener("load", fillTulips);

  var reviewButtons = Array.prototype.slice.call(
    document.querySelectorAll("[data-show-reviews]"),
  );

  reviewButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      var section = button.closest("[data-review-section]");
      if (!section) {
        return;
      }

      Array.prototype.forEach.call(
        section.querySelectorAll("[data-review-card]"),
        function (card) {
          card.classList.remove("hidden-review");
        },
      );
      button.remove();
      fillTulips();
    });
  });

  var clickableCards = Array.prototype.slice.call(
    document.querySelectorAll("[data-card-link]"),
  );

  clickableCards.forEach(function (card) {
    card.addEventListener("click", function (event) {
      if (
        event.target.closest(
          "a, button, input, textarea, select, label, summary",
        )
      ) {
        return;
      }

      var href = card.getAttribute("data-card-link");
      if (href) {
        window.location.href = href;
      }
    });
  });
});
