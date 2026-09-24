# Morné Augustyn — personal CV site

A single-page, dependency-free personal site built from my CV.
Product, Implementation & Commercial Growth Leader · Stellenbosch, South Africa.

## Files

```
index.html                     all content
assets/styles.css              styling (dark theme, responsive, print-friendly)
assets/main.js                 scroll reveals, scrollspy, mobile nav
assets/Morne-Augustyn-CV.pdf   downloadable CV
```

No build step, no frameworks, no tracking.

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
- Headline metrics are `<article class="stat">` blocks; the `--fill` inline value sets the bar width.
- Colours and spacing are CSS variables at the top of `assets/styles.css`.

When the PDF changes, replace `assets/Morne-Augustyn-CV.pdf` (keep the filename).
