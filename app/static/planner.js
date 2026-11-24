// Planner pages (M4): the commodity-first autocomplete, the target
// stepper, participant toggles, and facility selectors all rebuild the
// URL state and swap <main> in place (the structures-page pattern) —
// the server is authoritative for every recomputation. The planner and
// plan pages share this file; each init is a no-op when its elements
// are absent, and one swapMain re-binds whichever page arrived.
// Page-scoped: base.html loads this only on /planner and /planner/plan.

window.initPlannerPage = () => {
  const searchInput = document.getElementById("target-search");
  if (!searchInput) return;

  const params = () => new URLSearchParams(window.location.search);

  // --- Autocomplete (the planner's search) --------------------------------
  const dropdown = document.getElementById("target-autocomplete");
  let choices = [];
  let activeIndex = -1;
  let debounce = null;

  function hideDropdown() {
    dropdown.hidden = true;
    activeIndex = -1;
  }

  function ownedBadge(entry) {
    if (entry.owned_originals && entry.owned_copies) {
      return `<span class="badge owned">Blueprint owned · BPO + BPC ×${entry.owned_copies}</span>`;
    }
    if (entry.owned_originals) {
      return `<span class="badge owned">Blueprint owned · BPO${entry.owned_copies ? " + BPC" : ""}</span>`;
    }
    if (entry.owned_copies) {
      return `<span class="badge owned">Blueprint owned · BPC ×${entry.owned_copies}</span>`;
    }
    return `<span class="badge missing">Blueprint not owned</span>`;
  }

  function render(active = 0) {
    dropdown.replaceChildren();
    choices.forEach((entry, index) => {
      const row = document.createElement("button");
      row.type = "button";
      row.className = "autocomplete-row" + (index === active ? " active" : "");
      const icon = document.createElement("img");
      icon.src = `https://images.evetech.net/types/${entry.type_id}/icon?size=32`;
      icon.alt = entry.type_name;
      const text = document.createElement("div");
      const nameLine = document.createElement("div");
      nameLine.className = "ac-name";
      nameLine.textContent = entry.type_name;
      const subLine = document.createElement("div");
      subLine.className = "ac-sub";
      subLine.textContent =
        `${entry.group_name || "—"} · built from ${entry.blueprint_name}` +
        ` — ${entry.products_per_run}/run` +
        (entry.max_production_limit
          ? ` · max ${entry.max_production_limit} runs/job`
          : "");
      text.append(nameLine, subLine);
      const right = document.createElement("div");
      right.className = "ac-right";
      right.innerHTML = ownedBadge(entry);
      row.append(icon, text, right);
      row.addEventListener("mousedown", (event) => {
        event.preventDefault();
        pick(entry);
      });
      dropdown.append(row);
    });
    const footer = document.createElement("div");
    footer.className = "autocomplete-footer";
    footer.textContent =
      choices.length + " match" + (choices.length === 1 ? "" : "es") +
      " · icons from the SDE mirror; blueprint ownership from the live blueprints table";
    dropdown.append(footer);
    dropdown.hidden = choices.length === 0;
    activeIndex = active;
  }

  function pick(entry) {
    searchInput.value = entry.type_name;
    hideDropdown();
    const next = new URLSearchParams();
    next.set("target", String(entry.type_id));
    if (searchInput.dataset.owned) next.set("owned", "1");
    swapMain("/planner?" + next.toString());
  }

  searchInput.addEventListener("input", () => {
    clearTimeout(debounce);
    const query = searchInput.value.trim();
    if (query.length < 2) {
      hideDropdown();
      return;
    }
    debounce = setTimeout(async () => {
      try {
        const owned = searchInput.dataset.owned ? "&owned=1" : "";
        const response = await fetch(
          "/planner/search?q=" + encodeURIComponent(query) + owned,
          { headers: { "X-Requested-With": "fetch" } }
        );
        if (!response.ok) return;
        choices = (await response.json()).entries || [];
        render();
      } catch {
        // Network hiccup: keep the previous dropdown state.
      }
    }, 150);
  });

  searchInput.addEventListener("keydown", (event) => {
    if (dropdown.hidden) return;
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      const delta = event.key === "ArrowDown" ? 1 : -1;
      render((activeIndex + delta + choices.length) % choices.length);
    } else if (event.key === "Enter" && activeIndex >= 0) {
      event.preventDefault();
      pick(choices[activeIndex]);
    } else if (event.key === "Escape") {
      hideDropdown();
    }
  });

  // --- Match From Inventory -------------------------------------------------
  const ownedToggle = document.getElementById("owned-toggle");
  ownedToggle?.addEventListener("click", () => {
    const next = params();
    if (next.get("owned")) next.delete("owned");
    else next.set("owned", "1");
    const query = next.toString();
    swapMain("/planner" + (query ? "?" + query : ""));
  });

  // --- Target count stepper ---------------------------------------------------
  document.querySelectorAll("#qty-stepper button").forEach((button) => {
    button.addEventListener("click", () => {
      const current = Number(document.getElementById("qty-stepper").dataset.qty);
      const next_qty = Math.max(1, current + Number(button.dataset.delta));
      if (next_qty === current) return;
      const next = params();
      next.set("qty", String(next_qty));
      swapMain("/planner?" + next.toString());
    });
  });

  // --- Participant toggles ------------------------------------------------------
  // The effective pool: an explicit `p` list, or the main's corp members
  // (the default). Toggling always serializes the resulting explicit
  // list — the server stays authoritative over who the default is.
  const participantsTable = document.getElementById("participants-table");
  const corpMembers = (participantsTable?.dataset.corpMembers || "")
    .split(",")
    .filter(Boolean)
    .map(Number);
  document.querySelectorAll(".participant-toggle").forEach((button) => {
    button.addEventListener("click", () => {
      const characterId = Number(button.dataset.character);
      const current = params();
      let pool = current.has("p")
        ? current.getAll("p").map(Number)
        : corpMembers.slice();
      pool = pool.includes(characterId)
        ? pool.filter((id) => id !== characterId)
        : [...pool, characterId];
      const next = params();
      next.delete("p");
      pool.forEach((id) => next.append("p", String(id)));
      const query = next.toString();
      swapMain("/planner" + (query ? "?" + query : ""));
    });
  });

  // --- Facility selectors -----------------------------------------------------
  document.querySelectorAll(".facility-select").forEach((select) => {
    select.addEventListener("change", () => {
      const next = params();
      const activity = select.dataset.activity;
      if (select.value && select.value === select.dataset.defaultId) {
        next.delete(activity);  // picking the default keeps links honest
      } else {
        next.set(activity, select.value);
      }
      const query = next.toString();
      swapMain("/planner" + (query ? "?" + query : ""));
    });
  });
};

window.initPlanPage = () => {
  // The plan page is server-rendered state; its controls (the re-run
  // button, the back link) are plain links the shared swap handler
  // intercepts. Kept for symmetry so swapMain can re-bind blindly.
};

// --- In-place page swaps (no full refreshes) ----------------------------------

function swapMain(url, push = true, keepScroll = false) {
  const scrollY = window.scrollY;
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
      window.initPlannerPage();
      window.initPlanPage();
      // A swapped page should land in view (the mocked Calculate
      // navigation arrives at the top of a new page) — unless the link
      // asked to keep the viewport (a view toggle deep in the page:
      // flipping it must not bounce the reader back to the top).
      if (keepScroll) window.scrollTo({ top: scrollY });
      else window.scrollTo({ top: 0 });
    })
    .catch(() => {
      window.location.assign(url);
    });
}

if (!window.initPlannerPageWired) {
  window.initPlannerPageWired = true;

  // Close the autocomplete on outside clicks. Re-queried at event time
  // so it survives main swaps.
  document.addEventListener("click", (event) => {
    const dropdown = document.getElementById("target-autocomplete");
    const searchInput = document.getElementById("target-search");
    if (dropdown && !dropdown.hidden && !dropdown.contains(event.target) &&
        event.target !== searchInput) {
      dropdown.hidden = true;
    }
  });

  // In-main planner links (Calculate, back to planner) swap in place;
  // modified clicks keep their native behavior. A link carrying
  // data-keep-scroll (the acquisition table's view toggle) keeps the
  // viewport where it was.
  document.addEventListener("click", (event) => {
    const link = event.target.closest("main a[href^='/planner']");
    if (!link) return;
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    swapMain(link.href, true, link.hasAttribute("data-keep-scroll"));
  });

  window.addEventListener("popstate", () => {
    if (document.getElementById("target-search") ||
        document.querySelector("main a[href^='/planner']")) {
      swapMain(window.location.href, false);
    }
  });
}

window.initPlannerPage();
window.initPlanPage();
