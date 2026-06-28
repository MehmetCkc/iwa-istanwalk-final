"use strict";

document.addEventListener("DOMContentLoaded", function () {
  var calendars = Array.prototype.slice.call(
    document.querySelectorAll("[data-tour-calendar]"),
  );

  calendars.forEach(function (calendar) {
    var shell = calendar.closest("[data-calendar-shell]");
    var root = shell ? shell.parentElement : calendar.parentElement;
    var days = Array.prototype.slice.call(
      calendar.querySelectorAll("[data-calendar-day]"),
    );
    var panels = Array.prototype.slice.call(
      root.querySelectorAll("[data-calendar-panel]"),
    );
    var prev = shell ? shell.querySelector("[data-calendar-prev]") : null;
    var next = shell ? shell.querySelector("[data-calendar-next]") : null;
    var label = shell ? shell.querySelector("[data-calendar-label]") : null;
    var isDateFilter = calendar.hasAttribute("data-date-picker");
    var currentWeek = 0;
    var maxWeek = days.reduce(function (max, day) {
      return Math.max(max, Number(day.getAttribute("data-calendar-week")) || 0);
    }, 0);

    function activateDay(day) {
      var key = day.getAttribute("data-calendar-day");

      days.forEach(function (item) {
        item.classList.toggle("active", item === day);
      });

      panels.forEach(function (panel) {
        panel.classList.toggle(
          "active",
          panel.getAttribute("data-calendar-panel") === key,
        );
      });
    }

    function showWeek(week) {
      currentWeek = Math.max(0, Math.min(maxWeek, week));
      var locked = shell && shell.hasAttribute("data-calendar-locked");

      days.forEach(function (day) {
        var weekValue = Number(day.getAttribute("data-calendar-week")) || 0;
        day.classList.toggle("hidden-week", weekValue !== currentWeek);
      });

      if (label) {
        label.textContent = "Week " + (currentWeek + 1);
      }

      if (prev) {
        prev.disabled = locked || currentWeek === 0;
      }

      if (next) {
        next.disabled = locked || currentWeek === maxWeek;
      }

      var activeVisible = days.some(function (day) {
        return (
          day.classList.contains("active") &&
          !day.classList.contains("hidden-week")
        );
      });

      if (!activeVisible && !isDateFilter) {
        var firstVisible = days.find(function (day) {
          return !day.classList.contains("hidden-week");
        });

        if (firstVisible) {
          activateDay(firstVisible);
        }
      }
    }

    calendar.addEventListener("click", function (event) {
      var day = event.target.closest("[data-calendar-day]");
      if (!day || day.disabled || day.classList.contains("past")) {
        return;
      }

      if (!isDateFilter) {
        activateDay(day);
      }
    });

    if (prev) {
      prev.addEventListener("click", function () {
        if (shell && shell.hasAttribute("data-calendar-locked")) {
          return;
        }
        showWeek(currentWeek - 1);
      });
    }

    if (next) {
      next.addEventListener("click", function () {
        if (shell && shell.hasAttribute("data-calendar-locked")) {
          return;
        }
        showWeek(currentWeek + 1);
      });
    }

    if (shell) {
      shell.addEventListener("calendar-lock-change", function () {
        showWeek(currentWeek);
      });
    }

    showWeek(0);
  });

  var bookingForm = document.querySelector("[data-booking-form]");

  if (!bookingForm) {
    return;
  }

  var bookingDate = bookingForm.querySelector("[data-booking-date]");
  var bookingTime = bookingForm.querySelector("[data-booking-time]");
  var bookingCount = bookingForm.querySelector("[data-booking-count]");
  var bookingSubmit = bookingForm.querySelector("[data-booking-submit]");
  var bookingRemaining = bookingForm.querySelector("[data-booking-remaining]");
  var participantFields = bookingForm.querySelector(
    "[data-participant-fields]",
  );

  function renderParticipantFields() {
    if (!participantFields) {
      return;
    }
    var people = Number(bookingCount.value) || 0;
    var extraPeople = Math.max(0, people - 1);
    participantFields.innerHTML = "";

    for (var index = 0; index < extraPeople; index += 1) {
      var label = document.createElement("label");
      label.textContent = "Friend " + (index + 1);

      var input = document.createElement("input");
      input.name = "participant_names[]";
      input.type = "text";
      input.required = true;
      input.placeholder = "Full name";

      participantFields.appendChild(label);
      participantFields.appendChild(input);
    }
  }

  function setPeopleLimit(limit) {
    var count = Math.max(0, Math.min(4, Number(limit) || 0));
    bookingCount.innerHTML = "";

    if (count === 0) {
      if (participantFields) {
        participantFields.innerHTML = "";
      }
      var empty = document.createElement("option");
      empty.value = "";
      empty.textContent = "No seats left";
      bookingCount.appendChild(empty);
      bookingSubmit.disabled = true;
      bookingSubmit.textContent = "No places left";
      if (bookingRemaining) {
        bookingRemaining.textContent = "No seats left for this time.";
      }
      return;
    }

    for (var index = 1; index <= count; index += 1) {
      var option = document.createElement("option");
      option.value = String(index);
      var friendCount = index - 1;
      option.textContent =
        friendCount === 0
          ? "No friends"
          : friendCount + " Friend" + (friendCount === 1 ? "" : "s");
      bookingCount.appendChild(option);
    }
    bookingSubmit.disabled = false;
    bookingSubmit.textContent = "Reserve spot";
    if (bookingRemaining) {
      bookingRemaining.textContent =
        count +
        " seat" +
        (count === 1 ? "" : "s") +
        " available for your booking.";
    }
    renderParticipantFields();
  }

  bookingCount.addEventListener("change", renderParticipantFields);

  document.addEventListener("click", function (event) {
    var slot = event.target.closest("[data-booking-slot-date]");
    if (!slot) {
      return;
    }

    Array.prototype.forEach.call(
      document.querySelectorAll("[data-booking-slot-date]"),
      function (item) {
        item.classList.toggle("selected", item === slot);
      },
    );

    // The selected slot decides both the hidden booking date/time and the seat dropdown.
    bookingDate.value = slot.getAttribute("data-booking-slot-date");
    bookingTime.value = slot.getAttribute("data-booking-slot-time");
    setPeopleLimit(slot.getAttribute("data-booking-slot-limit"));
  });
});
