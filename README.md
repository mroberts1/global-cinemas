# Global Cinemas

An atlas of film movements from the Cinema of Attractions (1895) to today's New Extremity. Trace influence across countries, decades, and waves.

Live site: TBD (Vercel)

## Stack

- SvelteKit + Vite + TypeScript
- `@sveltejs/adapter-static` → Vercel
- Python scrapers (Letterboxd, cinemawavesblog.com)

## Data sources

- Billy Bibbić's Letterboxd list of film movements
- cinemawavesblog.com sitemap (43 movements)
- Augmented with periods, coordinates, summaries

Movement JSON files live in `src/lib/data/movements/<slug>.json`.

## Routes

- `/` — card grid of all movements
- `/movement/[slug]` — detail page per movement
- `/timeline` — chronological list
- `/graph` — influence edges between movements
- `/regions` — grouped by region of origin
- `/about` — project background

## Local development

```sh
npm install
npm run dev
```

Production build:

```sh
npm run build      # writes to ./build
npm run preview
```

## Scrapers

Python virtualenv lives in `.venv/`. To re-run:

```sh
.venv/bin/python scrapers/scrape_cinemawaves.py
.venv/bin/python scrapers/scrape_billy_list.py
.venv/bin/python scrapers/augment_cinemawaves_periods.py
.venv/bin/python scrapers/build_movements.py
```
