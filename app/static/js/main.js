import spacetime from "https://cdn.jsdelivr.net/npm/spacetime/+esm";
import { ClearFlatpickr } from "/static/js/components/clear_flatpickr.js";
import { ModalFrame } from "/static/js/components/modal_frame.js";
import { registerControllers } from "/static/js/vendor/binder/binder.js";
import { DynamicFrame, DynamicFrameRouter } from "/static/js/vendor/binder/core/dynamic_frame.js";

window.initDatePicker = picker => {
    const tz = document.getElementById("timezone")?.innerText;
    if (!tz) {
        console.warning(`[initDatePicker] Attempted to initialise date picker without timezone`);
        return;
    }

    const today = spacetime.now(tz);
    let date = today.format("Y-m-d");
    let hour = today.hour();
    let mins = today.minute();
    mins = Math.floor(mins / 5) * 5; // Round minutes to nearest 5 mins

    const pickerType = picker.getAttribute("data-date-type");
    const dateFormat = picker.getAttribute("data-date-format");
    let value = picker.getAttribute("data-date-value");
    let setDefault = picker.hasAttribute("data-set-default");

    // If we have a number then it will be an epoch in seconds
    // Flatpickr expects an epoch to be in milliseconds
    if (value && !isNaN(value)) {
        value = Number(value) * 1000;
    }

    if (pickerType === "time") {
        let defaultValue = value;
        if (!value && setDefault) defaultValue = `${date} ${hour}:${mins}`;
        flatpickr(picker, {
            enableTime: true,
            noCalendar: true,
            altInput: true,
            altFormat: dateFormat || "H:i",
            dateFormat: "Y-m-d H:i",
            time_24hr: true,
            defaultDate: defaultValue,
        });
    } else if (pickerType === "date") {
        let defaultValue = value;
        if (!value && setDefault) defaultValue = date;
        flatpickr(picker, {
            altInput: true,
            altFormat: dateFormat || "F j, Y",
            dateFormat: "Y-m-d",
            defaultDate: defaultValue,
            locale: {
                firstDayOfWeek: 1,
            },
        });
    } else if (pickerType === "datetime") {
        let defaultValue = value;
        if (!value && setDefault) defaultValue = `${date} ${hour}:${mins}`;
        flatpickr(picker, {
            altInput: true,
            altFormat: dateFormat || "H:i o\\n F j, Y",
            enableTime: true,
            time_24hr: true,
            dateFormat: "Y-m-d H:i",
            defaultDate: defaultValue,
            locale: {
                firstDayOfWeek: 1,
            },
        });
    }
};

window.initTomSelect = select => {
    if (select.tomselect) return;

    // Element has been cached by the dynamic-frame-router
    // We need to do some extra work to re-initialise it
    if (select.classList.contains("tomselected")) {
        select.classList.remove("tomselected");
        select.classList.remove("ts-hidden");
        select.classList.remove("ts-hidden-accessible");

        if (select.nextElementSibling.classList.contains("ts-wrapper")) {
            select.nextElementSibling.remove();
        }
    }

    const options = {};
    new TomSelect(select, options);
};

window.addEventListener("DOMContentLoaded", () => {
    const pickers = document.querySelectorAll(".flatpickr");
    pickers.forEach(picker => window.initDatePicker(picker));

    const selects = document.querySelectorAll("select.tomselect");
    selects.forEach(select => window.initTomSelect(select));

    registerControllers(DynamicFrame, DynamicFrameRouter, ModalFrame, ClearFlatpickr);
});

// Whenever a dynamic-frame updates re-initialise the datepickers and lightboxes
window.addEventListener("dynamic-frame:updated", e => {
    const pickers = e.target.querySelectorAll(".flatpickr");
    pickers.forEach(picker => window.initDatePicker(picker));

    const selects = document.querySelectorAll("select.tomselect");
    selects.forEach(select => window.initTomSelect(select));
});

window.flash = (message, type = "info") => {
    const flashContainer = document.querySelector("#flash-messages");

    let newFlash = document.createElement("div");
    newFlash.innerHTML = `
        <div class="alert alert-${type}"
                role="alert"
                aria-live="assertive"
                aria-atomic="true"
                data-bs-autohide="true">
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button onclick="this.parentNode.parentNode.remove()"
                        type="button"
                        class="btn-close me-2 m-auto"
                        data-bs-dismiss="toast"
                        aria-label="Close">
                </button>
            </div>
        </div>`;

    flashContainer.insertBefore(newFlash, flashContainer.firstChild);
};
