"use strict";
(() => {
  const editionHome = (year) => year <= 2008 ? "/2007/" : year <= 2012 ? "/2009/" : "/2013/";
  const validYear = (value) => /^\d{4}$/.test(String(value)) && Number(value) >= 2006 && Number(value) <= 2026;
  const query = new URLSearchParams(location.search);
  const yearFromUrl = query.get("year");
  const embeddedHomepage = query.get("archive-embed") === "1";
  if (embeddedHomepage) document.documentElement.classList.add("archive-year-embedded");
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
    function showHomepageBelowSlider() {
      if (embeddedHomepage || control.id === "archive-year") return null;
      let preview = document.getElementById("archive-year-home-preview");
      if (!preview) {
        preview = document.createElement("iframe");
        preview.id = "archive-year-home-preview";
        preview.className = "archive-year-home-preview";
        preview.title = "Selected year homepage";
        preview.loading = "eager";
        preview.referrerPolicy = "no-referrer";
        preview.addEventListener("load", () => {
          try {
            const page = preview.contentDocument;
            if (!page) return;
            page.documentElement.classList.add("archive-year-embedded");
            for (const link of page.querySelectorAll("a[href]")) {
              if (link.target !== "_blank") link.target = "_top";
            }
          } catch (_) {}
        });
        const toolbar = control.closest(".archive-year-global");
        for (const node of [...document.body.children]) {
          if (node === toolbar) continue;
          node.hidden = true;
          node.setAttribute("aria-hidden", "true");
        }
        toolbar.insertAdjacentElement("afterend", preview);
      }
      const url = new URL(homeLink.href, location.href);
      url.searchParams.set("archive-embed", "1");
      preview.title = "Selected year homepage, " + control.value;
      preview.src = url.href;
      return preview;
    }
    control.addEventListener("input", () => {
      updateGlobalControl();
      showHomepageBelowSlider();
    });
    control.addEventListener("change", () => {
      if (control.id === "archive-year" || embeddedHomepage) return;
      const preview = document.getElementById("archive-year-home-preview");
      if (!preview) {
        location.href = homeLink.href;
        return;
      }
      const target = new URL(homeLink.href, location.href);
      const current = location.pathname + location.search;
      const next = target.pathname + target.search;
      if (current !== next) history.pushState({ archiveYearPreview: true }, "", next);
    });
    updateGlobalControl();
  }

  window.addEventListener("popstate", () => {
    if (document.getElementById("archive-year-home-preview")) location.reload();
  });
})();
