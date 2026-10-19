"use strict"; (() => {
 const mapping = {"1362122742000": "/bluescholars/2013/blog/page/2/", "1358016466000": "/bluescholars/2013/blog/page/3/"};
 const params = new URLSearchParams(location.search);
 const offset = params.get("offset");
 if (location.pathname.replace(/\/$/, "") === "/bluescholars/2013/blog" && [...params].length === 1 && offset && mapping[offset]) {
  location.replace(mapping[offset] + location.hash);
 }
 if (typeof document !== "undefined") {
 const menu = document.querySelector("#mobileMenuLink a[aria-controls='mobileNav']");
 const mobileNav = document.getElementById("mobileNav");
 if (menu && mobileNav) {
  const setOpen = open => { document.body.classList.toggle("archive-menu-open", open); menu.setAttribute("aria-expanded", String(open)); };
  menu.addEventListener("click", event => { event.preventDefault(); setOpen(menu.getAttribute("aria-expanded") !== "true"); });
  menu.addEventListener("keydown", event => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); menu.click(); } });
  mobileNav.addEventListener("click", event => { if (event.target.closest("a")) setOpen(false); });
 }
 }
})();
