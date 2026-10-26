"use strict";
(() => {
  const slider = document.getElementById("archive-year");
  if (!slider) return;
  const yearOut = document.getElementById("archive-year-output");
  const summary = document.getElementById("archive-era-summary");
  const count = document.getElementById("archive-year-count");
  const cards = [...document.querySelectorAll(".archive-timeline-results .archive-site-card")];
  function update() {
    const year = Number(slider.value);
    yearOut.value = year;
    yearOut.textContent = year;
    slider.setAttribute("aria-valuetext", String(year));
    let siteCount = 0;
    for (const card of cards) {
      const show = year >= Number(card.dataset.startYear) && year <= Number(card.dataset.endYear);
      card.hidden = !show;
      if (show && !card.classList.contains("timeline-edition-card")) siteCount++;
    }
    summary.textContent = year < 2009
      ? "The early Blue Scholars era · Twitter is not yet in the recovered record"
      : year === 2009
        ? "Twitter enters the recovered record"
        : "Showing archived material available in this year";
    count.textContent = siteCount + " related archive" + (siteCount === 1 ? "" : "s")
      + " with dated material in " + year + ".";
    document.querySelectorAll(".archive-timeline-results").forEach(node => { node.dataset.year = String(year); });
  }
  slider.addEventListener("input", update);
  update();
})();
