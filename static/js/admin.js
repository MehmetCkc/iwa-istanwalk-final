(() => {
  const DISPLAY_LIMIT = 20;

  document.querySelectorAll("[data-admin-search]").forEach((searchInput) => {
    const sectionName = searchInput.dataset.adminSearch;
    const list = document.querySelector(`[data-admin-list="${sectionName}"]`);
    if (!list) return;

    const items = Array.from(list.querySelectorAll("[data-admin-item]"));
    const resultLabel = document.querySelector(
      `[data-admin-result="${sectionName}"]`,
    );
    const emptyMessage = document.querySelector(
      `[data-admin-empty="${sectionName}"]`,
    );
    const pagination = document.querySelector(
      `[data-admin-pagination="${sectionName}"]`,
    );
    const previousButton = pagination?.querySelector("[data-admin-prev]");
    const nextButton = pagination?.querySelector("[data-admin-next]");
    const pageLabel = pagination?.querySelector("[data-admin-page]");
    let currentPage = 1;

    const updateList = () => {
      // Filter the full DOM collection first, then expose only the
      // current 20-row page so search still reaches later records.
      const query = searchInput.value.trim().toLocaleLowerCase();
      const matches = items.filter((item) =>
        item.textContent.toLocaleLowerCase().includes(query),
      );
      const pageCount = Math.max(1, Math.ceil(matches.length / DISPLAY_LIMIT));
      currentPage = Math.min(currentPage, pageCount);
      const start = (currentPage - 1) * DISPLAY_LIMIT;
      const pageItems = matches.slice(start, start + DISPLAY_LIMIT);

      items.forEach((item) => {
        item.hidden = true;
      });
      pageItems.forEach((item) => {
        item.hidden = false;
      });

      if (resultLabel) {
        const firstShown = matches.length ? start + 1 : 0;
        const lastShown = Math.min(start + DISPLAY_LIMIT, matches.length);
        resultLabel.textContent = `${firstShown}–${lastShown} of ${matches.length} shown`;
      }
      if (emptyMessage) emptyMessage.hidden = matches.length !== 0;
      if (pagination) pagination.hidden = matches.length <= DISPLAY_LIMIT;
      if (previousButton) previousButton.disabled = currentPage === 1;
      if (nextButton) nextButton.disabled = currentPage === pageCount;
      if (pageLabel)
        pageLabel.textContent = `Page ${currentPage} / ${pageCount}`;
    };

    searchInput.addEventListener("input", () => {
      // A narrower result set may not contain the page currently shown.
      currentPage = 1;
      updateList();
    });
    previousButton?.addEventListener("click", () => {
      currentPage = Math.max(1, currentPage - 1);
      updateList();
      searchInput.scrollIntoView({ behavior: "smooth", block: "center" });
    });
    nextButton?.addEventListener("click", () => {
      currentPage += 1;
      updateList();
      searchInput.scrollIntoView({ behavior: "smooth", block: "center" });
    });
    updateList();
  });
})();
