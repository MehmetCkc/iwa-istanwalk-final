"use strict";

document.addEventListener("DOMContentLoaded", function () {
  var filterGroups = Array.prototype.slice.call(
    document.querySelectorAll("[data-filter-group]"),
  );
  var cards = Array.prototype.slice.call(
    document.querySelectorAll("[data-tour-card]"),
  );

  if (!filterGroups.length || !cards.length) {
    return;
  }

  var activeFilters = {
    category: [],
    language: [],
    durationMin: null,
    durationMax: null,
    dateStart: "",
    dateEnd: "",
  };

  function isDateInRange(dateValue) {
    // YYYY-MM-DD strings sort chronologically, so range checks do not need
    // timezone-sensitive Date conversion.
    if (!activeFilters.dateStart) {
      return true;
    }
    if (!activeFilters.dateEnd) {
      return dateValue === activeFilters.dateStart;
    }
    return (
      dateValue >= activeFilters.dateStart && dateValue <= activeFilters.dateEnd
    );
  }

  function applyTourFilters() {
    cards.forEach(function (card) {
      var category = card.getAttribute("data-category") || "";
      var languages = (card.getAttribute("data-languages") || "").split(/\s+/);
      var duration = Number(card.getAttribute("data-duration")) || 0;
      var dates = (card.getAttribute("data-dates") || "").split(/\s+/);
      var categoryMatches =
        activeFilters.category.length === 0 ||
        activeFilters.category.indexOf(category) !== -1;
      var languageMatches =
        activeFilters.language.length === 0 ||
        activeFilters.language.some(function (language) {
          return languages.indexOf(language) !== -1;
        });
      var minDurationMatches =
        activeFilters.durationMin === null ||
        duration >= activeFilters.durationMin;
      var maxDurationMatches =
        activeFilters.durationMax === null ||
        duration <= activeFilters.durationMax;
      var dateMatches = dates.some(isDateInRange);

      card.classList.toggle(
        "hidden",
        !categoryMatches ||
          !languageMatches ||
          !minDurationMatches ||
          !maxDurationMatches ||
          !dateMatches,
      );
    });
  }

  function updateDatePieces() {
    var pieces = Array.prototype.slice.call(
      document.querySelectorAll("[data-date-piece]"),
    );
    var labels = Array.prototype.slice.call(
      document.querySelectorAll("[data-date-range-label]"),
    );
    var labelText = "Any date";

    pieces.forEach(function (piece) {
      var value = piece.getAttribute("data-date-piece");
      var selected = activeFilters.dateStart && isDateInRange(value);
      piece.classList.toggle("selected", selected);
      piece.classList.toggle(
        "range-edge",
        value === activeFilters.dateStart || value === activeFilters.dateEnd,
      );
    });

    if (
      activeFilters.dateStart &&
      (!activeFilters.dateEnd ||
        activeFilters.dateStart === activeFilters.dateEnd)
    ) {
      labelText = activeFilters.dateStart;
    } else if (activeFilters.dateStart) {
      labelText = activeFilters.dateStart + " / " + activeFilters.dateEnd;
    }

    labels.forEach(function (label) {
      label.textContent = labelText;
    });
  }

  filterGroups.forEach(function (filterGroup) {
    filterGroup.addEventListener("click", function (event) {
      var button = event.target.closest("[data-filter]");
      if (!button) {
        return;
      }

      var type = filterGroup.getAttribute("data-filter-type") || "category";
      var value = button.getAttribute("data-filter");
      var allButton = filterGroup.querySelector('[data-filter="all"]');
      var selectedValues = activeFilters[type];

      if (value === "all") {
        activeFilters[type] = [];
      } else if (selectedValues.indexOf(value) === -1) {
        selectedValues.push(value);
      } else {
        selectedValues.splice(selectedValues.indexOf(value), 1);
      }

      Array.prototype.forEach.call(
        filterGroup.querySelectorAll(".chip"),
        function (chip) {
          var chipValue = chip.getAttribute("data-filter");
          chip.classList.toggle(
            "on",
            chipValue === "all"
              ? activeFilters[type].length === 0
              : activeFilters[type].indexOf(chipValue) !== -1,
          );
        },
      );

      if (allButton && activeFilters[type].length === 0) {
        allButton.classList.add("on");
      }
      applyTourFilters();
    });
  });

  var durationMinFilter = document.querySelector("[data-duration-min]");
  var durationMaxFilter = document.querySelector("[data-duration-max]");

  function updateDurationFilter() {
    var minValue = durationMinFilter ? Number(durationMinFilter.value) : 0;
    var maxValue = durationMaxFilter ? Number(durationMaxFilter.value) : 0;

    activeFilters.durationMin = minValue > 0 ? minValue : null;
    activeFilters.durationMax = maxValue > 0 ? maxValue : null;
  }

  [durationMinFilter, durationMaxFilter].forEach(function (durationFilter) {
    if (!durationFilter) {
      return;
    }
    durationFilter.addEventListener("input", function () {
      updateDurationFilter();
      applyTourFilters();
    });
  });
  updateDurationFilter();

  var datePicker = document.querySelector("[data-filter-month]");
  var dateGrid = datePicker
    ? datePicker.querySelector("[data-date-grid]")
    : null;
  var datePrev = datePicker
    ? datePicker.querySelector("[data-date-prev]")
    : null;
  var dateNext = datePicker
    ? datePicker.querySelector("[data-date-next]")
    : null;
  var dateClear = datePicker
    ? datePicker.querySelector("[data-date-clear]")
    : null;
  var clearFilters = document.querySelector("[data-clear-filters]");
  var visibleStart =
    datePicker && datePicker.getAttribute("data-initial-date")
      ? new Date(datePicker.getAttribute("data-initial-date") + "T00:00:00")
      : new Date();
  visibleStart.setDate(visibleStart.getDate() - visibleStart.getDay());

  function formatDateKey(date) {
    var month = String(date.getMonth() + 1).padStart(2, "0");
    var day = String(date.getDate()).padStart(2, "0");
    return date.getFullYear() + "-" + month + "-" + day;
  }

  function renderDateCalendar() {
    if (!dateGrid) {
      return;
    }

    dateGrid.innerHTML = "";

    // The filter shows a rolling two-week window instead of a full monthly calendar.
    for (var index = 0; index < 14; index += 1) {
      var day = new Date(visibleStart);
      day.setDate(visibleStart.getDate() + index);
      var key = formatDateKey(day);
      var button = document.createElement("button");
      button.type = "button";
      button.className = "month-day";
      button.textContent = String(day.getDate());
      button.setAttribute("data-date-piece", key);
      dateGrid.appendChild(button);
    }
    updateDatePieces();
  }

  if (datePicker) {
    datePicker.addEventListener("click", function (event) {
      var piece = event.target.closest("[data-date-piece]");
      if (!piece) {
        return;
      }

      var selectedDate = piece.getAttribute("data-date-piece");
      // The first click starts a range; the second closes it and swaps
      // the endpoints when the user chooses an earlier date.
      if (!activeFilters.dateStart || activeFilters.dateEnd) {
        activeFilters.dateStart = selectedDate;
        activeFilters.dateEnd = "";
      } else if (selectedDate < activeFilters.dateStart) {
        activeFilters.dateEnd = activeFilters.dateStart;
        activeFilters.dateStart = selectedDate;
      } else {
        activeFilters.dateEnd = selectedDate;
      }

      updateDatePieces();
      applyTourFilters();
    });
  }

  if (datePrev) {
    datePrev.addEventListener("click", function () {
      visibleStart.setDate(visibleStart.getDate() - 14);
      renderDateCalendar();
    });
  }

  if (dateNext) {
    dateNext.addEventListener("click", function () {
      visibleStart.setDate(visibleStart.getDate() + 14);
      renderDateCalendar();
    });
  }

  if (dateClear) {
    dateClear.addEventListener("click", function () {
      activeFilters.dateStart = "";
      activeFilters.dateEnd = "";
      updateDatePieces();
      applyTourFilters();
    });
  }

  if (clearFilters) {
    clearFilters.addEventListener("click", function () {
      activeFilters.category = [];
      activeFilters.language = [];
      activeFilters.durationMin = null;
      activeFilters.durationMax = null;
      activeFilters.dateStart = "";
      activeFilters.dateEnd = "";
      filterGroups.forEach(function (filterGroup) {
        Array.prototype.forEach.call(
          filterGroup.querySelectorAll(".chip"),
          function (chip) {
            chip.classList.toggle(
              "on",
              chip.getAttribute("data-filter") === "all",
            );
          },
        );
      });
      if (durationMinFilter) {
        durationMinFilter.value = "";
      }
      if (durationMaxFilter) {
        durationMaxFilter.value = "";
      }
      updateDurationFilter();
      updateDatePieces();
      applyTourFilters();
    });
  }

  renderDateCalendar();
});
