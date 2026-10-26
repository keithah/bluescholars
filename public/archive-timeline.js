"use strict";
(() => {
  const editionHome = (year) => year <= 2008 ? "/2007/" : year <= 2012 ? "/2009/" : "/2013/";
  const validYear = (value) => /^\d{4}$/.test(String(value)) && Number(value) >= 2006 && Number(value) <= 2026;
  const yearFromUrl = new URLSearchParams(location.search).get("year");
  const slider = document.getElementById("archive-year");
  const globalSliders = [...document.querySelectorAll(".archive-year-global-control")];

  if (slider) {
    if (validYear(yearFromUrl)) slider.value = yearFromUrl;
    const yearOut = document.getElementById("archive-year-output");
    const summary = document.getElementById("archive-era-summary");
    const count = document.getElementById("archive-year-count");
    const selectedHome = document.querySelector(".archive-home .archive-year-home");
    const cards = [...document.querySelectorAll(".archive-timeline-results .archive-site-card")];
    function updateCards() {
      const year = Number(slider.value);
      if (yearOut) {
        yearOut.value = year;
        yearOut.textContent = year;
      }
      slider.setAttribute("aria-valuetext", String(year));
      let siteCount = 0;
      for (const card of cards) {
        const show = year >= Number(card.dataset.startYear) && year <= Number(card.dataset.endYear);
        card.hidden = !show;
        if (show && !card.classList.contains("timeline-edition-card")) siteCount++;
      }
      if (summary) summary.textContent = year < 2009
        ? "The early Blue Scholars era · Twitter is not yet in the recovered record"
        : year === 2009
          ? "Twitter enters the recovered record"
          : "Showing archived material available in this year";
      if (selectedHome) {
        const timeline = slider.closest(".archive-timeline");
        const basePath = timeline ? timeline.dataset.basePath || "" : "";
        selectedHome.href = basePath + editionHome(year) + "?year=" + year;
        selectedHome.textContent = "Open " + year + " homepage";
      }
      if (count) count.textContent = siteCount + " related archive" + (siteCount === 1 ? "" : "s")
        + " with dated material in " + year + ".";
      document.querySelectorAll(".archive-timeline-results").forEach(node => { node.dataset.year = String(year); });
    }
    slider.addEventListener("input", updateCards);
    document.querySelectorAll(".archive-timeline-results a.archive-site-card").forEach((link) => {
      link.addEventListener("click", () => {
        const target = new URL(link.href, location.href);
        if (target.origin === location.origin) {
          target.searchParams.set("year", String(slider.value));
          link.href = target.pathname + target.search + target.hash;
        }
      });
    });
    updateCards();
  }

  for (const control of globalSliders) {
    const section = control.closest(".archive-year-global");
    const output = section.querySelector("output");
    const homeLink = section.querySelector(".archive-year-home");
    const initialYear = validYear(yearFromUrl) ? Number(yearFromUrl) : Number(control.dataset.defaultYear || control.value);
    control.value = String(initialYear);
    function updateGlobalControl() {
      const year = Number(control.value);
      output.value = String(year);
      output.textContent = String(year);
      control.setAttribute("aria-valuetext", String(year));
      const basePath = section.dataset.basePath || "";
      homeLink.href = basePath + editionHome(year) + "?year=" + year;
      homeLink.textContent = "Open " + year + " homepage";
    }
    control.addEventListener("input", updateGlobalControl);
    control.addEventListener("change", () => {
      if (control.id !== "archive-year") location.href = homeLink.href;
    });
    updateGlobalControl();
  }
})();
