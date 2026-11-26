// Roster corporation panels: remembered open/closed per corporation
// (the corp-rows.js localStorage pattern, picker-independent — the
// assets toolbar's copy stays coupled to its Select/Deselect pills).
// Loaded immediately after the panel markup so remembered states apply
// during parsing, before the browser's first paint.

window.initRosterCorps = () => {
  const rows = document.querySelectorAll("details.roster-corp");
  rows.forEach((row) => {
    const name = row.querySelector(".corp-name").textContent.trim();
    const key = `roster-corp-open:${name}`;
    let saved = null;
    try {
      saved = localStorage.getItem(key);
    } catch (error) {
      /* private browsing mode */
    }
    if (saved !== null) row.open = saved === "true";
    row.addEventListener("toggle", () => {
      try {
        localStorage.setItem(key, String(row.open));
      } catch (error) {
        /* private browsing mode */
      }
    });
  });
};

window.initRosterCorps();
