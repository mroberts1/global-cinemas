"""Build per-movement JSON files at src/lib/data/movements/<slug>.json.

Combines three sources:
    1. src/lib/data/manual/billy_movements.json — canonical films per movement
    2. src/lib/data/manual/cinemawaves.json — essay text + dates
    3. src/lib/data/manual/enrichment.json — country, region, coords, influences

Slug matching is fuzzy (handles "Direct And Cinema Verite" vs "Direct Cinema &
Cinema Vertie"). Reports any unmatched movements at the end.

Run after scrape_billy_list.py + scrape_cinemawaves.py + augment_cinemawaves_periods.py.
"""
from __future__ import annotations

import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

PROJ = Path(__file__).resolve().parent.parent
DATA = PROJ / "src" / "lib" / "data"
MANUAL = DATA / "manual"
OUT_DIR = DATA / "movements"

BILLY = MANUAL / "billy_movements.json"
CW = MANUAL / "cinemawaves.json"
ENRICH = MANUAL / "enrichment.json"


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").strip().lower())
    return re.sub(r"-{2,}", "-", s).strip("-")


def normalize_for_match(s: str) -> str:
    """Drop generic suffixes & punctuation so 'New British Wave' ~ 'British New Wave'."""
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    # Treat "and" / "&" as same
    return s


def fuzzy_match(target: str, candidates: list[str], threshold: float = 0.7) -> tuple[str | None, float]:
    """Return (best_candidate, score) — None if below threshold."""
    nt = normalize_for_match(target)
    best = (None, 0.0)
    for c in candidates:
        nc = normalize_for_match(c)
        # Direct containment bonus
        if nt == nc:
            return (c, 1.0)
        s = SequenceMatcher(None, nt, nc).ratio()
        # Bonus for token overlap
        nt_tokens = set(nt.split())
        nc_tokens = set(nc.split())
        if nt_tokens and nc_tokens:
            overlap = len(nt_tokens & nc_tokens) / max(len(nt_tokens), len(nc_tokens))
            s = max(s, overlap)
        if s > best[1]:
            best = (c, s)
    if best[1] >= threshold:
        return best
    return (None, best[1])


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load sources
    billy = json.loads(BILLY.read_text("utf-8"))
    cw = json.loads(CW.read_text("utf-8"))
    enrich_raw = json.loads(ENRICH.read_text("utf-8"))
    # Drop schema/comment keys
    enrich = {k: v for k, v in enrich_raw.items() if not k.startswith("_")}

    # Resolve aliases — _alias_of points from a "billy slug" to the canonical "cw slug"
    aliases: dict[str, str] = {}
    for slug, payload in list(enrich.items()):
        if isinstance(payload, dict) and "_alias_of" in payload:
            aliases[slug] = payload["_alias_of"]

    def canonical(s: str) -> str:
        return aliases.get(s, s)

    billy_movements = billy.get("movements", [])
    cw_movements = cw.get("movements", [])
    print(
        f"[load] billy: {len(billy_movements)} movements, "
        f"cinemawaves: {len(cw_movements)} movements, "
        f"enrich: {len(enrich)} entries, aliases: {len(aliases)}",
        file=sys.stderr,
    )

    # Build cinemawaves index by slug for fast lookup
    cw_by_slug = {m["slug"]: m for m in cw_movements}

    # All slugs we want to emit (union of billy + cw + enrich)
    all_slugs: dict[str, dict] = {}

    # Start with cinemawaves entries (richer data)
    for m in cw_movements:
        all_slugs[m["slug"]] = {"_source_cw": m}

    # Match billy movements into cinemawaves slugs (fuzzy + alias)
    for bm in billy_movements:
        target_name = bm["raw_name"]
        target_slug = bm["slug"]

        # 1) Try alias first (handles known slug differences like budapest-school → budapest-school-film-movement)
        if target_slug in aliases:
            chosen_slug = aliases[target_slug]
        # 2) Direct slug match against cw
        elif target_slug in cw_by_slug:
            chosen_slug = target_slug
        else:
            # 3) Fuzzy match against cw names
            cand_names = [m["name"] for m in cw_movements]
            match, score = fuzzy_match(target_name, cand_names)
            if match:
                chosen_slug = next(m["slug"] for m in cw_movements if m["name"] == match)
                print(
                    f"[fuzzy] billy '{target_name}' → cw '{match}' (score {score:.2f})",
                    file=sys.stderr,
                )
            else:
                # 4) Brand-new slug — billy-only
                chosen_slug = target_slug
                print(f"[billy-only] {target_name!r} → slug={chosen_slug}", file=sys.stderr)
                all_slugs[chosen_slug] = {}

        all_slugs.setdefault(chosen_slug, {})["_source_billy"] = bm

    # Compose final outputs
    composed: list[dict] = []
    missing_enrich: list[str] = []
    for slug, sources in sorted(all_slugs.items()):
        cw_m = sources.get("_source_cw")
        bm = sources.get("_source_billy")
        # Pull enrichment for this slug, falling back to alias-resolved enrichment
        en = enrich.get(slug, {})
        if not en:
            # Look for any aliased entry pointing here
            for alias_slug, target in aliases.items():
                if target == slug and alias_slug in enrich:
                    en = enrich[alias_slug]
                    break
        if not en:
            missing_enrich.append(slug)

        # Resolve display name (prefer cinemawaves, fallback billy, fallback slug)
        if cw_m:
            raw_name = cw_m.get("name", slug.replace("-", " ").title())
        elif bm:
            raw_name = bm.get("name") or bm.get("raw_name", slug)
        else:
            raw_name = slug.replace("-", " ")

        # Title-case while preserving small words and known capitalisations
        small = {"a", "an", "and", "of", "the", "in", "on", "for", "&"}
        def smart_title(s: str) -> str:
            words = s.split()
            out_words = []
            for i, w in enumerate(words):
                lw = w.lower()
                # Always capitalize first/last word and proper nouns
                if i == 0 or i == len(words) - 1:
                    out_words.append(w[:1].upper() + w[1:] if w else w)
                elif lw in small:
                    out_words.append(lw)
                else:
                    out_words.append(w[:1].upper() + w[1:] if w else w)
            return " ".join(out_words)
        name = smart_title(raw_name)
        # Manual fixups
        name = name.replace("L.A.", "L.A.").replace("L.a.", "L.A.")
        name = re.sub(r"\bUsa\b", "USA", name)

        # Period — prefer cw, fallback billy
        period = {"start": None, "end": None}
        period_raw = ""
        if cw_m and cw_m.get("period", {}).get("start"):
            period = cw_m["period"]
            period_raw = cw_m.get("period_raw", "")
        elif bm and bm.get("period", {}).get("start"):
            period = bm["period"]
            period_raw = bm.get("period_raw", "")

        # Summary — prefer cw essay, fallback billy
        summary = (cw_m.get("summary") if cw_m else "") or (bm.get("summary") if bm else "")
        long_description = (cw_m.get("long_description") if cw_m else "") or summary

        # Films — billy is the source of truth
        films = bm.get("films", []) if bm else []

        # Key directors — derive from billy films
        directors = []
        seen_dir = set()
        for f in films:
            d = (f.get("director") or "").strip()
            if d and d not in seen_dir:
                directors.append(d)
                seen_dir.add(d)

        # External links
        cinema_waves_url = cw_m.get("url") if cw_m else None

        # Compose
        out = {
            "slug": slug,
            "name": name,
            "period_raw": period_raw,
            "period": period,
            "country": en.get("country") or "",
            "countries": en.get("countries") or ([en["country"]] if en.get("country") else []),
            "region": en.get("region") or "",
            "coords": en.get("coords") or [],
            "summary": summary,
            "long_description": long_description,
            "key_directors": directors[:12],
            "canonical_films": films,
            "influences_from": en.get("influences_from", []),
            "influences_to": en.get("influences_to", []),
            "cinema_waves_url": cinema_waves_url,
            "letterboxd_list_url": "https://letterboxd.com/billybibbic/list/guide-to-film-movements-history-of-art-cinema/",
        }
        composed.append(out)

        # Write per-movement file
        out_path = OUT_DIR / f"{slug}.json"
        out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n[build] wrote {len(composed)} movements to {OUT_DIR}", file=sys.stderr)
    if missing_enrich:
        print(
            f"\n[warn] {len(missing_enrich)} movements missing from enrichment.json:",
            file=sys.stderr,
        )
        for s in missing_enrich:
            print(f"  - {s}", file=sys.stderr)

    # Summary table
    print("\n[summary] (sorted by start year)", file=sys.stderr)
    composed.sort(key=lambda m: m.get("period", {}).get("start") or 9999)
    for m in composed:
        start = m["period"].get("start") or "?"
        end = m["period"].get("end") or ""
        country = m.get("country") or "?"
        n_films = len(m["canonical_films"])
        print(
            f"  {start!s:>5}{f'–{end}' if end else '':>6}  "
            f"{m['name']:38s}  {country:18s}  {n_films:2d} films",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
