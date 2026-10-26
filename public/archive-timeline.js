"use strict";
(() => {
  const validYear = (value) => /^\d{4}$/.test(String(value)) && Number(value) >= 2006 && Number(value) <= 2026;
  const routesFor = (node) => {
    try { return JSON.parse(node?.dataset.homeRoutes || "{}"); } catch (_) { return {}; }
  };
  const query = new URLSearchParams(location.search);
  const yearFromUrl = query.get("year");
  const embeddedHomepage = query.get("archive-embed") === "1";
  if (embeddedHomepage) document.documentElement.classList.add("archive-year-embedded");
  const slider = document.getElementById("archive-year");
  const globalSliders = [...document.querySelectorAll(".archive-year-global-control")];

  if (slider) {
    if (validYear(yearFromUrl)) slider.value = yearFromUrl;
    let yearSelected = validYear(yearFromUrl);
    const yearOut = document.getElementById("archive-year-output");
    const summary = document.getElementById("archive-era-summary");
    const count = document.getElementById("archive-year-count");
    const selectedHome = document.querySelector(".archive-home .archive-year-home");
      const timeline = slider.closest(".archive-timeline");
      const basePath = timeline ? timeline.dataset.basePath || "" : "";
      const homeRoutes = routesFor(timeline);
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
        const cardRoutes = routesFor(card);
        const show = !yearSelected || Object.hasOwn(cardRoutes, String(year));
        card.hidden = !show;
        if (show && yearSelected) {
          const target = new URL(basePath + cardRoutes[String(year)], location.href);
          if (target.origin === location.origin) {
            target.searchParams.set("year", String(year));
            card.href = target.pathname + target.search + target.hash;
          }
        }
        if (show && !card.classList.contains("timeline-edition-card")) siteCount++;
      }
      if (summary) summary.textContent = !yearSelected
        ? "All recovered archives are listed · move the slider to browse a year"
        : year < 2009
          ? "The early Blue Scholars era · Twitter is not yet in the recovered record"
          : year === 2009
            ? "Twitter enters the recovered record"
            : "Showing archived material available in this year";
      if (selectedHome) {
        const route = homeRoutes[String(year)];
        if (route) {
          selectedHome.href = basePath + route + "?year=" + year;
          selectedHome.textContent = "Open " + year + " homepage";
          selectedHome.removeAttribute("aria-disabled");
        } else {
          selectedHome.removeAttribute("href");
          selectedHome.setAttribute("aria-disabled", "true");
          selectedHome.textContent = "No homepage capture for " + year;
        }
      }
      if (count) count.textContent = !yearSelected
        ? siteCount + " related archive" + (siteCount === 1 ? "" : "s") + " listed. Move the slider to filter by year."
        : siteCount + " related archive" + (siteCount === 1 ? "" : "s") + " with dated material in " + year + ".";
      document.querySelectorAll(".archive-timeline-results").forEach(node => { node.dataset.year = String(year); });
    }
    slider.addEventListener("input", () => { yearSelected = true; updateCards(); });
    document.querySelectorAll(".archive-timeline-results a.archive-site-card").forEach((link) => {
      link.addEventListener("click", () => {
        const route = yearSelected ? routesFor(link)[String(slider.value)] : null;
        if (route) {
          const timeline = slider.closest(".archive-timeline");
          const target = new URL((timeline?.dataset.basePath || "") + route, location.href);
          if (target.origin === location.origin) {
            target.searchParams.set("year", String(slider.value));
            link.href = target.pathname + target.search + target.hash;
          }
        }
      });
    });
    updateCards();
  }

  for (const control of globalSliders) {
    const section = control.closest(".archive-year-global");
    const output = section.querySelector("output");
    const homeLink = section.querySelector(".archive-year-home");
    const homeRoutes = routesFor(section);
    const initialYear = validYear(yearFromUrl) ? Number(yearFromUrl) : Number(control.dataset.defaultYear || control.value);
    control.value = String(initialYear);
    function updateGlobalControl() {
      const year = Number(control.value);
      output.value = String(year);
      output.textContent = String(year);
      control.setAttribute("aria-valuetext", String(year));
      const basePath = section.dataset.basePath || "";
      const route = homeRoutes[String(year)];
      if (route) {
        homeLink.href = basePath + route + "?year=" + year;
        homeLink.textContent = "Open " + year + " homepage";
        homeLink.removeAttribute("aria-disabled");
      } else {
        homeLink.removeAttribute("href");
        homeLink.setAttribute("aria-disabled", "true");
        homeLink.textContent = "No homepage capture for " + year;
      }
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
        const missing = document.createElement("p");
        missing.id = "archive-year-home-missing";
        missing.className = "archive-year-home-missing";
        missing.setAttribute("role", "status");
        toolbar.insertAdjacentElement("afterend", missing);
      }
      const missing = document.getElementById("archive-year-home-missing");
      const route = homeRoutes[String(control.value)];
      preview.hidden = !route;
      missing.hidden = Boolean(route);
      if (!route) {
        missing.textContent = "No homepage capture for " + control.value + " in this archive. Choose a year with a preserved page.";
        return null;
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
      if (!preview && homeLink.href) {
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
