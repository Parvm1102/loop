"""Deterministic cost / profit model for the four return routes.

For a returned unit we estimate the profit (or loss) of each disposition route
and let the optimizer pick the best. Crucially the resale revenue is *risk
adjusted* by a realization probability driven by quality and fraud — otherwise
RESELL/P2P, which have the highest nominal value, would always win regardless of
how damaged or suspicious the item is.

    realize = sell_through(quality) * (1 - fraud_risk)
    expected_revenue = nominal_value * realize

DONATE has no revenue, so it is the risk-immune floor that wins when every
resale route is dragged down by low quality or high fraud. All multipliers and
rates live in settings so the model is tunable without code changes.

Logistics: a return leg (buyer -> facility) and a resale leg (facility -> next
buyer) are both charged. RESELL/REFURBISH pay the inter-city distance per leg;
P2P/DONATE stay in-city (cheaper). Big/delicate items cost more per km.
"""

from django.conf import settings

ROUTES = ("RESELL", "REFURBISH", "P2P", "DONATE")


def _clamp01(v) -> float:
    try:
        return max(0.0, min(1.0, float(v)))
    except (TypeError, ValueError):
        return 0.0


def rate_per_km(size_class: str, fragility: str) -> float:
    rates = settings.REROUTING_RATE_PER_KM
    mult = settings.REROUTING_FRAGILITY_MULT
    base = rates.get(size_class, rates["small"])
    return base * mult.get(fragility, mult["rigid"])


def repair_cost(quality, mrp) -> int:
    """Cost to refurbish: scales with the quality gap, capped to a share of MRP."""
    raw = (1.0 - _clamp01(quality)) * (mrp or 0) * settings.REROUTING_REPAIR_FACTOR
    return round(min(raw, settings.REROUTING_REPAIR_MAX_PCT * (mrp or 0)))


def sell_through(quality) -> float:
    """Realization probability from condition: SELL_BASE at q=0, 1.0 at q=1."""
    base = settings.REROUTING_SELL_THROUGH_BASE
    return base + (1.0 - base) * _clamp01(quality)


def _realize(quality, fraud, fraud_weight) -> float:
    fraud_risk = _clamp01(fraud) * fraud_weight
    return _clamp01(sell_through(quality) * (1.0 - fraud_risk))


def compute(
    *, mrp, paid, est_value, quality, fraud, size_class, fragility,
    distance_km, storage=0,
) -> dict:
    """Return per-route {revenue, costs, realize, profit} plus the inputs used."""
    mrp = mrp or 0
    est_value = est_value or 0
    storage = storage or 0

    rate = rate_per_km(size_class, fragility)
    ship_full = round(distance_km * rate)                    # one inter-city leg
    ship_local = round(settings.REROUTING_LOCAL_KM * rate)   # one in-city leg
    repair = repair_cost(quality, mrp)
    refurb_value = round(settings.REROUTING_REFURB_RESALE_PCT * mrp)
    p2p_value = round(settings.REROUTING_P2P_RESALE_PCT * est_value)

    fr = settings.REROUTING_FRAUD_RESALE_RISK
    refurb_fraud_w = fr * (1.0 - settings.REROUTING_REFURB_FRAUD_MITIGATION)
    refurb_q = settings.REROUTING_REFURB_TARGET_QUALITY

    realize_resale = _realize(quality, fraud, fr)            # RESELL & P2P
    realize_refurb = _realize(refurb_q, fraud, refurb_fraud_w)

    routes = {
        "RESELL": {
            "revenue": round(est_value * realize_resale),
            "costs": ship_full * 2 + storage,
            "realize": round(realize_resale, 3),
        },
        "REFURBISH": {
            "revenue": round(refurb_value * realize_refurb),
            "costs": repair + ship_full * 2 + storage,
            "realize": round(realize_refurb, 3),
        },
        "P2P": {
            "revenue": round(p2p_value * realize_resale),
            "costs": ship_local * 2 + storage,
            "realize": round(realize_resale, 3),
        },
        "DONATE": {
            "revenue": 0,
            "costs": ship_local + storage,
            "realize": 0.0,
        },
    }
    for r in routes.values():
        r["profit"] = r["revenue"] - r["costs"]

    return {
        "routes": routes,
        "inputs": {
            "mrp": mrp,
            "paid": paid,
            "est_value": est_value,
            "quality": round(_clamp01(quality), 3),
            "fraud": round(_clamp01(fraud), 3),
            "size_class": size_class,
            "fragility": fragility,
            "distance_km": distance_km,
            "storage": storage,
            "rate_per_km": round(rate, 2),
            "ship_full": ship_full,
            "ship_local": ship_local,
            "repair": repair,
            "refurb_value": refurb_value,
            "p2p_value": p2p_value,
        },
    }
