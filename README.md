# Morné Augustyn — personal CV site

A single-page, dependency-free personal site built from my CV.
Product, Implementation & Commercial Growth Leader · Stellenbosch, South Africa.

## Files

```
index.html                     all content
assets/styles.css              styling (dark theme, responsive, print-friendly)
assets/main.js                 scroll reveals, scrollspy, mobile nav
assets/world.svg               generated operating-footprint map
assets/Morne-Augustyn-CV.pdf   downloadable CV
tools/build_map.py             regenerates assets/world.svg
```

No frameworks, no runtime dependencies, no tracking. The map is pre-generated
to a static SVG, so the page ships no mapping library.

## Run locally

```bash
python3 -m http.server 8000
# then open http://localhost:8000
```

## Deploy (GitHub Pages)

1. Push this repo to GitHub.
2. Settings → Pages → Source: **Deploy from a branch** → `main` / `/ (root)`.
3. The site goes live at `https://<username>.github.io/<repo>/` within a minute or two.

Any static host works too (Netlify, Cloudflare Pages, Vercel) — just point it at the repo root.

## Updating content

Everything is plain HTML in `index.html`:

- Roles live in the `.timeline` section as `<article class="job">` blocks.
- Sutera mandates are `<details class="mandate">` accordions.
- Headline metrics are `<article class="stat">` blocks; each has an inline SVG before/after chart.
- Colours and spacing are CSS variables at the top of `assets/styles.css`.

When the PDF changes, replace `assets/Morne-Augustyn-CV.pdf` (keep the filename).

## Regenerating the map

`assets/world.svg` is built from Natural Earth data (via the `world-atlas`
topojson). To change which countries are highlighted, edit the `HIGHLIGHT`
dict in `tools/build_map.py` and re-run:

```bash
curl -sL -o /tmp/countries-110m.json \
  https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json
python3 tools/build_map.py /tmp/countries-110m.json assets/world.svg
```

The script needs only the Python standard library. It fails loudly if a
highlighted country name is not found in the source data.
