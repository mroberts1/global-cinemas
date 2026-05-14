"""Augment cinemawaves.json with period strings from the index pages.

The 43 individual movement pages don't include year ranges in their titles, but
the index pages (movements/, movements-page2/, movements-page3/) DO show them
in the link text: "Czechoslovak New Wave (1962-1970)".

Run after scrape_cinemawaves.py.
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

INDEX_URLS = [
    "https://cinemawavesblog.com/movements/",
    "https://cinemawavesblog.com/movements-page2/",
    "https://cinemawavesblog.com/movements-page3/",
]
DATA_PATH = Path(__file__).resolve().parent.parent / "src" / "lib" / "data" / "manual" / "cinemawaves.json"


def parse_year_range(s: str) -> tuple[int | None, int | None]:
    s = (s or "").replace("–", "-").replace("—", "-")
    nums = re.findall(r"(?:18|19|20)\d{2}", s)
    start = int(nums[0]) if nums else None
    end = int(nums[1]) if len(nums) > 1 else None
    return start, end


def collect_periods() -> dict[str, str]:
    """Visit each index page and return {url: period_str}."""
    periods: dict[str, str] = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120 Safari/537.36"
        )
        page = ctx.new_page()
        for idx_url in INDEX_URLS:
            print(f"[index] {idx_url}", file=sys.stderr)
            page.goto(idx_url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(2200)
            links = page.eval_on_selector_all(
                "a",
                """els => els.map(a => ({
                    text: (a.textContent || '').trim(),
                    href: a.getAttribute('href') || ''
                }))""",
            )
            for l in links:
                href = (l.get("href") or "").rstrip("/")
                text = l.get("text") or ""
                if not re.search(r"cinemawavesblog\.com/movements(-page\d+)?/[a-z0-9-]+$", href):
                    continue
                m = re.search(r"\(([^)]+)\)\s*$", text)
                if not m:
                    continue
                url = href + "/"
                periods[url] = m.group(1).strip()
            time.sleep(2)
        browser.close()
    return periods


def main() -> int:
    periods = collect_periods()
    print(f"[periods] collected {len(periods)} period strings", file=sys.stderr)

    with DATA_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    n_updated = 0
    for m in data["movements"]:
        url = m["url"]
        # Try a few normalisations of the URL
        for u in (url, url.rstrip("/") + "/"):
            if u in periods:
                pr = periods[u]
                # Strip leading "est. " etc.
                pr = re.sub(r"^(est\.?|c\.?|circa)\s*", "", pr, flags=re.I).strip()
                m["period_raw"] = pr
                start, end = parse_year_range(pr)
                m["period"] = {"start": start, "end": end}
                n_updated += 1
                break

    with DATA_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[done] updated {n_updated}/{len(data['movements'])} entries", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
