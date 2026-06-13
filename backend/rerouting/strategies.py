"""Route-decision strategies and the keep-it offer.

Two strategies decide what to do with a returned unit:

* **EV** (`ev_result`) — the deterministic Expected-Value optimizer over the
  risk-adjusted cost model. Always runs; always available.
* **LLM** (`llm_result`) — a model that reasons over the same data plus history.
  Authoritative when it answers; falls back to EV otherwise.

They run in parallel (see tasks.py); `finalize` blends them (LLM wins if present)
and, when every route loses money, may attach a return-prevention offer.

`build_context` snapshots everything both strategies need into plain dicts so the
Celery subtasks can read them off the RouteDecision row without touching the ORM
graph or passing heavy objects through the broker.
"""

import logging

from django.conf import settings

from services import ai

from . import costs, geo, llm, optimizer
from .models import (
    DecisionStatus,
    OfferStatus,
    ReturnOffer,
    RouteDecision,
    StrategyKinds,
)

log = logging.getLogger(__name__)


def seller_history(seller) -> dict:
    """Light reputation snapshot for the seller (cheap aggregate queries)."""
    from catalog.models import Product
    from marketplace.models import Order

    if not seller:
        return {}
    products = Product.objects.filter(seller=seller).count()
    orders = Order.objects.filter(listing__unit__product__seller=seller)
    total = orders.count()
    returns = orders.exclude(return_reason="").count()
    return {
        "products_listed": products,
        "orders_total": total,
        "returns_total": returns,
        "return_rate": round(returns / total, 3) if total else 0.0,
    }


def _quality(assessment, vlm) -> float:
    if assessment.quality_score is not None:
        return assessment.quality_score
    return vlm.get("quality_estimate", vlm.get("quality", 0.5))


def build_context(assessment):
    """Return (context, cost) dicts for one return assessment."""
    unit = assessment.unit
    product = unit.product
    order = assessment.order
    seller = product.seller
    buyer = order.buyer if order else None

    vlm = assessment.vlm_result or {}
    quality = _quality(assessment, vlm)
    fraud = assessment.fraud_score or 0.0
    # Prefer the durable grader-derived attributes persisted on the product (set
    # by grading.orchestrator); fall back to this run's VLM, then to defaults.
    attrs = product.attributes or {}
    size_class = attrs.get("size_class") or vlm.get("size_class") or "small"
    fragility = attrs.get("fragility") or vlm.get("fragility") or "rigid"
    grade = assessment.suggested_grade or unit.grade or "B"

    est_value = unit.est_value
    if not est_value:
        est_value = ai.price(product.id, product.mrp, grade)["est_value"]

    paid = order.listing.price if order and order.listing_id else product.mrp
    distance_km = geo.distance_between(seller, buyer)

    cost = costs.compute(
        mrp=product.mrp,
        paid=paid,
        est_value=est_value,
        quality=quality,
        fraud=fraud,
        size_class=size_class,
        fragility=fragility,
        distance_km=distance_km,
        storage=unit.storage_cost_accrued or 0,
    )

    context = {
        "product": {
            "title": product.title,
            "category": product.category,
            "mrp": product.mrp,
        },
        "grade": grade,
        "quality": cost["inputs"]["quality"],
        "fraud": cost["inputs"]["fraud"],
        "confidence": assessment.confidence,
        "size_class": size_class,
        "fragility": fragility,
        "est_value": est_value,
        "paid": paid,
        "distance_km": distance_km,
        "storage": unit.storage_cost_accrued or 0,
        "return_reason": getattr(order, "return_reason", "") if order else "",
        "defects": vlm.get("defects", []),
        "condition_summary": vlm.get("condition_summary", ""),
        "buyer_history": assessment.history_signals or {},
        "seller_history": seller_history(seller),
    }
    return context, cost


# --- strategies --------------------------------------------------------------

def ev_result(cost: dict) -> dict:
    """Deterministic Expected-Value pick."""
    return optimizer.optimize(cost)


def llm_result(context: dict, cost: dict):
    """LLM pick, or None when no provider answered (caller falls back to EV)."""
    return llm.decide(context, cost)


def finalize(decision: RouteDecision, ev: dict, llm_out) -> RouteDecision:
    """Blend the two strategies onto the decision and persist; may add an offer.

    The LLM is authoritative when it answered; otherwise EV decides. EV always
    supplies the money figures (profit/loss/ranking) used for the offer.
    """
    ev = ev or {}
    decision.costs = decision.costs or {}
    decision.ev_route = ev.get("route", "")

    if llm_out and llm_out.get("route"):
        decision.route = llm_out["route"]
        decision.llm_route = llm_out["route"]
        decision.decided_by = StrategyKinds.LLM
        decision.confidence = llm_out.get("confidence")
        decision.reasoning = llm_out.get("reasoning", "")
    else:
        decision.route = ev.get("route", "")
        decision.decided_by = StrategyKinds.EV
        decision.confidence = None
        decision.reasoning = _ev_reasoning(ev)

    decision.costs["ev"] = ev
    decision.status = DecisionStatus.DONE
    decision.error = ""
    decision.save()

    try:
        maybe_offer(decision, ev)
    except Exception:  # noqa: BLE001 — an offer failure must not fail the decision
        log.exception("offer creation failed for decision %s", decision.id)
    return decision


def _ev_reasoning(ev: dict) -> str:
    ranking = ev.get("ranking") or []
    parts = ", ".join(f"{r['route']} ₹{r['profit']}" for r in ranking[:4])
    return f"EV optimizer: best is {ev.get('route')} (profit ₹{ev.get('profit')}). {parts}".strip()


# --- keep-it offer -----------------------------------------------------------

def maybe_offer(decision: RouteDecision, ev: dict):
    """Create a return-prevention offer when every route loses money.

    Only when the item is genuinely usable and fraud is low — we don't bribe
    likely fraudsters. The offer is cash-majority so the customer feels fairly
    compensated; the remainder is green credits, which cost the company less than
    par because they guarantee a follow-on order.
    """
    ctx = decision.context or {}
    loss = (ev or {}).get("loss", 0)
    if loss <= 0:
        return None

    quality = ctx.get("quality", 0.0)
    fraud = ctx.get("fraud", 1.0)
    paid = ctx.get("paid", 0) or 0
    if fraud > settings.REROUTING_OFFER_FRAUD_MAX:
        return None
    if quality < settings.REROUTING_OFFER_MIN_QUALITY:
        return None

    # Make-whole = the depreciation the customer would eat by keeping it, capped
    # at the loss we'd otherwise take. Never offer more than the return costs us.
    make_whole = round(min(paid * (1.0 - quality), loss))
    if make_whole <= 0:
        return None

    cash = round(settings.REROUTING_OFFER_CASH_SHARE * make_whole)
    credits = max(make_whole - cash, 0)
    company_cost = round(cash + settings.REROUTING_CREDIT_COST_FACTOR * credits)

    offer, _ = ReturnOffer.objects.update_or_create(
        decision=decision,
        defaults={
            "order": decision.order,
            "status": OfferStatus.PENDING,
            "cash_refund": cash,
            "green_credits": credits,
            "expected_loss": loss,
            "company_cost": company_cost,
            "message": (
                f"Keep your item and get ₹{cash} back plus {credits} green "
                f"credits — no need to return it."
            ),
            "responded_at": None,
        },
    )
    return offer
