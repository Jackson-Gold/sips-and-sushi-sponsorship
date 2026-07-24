/**
 * Web3Forms submit helpers for guest invite + sponsor partnership forms.
 */
(function () {
  function getConfig() {
    const cfg = window.SIPS_FORM_CONFIG || {};
    return {
      accessKey: cfg.accessKey || "",
    };
  }

  async function submitForm(form, feedback) {
    const cfg = getConfig();
    feedback.textContent = "";
    feedback.classList.remove("is-ok", "is-err");

    if (!cfg.accessKey || cfg.accessKey === "YOUR_WEB3FORMS_ACCESS_KEY") {
      feedback.textContent =
        "Form is not configured yet. Set WEB3FORMS_ACCESS_KEY on Vercel (or js/form-config.js locally).";
      feedback.classList.add("is-err");
      return;
    }

    // Honeypot (checkbox: only flag when checked; .value is always "on")
    const trap = form.querySelector('[name="botcheck"]');
    if (trap && (trap.type === "checkbox" ? trap.checked : Boolean(trap.value))) {
      return;
    }

    const data = new FormData(form);
    data.set("access_key", cfg.accessKey);

    const btn = form.querySelector('button[type="submit"]');
    if (btn) btn.disabled = true;
    feedback.textContent = "Sending…";

    try {
      const res = await fetch("https://api.web3forms.com/submit", {
        method: "POST",
        body: data,
      });
      const json = await res.json();
      if (json.success) {
        feedback.textContent = "Received — thank you. We’ll be in touch.";
        feedback.classList.add("is-ok");
        form.reset();
      } else {
        throw new Error(json.message || "Submit failed");
      }
    } catch (err) {
      feedback.textContent = "Something went wrong. Please try again in a moment.";
      feedback.classList.add("is-err");
    } finally {
      if (btn) btn.disabled = false;
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-sips-form]").forEach((form) => {
      const feedback =
        form.querySelector(".form-feedback") ||
        form.parentElement.querySelector(".form-feedback");
      form.addEventListener("submit", (e) => {
        e.preventDefault();
        if (feedback) submitForm(form, feedback);
      });
    });
  });
})();
