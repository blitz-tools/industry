// Structures registry (M3): activity chips drive the structure-type
// list and rig visibility, the structure type gates the supercapital
// flag, and the solar-system field is a local type-ahead (systems the
// syncs have resolved). Page-scoped: base.html loads this only on
// /structures.
(() => {
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
  const activityLabels = JSON.parse(
    form.querySelector('[data-activity-labels]')?.dataset.activityLabels || "{}"
  );
  const securitySelect = form.querySelector("#security-select");

  const ecTypes = new Set(["raitaru", "azbel", "sotiyo"]);

  function selectedActivity() {
    return form.querySelector('input[name="activity"]:checked')?.value || "";
  }

  // Filter the structure-type list to what the activity hosts, keeping
  // the current selection when it is still valid.
  function refreshTypeOptions() {
    const activity = selectedActivity();
    const allowed = new Set(activityTypes[activity] || []);
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

  form.querySelectorAll('input[name="activity"]').forEach((radio) => {
    radio.addEventListener("change", () => {
      refreshTypeOptions();
      refreshRigFields();
    });
  });
  typeSelect.addEventListener("change", refreshTypeDerived);
  refreshTypeOptions();
  refreshRigFields();

  // --- System type-ahead (local: resolved systems) -------------------------
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

  function render(active = 0) {
    dropdown.replaceChildren();
    choices.forEach((system, index) => {
      const row = document.createElement("div");
      row.className = "autocomplete-row" + (index === active ? " active" : "");
      const name = document.createElement("div");
      const nameLine = document.createElement("div");
      nameLine.className = "ac-name";
      nameLine.textContent = system.name;
      const subLine = document.createElement("div");
      subLine.className = "ac-sub";
      subLine.textContent = "solar system · #" + system.system_id;
      name.append(nameLine, subLine);
      row.append(name);
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
    if (securitySelect) securitySelect.hidden = true;
    hideDropdown();
  }

  queryInput.addEventListener("input", () => {
    // Editing the text invalidates the picked id; the security class
    // hand-set control returns until a system is picked again.
    systemId.value = "";
    if (securitySelect) securitySelect.hidden = false;
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

  document.addEventListener("click", (event) => {
    if (!dropdown.hidden && !dropdown.contains(event.target) &&
        event.target !== queryInput) {
      hideDropdown();
    }
  });
})();
