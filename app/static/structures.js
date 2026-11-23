// Structures registry (M3): activity chips drive the structure-type
// list and rig visibility, the structure type gates the supercapital
// flag, and the solar-system field is a local type-ahead (systems the
// syncs have resolved) that selects the matching security chip on
// pick. Navigation and saves swap <main> in place (the assets-page
// pattern) instead of full page loads; swapped markup carries no
// executable scripts, so initStructuresPage re-binds after every swap.
// Page-scoped: base.html loads this only on /structures.

window.initStructuresPage = () => {
  const form = document.querySelector(".structure-form");
  if (!form) return;

  const typeSelect = form.querySelector("#struct-type");
  const activityTypes = JSON.parse(typeSelect.dataset.activityTypes || "{}");
  const rigFields = {
    me: form.querySelector(".field-me-rig"),
    te: form.querySelector(".field-te-rig"),
  };
  const supercapField = form.querySelector("#scap-field");
  const defaultLabel = form.querySelector("#default-label");
  const activityLabels = JSON.parse(form.dataset.activityLabels || "{}");

  const ecTypes = new Set(["raitaru", "azbel", "sotiyo"]);

  // --- Toggleable chip groups -----------------------------------------------
  // Chips are radios labeled as pills: keyboard-navigable, and a
  // selected chip unselects on a second click (radios can't do that
  // natively — remember the checked state and clear it).
  function makeToggleable(name) {
    const radios = form.querySelectorAll(`input[name="${name}"]`);
    radios.forEach((radio) => {
      radio.addEventListener("change", syncChipStyles);
      radio.addEventListener("click", () => {
        if (radio.checked && radio.dataset.wasChecked === "1") {
          radio.checked = false;
          radio.dataset.wasChecked = "";
          syncChipStyles();
          form.dispatchEvent(new Event("chips:" + name));
        } else if (radio.checked) {
          radios.forEach((other) => {
            other.dataset.wasChecked = other === radio ? "1" : "";
          });
          syncChipStyles();
        }
      });
    });
    form.querySelector(`input[name="${name}"]:checked`)?.setAttribute(
      "data-was-checked", "1");
    return radios;
  }

  // The server renders the initial `selected` classes; the JS owns
  // them from the first interaction on, so they move (or clear) with
  // the checked radio.
  function syncChipStyles() {
    form.querySelectorAll(".chip-row input[type=radio]").forEach((radio) => {
      radio.closest(".chip-button")?.classList.toggle("selected", radio.checked);
    });
  }

  function selectSecurityChip(securityClass) {
    form.querySelectorAll('input[name="security_class"]').forEach((radio) => {
      radio.checked = radio.value === securityClass;
      radio.dataset.wasChecked = radio.checked ? "1" : "";
    });
    syncChipStyles();
  }

  // With a solar system selected, the security class is the system's —
  // the chips lock to it (the server resolves security from the system
  // at save regardless, so the lock is honest UI, not the enforcement).
  function setSecurityLocked(locked) {
    const row = form.querySelector("#security-chips");
    if (!row) return;
    row.classList.toggle("locked", locked);
    row.querySelectorAll('input[name="security_class"]').forEach((radio) => {
      radio.disabled = locked;
    });
  }

  // --- Activity-driven form state --------------------------------------------

  function selectedActivity() {
    return form.querySelector('input[name="activity"]:checked')?.value || "";
  }

  // Filter the structure-type list to what the activity hosts, keeping
  // the current selection when it is still valid.
  function refreshTypeOptions() {
    const allowed = new Set(activityTypes[selectedActivity()] || []);
    const current = typeSelect.value;
    let firstVisible = null;
    for (const option of typeSelect.options) {
      const visible = allowed.has(option.value);
      option.hidden = !visible;
      option.disabled = !visible;
      if (visible && firstVisible === null) firstVisible = option;
    }
    if (!allowed.has(current) && firstVisible) {
      typeSelect.value = firstVisible.value;
    }
    refreshTypeDerived();
  }

  // The supercapital flag exists only on engineering complexes.
  function refreshTypeDerived() {
    if (supercapField) {
      supercapField.hidden = !ecTypes.has(typeSelect.value);
    }
  }

  function refreshRigFields() {
    const activity = selectedActivity();
    // Mirrors app.facilities.ACTIVITY_RIG_FIELDS: manufacturing and
    // reactions use both rigs, invention only time, copying none.
    const uses = {
      manufacturing: ["me", "te"],
      reactions: ["me", "te"],
      invention: ["te"],
      copying: [],
    }[activity] || ["me", "te"];
    for (const [field, element] of Object.entries(rigFields)) {
      if (element) element.hidden = !uses.includes(field);
    }
    if (defaultLabel) {
      defaultLabel.textContent =
        "Default for " + (activityLabels[activity] || "this activity");
    }
  }

  makeToggleable("activity").forEach((radio) => {
    radio.addEventListener("change", () => {
      refreshTypeOptions();
      refreshRigFields();
    });
    radio.addEventListener("click", () => {
      refreshTypeOptions();
      refreshRigFields();
    });
  });
  makeToggleable("security_class");
  typeSelect.addEventListener("change", refreshTypeDerived);
  refreshTypeOptions();
  refreshRigFields();
  syncChipStyles();

  // --- System type-ahead (local: resolved systems) ---------------------------
  const queryInput = form.querySelector("#system-query");
  const systemId = form.querySelector("#system-id");
  const dropdown = form.querySelector("#system-autocomplete");
  if (!queryInput || !systemId || !dropdown) return;

  let choices = [];
  let activeIndex = -1;
  let debounce = null;

  function hideDropdown() {
    dropdown.hidden = true;
    activeIndex = -1;
  }

  function securityBadge(system) {
    if (!system.security_class) return "";
    const classes = {
      high: "hisec", low: "lowsec", null: "nullsec",
    };
    const label = {
      high: "high", low: "low", null: "null",
    }[system.security_class];
    return `<span class="badge ${classes[system.security_class]}">` +
      `${label} ${Number(system.security_status).toFixed(1)}</span>`;
  }

  function render(active = 0) {
    dropdown.replaceChildren();
    choices.forEach((system, index) => {
      const row = document.createElement("div");
      row.className = "autocomplete-row" + (index === active ? " active" : "");
      const text = document.createElement("div");
      const nameLine = document.createElement("div");
      nameLine.className = "ac-name";
      nameLine.textContent = system.name;
      const subLine = document.createElement("div");
      subLine.className = "ac-sub";
      subLine.textContent = system.security_class
        ? `security ${Number(system.security_status).toFixed(1)} · ` +
          `${{ high: "highsec", low: "lowsec", null: "nullsec" }[system.security_class]}`
        : "solar system · security unknown";
      text.append(nameLine, subLine);
      const right = document.createElement("div");
      right.className = "ac-right";
      right.innerHTML = securityBadge(system);
      row.append(text, right);
      row.addEventListener("mousedown", (event) => {
        event.preventDefault();
        pick(system);
      });
      dropdown.append(row);
    });
    const footer = document.createElement("div");
    footer.className = "autocomplete-footer";
    footer.textContent =
      choices.length + " match" + (choices.length === 1 ? "" : "es") +
      " · resolved systems only (ESI search is gone); others land when a sync sees them";
    dropdown.append(footer);
    dropdown.hidden = choices.length === 0;
    activeIndex = active;
  }

  function pick(system) {
    queryInput.value = system.name;
    systemId.value = system.system_id;
    // A picked system selects its security chip and locks the group —
    // the class derives from the system (unknown security keeps the
    // chips unselected but still locked; the save resolves it).
    selectSecurityChip(system.security_class || null);
    setSecurityLocked(true);
    hideDropdown();
  }

  queryInput.addEventListener("input", () => {
    // Editing the text invalidates the picked id and the derived
    // security; the chips unlock and return to the user's hand until a
    // system is picked again.
    systemId.value = "";
    selectSecurityChip(null);
    setSecurityLocked(false);
    clearTimeout(debounce);
    const query = queryInput.value.trim();
    if (query.length < 2) {
      hideDropdown();
      return;
    }
    debounce = setTimeout(async () => {
      try {
        const response = await fetch(
          "/structures/systems/search?q=" + encodeURIComponent(query),
          { headers: { "X-Requested-With": "fetch" } }
        );
        if (!response.ok) return;
        choices = (await response.json()).systems || [];
        render();
      } catch {
        // Network hiccup: keep the previous dropdown state.
      }
    }, 150);
  });

  queryInput.addEventListener("keydown", (event) => {
    if (dropdown.hidden) return;
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      const delta = event.key === "ArrowDown" ? 1 : -1;
      const next = (activeIndex + delta + choices.length) % choices.length;
      render(next);
    } else if (event.key === "Enter" && activeIndex >= 0) {
      event.preventDefault();
      pick(choices[activeIndex]);
    } else if (event.key === "Escape") {
      hideDropdown();
    }
  });

  // Edit state with a stored system starts locked (the import prefill
  // and a saved structure both carry one).
  setSecurityLocked(Boolean(systemId.value));
};

// --- In-place page swaps (no full refresh) -----------------------------------
// Registered once: swaps <main> from a fetched page and re-binds the
// page's behaviors. Falls back to a full navigation on any surprise.

function swapMain(url, push = true) {
  fetch(url, { headers: { "X-Requested-With": "fetch" } })
    .then((response) => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.text();
    })
    .then((html) => {
      const doc = new DOMParser().parseFromString(html, "text/html");
      const current = document.querySelector("main");
      const next = doc.querySelector("main");
      if (!current || !next) throw new Error("unexpected page shape");
      current.replaceChildren(...next.childNodes);
      if (push) history.pushState({}, "", url);
      window.initStructuresPage();
      // An opened panel (add/edit/import) should land in view, like
      // the old fragment navigation did.
      const panel = document.getElementById("structure-form");
      if (panel && !panel.hidden) panel.scrollIntoView({ behavior: "smooth" });
    })
    .catch(() => {
      window.location.assign(url);
    });
}

if (!window.initStructuresPageWired) {
  window.initStructuresPageWired = true;

  // Submit a form through the in-place swap machinery.
  function submitViaFetch(form) {
    fetch(form.action, {
      method: "POST",
      body: new FormData(form),
      headers: { "X-Requested-With": "fetch" },
    })
      .then((response) => response.text())
      .then((html) => {
        const doc = new DOMParser().parseFromString(html, "text/html");
        document.querySelector("main").replaceChildren(
          ...doc.querySelector("main").childNodes);
        // Both the success redirect and a 422 error re-render land on
        // /structures.
        history.pushState({}, "", "/structures");
        window.initStructuresPage();
      })
      .catch(() => form.submit());
  }

  // Delete confirmations: the in-app dialog, not the browser popup.
  // The pending form is remembered; Confirm submits it through the
  // swap path, Cancel/Escape/backdrop just close.
  let pendingDelete = null;

  function openDeleteDialog(form) {
    const dialog = document.getElementById("delete-dialog");
    if (!dialog) {
      submitViaFetch(form);  // no dialog in the markup: proceed
      return;
    }
    pendingDelete = form;
    dialog.querySelector('[data-role="activity"]').textContent =
      form.dataset.activity || "";
    dialog.querySelector('[data-role="structure"]').textContent =
      form.dataset.structureName || "";
    dialog.onclose = () => { pendingDelete = null; };  // Escape/backdrop
    dialog.showModal();
  }

  document.addEventListener("click", (event) => {
    const dialog = document.getElementById("delete-dialog");
    if (!dialog || !dialog.open) return;
    if (event.target.id === "delete-confirm") {
      dialog.close();
      if (pendingDelete) submitViaFetch(pendingDelete);
      pendingDelete = null;
    } else if (event.target.id === "delete-cancel" ||
               event.target === dialog) {  // backdrop click
      dialog.close();
      pendingDelete = null;
    }
  });

  // Close the type-ahead dropdown on outside clicks. Re-queried at
  // event time so it survives main swaps (a per-init listener would
  // pile up on every swap).
  document.addEventListener("click", (event) => {
    const dropdown = document.getElementById("system-autocomplete");
    const queryInput = document.getElementById("system-query");
    if (dropdown && !dropdown.hidden && !dropdown.contains(event.target) &&
        event.target !== queryInput) {
      dropdown.hidden = true;
    }
  });

  // In-main links (Add structure, row Edit, Import, Cancel) swap in
  // place; modified clicks keep their native behavior.
  document.addEventListener("click", (event) => {
    const link = event.target.closest("main a[href^='/structures']");
    if (!link) return;
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    swapMain(link.href);
  });

  // Form posts (save structure, deletes) swap in place. Deletes route
  // through the confirmation dialog first.
  document.addEventListener("submit", (event) => {
    const form = event.target;
    if (!form.closest("main") || form.method.toLowerCase() !== "post") return;
    if (event.defaultPrevented) return;
    event.preventDefault();
    if (form.classList.contains("delete-form")) {
      openDeleteDialog(form);
      return;
    }
    submitViaFetch(form);
  });

  window.addEventListener("popstate", () => {
    if (document.getElementById("structure-form")) {
      swapMain(window.location.href, false);
    }
  });
}

window.initStructuresPage();
