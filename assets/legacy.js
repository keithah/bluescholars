"use strict"; (() => {
 const mapping = {"1362122742000": "/bluescholars/2013/blog/page/2/", "1358016466000": "/bluescholars/2013/blog/page/3/"};
 const params = new URLSearchParams(location.search);
 const offset = params.get("offset");
 if (location.pathname.replace(/\/$/, "") === "/bluescholars/2013/blog" && [...params].length === 1 && offset && mapping[offset]) {
  location.replace(mapping[offset] + location.hash);
 }
})();
