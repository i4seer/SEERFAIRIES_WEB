# Seer Fairies

Independent static website for B. Carter’s Seer Fairies collection. Host name: `fairies.i4seer.com` (existing CNAME retained).

The site includes a homepage, searchable/filterable catalog, 22 case pages, The Seer, About, News, Contact, other series, and a custom 404 page. All fonts, artwork, styles, and scripts are local. No JavaScript framework or external build dependencies are required to serve it.

## Build and preview

With Python installed, run `python scripts/build_site.py`. Preview using `python -m http.server 8771` from this folder, then open `http://127.0.0.1:8771/`. Directory-based routes need a static host that serves `index.html`. GitHub Pages supports this layout. Publish the repository root; deployment is separate from the local build.

## Maintain the books

- `data/books.json`: titles, routes, copy, cover provenance, publication status, and edition URLs.
- `data/site.json`: branding, canonical host, and browsing groups.
- `scripts/build_site.py`: page layouts and editorial content.
- `assets/site.css` and `assets/site.js`: theme, responsive behavior, catalog filters, and mobile menu.

To refresh current print art and approved jacket text, install Pillow in your chosen Python environment and run `python scripts/build_site.py --source C:/SEERFAIRIES`. The script extracts the front from each latest `images-print/cover-print-ready-no-barcode.png` using `build-metadata.json` geometry, and reads Fairies’ `images-print/background-text.txt` format. It preserves edition links and publication status. It does not interpret an ISBN or a source README status as proof of release.

Books 1–16 currently have finished print artwork and approved jacket copy. Books 17–22 use clearly marked typographic case-file panels and spoiler-light summaries derived from their metadata. Their generic, repeated `images-kindle/m00.jpg` files are intentionally not presented as cover art. The refresh command will use a future print cover when one exists. Review summaries when replacing them with final jacket copy.

Published editions verified October 22, 2026: The Púca, The Sluagh, and The Each-Uisge, each in Kindle and paperback. Evidence and edition URLs are in `docs/amazon-editions.json`. Keep other books forthcoming until release is verified. Do not import production status conventions from other collections without checking them.

## Visual assets

The current book covers are extracted from the author’s supplied print-ready artwork. The atmospheric woodland hero was made using the built-in image generation tool, inspired by The Púca and The Each-Uisge covers. Original PNG and optimized WebP are in `assets/`; the exact prompt is saved in `docs/hero-art-direction.txt`. Fonts are the supplied local EB Garamond files.

Canonical URLs, social previews, Book structured data, sitemap, robots file, local favicon, and a web manifest are generated. Keep `CNAME` aligned with `data/site.json` if the domain changes. Assets receive content hashes for cache refreshes. No analytics, signup, checkout, or contact-form backend is included; contact addresses use existing publisher email links.

The existing Git repository and CNAME were preserved. No hosting deployment was performed as part of creating the local site.
