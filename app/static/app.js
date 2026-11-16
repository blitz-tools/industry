// Page behaviors, each block self-guarded so any page can carry any subset.
// Assets-page blocks are wrapped in window.initAssetsPage() so they can be
// re-bound after an in-place content swap (see swapAssetsPage) — swapped
// markup carries no executing scripts of its own.

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

// --- Collapsible nav groups (Character, Corporation) ------------------------
(function () {
  document.querySelectorAll(".nav-group").forEach((group) => {
    const toggle = group.querySelector(".nav-group-toggle");
    const items = group.querySelector(".nav-group-items");
    if (!toggle || !items) return;

    // Storage key derives from the group id: #nav-corp-group keeps its
    // existing nav-corp-open key; #nav-character-group gets its own.
    const storageKey = `nav-${group.id.replace(/-group$/, "")}-open`;

    const setOpen = (open) => {
      items.hidden = !open;
      toggle.setAttribute("aria-expanded", String(open));
      try {
        localStorage.setItem(storageKey, String(open));
      } catch (error) {
        /* private browsing mode */
      }
    };

    toggle.addEventListener("click", () => setOpen(items.hidden));

    // The server already expanded the group when it holds the active
    // link; otherwise apply the remembered state.
    if (!items.querySelector("a.active")) {
      let saved = null;
      try {
        saved = localStorage.getItem(storageKey);
      } catch (error) {
        /* private browsing mode */
      }
      if (saved !== null) setOpen(saved === "true");
    }
  });
})();

// --- Assets page: in-place content swap ---------------------------------------
// Filter changes fetch the new page and swap <main>'s content instead of a
// full navigation — no white-flash redraw, and scroll position survives.
// The URL is kept current via pushState so refresh/back still work.
const swapAssetsPage = async (url, { push = true } = {}) => {
  try {
    const response = await fetch(url, { headers: { "X-Requested-With": "fetch" } });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const doc = new DOMParser().parseFromString(await response.text(), "text/html");
    const current = document.querySelector("main");
    const next = doc.querySelector("main");
    if (!current || !next) throw new Error("unexpected page shape");
    current.replaceChildren(...next.childNodes);
    if (push) history.pushState({}, "", url);
    // Swapped markup carries script tags that do not execute — re-bind
    // its behaviors by hand, synchronously, before the next paint.
    window.initCorpRows?.();
    window.initAssetsPage?.();
  } catch (error) {
    // Anything unexpected: fall back to a full navigation.
    window.location.assign(url);
  }
};

window.addEventListener("popstate", () => {
  if (document.querySelector("#asset-filter")) {
    swapAssetsPage(window.location.href, { push: false });
  }
});

// --- Filter forms that submit on change ---------------------------------------
// Simple dropdown filters (character picker on the data pages): changing
// the select navigates; <noscript> fallbacks carry an Apply button.
document.querySelectorAll("form[data-autosubmit]").forEach((form) => {
  form.addEventListener("change", () => form.submit());
});

// --- Assets page behaviors (re-bound after every swap) ------------------------
window.initAssetsPage = () => {
  // Asset structure panels. The fragment route is page-specific (character
  // vs corporation browser) and travels on the filter form.
  const structures = document.querySelectorAll("details.structure");
  if (structures.length) {
    const fragmentBase =
      document.querySelector("#asset-filter")?.dataset.fragmentBase ||
      "/assets/structure";
    const load = async (details, params) => {
      const body = details.querySelector(".structure-body");
      body.textContent = "Loading…";
      try {
        const response = await fetch(
          `${fragmentBase}/${details.dataset.locationId}?${params}`
        );
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        body.innerHTML = await response.text();
      } catch (error) {
        body.innerHTML = '<p class="warn">Failed to load — try again.</p>';
      }
    };

    // First expansion: page 1, carrying the page-level character and
    // category filters. The character selection may live only in the
    // session (bare /assets URL), so fall back to the picker's embedded
    // effective selection.
    const initialParams = () => {
      const params = new URLSearchParams();
      params.set("page", "1");
      const pageQuery = new URLSearchParams(window.location.search);
      let chars = pageQuery.get("chars");
      if (chars === null) {
        const picker = document.querySelector(".char-picker");
        chars = picker ? picker.dataset.chars || "" : "";
      }
      if (chars) params.set("chars", chars);
      const category = pageQuery.get("category");
      if (category) params.set("category", category);
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
      // Pagination and column-sort links inside the panel fetch and swap
      // in place; their hrefs already carry every param (page, chars,
      // category, sort, dir), so the link's own query is the fetch's
      // query.
      details.addEventListener("click", (event) => {
        const link = event.target.closest(".pagination a, thead a.sort-link");
        if (!link) return;
        event.preventDefault();
        load(details, new URLSearchParams(new URL(link.href).search));
      });
    });
  }

  // Assets filter form: submit on change via in-place swap. The form's
  // action is the page it belongs to (character or corporation browser);
  // the character selection only exists on the character page.
  const form = document.querySelector("#asset-filter");
  if (form) {
    const apply = () => {
      const params = new URLSearchParams();
      const boxes = [...form.querySelectorAll('input[name="chars"]')];
      if (boxes.length) {
        const checked = boxes.filter((box) => box.checked).map((box) => box.value);
        // Always carry the selection: "all" when every box is checked (so
        // the session remembers All, not a stale partial list), the joined
        // ids otherwise — empty for none.
        params.set(
          "chars",
          checked.length === boxes.length ? "all" : checked.join(",")
        );
      }
      for (const name of ["region", "category"]) {
        const value = form.querySelector(`select[name="${name}"]`).value;
        if (value) params.set(name, value);
      }
      const query = params.toString();
      const action = form.getAttribute("action") || "/assets";
      swapAssetsPage(action + (query ? `?${query}` : ""));
    };

    form.addEventListener("change", apply);

    // Select All / None and per-corporation toggles set checkbox state,
    // then apply like any other change.
    form.addEventListener("click", (event) => {
      const select = event.target.closest("[data-select]");
      if (select) {
        const check = select.dataset.select === "all";
        form.querySelectorAll('input[name="chars"]').forEach((box) => {
          box.checked = check;
        });
        apply();
        return;
      }
      const corp = event.target.closest(".corp-toggle");
      if (corp) {
        event.preventDefault(); // don't toggle the row's open/closed state
        const row = corp.closest(".corp-row");
        const boxes = [...row.querySelectorAll('input[name="chars"]')];
        const check = !boxes.every((box) => box.checked);
        boxes.forEach((box) => {
          box.checked = check;
        });
        apply();
      }
    });
  }

  // Sync button feedback.
  const syncForm = document.querySelector(".sync-form");
  if (syncForm) {
    syncForm.addEventListener("submit", () => {
      const button = syncForm.querySelector("button");
      if (button) {
        button.disabled = true;
        button.textContent = "Syncing…";
      }
    });
  }
};

window.initAssetsPage();
