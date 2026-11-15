// Dev-only auto refresh (DEV_AUTO_RELOAD): polls the site-version token
// and reloads when code, templates, or static files change. The script
// tag is only rendered when the flag is set; production never loads it.
(function () {
  let version = null;
  const poll = async () => {
    try {
      const response = await fetch("/__dev/version", { cache: "no-store" });
      if (!response.ok) return;
      const current = await response.text();
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
