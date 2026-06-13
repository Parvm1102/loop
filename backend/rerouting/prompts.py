"""LLM prompt + response schema for the route-decision strategy.

Plain text chat (no images): the model is handed the AI grader's read on the
returned item, the parties' locations, and the deterministic per-route profit
estimate, and asked to pick one route. The schema keeps its answer to a single
structured object so parsing is reliable.
"""

import json

SYSTEM_PROMPT = (
    "You are the reverse-logistics strategist for a circular marketplace. A "
    "customer has returned an item; choose the single best disposition route to "
    "maximize the company's financial and environmental outcome.\n"
    "- RESELL: list it again as-is. Best when quality is high and fraud is low.\n"
    "- REFURBISH: pay to repair, then resell. Worth it when the repair cost is "
    "small relative to the resale value it unlocks.\n"
    "- P2P: hand to a local peer-to-peer buyer at a discount. Best when condition "
    "is acceptable but inter-city resale logistics would erode the margin.\n"
    "- DONATE: give away for green credits and goodwill. Best when the item is low "
    "value or quality, or every resale route loses money.\n"
    "You are given a deterministic per-route profit estimate — trust those "
    "numbers, but apply judgement on quality, fraud and reputation (e.g. avoid "
    "reselling an item with high fraud risk even if nominal profit looks high). "
    "Respond with ONLY a JSON object: {route, confidence (0..1), reasoning (one "
    "or two sentences)}."
)


def build_messages(context: dict, cost: dict) -> list:
    routes = (cost or {}).get("routes", {})
    inp = (cost or {}).get("inputs", {})
    profit_lines = "\n".join(
        f"- {r}: profit ₹{v.get('profit')} "
        f"(revenue ₹{v.get('revenue')}, costs ₹{v.get('costs')}, "
        f"realize {v.get('realize')})"
        for r, v in routes.items()
    )
    product = context.get("product", {})
    user = f"""RETURNED ITEM
- Product: {product.get('title')} ({product.get('category')}), MRP ₹{product.get('mrp')}
- Customer paid: ₹{context.get('paid')}
- AI grade: {context.get('grade')} | quality {context.get('quality')} | fraud {context.get('fraud')} | confidence {context.get('confidence')}
- Size / handling: {context.get('size_class')} / {context.get('fragility')}
- Estimated resale value (as-is): ₹{context.get('est_value')}
- Seller <-> customer distance: {context.get('distance_km')} km | storage accrued ₹{context.get('storage')}
- Return reason: {context.get('return_reason') or 'n/a'}
- Defects: {', '.join(context.get('defects') or []) or 'none noted'}
- Buyer history: {json.dumps(context.get('buyer_history', {}), default=str)}
- Seller history: {json.dumps(context.get('seller_history', {}), default=str)}

DETERMINISTIC PROFIT ESTIMATE (₹, higher is better):
{profit_lines}
Per-leg logistics: ₹{inp.get('ship_full')} inter-city, ₹{inp.get('ship_local')} local; repair est ₹{inp.get('repair')}.

Pick the single best route."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


def decision_schema() -> dict:
    """Strict JSON schema for constrained decoding of the route choice."""
    return {
        "name": "route_decision",
        "strict": True,
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "route": {
                    "type": "string",
                    "enum": ["RESELL", "REFURBISH", "P2P", "DONATE"],
                },
                "confidence": {"type": "number"},
                "reasoning": {"type": "string"},
            },
            "required": ["route", "confidence", "reasoning"],
        },
    }
