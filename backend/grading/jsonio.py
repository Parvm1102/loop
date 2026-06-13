"""Deterministic JSON recovery from LLM text output.

Constrained decoding (response_format json_schema / json_object) is the first
line of defense. This module is the deterministic second line, for models that
still wrap their answer in reasoning tags or prose:

  1. Strip known reasoning wrappers — <think>/<thinking>/<thought>/<reason[ing]> —
     including an *unterminated* opening tag (model truncated mid-thought).
  2. Strip Markdown code fences (```json ... ```).
  3. Scan for the first BALANCED {...} object, honoring JSON string literals and
     backslash escapes so braces inside strings or leftover prose never confuse
     the scan (a naive first-'{' / last-'}' slice does).
  4. json.loads, then a minimal trailing-comma repair retry.

It raises ValueError only when no balanced JSON object can be recovered at all,
so the caller can tell a genuine model failure apart from a formatting quirk and
avoid falling back to the mock for the latter.
"""

import json
import re

# Reasoning wrappers some models emit around (or before) the JSON answer.
_THINK_TAGS = ("think", "thinking", "thought", "reason", "reasoning")
# A full <tag>...</tag> block OR an unclosed <tag>... running to end-of-string.
_THINK_RE = re.compile(
    r"<(" + "|".join(_THINK_TAGS) + r")\b[^>]*>.*?(?:</\1\s*>|$)",
    re.DOTALL | re.IGNORECASE,
)
_FENCE_RE = re.compile(r"```[a-zA-Z0-9_+-]*\s*(.*?)```", re.DOTALL)
# Trailing comma before a closing } or ] — the most common machine-JSON defect.
_TRAILING_COMMA_RE = re.compile(r",(\s*[}\]])")


def _strip_think(text: str) -> str:
    return _THINK_RE.sub("", text)


def _balanced_object(text: str):
    """Return the first balanced {...} substring of `text`, or None.

    String-aware: braces inside JSON string literals are ignored and backslash
    escapes are skipped, so prose or reasoning containing stray braces cannot
    derail the scan.
    """
    start = text.find("{")
    if start < 0:
        return None
    depth = 0
    in_str = esc = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None  # unbalanced (model truncated)


def extract_json(text: str) -> dict:
    """Best-effort, deterministic parse of a JSON object from model text."""
    if not text or not text.strip():
        raise ValueError("empty model response")

    # 1) Fast path: the whole response is already a clean JSON object.
    try:
        obj = json.loads(text.strip())
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass

    # 2) Drop reasoning wrappers, then prefer a fenced block, else the remainder.
    stripped = _strip_think(text)
    candidates = []
    fence = _FENCE_RE.search(stripped)
    if fence:
        candidates.append(fence.group(1))
    candidates.append(stripped)

    # 3 + 4) First balanced {...}, with a trailing-comma repair retry.
    for cand in candidates:
        span = _balanced_object(cand)
        if not span:
            continue
        for attempt in (span, _TRAILING_COMMA_RE.sub(r"\1", span)):
            try:
                obj = json.loads(attempt)
                if isinstance(obj, dict):
                    return obj
            except json.JSONDecodeError:
                continue

    raise ValueError("no balanced JSON object found in model response")
