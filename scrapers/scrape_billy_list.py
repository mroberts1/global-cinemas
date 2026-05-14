"""Scrape Billy Bibbić's Letterboxd Film Movements list.

Each movement section is announced by a long note inside the FIRST film of that
movement. The note format is:

    _________________________________________
    MOVEMENT NAME (year range)
    A paragraph or two of essay text...
    Directed by: <director>

Subsequent films in the same movement just have "Directed by: <director>".

Output: ~/global-cinemas/src/lib/data/manual/billy_movements.json
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "https://letterboxd.com/billybibbic/list/guide-to-film-movements-history-of-art-cinema/detail/"
OUT_DIR = Path(__file__).resolve().parent.parent / "src" / "lib" / "data" / "manual"
OUT_PATH = OUT_DIR / "billy_movements.json"


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.strip().lower())
    return re.sub(r"-{2,}", "-", s).strip("-")


def parse_year_range(s: str) -> tuple[int | None, int | None]:
    """Pull a year range like '1895 - 1910s' or 'early 1920s – late 1930s' or '1962-1970'."""
    s = s.replace("–", "-").replace("—", "-")
    nums = re.findall(r"(?:18|19|20)\d{2}", s)
    start = int(nums[0]) if nums else None
    end = int(nums[1]) if len(nums) > 1 else None
    return start, end


def parse_movement_note(text: str) -> dict | None:
    """Parse the note text from the first film of a movement.

    Returns dict with name, period, summary, or None if no movement header detected.
    """
    # Strip lots of underscores
    cleaned = re.sub(r"_+", "\n", text).strip()
    # First line that's mostly uppercase and short is the movement name
    lines = [ln.strip() for ln in cleaned.splitlines() if ln.strip()]
    name = None
    name_idx = None
    period_str = None
    summary_remainder = ""
    for i, ln in enumerate(lines):
        # Match "MOVEMENT NAME (1895 - 1910s)" at the START of the line; essay
        # text often runs on directly after the closing paren with no break.
        m = re.match(
            r"([A-Z][A-Z &\-\'’]{3,80}?)\s*\(([^)]+)\)(.*)$",
            ln,
        )
        if m and len(m.group(1).strip()) > 3:
            name = m.group(1).strip()
            period_str = m.group(2).strip()
            summary_remainder = (m.group(3) or "").strip()
            name_idx = i
            break
        # Fallback: bare ALL-CAPS line (no period parens)
        m2 = re.match(r"([A-Z][A-Z &\-\'’]{3,80})\s*$", ln)
        if m2 and len(m2.group(1).strip()) > 3:
            name = m2.group(1).strip()
            period_str = ""
            name_idx = i
            break
    if not name:
        return None
    summary_lines: list[str] = []
    if summary_remainder:
        summary_lines.append(summary_remainder)
    summary_lines.extend(lines[name_idx + 1 :])
    # Drop "Directed by: ..." lines from the summary
    summary_lines = [ln for ln in summary_lines if not ln.lower().startswith("directed by:")]
    summary = " ".join(summary_lines).strip()
    start, end = parse_year_range(period_str) if period_str else (None, None)
    return {
        "name": name.title(),
        "raw_name": name,
        "slug": slugify(name),
        "period_raw": period_str,
        "period": {"start": start, "end": end},
        "summary": summary[:1200],
    }


def fetch_items(page, url: str) -> list[dict]:
    """Fetch (title, year, director, note, href) for each list entry in document order."""
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(8000)
    for _ in range(20):
        page.evaluate("window.scrollBy(0, 2500)")
        page.wait_for_timeout(500)
    # One more wait to let lazy content settle
    page.wait_for_timeout(2000)

    return page.evaluate(
        """
        () => {
            const items = [...document.querySelectorAll(
                '.list-detailed-entries-list > .listitem'
            )];
            return items.map((it, idx) => {
                const frame = it.querySelector('.frame-title');
                let title = frame ? frame.textContent.trim() : '';
                let year = '';
                const ym = title.match(/\\(((?:18|19|20)\\d{2})\\)$/);
                if (ym) {
                    year = ym[1];
                    title = title.replace(/\\s*\\((?:18|19|20)\\d{2}\\)$/, '').trim();
                }
                const link = it.querySelector('a.frame, .frame');
                const href = link ? link.getAttribute('href') || '' : '';
                const noteEl = it.querySelector(
                    '.body-text, .notes, .review, .listitem-note'
                );
                let note = noteEl ? noteEl.textContent : (it.textContent || '');
                let director = '';
                const dm = note.match(/Directed by:\\s*([^\\n]+?)(?=\\s{2,}|$|\\n)/);
                if (dm) director = dm[1].trim().split(/\\s{2,}/)[0].trim();
                return {idx, title, year, director, href, note: note.trim()};
            });
        }
        """
    )


def stitch_movements(items: list[dict]) -> list[dict]:
    movements: list[dict] = []
    current: dict | None = None
    for it in items:
        meta = parse_movement_note(it["note"])
        if meta:
            current = {
                **meta,
                "films": [],
            }
            movements.append(current)
        if current is not None:
            current["films"].append(
                {
                    "title": it["title"],
                    "year": it["year"],
                    "director": it["director"],
                    "letterboxd_url": ("https://letterboxd.com" + it["href"]) if it["href"] else "",
                }
            )
    return movements


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    base = "https://letterboxd.com/billybibbic/list/guide-to-film-movements-history-of-art-cinema/detail/"
    urls = [base] + [f"{base}page/{n}/" for n in range(2, 10)]
    all_items: list[dict] = []
    import time as _t
    for url_i, url in enumerate(urls):
        print(f"[fetch] {url}", file=sys.stderr)
        # Use a fresh browser per page — Letterboxd blocks subsequent
        # /detail/page/N/ loads within the same session, returning empty content.
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120 Safari/537.36"
            )
            page = ctx.new_page()
            try:
                items = fetch_items(page, url)
            except Exception as e:
                print(f"[fetch] err: {e}", file=sys.stderr)
                items = []
            browser.close()
        print(f"  {len(items)} items", file=sys.stderr)
        if not items:
            # End of pagination
            break
        all_items.extend(items)
        # Long cooldown between pages
        if url_i < len(urls) - 1:
            _t.sleep(20)
    movements = stitch_movements(all_items)
    print(f"\n[stitch] {len(movements)} movements from {len(all_items)} films", file=sys.stderr)
    for m in movements:
        period = m.get("period_raw") or ""
        print(
            f"  - {m['raw_name']:40s} {period[:25]:25s} "
            f"{len(m['films']):2d} films",
            file=sys.stderr,
        )
    with OUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "source": base,
                "n_movements": len(movements),
                "n_films": len(all_items),
                "movements": movements,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
    print(f"[done] {OUT_PATH}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
