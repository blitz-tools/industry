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
    // A Re-run visit keeps its fork context across a target change —
    // the re-plan is still the re-plan (the old plan is superseded on
    // save). Everything else resets: a new target is a new plan shape.
    const fork = params().get("from_plan");
    if (fork) next.set("from_plan", fork);
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

  // Direct count entry: type a number into the stepper value and press
  // Enter (or leave the field). Anything that isn't a number resets to
  // the current count — the server stays authoritative and clamps to ≥1.
  // A typed count commits QUIETLY — the URL and the Calculate link pick
  // it up without a re-resolve — because navigating on blur races a
  // Calculate click fired on the same blur (two swaps, and the stale
  // Calculate href could win, silently dropping the typed count). The
  // +/− buttons keep their live re-resolve.
  const qtyInput = document.querySelector("#qty-stepper .stepper-value");
  const resetQtyInput = () => {
    qtyInput.value = Number(
      document.getElementById("qty-stepper").dataset.qty
    ).toLocaleString("en-US");
  };
  qtyInput?.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      qtyInput.blur();
    }
  });
  qtyInput?.addEventListener("change", () => {
    const raw = qtyInput.value.replace(/,/g, "").trim();
    if (!/^\d+$/.test(raw)) {
      resetQtyInput();
      return;
    }
    const next_qty = Math.max(1, parseInt(raw, 10));
    const stepper = document.getElementById("qty-stepper");
    if (next_qty === Number(stepper.dataset.qty)) {
      resetQtyInput();
      return;
    }
    stepper.dataset.qty = String(next_qty);
    const next = params();
    next.set("qty", String(next_qty));
    const query = next.toString();
    history.replaceState(
      {}, "", "/planner" + (query ? "?" + query : "")
    );
    const calculate = document.getElementById("calculate-link");
    if (calculate) {
      const url = new URL(calculate.href);
      url.searchParams.set("qty", String(next_qty));
      calculate.href = url.toString();
    }
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

  // --- Facility selectors (chip-model dropdowns) -------------------------------
  // Same semantics as the selects they replaced: picking the registry
  // default drops the URL param (absence-means-default keeps links
  // honest); anything else serializes the override. Selection applies
  // immediately — one option per activity, no multi-step to batch.
  document.querySelectorAll(".facility-drop").forEach((drop) => {
    const trigger = drop.querySelector(".drop-chip");
    const panel = drop.querySelector(".drop-panel");
    trigger.addEventListener("click", () => {
      panel.hidden = !panel.hidden;
    });
    drop.querySelectorAll(".drop-option").forEach((option) => {
      option.addEventListener("click", () => {
        const next = params();
        const activity = drop.dataset.activity;
        if (option.dataset.id === drop.dataset.defaultId) {
          next.delete(activity);
        } else {
          next.set(activity, option.dataset.id);
        }
        const query = next.toString();
        swapMain("/planner" + (query ? "?" + query : ""), true, true);
      });
    });
  });
};

window.initPlanPage = () => {
  // The plan page's remaining controls are plain links the shared swap
  // handler intercepts, except the Material sources multi-select — the
  // one control both pages carry, so it binds here (initPlanPage runs
  // on both; initPlannerPage early-returns wherever the search box is
  // absent). Checkbox state is local until Apply constructs the next
  // URL; the swap keeps the viewport.
  // Saving is an intentional departure: clear the unsaved-plan flag on
  // submit so the export POST navigates without the guard.
  document.querySelector("main .export-form")?.addEventListener(
    "submit", () => { unsavedPlanUrl = null; }
  );

  // Abandon confirmation (the structures delete-dialog pattern): the
  // Abandon button opens the on-page dialog; Confirm submits the form
  // through its form= attribute — a native POST navigation, per the
  // /plans/{id}/{action} pin (action POSTs never swap in place).
  // Cancel/Escape/backdrop just close.
  const abandonOpen = document.getElementById("abandon-open");
  const abandonDialog = document.getElementById("abandon-dialog");
  if (abandonOpen && abandonDialog) {
    abandonOpen.addEventListener("click", () => abandonDialog.showModal());
    abandonDialog.addEventListener("click", (event) => {
      if (event.target.id === "abandon-cancel" || event.target === abandonDialog) {
        abandonDialog.close();
      }
    });
  }

  // Export plan (↗): the multibuy shopping list in an on-page dialog —
  // a large fixed-width text box to copy from, not a file download
  // (the link stays the no-script fallback and downloads the .txt).
  // The list rides the page render (the same materialized acquisition
  // rows the table shows), so the dialog opens instantly and never
  // disagrees with the table.
  const exportLink = document.getElementById("export-plan");
  const exportDialog = document.getElementById("multibuy-dialog");
  if (exportLink && exportDialog) {
    const textBox = document.getElementById("multibuy-text");
    const copyButton = document.getElementById("multibuy-copy");
    exportLink.addEventListener("click", (event) => {
      event.preventDefault();
      exportDialog.showModal();
    });
    copyButton.addEventListener("click", () => {
      textBox.select();
      const done = () => {
        copyButton.textContent = "Copied";
        setTimeout(() => { copyButton.textContent = "Copy"; }, 1500);
      };
      if (navigator.clipboard?.writeText) {
        navigator.clipboard.writeText(textBox.value).then(done, () => {
          document.execCommand("copy");  // selection fallback
          done();
        });
      } else {
        document.execCommand("copy");  // selection fallback
        done();
      }
    });
    exportDialog.addEventListener("click", (event) => {
      if (event.target.id === "multibuy-close" || event.target === exportDialog) {
        exportDialog.close();
      }
    });
  }
  const select = document.getElementById("material-source-select");
  if (select) {
    const button = select.querySelector(".drop-chip");
    const panel = select.querySelector(".drop-panel");
    const allBox = select.querySelector("#src-all-box");
    const corpBoxes = () =>
      [...select.querySelectorAll(".src-option")].filter(
        (box) => !box.value.startsWith("hangar:")
      );

    // "All offices" is checked exactly when the selection IS the
    // default set: every corp-side source on, no personal hangar —
    // re-synced after every change, so manual and default paths land
    // on the same state (and Apply's drop-to-default is never wrong).
    const syncAllBox = () => {
      const corp = corpBoxes();
      const personal = [...select.querySelectorAll(".src-option")].filter(
        (box) => box.value.startsWith("hangar:")
      );
      allBox.checked =
        corp.length > 0 &&
        corp.every((box) => box.checked) &&
        !personal.some((box) => box.checked);
    };

    button.addEventListener("click", () => {
      panel.hidden = !panel.hidden;
    });
    // "All offices" is a select-all over the corp-side sources: on
    // checks every office/container option (personal stays off), off
    // clears them. syncAllBox keeps the box in step with manual
    // changes, so both paths land on the same state.
    allBox?.addEventListener("change", () => {
      const corpOn = allBox.checked;
      select.querySelectorAll(".src-option").forEach((box) => {
        box.checked = corpOn && !box.value.startsWith("hangar:");
      });
    });
    select.querySelectorAll(".src-option").forEach((box) => {
      box.addEventListener("change", syncAllBox);
    });
    select.querySelector("#src-apply")?.addEventListener("click", () => {
      const next = new URLSearchParams(window.location.search);
      next.delete("src");
      if (!(allBox && allBox.checked)) {
        const refs = [...select.querySelectorAll(".src-option")]
          .filter((box) => box.checked)
          .map((box) => box.value);
        if (refs.length) refs.forEach((ref) => next.append("src", ref));
        else next.append("src", "");  // explicit-empty sentinel
      }
      const query = next.toString();
      const base = window.location.pathname;
      swapMain(base + (query ? "?" + query : ""), true, true);
    });
  }
};

// --- Unsaved-plan guard (M6) ---------------------------------------------------
// The calculated chain is URL state until Render plan snapshots it, so
// leaving /planner/plan without saving loses the work-in-progress.
// Departures covered: in-main link swaps (back to planner), back/forward,
// and sidebar navigation — all through the on-page dialog (the
// structures delete-dialog pattern; no browser popups). Tab close,
// refresh, and the address bar stay ungoverned: the calculation is URL
// state, so history or reopen-tab restores it. Same-page control
// rebuilds (the source selector, the acquisition toggle) never prompt,
// and the save form clears the flag on submit so the export POST
// navigates freely.

let unsavedPlanUrl = null;
let pendingLeave = null;
let pendingStay = null;

function refreshUnsavedPlan() {
  unsavedPlanUrl = document.querySelector("main .export-form")
    ? window.location.href
    : null;
}

function guardUnsavedPlanLeave(destination, onLeave, onStay) {
  if (unsavedPlanUrl === null) {
    onLeave();
    return;
  }
  const target = new URL(destination, window.location.origin);
  if (target.pathname === new URL(unsavedPlanUrl).pathname) {
    onLeave();
    return;
  }
  const dialog = document.getElementById("unsaved-plan-dialog");
  if (!dialog) {
    onLeave();  // no dialog in the markup: proceed
    return;
  }
  pendingLeave = onLeave;
  pendingStay = onStay;
  dialog.onclose = () => {  // any close without Leave = stay
    if (pendingStay) pendingStay();
    pendingLeave = pendingStay = null;
  };
  dialog.showModal();
}

window.initPlansPage = () => {
  // Plans list: bulk management (Activate / Abandon / Delete over the
  // checkbox selection). Abandon and Delete confirm through on-page
  // dialogs (the structures pattern); their bar buttons are real
  // submits carrying data-confirm, so the no-script path still works —
  // and the dialog confirms submit the same form WITHOUT data-confirm,
  // which is how the interception lets them through (no loop).
  const form = document.getElementById("plans-bulk-form");
  if (!form) return;
  const dialogs = {
    abandon: document.getElementById("bulk-abandon-dialog"),
    delete: document.getElementById("bulk-delete-dialog"),
  };

  // Header checkbox: selects/deselects every row, and reflects the
  // rows back (checked when all are, indeterminate on a partial
  // selection).
  const selectAll = document.getElementById("bulk-select-all");
  if (selectAll) {
    const rowBoxes = () => form.querySelectorAll('input[name="plan_id"]');
    const syncSelectAll = () => {
      const boxes = Array.from(rowBoxes());
      selectAll.checked = boxes.length > 0 && boxes.every((box) => box.checked);
      selectAll.indeterminate =
        boxes.some((box) => box.checked) && !selectAll.checked;
    };
    selectAll.addEventListener("change", () => {
      rowBoxes().forEach((box) => { box.checked = selectAll.checked; });
      syncSelectAll();
    });
    form.addEventListener("change", (event) => {
      if (event.target.name === "plan_id") syncSelectAll();
    });
    syncSelectAll();
  }
  form.addEventListener("submit", (event) => {
    const kind = event.submitter?.dataset?.confirm;
    if (!kind || !dialogs[kind]) return;
    event.preventDefault();
    dialogs[kind].showModal();
  });
  Object.values(dialogs).forEach((dialog) => {
    if (!dialog) return;
    dialog.addEventListener("click", (event) => {
      if (event.target.closest("[data-cancel]") || event.target === dialog) {
        dialog.close();
      }
    });
  });
};

// --- In-place page swaps (no full refreshes) ----------------------------------

function swapMain(url, push = true, keepScroll = true) {
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
      refreshUnsavedPlan();
      window.initPlannerPage();
      window.initPlanPage();
      window.initPlansPage();
      // Interactions keep the viewport where it was (the owner's
      // standing call: a control deep in the page must never bounce the
      // reader to the top); only cross-page navigations (Calculate,
      // back to planner) land at the top of the arriving page.
      if (keepScroll) window.scrollTo({ top: scrollY });
      else window.scrollTo({ top: 0 });
    })
    .catch(() => {
      window.location.assign(url);
    });
}

if (!window.initPlannerPageWired) {
  window.initPlannerPageWired = true;

  // Close the autocomplete and any open dropdown panel on outside
  // clicks. Re-queried at event time so it survives main swaps.
  document.addEventListener("click", (event) => {
    const dropdown = document.getElementById("target-autocomplete");
    const searchInput = document.getElementById("target-search");
    if (dropdown && !dropdown.hidden && !dropdown.contains(event.target) &&
        event.target !== searchInput) {
      dropdown.hidden = true;
    }
    document.querySelectorAll(".drop-panel").forEach((panel) => {
      if (!panel.hidden && !panel.parentElement.contains(event.target)) {
        panel.hidden = true;
      }
    });
  });

  // In-main planner and plans links (Calculate, back to planner, plan
  // detail, list) swap in place; modified clicks keep their native
  // behavior. Cross-page links land at the top of the arriving page;
  // same-page links (the acquisition table's view toggle) and anything
  // carrying data-keep-scroll keep the viewport where it was.
  document.addEventListener("click", (event) => {
    const link = event.target.closest(
      "main a[href^='/planner'], main a[href^='/plans']"
    );
    if (!link) return;
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    // Plan action links (/plans/{id}/copy, /rerun — later /multibuy)
    // are one-shot redirects and must NOT swap in place: the swap
    // pushStates the action URL, whose empty query strip wipes the
    // planner state on the next control click (the target stepper
    // rebuilt /planner?qty=11 with no target — the whole selection
    // cleared). Let the browser follow the redirect natively so the
    // address bar lands on the real URL.
    const path = new URL(link.href).pathname;
    if (/^\/plans\/\d+\/[a-z]+$/.test(path)) return;
    event.preventDefault();
    // Leaving an unsaved calculation prompts first (Stay keeps this
    // page — the default was already prevented).
    guardUnsavedPlanLeave(link.href, () => {
      const samePage =
        new URL(link.href).pathname === window.location.pathname;
      swapMain(
        link.href, true,
        link.hasAttribute("data-keep-scroll") || samePage
      );
    }, null);
  });

  // Purchase⇄Build markings (chips and phase-bulk) POST to
  // /plans/{id}/sourcing. Scripting off: the native POST 303s back to
  // the detail (landing at ?open={phase}#phase-row-{phase}). Scripting
  // on: the POST swaps the page in place instead — the viewport never
  // moves (the no-JS anchor would snap it), and the phase tree's
  // expanded/collapsed rows are restored over the fresh markup so
  // flipping a chip deep in the tree doesn't collapse context. The
  // history entry is the FINAL detail URL from the redirect, never the
  // action URL (the /plans/{id}/{action} pin), with the no-JS landing
  // params stripped — scripting already restored the state they carry.
  document.addEventListener("submit", (event) => {
    const form = event.target.closest("form[action$='/sourcing']");
    if (!form) return;
    event.preventDefault();
    const scrollY = window.scrollY;
    const openRows = Array.from(
      document.querySelectorAll("details.phase-row")
    ).filter((row) => row.open).map((row) => row.id);
    fetch(form.action, {
      method: "POST",
      body: new FormData(form),
      headers: { "X-Requested-With": "fetch" },
    })
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.text().then(
          (html) => ({ url: response.url, html })
        );
      })
      .then(({ url, html }) => {
        const doc = new DOMParser().parseFromString(html, "text/html");
        const current = document.querySelector("main");
        const next = doc.querySelector("main");
        if (!current || !next) throw new Error("unexpected page shape");
        current.replaceChildren(...next.childNodes);
        const clean = new URL(url, window.location.origin);
        clean.search = "";
        clean.hash = "";
        history.pushState({}, "", clean.pathname);
        refreshUnsavedPlan();
        window.initPlannerPage();
        window.initPlanPage();
        window.initPlansPage();
        document.querySelectorAll("details.phase-row").forEach((row) => {
          row.open = openRows.includes(row.id);
        });
        window.scrollTo({ top: scrollY });
      })
      .catch(() => {
        form.submit();  // native fallback: the full-navigation POST
      });
  });

  window.addEventListener("popstate", () => {
    const run = () => {
      if (document.getElementById("target-search") ||
          document.querySelector(
            "main a[href^='/planner'], main a[href^='/plans']"
          )) {
        swapMain(window.location.href, false);
      }
    };
    // Back/forward off an unsaved plan page prompts; staying restores
    // the plan URL on top of the history (the DOM never left).
    guardUnsavedPlanLeave(
      window.location.href,
      run,
      () => history.pushState({}, "", unsavedPlanUrl)
    );
  });

  // Sidebar navigation is a departure too, but it leaves the page
  // entirely (no swap): while a plan is unsaved, route it through the
  // same on-page dialog — Leave navigates for real. Re-queried at
  // event time so it survives main swaps. Tab close, refresh, and the
  // address bar stay ungoverned by design: no browser popups (the
  // owner's call — the structures delete-dialog is the confirmation
  // pattern of record), and the calculation is URL state, so history
  // or reopen-tab restores it.
  document.addEventListener("click", (event) => {
    if (unsavedPlanUrl === null) return;
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    const link = event.target.closest("aside a[href]");
    if (!link) return;
    const href = link.getAttribute("href") || "";
    if (!href || href.startsWith("#")) return;
    event.preventDefault();
    guardUnsavedPlanLeave(link.href, () => {
      window.location.assign(link.href);
    }, null);
  });

  // The guard dialog's buttons (the structures delete-dialog pattern:
  // the pending action is stored; Leave submits through the swap path;
  // Cancel/Escape/backdrop just close). Re-queried at event time so it
  // survives main swaps.
  document.addEventListener("click", (event) => {
    const dialog = document.getElementById("unsaved-plan-dialog");
    if (!dialog || !dialog.open) return;
    if (event.target.id === "unsaved-plan-leave") {
      const leave = pendingLeave;
      pendingLeave = pendingStay = null;
      unsavedPlanUrl = null;  // leaving intentionally — prompt once
      dialog.close();
      if (leave) leave();
    } else if (event.target.id === "unsaved-plan-stay" ||
               event.target === dialog) {  // backdrop click
      dialog.close();
    }
  });
}

window.initPlannerPage();
window.initPlanPage();
window.initPlansPage();
refreshUnsavedPlan();
