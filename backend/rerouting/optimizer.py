"""Expected-Value optimizer: pick the most profitable (least lossy) route.

Pure function over the cost breakdown from costs.compute(). This is strategy #2
and the deterministic fallback for the LLM strategy; it also supplies the money
figures (best profit, per-route ranking, loss) the offer logic needs.
"""


def optimize(costs: dict) -> dict:
    """Return {route, profit, loss, ranking} for the per-route cost breakdown."""
    routes = (costs or {}).get("routes", {})
    if not routes:
        return {"route": "", "profit": 0, "loss": 0, "ranking": []}

    ranking = sorted(
        routes.items(), key=lambda kv: kv[1].get("profit", 0), reverse=True
    )
    best_route, best = ranking[0]
    best_profit = best.get("profit", 0)
    return {
        "route": best_route,
        "profit": best_profit,
        "loss": max(0, -best_profit),
        "ranking": [
            {"route": r, "profit": v.get("profit", 0)} for r, v in ranking
        ],
    }
