"use strict";

document.addEventListener("DOMContentLoaded", function () {
  var editorRoot = document.querySelector(".tour-editor");

  if (!editorRoot) {
    return;
  }

  function languageOptions() {
    var options = editorRoot.getAttribute("data-language-options") || "";
    return options.split("|").filter(Boolean);
  }

  function makeSelect(name) {
    var select = document.createElement("select");
    select.name = name;
    select.required = true;
    languageOptions().forEach(function (language) {
      var option = document.createElement("option");
      option.value = language;
      option.textContent = language;
      select.appendChild(option);
    });
    return select;
  }

  function makeTimeRow(key, timeValue, languageValue) {
    var row = document.createElement("div");
    row.className = "time-slot-row";

    var input = document.createElement("input");
    input.type = "time";
    input.name = "time_" + key + "[]";
    input.value = timeValue || "";

    var select = makeSelect("language_" + key + "[]");
    if (languageValue) {
      select.value = languageValue;
    }

    var deleteTime = document.createElement("button");
    deleteTime.className = "time-delete";
    deleteTime.type = "button";
    deleteTime.setAttribute("data-delete-time", "");
    deleteTime.textContent = "Remove";

    row.appendChild(input);
    row.appendChild(select);
    row.appendChild(deleteTime);
    return row;
  }

  function dateKeyAfterWeeks(dateKey, weeks) {
    var date = new Date(dateKey + "T00:00:00");
    if (Number.isNaN(date.getTime())) {
      return "";
    }
    date.setDate(date.getDate() + weeks * 7);
    var month = String(date.getMonth() + 1).padStart(2, "0");
    var day = String(date.getDate()).padStart(2, "0");
    return date.getFullYear() + "-" + month + "-" + day;
  }

  function selectedSchedule() {
    var activePanel = editorRoot.querySelector("[data-calendar-panel].active");
    var sourceRow = activePanel
      ? activePanel.querySelector(".time-slot-row")
      : null;
    var sourceTime = sourceRow
      ? sourceRow.querySelector("input[type='time']")
      : null;
    var sourceLanguage = sourceRow ? sourceRow.querySelector("select") : null;

    if (
      !activePanel ||
      !sourceTime ||
      !sourceTime.value ||
      !sourceLanguage ||
      !sourceLanguage.value
    ) {
      return null;
    }

    return {
      panel: activePanel,
      dateKey: activePanel.getAttribute("data-calendar-panel"),
      dateLabel: activePanel.querySelector(".schedule-date")
        ? activePanel.querySelector(".schedule-date").textContent.trim()
        : activePanel.getAttribute("data-calendar-panel"),
      time: sourceTime.value,
      language: sourceLanguage.value,
    };
  }

  function setWeeklyFlash(message, isError) {
    var flash = editorRoot.querySelector("[data-repeat-weekly-flash]");
    if (!flash) {
      return;
    }
    flash.textContent = message || "";
    flash.hidden = !message;
    flash.classList.toggle("bad", Boolean(isError));
  }

  function setCalendarLocked(locked) {
    var shell = editorRoot.querySelector("[data-calendar-shell]");
    if (!shell) {
      return;
    }
    shell.toggleAttribute("data-calendar-locked", locked);
    shell.dispatchEvent(new CustomEvent("calendar-lock-change"));
  }

  function applyWeeklyRecurrence(schedule) {
    if (!schedule) {
      return;
    }
    for (var week = 1; week <= 4; week += 1) {
      var targetKey = dateKeyAfterWeeks(schedule.dateKey, week);
      var targetPanel = targetKey
        ? editorRoot.querySelector('[data-calendar-panel="' + targetKey + '"]')
        : null;
      var targetList = targetPanel
        ? targetPanel.querySelector("[data-time-slot-list]")
        : null;
      if (!targetList) {
        continue;
      }

      var targetRow = targetList.querySelector(".time-slot-row");
      if (!targetRow) {
        targetList.appendChild(
          makeTimeRow(targetKey, schedule.time, schedule.language),
        );
        continue;
      }

      var targetTime = targetRow.querySelector("input[type='time']");
      var targetLanguage = targetRow.querySelector("select");
      if (targetTime) {
        targetTime.value = schedule.time;
      }
      if (targetLanguage) {
        targetLanguage.value = schedule.language;
      }
    }
  }

  function refreshStopControls() {
    var stopList = editorRoot.querySelector("[data-stop-list]");
    var stops = stopList
      ? Array.prototype.slice.call(stopList.querySelectorAll(".editor-stop"))
      : [];
    stops.forEach(function (stop, index) {
      var badge = stop.querySelector(".stop-badge");
      var button = stop.querySelector("[data-delete-stop]");
      if (badge) {
        badge.textContent = index + 1 + " stop";
      }
      if (button) {
        button.disabled = stops.length <= 4;
      }
    });
  }

  // One delegated handler also covers rows added after the page loads.
  editorRoot.addEventListener("click", function (event) {
    var addTime = event.target.closest("[data-add-time]");
    if (addTime) {
      var panel = addTime.closest("[data-calendar-panel]");
      var list = panel ? panel.querySelector("[data-time-slot-list]") : null;
      if (panel && list) {
        // Each date currently supports one departure row, matching the server-side form parser.
        if (list.querySelector(".time-slot-row")) {
          return;
        }
        var key = panel.getAttribute("data-calendar-panel");
        list.appendChild(makeTimeRow(key));
      }
      return;
    }

    var deleteTime = event.target.closest("[data-delete-time]");
    if (deleteTime) {
      var timeRow = deleteTime.closest(".time-slot-row");
      if (timeRow) {
        timeRow.remove();
        var repeatSwitchAfterDelete = editorRoot.querySelector(
          "[data-repeat-weekly]",
        );
        if (
          repeatSwitchAfterDelete &&
          repeatSwitchAfterDelete.checked &&
          deleteTime.closest("[data-calendar-panel].active")
        ) {
          repeatSwitchAfterDelete.checked = false;
          setCalendarLocked(false);
          setWeeklyFlash(
            "Weekly repeat is off. Select a date and time to turn it on again.",
          );
        }
      }
      return;
    }

    var addGuide = event.target.closest("[data-add-guide]");
    if (addGuide) {
      var guideList = editorRoot.querySelector("[data-guide-list]");
      if (guideList) {
        var guideRow = document.createElement("div");
        guideRow.className = "guide-editor-row";

        var guideEmail = document.createElement("input");
        guideEmail.name = "guide_email[]";
        guideEmail.type = "email";
        guideEmail.placeholder = "Guide email";
        guideEmail.required = true;

        var guideStatus = document.createElement("input");
        guideStatus.type = "text";
        guideStatus.value = "Pending guide";
        guideStatus.readOnly = true;

        var deleteGuide = document.createElement("button");
        deleteGuide.className = "guide-delete";
        deleteGuide.type = "button";
        deleteGuide.setAttribute("data-delete-guide", "");
        deleteGuide.textContent = "Delete guide";

        guideRow.appendChild(guideEmail);
        guideRow.appendChild(guideStatus);
        guideRow.appendChild(deleteGuide);
        guideList.appendChild(guideRow);
      }
      return;
    }

    var deleteGuide = event.target.closest("[data-delete-guide]");
    if (deleteGuide) {
      var guideRowToDelete = deleteGuide.closest(".guide-editor-row");
      if (
        guideRowToDelete &&
        !guideRowToDelete.classList.contains("fixed-guide-row")
      ) {
        guideRowToDelete.remove();
      }
      return;
    }

    var addStop = event.target.closest("[data-add-stop]");
    if (addStop) {
      var stopList = editorRoot.querySelector("[data-stop-list]");
      if (stopList) {
        var stopNumber = stopList.querySelectorAll(".editor-stop").length + 1;
        var stop = document.createElement("article");
        stop.className = "timeline-stop editor-stop";
        stop.innerHTML = [
          '<div class="stop-node"></div>',
          '<div class="stop-copy">',
          '<span class="stop-badge">' + stopNumber + " stop</span>",
          '<div class="stop-card">',
          '<button class="stop-delete" type="button" data-delete-stop>Delete stop</button>',
          "<label>Stop name</label>",
          '<input name="stop_name[]" type="text" required>',
          "<label>Description</label>",
          '<textarea name="stop_description[]" required></textarea>',
          "</div>",
          "</div>",
          '<label class="stop-upload">',
          '<img src="/static/images/sultanahmet-3.svg" alt="">',
          "<span>Upload image</span>",
          '<input name="stop_image[]" type="file" accept="image/*">',
          "</label>",
        ].join("");
        stopList.appendChild(stop);
        refreshStopControls();
        if (window.fillIstanwalkTulips) {
          window.fillIstanwalkTulips();
        }
      }
      return;
    }

    var deleteStop = event.target.closest("[data-delete-stop]");
    if (deleteStop) {
      var currentStopList = editorRoot.querySelector("[data-stop-list]");
      var currentStops = currentStopList
        ? Array.prototype.slice.call(
            currentStopList.querySelectorAll(".editor-stop"),
          )
        : [];
      if (currentStops.length > 4) {
        deleteStop.closest(".editor-stop").remove();
        refreshStopControls();
        if (window.fillIstanwalkTulips) {
          window.fillIstanwalkTulips();
        }
      }
    }
  });

  // FileReader previews stay in the browser; the actual files are still
  // submitted normally with the form.
  editorRoot.addEventListener("change", function (event) {
    var repeatWeekly = event.target.closest("[data-repeat-weekly]");
    if (repeatWeekly) {
      if (!repeatWeekly.checked) {
        setCalendarLocked(false);
        setWeeklyFlash("Weekly repeat is off. You can choose dates normally.");
        return;
      }

      var schedule = selectedSchedule();
      if (!schedule) {
        repeatWeekly.checked = false;
        setCalendarLocked(false);
        setWeeklyFlash(
          "Select a date and time before turning on weekly repeat.",
          true,
        );
        return;
      }

      applyWeeklyRecurrence(schedule);
      setCalendarLocked(true);
      setWeeklyFlash(
        "You have selected " +
          schedule.dateLabel +
          " at " +
          schedule.time +
          " in " +
          schedule.language +
          ". It will repeat weekly for 1 month.",
      );
      return;
    }

    var scheduleField = event.target.closest(
      ".editor-time-panels input[type='time'], .editor-time-panels select",
    );
    var repeatSwitch = editorRoot.querySelector("[data-repeat-weekly]");
    if (scheduleField && repeatSwitch && repeatSwitch.checked) {
      var updatedSchedule = selectedSchedule();
      if (updatedSchedule) {
        applyWeeklyRecurrence(updatedSchedule);
        setWeeklyFlash(
          "You have selected " +
            updatedSchedule.dateLabel +
            " at " +
            updatedSchedule.time +
            " in " +
            updatedSchedule.language +
            ". It will repeat weekly for 1 month.",
        );
      }
    }

    var mainImageInput = event.target.closest("[data-main-image-input]");
    if (mainImageInput && mainImageInput.files && mainImageInput.files[0]) {
      var mainPreview = mainImageInput
        .closest(".main-image-upload")
        .querySelector("img");
      var mainFile = mainImageInput.files[0];
      if (
        mainPreview &&
        mainFile.type &&
        mainFile.type.indexOf("image/") === 0
      ) {
        var mainReader = new FileReader();
        mainReader.addEventListener("load", function () {
          mainPreview.src = mainReader.result;
        });
        mainReader.readAsDataURL(mainFile);
      }
      return;
    }

    var galleryInput = event.target.closest(
      ".gallery-upload input[type='file']",
    );
    if (galleryInput && galleryInput.files && galleryInput.files[0]) {
      var galleryPreview = galleryInput
        .closest(".gallery-upload")
        .querySelector("img");
      var galleryFile = galleryInput.files[0];
      if (
        galleryPreview &&
        galleryFile.type &&
        galleryFile.type.indexOf("image/") === 0
      ) {
        var galleryReader = new FileReader();
        galleryReader.addEventListener("load", function () {
          galleryPreview.src = galleryReader.result;
        });
        galleryReader.readAsDataURL(galleryFile);
      }
      return;
    }

    var fileInput = event.target.closest(".stop-upload input[type='file']");
    if (!fileInput || !fileInput.files || !fileInput.files[0]) {
      return;
    }

    var image = fileInput.closest(".stop-upload").querySelector("img");
    var file = fileInput.files[0];
    if (!image || !file.type || file.type.indexOf("image/") !== 0) {
      return;
    }

    var reader = new FileReader();
    reader.addEventListener("load", function () {
      image.src = reader.result;
    });
    reader.readAsDataURL(file);
  });

  refreshStopControls();
});
