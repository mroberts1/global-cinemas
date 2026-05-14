"""Scrape CinemaWaves Blog movements via the WordPress sitemap.

Uses the canonical sitemap (https://cinemawavesblog.com/page-sitemap1.xml) to
get the COMPLETE list of movement URLs (43 as of May 2026), then visits each
to extract title, year range, country, key directors, and the essay text.

Output: ~/global-cinemas/src/lib/data/manual/cinemawaves.json
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

SITEMAP_URLS = [
    "https://cinemawavesblog.com/page-sitemap1.xml",
    "https://cinemawavesblog.com/page-sitemap2.xml",
]
OUT_DIR = Path(__file__).resolve().parent.parent / "src" / "lib" / "data" / "manual"
OUT_PATH = OUT_DIR / "cinemawaves.json"

# Index pages (NOT movements themselves)
INDEX_SLUGS = {"movements", "movements-page2", "movements-page3"}


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.strip().lower())
    return re.sub(r"-{2,}", "-", s).strip("-")


def parse_year_range(s: str) -> tuple[int | None, int | None]:
    s = (s or "").replace("–", "-").replace("—", "-")
    nums = re.findall(r"(?:18|19|20)\d{2}", s)
    start = int(nums[0]) if nums else None
    end = int(nums[1]) if len(nums) > 1 else None
    return start, end


def collect_urls_from_sitemaps() -> list[str]:
    urls: set[str] = set()
    for sm in SITEMAP_URLS:
        try:
            with urllib.request.urlopen(sm, timeout=15) as r:
                xml = r.read().decode("utf-8", errors="replace")
        except Exception as e:
            print(f"[sitemap err] {sm}: {e}", file=sys.stderr)
            continue
        for m in re.finditer(r"<loc>(https://cinemawavesblog\.com/movements[^<]+)</loc>", xml):
            url = m.group(1).rstrip("/")
            slug = url.rsplit("/", 1)[-1]
            if slug in INDEX_SLUGS:
                continue
            urls.add(url + "/")
    return sorted(urls)


def fetch_movement_page(page, url: str) -> dict:
    """Visit a single CinemaWaves movement page and pull structured info."""
    page.goto(url, wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(1800)
    info = page.evaluate(
        """() => {
            const article = document.querySelector('article, main, .entry-content, .post-content') || document.body;
            const title = (document.querySelector('h1, .entry-title, .post-title') || {}).textContent?.trim() || '';
            const headings = [...article.querySelectorAll('h2, h3')].map(h => h.textContent.trim());
            const ps = [...article.querySelectorAll('p')]
                .map(p => p.textContent.trim())
                .filter(t => t.length > 50);
            // Look for explicit metadata in tables / definition lists
            const dts = [...article.querySelectorAll('dt, th, strong')].map(el => el.textContent.trim());
            const sidekick = [...article.querySelectorAll('aside, .sidebar, .meta')].map(el => el.textContent.trim()).join('\\n');
            const fullText = article.textContent || '';
            return {title, headings, paragraphs: ps.slice(0, 14), strongs: dts.slice(0, 60), sidekick: sidekick.slice(0, 2000), full: fullText};
        }"""
    )
    full = info.get("full") or ""
    title = info.get("title") or ""
    # Heuristics: parse "(est. 1962-1970)" or similar from title
    period_str = ""
    m_period = re.search(r"\(\s*(?:est\.?|c\.?|circa)?\s*([0-9]{4}.*?)\)", title)
    if m_period:
        period_str = m_period.group(1).strip()
    start, end = parse_year_range(period_str)
    summary = " ".join(info.get("paragraphs", [])[:3])[:1500]
    long_desc = " ".join(info.get("paragraphs", [])[:12])[:6000]
    name = re.sub(r"\s*\([^)]*\)\s*$", "", title).strip() or url.rsplit("/", 2)[-2].replace("-", " ").title()

    # Look for "Country: X" or "Origin: X" patterns in text
    country = None
    cm = re.search(r"(?:Country|Origin|Region|Location)\s*[:\-]\s*([A-Z][A-Za-z\s,&]{2,40})", full)
    if cm:
        country = cm.group(1).strip().rstrip(".")

    return {
        "name": name,
        "slug": slugify(name),
        "period_raw": period_str,
        "period": {"start": start, "end": end},
        "country_guess": country,
        "title": title,
        "summary": summary,
        "long_description": long_desc,
        "headings": info.get("headings", []),
        "url": url,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    urls = collect_urls_from_sitemaps()
    print(f"[sitemap] {len(urls)} movement URLs collected", file=sys.stderr)
    movements: list[dict] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120 Safari/537.36"
        )
        page = ctx.new_page()
        for i, url in enumerate(urls, 1):
            print(f"  [{i:2d}/{len(urls)}] {url}", file=sys.stderr)
            try:
                m = fetch_movement_page(page, url)
                movements.append(m)
                print(
                    f"      → {m['name']!r} {m['period_raw']!r} ({len(m['summary'])} chars summary)",
                    file=sys.stderr,
                )
            except Exception as e:
                print(f"      ERR: {e}", file=sys.stderr)
            time.sleep(1.5)
        browser.close()

    with OUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(
            {"source": "cinemawavesblog.com", "n_movements": len(movements), "movements": movements},
            f,
            indent=2,
            ensure_ascii=False,
        )
    print(f"\n[done] {OUT_PATH} ({len(movements)} movements)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
