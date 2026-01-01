#!/usr/bin/env python3
"""Small helper for managing `quotes.json`.

Usage examples:
    from quotes_helper import add_quote
    add_quote(text, author=..., source=..., tags=[...], notes=...)
"""
import json
import uuid
from datetime import date
from pathlib import Path
from typing import List, Optional


BASE = Path(__file__).parent
JSON_PATH = BASE / "quotes.json"


def load_quotes() -> List[dict]:
    if not JSON_PATH.exists():
        return []
    return json.loads(JSON_PATH.read_text(encoding="utf-8"))


def save_quotes(data: List[dict]) -> None:
    JSON_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def update_quote(qid: str, *, text: Optional[str] = None, author: Optional[str] = None,
                 source: Optional[str] = None, tags: Optional[List[str]] = None,
                 notes: Optional[str] = None, date: Optional[str] = None) -> Optional[dict]:
    """Update an existing quote by id. Returns the updated object or None if not found."""
    data = load_quotes()
    for i, q in enumerate(data):
        if q.get("id") == qid:
            if text is not None:
                q["text"] = text
            if author is not None:
                q["author"] = author
            if source is not None:
                q["source"] = source
            if tags is not None:
                q["tags"] = tags
            if notes is not None:
                q["notes"] = notes
            if date is not None:
                q["date"] = date
            data[i] = q
            save_quotes(data)
            return q
    return None


def delete_quote(qid: str) -> bool:
    """Delete a quote by id. Returns True if deleted, False if not found."""
    data = load_quotes()
    for i, q in enumerate(data):
        if q.get("id") == qid:
            del data[i]
            save_quotes(data)
            return True
    return False


def _unique_uuid(existing_ids: set) -> str:
    new_id = str(uuid.uuid4())
    while new_id in existing_ids:
        new_id = str(uuid.uuid4())
    return new_id


def add_quote(text: str,
              author: Optional[str] = None,
              source: Optional[str] = None,
              tags: Optional[List[str]] = None,
              notes: Optional[str] = None,
              created_date: Optional[str] = None) -> dict:
    data = load_quotes()
    existing_ids = {q.get("id") for q in data}
    obj = {
        "id": _unique_uuid(existing_ids),
        "text": text,
        "author": author or None,
        "source": source or None,
        "tags": tags or [],
        "date": created_date or date.today().isoformat(),
        "notes": notes or None,
    }
    data.append(obj)
    save_quotes(data)
    return obj


if __name__ == '__main__':
    # quick demo: add a sample quote when run directly
    sample = add_quote(
        "Every day it gets easier. But you have to do it every day—that's the hard part.",
        author="Jogging Monkey",
        source="Bojack Horseman Season 2, Episode 12",
        tags=["theises", "motivation", "exercise"],
        notes="This is the make a good quote for the theises project."
    )
    print("Added:", sample["id"])


from difflib import SequenceMatcher
from typing import Tuple
import re


def _token_set_similarity(a: str, b: str) -> float:
    """Jaccard-like similarity on token sets (0-1)."""
    if not a or not b:
        return 0.0
    toks_a = set(re.findall(r"\w+", a.lower()))
    toks_b = set(re.findall(r"\w+", b.lower()))
    if not toks_a or not toks_b:
        return 0.0
    inter = toks_a & toks_b
    union = toks_a | toks_b
    return len(inter) / len(union)


def _partial_ratio(a: str, b: str) -> float:
    """A simple partial-ratio: best SequenceMatcher ratio between `a` and any substring of `b`.
    Works best when `a` is shorter than `b`.
    """
    if not a or not b:
        return 0.0
    a = a.lower()
    b = b.lower()
    if len(a) >= len(b):
        return SequenceMatcher(None, a, b).ratio()
    best = 0.0
    la = len(a)
    # slide over b with window size from la to min(len(b), la*2)
    max_window = min(len(b), max(la, la * 2))
    for window in range(la, max_window + 1):
        for i in range(0, len(b) - window + 1):
            sub = b[i:i+window]
            r = SequenceMatcher(None, a, sub).ratio()
            if r > best:
                best = r
                if best >= 1.0:
                    return 1.0
    return best


def _score(a: str, b: str) -> float:
    """Return a blended similarity score (0-1) using several heuristics.

    Heuristics used:
    - exact substring match -> 1.0
    - SequenceMatcher ratio
    - partial ratio (good for short queries)
    - token-set similarity (Jaccard)
    The final score is the maximum of these — conservative but effective for short/broken queries.
    """
    if not a or not b:
        return 0.0
    a_low = a.lower().strip()
    b_low = b.lower().strip()
    if a_low in b_low:
        return 1.0
    seq = SequenceMatcher(None, a_low, b_low).ratio()
    part = _partial_ratio(a_low, b_low)
    token = _token_set_similarity(a_low, b_low)
    return max(seq, part, token)


def _best_substring_match(a: str, b: str) -> tuple:
    """Find substring of `b` that best matches `a` using SequenceMatcher.

    Returns (best_score, substring) where substring is taken from the original `b` text.
    """
    if not a or not b:
        return 0.0, ""
    a_low = a.lower()
    b_low = b.lower()
    if a_low in b_low:
        start = b_low.find(a_low)
        return 1.0, b[start:start+len(a_low)]
    best = 0.0
    best_sub = ""
    la = len(a_low)
    # window sizes from la to min(len(b), la*2)
    max_window = min(len(b_low), max(la, la * 2))
    for window in range(la, max_window + 1):
        for i in range(0, len(b_low) - window + 1):
            sub = b_low[i:i+window]
            r = SequenceMatcher(None, a_low, sub).ratio()
            if r > best:
                best = r
                best_sub = b[i:i+window]
                if best >= 1.0:
                    return best, best_sub
    return best, best_sub


def fuzzy_search(query: str, fields: Tuple[str, ...] = ("text", "author", "source"), min_score: float = 0.35, limit: int = 10) -> List[dict]:
    """Fuzzy-search quotes.

    - query: search string
    - fields: which object fields to compare against the query
    - min_score: minimum similarity (0-1) to include
    - limit: max results returned, sorted by score desc

    Returns a list of dicts with an added `_score` key.
    """
    data = load_quotes()
    results = []
    for q in data:
        best = 0.0
        best_snippet = ""
        best_field = None
        # score each field and remember best snippet/field
        for f in fields:
            val = q.get(f) or ""
            s = _score(query, val)
            # get substring match info
            part_score, snippet = _best_substring_match(query, val)
            # pick higher of s and part_score for this field
            field_score = max(s, part_score)
            if field_score > best:
                best = field_score
                best_snippet = snippet
                best_field = f
        # also compare against full text explicitly
        val = q.get("text", "")
        s = _score(query, val)
        part_score, snippet = _best_substring_match(query, val)
        field_score = max(s, part_score)
        if field_score > best:
            best = field_score
            best_snippet = snippet
            best_field = "text"
        if best >= min_score:
            r = q.copy()
            r["_score"] = round(best, 3)
            r["_match_field"] = best_field
            r["_match_snippet"] = best_snippet
            results.append(r)
    results.sort(key=lambda x: x["_score"], reverse=True)
    return results[:limit]


def search_by_tag(tag: str) -> List[dict]:
    """Return quotes that contain `tag` (case-insensitive) in their tags list."""
    data = load_quotes()
    t = tag.lower()
    return [q for q in data if any((tt or "").lower() == t for tt in q.get("tags", []))]


def _cli_search():
    import argparse
    parser = argparse.ArgumentParser(description="Fuzzy search quotes")
    parser.add_argument("query", nargs="?", help="Search query (or leave empty to list all)")
    parser.add_argument("--min-score", type=float, default=0.35)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--tag", help="Search by exact tag instead of fuzzy")
    args = parser.parse_args()
    if args.tag:
        res = search_by_tag(args.tag)
    elif args.query:
        res = fuzzy_search(args.query, min_score=args.min_score, limit=args.limit)
    else:
        res = load_quotes()
    for r in res:
        score = r.get("_score")
        s = f" [{score}]" if score is not None else ""
        print(f"{r.get('id')} {s}\n  {r.get('text')}\n  — {r.get('author')} ({r.get('source')})\n")


if __name__ == '__main__':
    # when invoked directly allow simple CLI search
    try:
        _cli_search()
    except SystemExit:
        # argparse may call sys.exit; ignore when used as module
        pass
