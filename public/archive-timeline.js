"use strict";
(() => {
  const validYear = (value) => /^\d{4}$/.test(String(value)) && Number(value) >= 2005 && Number(value) <= 2026;
  const routesFor = (node) => {
    try { return JSON.parse(node?.dataset.homeRoutes || "{}"); } catch (_) { return {}; }
  };
  const activityYearsFor = (node, routes) => {
    try {
      const years = JSON.parse(node?.dataset.activityYears || "[]");
      if (Array.isArray(years) && years.length) return years.map(Number).filter(validYear).sort((a, b) => a - b);
    } catch (_) {}
    return Object.keys(routes || {}).map(Number).filter(validYear).sort((a, b) => a - b);
  };
  const closestYear = (value, years) => years.reduce((best, year) =>
    Math.abs(year - value) < Math.abs(best - value) ||
    (Math.abs(year - value) === Math.abs(best - value) && year < best) ? year : best, years[0]);
  const enableYearKeyboard = (control, years) => {
    control.addEventListener("keydown", (event) => {
      if (!years.length || !["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Home", "End"].includes(event.key)) return;
      event.preventDefault();
      const current = years.indexOf(closestYear(Number(control.value), years));
      const next = event.key === "Home" ? 0 : event.key === "End" ? years.length - 1
        : current + (["ArrowRight", "ArrowUp"].includes(event.key) ? 1 : -1);
      control.value = String(years[Math.max(0, Math.min(years.length - 1, next))]);
      control.dispatchEvent(new Event("input", { bubbles: true }));
      control.dispatchEvent(new Event("change", { bubbles: true }));
    });
  };
  const closestRoute = (routes, year) => {
    const keys = Object.keys(routes || {}).map(Number).filter(validYear).sort((a, b) => a - b);
    if (!keys.length) return null;
    const selected = closestYear(Number(year), keys);
    return { year: selected, route: routes[String(selected)] };
  };
  // Preserve the early site's table geometry while fitting it to small screens.
  // Browser zoom scales image-map hit areas along with the original artwork.
  if (/\/lj\//.test(location.pathname || "")) document.documentElement.classList.add("archive-lj-layout");
  if (/\/(prometheusbrown|sabzi)\//.test(location.pathname || "")) document.documentElement.classList.add("archive-artist-layout");
  // Keep the 2005 platform's absolute header coordinates inside its own page,
  // below the restoration controls. Preserve the source background on that page.
  if (/\/lj\//.test(location.pathname || "") && document.querySelector("body > #Logo")) {
    const shell = document.createElement("div");
    shell.className = "archive-lj-original";
    shell.style.background = getComputedStyle(document.body).background;
    for (const child of [...document.body.childNodes]) {
      if (child.nodeType === 1 && child.matches(".archive-year-global, .archive-restoration-notice, script")) continue;
      shell.appendChild(child);
    }
    document.body.appendChild(shell);
    document.body.style.backgroundImage = "none";
  }
  const originalLayoutStyles = new WeakMap();
  const fitEarlyLayout = () => {
    const path = location.pathname || "";
    let selector = "";
    if (/\/(2007|2009|masslinemedia|massline-forums|206proof|lj)\//.test(path))
      selector = "body > table, body > center, body > #page, body > #Header, body > #Body, body > #shadowhack1, body > .s-header";
    if (/\/myspace\//.test(path)) selector = "body > table, body > div:not([class])";
    if (/\/twitter-[^/]+\//.test(path)) selector = "body > .twitter-original";
    if (!selector) return;
    const available = Math.min(document.documentElement.clientWidth, document.body.clientWidth);
    for (const container of document.querySelectorAll(selector)) {
      if (!originalLayoutStyles.has(container)) originalLayoutStyles.set(container, {width:container.style.width, zoom:container.style.zoom});
      const original = originalLayoutStyles.get(container);
      container.style.width = original.width;
      container.style.zoom = original.zoom;
      if (window.innerWidth > 600) continue;
      const width = Math.max(container.offsetWidth, container.scrollWidth);
      if (width > available && available > 0) {
        container.style.width = width + "px";
        container.style.zoom = String(available / width);
      }
    }
  };
  fitEarlyLayout();
  window.addEventListener("resize", fitEarlyLayout);
  const query = new URLSearchParams(location.search);
  const yearFromUrl = query.get("year");
  const embeddedHomepage = query.get("archive-embed") === "1";
  if (embeddedHomepage) document.documentElement.classList.add("archive-year-embedded");
  const slider = document.getElementById("archive-year");
  const globalSliders = [...document.querySelectorAll(".archive-year-global-control")];

  if (slider) {
    const activityYears = activityYearsFor(slider.closest(".archive-timeline"), routesFor(slider.closest(".archive-timeline")));
    if (activityYears.length) slider.value = String(closestYear(validYear(yearFromUrl) ? Number(yearFromUrl) : Number(slider.value), activityYears));
    enableYearKeyboard(slider, activityYears);
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
        const show = !yearSelected || Object.keys(cardRoutes).length > 0;
        card.hidden = !show;
        if (show && yearSelected) {
          const selected = closestRoute(cardRoutes, year);
          if (selected) {
            const target = new URL(basePath + selected.route, location.href);
            if (target.origin !== location.origin) continue;
            target.searchParams.set("year", String(selected.year));
            card.href = target.pathname + target.search + target.hash;
          }
        }
        if (show && !card.classList.contains("timeline-edition-card")) siteCount++;
      }
      if (summary) summary.textContent = !yearSelected
        ? "Blue Scholars site activity · move the slider to an archived update"
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
        ? siteCount + " related archive" + (siteCount === 1 ? "" : "s") + " listed. Move the timeline to browse Blue Scholars captures."
        : siteCount + " related archive" + (siteCount === 1 ? "" : "s") + " listed; links open the closest available capture to " + year + ".";
      document.querySelectorAll(".archive-timeline-results").forEach(node => { node.dataset.year = String(year); });
      const preview = document.getElementById("archive-year-home-preview");
      const selected = closestRoute(homeRoutes, year);
      if (preview && selected) {
        const target = new URL(basePath + selected.route, location.href);
        target.searchParams.set("year", String(selected.year));
        target.searchParams.set("archive-embed", "1");
        if (preview.src !== target.href) preview.src = target.href;
        preview.title = "Blue Scholars homepage, " + selected.year;
      }
    }
    slider.addEventListener("input", () => {
      if (activityYears.length) slider.value = String(closestYear(Number(slider.value), activityYears));
      yearSelected = true;
      updateCards();
    });
    document.querySelectorAll(".archive-timeline-results a.archive-site-card").forEach((link) => {
      link.addEventListener("click", () => {
        const selected = yearSelected ? closestRoute(routesFor(link), Number(slider.value)) : null;
        if (selected) {
          const timeline = slider.closest(".archive-timeline");
          const target = new URL((timeline?.dataset.basePath || "") + selected.route, location.href);
          if (target.origin === location.origin) {
            target.searchParams.set("year", String(selected.year));
            link.href = target.pathname + target.search + target.hash;
          }
        }
      });
    });
    document.getElementById("archive-year-home-preview")?.addEventListener("load", (event) => {
      try {
        const page = event.currentTarget.contentDocument;
        if (!page) return;
        page.documentElement.classList.add("archive-year-embedded");
        for (const link of page.querySelectorAll("a[href]")) if (link.target !== "_blank") link.target = "_top";
      } catch (_) {}
    });
    updateCards();
  }

  for (const control of globalSliders) {
    const section = control.closest(".archive-year-global");
    const output = section.querySelector("output");
    const homeLink = section.querySelector(".archive-year-home");
    const homeRoutes = routesFor(section);
    const activityYears = activityYearsFor(section, homeRoutes);
    enableYearKeyboard(control, activityYears);
    const rawInitialYear = validYear(yearFromUrl) ? Number(yearFromUrl) : Number(control.dataset.defaultYear || control.value);
    const initialYear = activityYears.length ? closestYear(rawInitialYear, activityYears) : rawInitialYear;
    control.value = String(initialYear);
    function updateGlobalControl() {
      const selectedYear = Number(control.value);
      const year = activityYears.length ? closestYear(selectedYear, activityYears) : selectedYear;
      control.value = String(year);
      output.value = String(year);
      output.textContent = String(year);
      control.setAttribute("aria-valuetext", String(year));
      const min = Number(control.min || year);
      const max = Number(control.max || year);
      const progress = max === min ? 100 : ((year - min) / (max - min)) * 100;
      control.closest(".archive-year-slider")?.style.setProperty("--timeline-progress", `${progress}%`);
      section.querySelectorAll(".archive-year-marker").forEach((marker) => {
        if (Number(marker.dataset.year) === year) marker.setAttribute("aria-current", "true");
        else marker.removeAttribute("aria-current");
      });
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
    section.querySelectorAll('.archive-year-marker').forEach((marker) => {
      marker.addEventListener("click", () => {
        if (!validYear(marker.dataset.year)) return;
        control.value = marker.dataset.year;
        control.dispatchEvent(new Event("input", { bubbles: true }));
        control.dispatchEvent(new Event("change", { bubbles: true }));
      });
    });
    updateGlobalControl();
  }

  window.addEventListener("popstate", () => {
    if (document.getElementById("archive-year-home-preview")) location.reload();
  });
})();
