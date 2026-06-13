"""LLM route-decision strategy (text only).

Reuses grading's provider table (settings.LLM_PROVIDERS) for a plain chat
completion and grading's deterministic JSON extractor to parse the answer. The
model picks a route given the grader signals and the EV profit estimate.

The LLM is *authoritative* — but only when it actually answers. If no provider
is configured, or the call/parse fails, decide() returns None and the caller
falls back to the EV optimizer. Format issues degrade json_schema -> json_object
(constrained -> loose); they never silently switch strategy mid-call.
"""

import logging

from django.conf import settings

from grading import jsonio

from . import prompts

log = logging.getLogger(__name__)

_OPENAI_COMPAT = ("gemini", "openai", "modal")
_VALID = {"RESELL", "REFURBISH", "P2P", "DONATE"}
# Models that rejected json_schema once; remembered so we don't retry it.
_NO_JSON_SCHEMA: set[str] = set()


def _clamp01(v, default):
    try:
        return max(0.0, min(1.0, float(v)))
    except (TypeError, ValueError):
        return default


def _resolve():
    """Return (model, client) for the configured provider, or (None, None)."""
    choice = (getattr(settings, "REROUTING_LLM_PROVIDER", "auto") or "auto").lower()
    if choice == "mock":
        return None, None
    if choice == "auto":
        names = _OPENAI_COMPAT
    elif choice in _OPENAI_COMPAT:
        names = (choice,)
    else:
        return None, None

    providers = getattr(settings, "LLM_PROVIDERS", {}) or {}
    for name in names:
        cfg = providers.get(name) or {}
        if not cfg.get("model"):
            continue
        if cfg.get("requires_key", True) and not cfg.get("api_key"):
            continue
        if not cfg.get("base_url") and not cfg.get("api_key"):
            continue
        try:
            from openai import OpenAI
        except Exception:  # noqa: BLE001 — SDK missing -> fall back to EV
            return None, None
        client = OpenAI(
            base_url=cfg.get("base_url") or None,
            api_key=cfg.get("api_key") or "missing",
            timeout=getattr(settings, "REROUTING_LLM_TIMEOUT", 20.0),
            max_retries=1,
        )
        return cfg["model"], client
    return None, None


def decide(context: dict, cost: dict):
    """Ask the LLM to choose a route. Returns a normalized dict or None."""
    model, client = _resolve()
    if not client:
        return None
    messages = prompts.build_messages(context, cost)
    try:
        content = _complete(client, model, messages)
        data = jsonio.extract_json(content)
    except Exception:  # noqa: BLE001 — any failure -> EV fallback
        log.exception("rerouting LLM failed; falling back to EV")
        return None

    route = str(data.get("route", "")).strip().upper()
    if route not in _VALID:
        return None
    return {
        "route": route,
        "confidence": _clamp01(data.get("confidence"), 0.6),
        "reasoning": str(data.get("reasoning", "")).strip(),
    }


def _complete(client, model, messages) -> str:
    """Chat completion with json_schema, degrading to json_object on rejection."""
    from openai import BadRequestError

    use_schema = model not in _NO_JSON_SCHEMA
    for _ in range(2):
        if use_schema:
            response_format = {
                "type": "json_schema",
                "json_schema": prompts.decision_schema(),
            }
        else:
            response_format = {"type": "json_object"}
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                response_format=response_format,
                temperature=0.1,
            )
            return (resp.choices[0].message.content or "").strip()
        except BadRequestError:
            if not use_schema:
                raise  # not a schema problem — let the caller fall back to EV
            _NO_JSON_SCHEMA.add(model)
            use_schema = False
    raise RuntimeError("unreachable")
