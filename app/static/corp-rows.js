// Corporation-row presentation for the assets toolbar. Loaded immediately
// after the picker markup (not at end of body) so remembered open/closed
// states and pagination apply during parsing — before the browser's first
// paint. Exposed as window.initCorpRows so an in-place content swap (see
// app.js swapAssetsPage) can re-bind the same behaviors to fresh markup.

window.initCorpRows = () => {
  // Remember open/closed per corporation.
  const rows = document.querySelectorAll("details.corp-row");
  if (!rows.length) return;

  // Align the Select/Deselect pills into one column: give each pill the
  // margin it needs to start where the widest row's pill naturally starts
  // (after the longest name/count), so every pill shares an x position.
  // Absorbs both name and count width variance; runs before first paint.
  const pills = [...rows].map((row) => row.querySelector(".corp-toggle"));
  if (pills.length > 1) {
    const target = Math.max(...pills.map((pill) => pill.getBoundingClientRect().left));
    pills.forEach((pill) => {
      const delta = target - pill.getBoundingClientRect().left;
      if (delta > 0) pill.style.marginLeft = `${delta}px`;
    });
  }

  const key = (name) => `corp-row-open:${name}`;
  rows.forEach((row) => {
    const name = row.querySelector(".corp-name").textContent.trim();
    if (row.open) {
      // A server-rendered open row (partial selection) counts as intent:
      // completing the selection must not slam it shut on re-render.
      try {
        localStorage.setItem(key(name), "true");
      } catch (error) {
        /* private browsing mode */
      }
    } else {
      let saved = null;
      try {
        saved = localStorage.getItem(key(name));
      } catch (error) {
        /* private browsing mode */
      }
      if (saved !== null) row.open = saved === "true";
    }
    row.addEventListener("toggle", () => {
      try {
        localStorage.setItem(key(name), String(row.open));
      } catch (error) {
        /* private browsing mode */
      }
    });
  });

  // Pagination. Rows stay in the DOM (checkboxes must all be present for
  // All/None and apply()); pagination only hides those beyond the current
  // page, so selection semantics are untouched and expand/collapse state
  // survives page turns.
  const PAGE_SIZE = 10;
  const picker = document.querySelector(".char-picker");
  const pageRows = [...picker.querySelectorAll(".corp-row")];
  if (pageRows.length <= PAGE_SIZE) return;

  const pages = Math.ceil(pageRows.length / PAGE_SIZE);
  let page = 1;

  const nav = document.createElement("div");
  nav.className = "corp-pagination";
  const prev = document.createElement("button");
  prev.type = "button";
  prev.className = "chip-button";
  prev.textContent = "‹";
  const label = document.createElement("span");
  label.className = "corp-page-label";
  const next = document.createElement("button");
  next.type = "button";
  next.className = "chip-button";
  next.textContent = "›";
  nav.append(prev, label, next);
  picker.append(nav);

  const show = () => {
    pageRows.forEach((row, index) => {
      row.hidden = Math.floor(index / PAGE_SIZE) !== page - 1;
    });
    label.textContent = `${page} / ${pages}`;
    prev.disabled = page === 1;
    next.disabled = page === pages;
  };
  prev.addEventListener("click", () => {
    page = Math.max(1, page - 1);
    show();
  });
  next.addEventListener("click", () => {
    page = Math.min(pages, page + 1);
    show();
  });
  show();
};

window.initCorpRows();
