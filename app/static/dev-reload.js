// Dev-only auto refresh (DEV_AUTO_RELOAD): polls the site-version token
// and reloads when code, templates, or static files change. The script
// tag is only rendered when the flag is set; production never loads it.
(function () {
  // Baseline: the token this page was rendered with (embedded in <body>),
  // so a page loaded while reloads were paused still refreshes once they
  // resume — its snapshot is mid-development and older than the token.
  let version = document.body.dataset.devVersion || null;
  const poll = async () => {
    try {
      const response = await fetch("/__dev/version", { cache: "no-store" });
      if (!response.ok) return;
      const current = await response.text();
      if (current === "paused") return; // development in progress; hold
      if (version !== null && current !== version) {
        location.reload();
        return;
      }
      version = current;
    } catch (error) {
      /* server mid-restart (uvicorn --reload): retry next tick — the
         version will have changed once it is back. */
    }
  };
  setInterval(poll, 2000);
  poll();
})();
