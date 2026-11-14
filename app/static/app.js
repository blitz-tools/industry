// Page behaviors, each block self-guarded so any page can carry any subset.

// --- Sidebar drawer (narrow screens) --------------------------------------
(function () {
  const toggle = document.querySelector(".menu-toggle");
  if (!toggle) return;

  const close = () => {
    document.body.classList.remove("nav-open");
    toggle.setAttribute("aria-expanded", "false");
  };

  toggle.addEventListener("click", () => {
    const open = document.body.classList.toggle("nav-open");
    toggle.setAttribute("aria-expanded", String(open));
  });

  document.querySelector(".backdrop").addEventListener("click", close);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") close();
  });
})();

// --- Corporation nav group --------------------------------------------------
(function () {
  const group = document.querySelector("#nav-corp-group");
  if (!group) return;
  const toggle = group.querySelector(".nav-group-toggle");
  const items = group.querySelector(".nav-group-items");
  if (!toggle || !items) return;

  const setOpen = (open) => {
    items.hidden = !open;
    toggle.setAttribute("aria-expanded", String(open));
    try {
      localStorage.setItem("nav-corp-open", String(open));
    } catch (error) {
      /* private browsing mode */
    }
  };

  toggle.addEventListener("click", () => setOpen(items.hidden));

  // The server already expanded the group on corporation pages; otherwise
  // apply the remembered state.
  if (!items.querySelector("a.active")) {
    let saved = null;
    try {
      saved = localStorage.getItem("nav-corp-open");
    } catch (error) {
      /* private browsing mode */
    }
    if (saved !== null) setOpen(saved === "true");
  }
})();

// --- Asset structure panels -------------------------------------------------
(function () {
  const structures = document.querySelectorAll("details.structure");
  if (!structures.length) return;

  const load = async (details, params) => {
    const body = details.querySelector(".structure-body");
    body.textContent = "Loading…";
    try {
      const response = await fetch(
        `/assets/structure/${details.dataset.locationId}?${params}`
      );
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      body.innerHTML = await response.text();
    } catch (error) {
      body.innerHTML = '<p class="warn">Failed to load — try again.</p>';
    }
  };

  // First expansion: page 1, carrying the page-level character and
  // category filters.
  const initialParams = () => {
    const params = new URLSearchParams();
    params.set("page", "1");
    const pageQuery = new URLSearchParams(window.location.search);
    for (const key of ["chars", "category"]) {
      const value = pageQuery.get(key);
      if (value) params.set(key, value);
    }
    return params;
  };

  structures.forEach((details) => {
    // First expansion fetches page 1; later expansions are instant.
    details.addEventListener("toggle", () => {
      if (details.open && !details.dataset.loaded) {
        details.dataset.loaded = "1";
        load(details, initialParams());
      }
    });
    // Pagination and column-sort links inside the panel fetch and swap in
    // place; their hrefs already carry every param (page, chars, category,
    // sort, dir), so the link's own query is the fetch's query.
    details.addEventListener("click", (event) => {
      const link = event.target.closest(".pagination a, thead a.sort-link");
      if (!link) return;
      event.preventDefault();
      load(details, new URLSearchParams(new URL(link.href).search));
    });
  });
})();

// --- Assets filter form: submit on change -----------------------------------
(function () {
  const form = document.querySelector("#asset-filter");
  if (!form) return;
  form.addEventListener("change", () => {
    const params = new URLSearchParams();
    const boxes = [...form.querySelectorAll('input[name="chars"]')];
    const checked = boxes.filter((box) => box.checked).map((box) => box.value);
    // All-checked (and none-checked) mean "every character": drop the param.
    if (checked.length && checked.length < boxes.length) {
      params.set("chars", checked.join(","));
    }
    for (const name of ["region", "category"]) {
      const value = form.querySelector(`select[name="${name}"]`).value;
      if (value) params.set(name, value);
    }
    const query = params.toString();
    window.location.assign("/assets" + (query ? `?${query}` : ""));
  });
})();

// --- Sync button feedback ----------------------------------------------------
(function () {
  const form = document.querySelector(".sync-form");
  if (!form) return;
  form.addEventListener("submit", () => {
    const button = form.querySelector("button");
    if (button) {
      button.disabled = true;
      button.textContent = "Syncing…";
    }
  });
})();
