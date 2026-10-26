# Seer Fairies

Independent static website for B. Carter’s Seer Fairies collection. Host name: `fairies.i4seer.com` (existing CNAME retained).

The site includes a homepage, a catalog of published books, 22 retained case pages, The Seer, About, News, Contact, other series, and a custom 404 page. The Books page has no search or filter controls or behavior. All fonts, artwork, styles, and scripts are local. No JavaScript framework or external build dependencies are required to serve it.

The public Books page and homepage shelves show published titles only: currently The Púca, The Sluagh, and The Each-Uisge. A single “More books in development” notice represents planned work. Unpublished source records and case pages remain ready for future releases; they are excluded from public shelves, related-book navigation, and the sitemap. Publication status is maintained in `data/books.json`.

## Build and preview

With Python installed, run `python scripts/build_site.py`. Preview using `python -m http.server 8771` from this folder, then open `http://127.0.0.1:8771/`. Directory-based routes need a static host that serves `index.html`. GitHub Pages supports this layout. Publish the repository root; deployment is separate from the local build.

## Maintain the books

- `data/books.json`: titles, routes, copy, cover provenance, publication status, and edition URLs.
- `data/site.json`: branding, canonical host, and browsing groups.
- `scripts/build_site.py`: page layouts and editorial content.
- `assets/site.css` and `assets/site.js`: theme, responsive behavior, catalog filters, and mobile menu.

To refresh current print art and approved jacket text, install Pillow and fonttools in your chosen Python environment and run `python scripts/build_site.py --source C:/SEERFAIRIES`. The script extracts the front from each latest `images-print/cover-print-ready-no-barcode.png` using actual `build-metadata.json` geometry, and reads the current `images-print/cover-copy.txt` sections. It also exports the text-free `background-dark-folklore-master.png` illustrations, local web fonts, source author/logo assets, and the homepage hero. It preserves edition links and publication status.

Books 1–20 currently have finished print covers. Books 21–22 have updated illustrations and approved jacket copy, but no finished cover wraps or print geometry. Those two cases show their actual source illustrations in clearly labeled preview panels. Future source refreshes will pick up finished print covers when available.

Published editions verified October 22, 2026: The Púca, The Sluagh, and The Each-Uisge, each in Kindle and paperback. Evidence and edition URLs are in `docs/amazon-editions.json`. Book 4 is in review and Book 5 is in writing, as updated by the author on October 26, 2026. Keep other unreleased books forthcoming until release is verified. Do not import production status conventions from other collections without checking them.

## Visual assets

The current book covers are extracted from the author’s supplied Dark Folklore print-ready artwork. The homepage hero uses the actual text-free Púca illustration. Each book banner uses its own scene; the homepage’s four browsing groups use corresponding illustrations from the collection. `data/fairies-artwork.json` records source fingerprints for all 22 cases.

The theme follows the covers: soot-black and forest surfaces, bone cream (`#f5ebd1`), autumn amber (`#ecad52`), and the individual accent palette of each book. Titles use the same Alegreya SC Black as the covers, with Charter for reading. Web fonts and their licenses are local in `assets/fonts/`. Historical hero art direction is retained in `docs/hero-art-direction.txt`.

## 2026-10-26 artwork refresh

Refreshed all 20 finished covers and illustrations for all 22 cases. Replaced the old photographic hero with the current engraved artwork, applied the cover typography and palette across the site, and added book-specific artwork banners. Published listings, edition links, contact details, and the existing hosting configuration are retained. The Books page has no search or filter capability. The update is local; deployment remains separate.

Canonical URLs, social previews, Book structured data, sitemap, robots file, local favicon, and a web manifest are generated. Keep `CNAME` aligned with `data/site.json` if the domain changes. Assets receive content hashes for cache refreshes. No analytics, signup, checkout, or contact-form backend is included; contact addresses use existing publisher email links.

The existing Git repository and CNAME were preserved. No hosting deployment was performed as part of creating the local site.
