"""Rerouting decision + return-prevention offer records.

A RouteDecision is one disposition decision for a returned unit — which of
RESELL / REFURBISH / P2P / DONATE maximizes outcome — produced by two strategies
running in parallel (deterministic Expected-Value optimizer and an LLM). The LLM
is authoritative; EV is the fallback and always supplies the money breakdown.

A ReturnOffer is the optional "keep it" proposal we make to the buyer when every
route loses money and fraud is low: a partial cash refund plus green credits. The
buyer accepts or declines from the Orders page.
"""

from django.db import models

from core.models import TimeStamped


class RouteChoices(models.TextChoices):
    RESELL = "RESELL", "Resell as-is"
    REFURBISH = "REFURBISH", "Refurbish & resell"
    P2P = "P2P", "Peer-to-peer exchange"
    DONATE = "DONATE", "Donate"


class DecisionStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    RUNNING = "RUNNING", "Running"
    DONE = "DONE", "Done"
    FAILED = "FAILED", "Failed"


class StrategyKinds(models.TextChoices):
    LLM = "llm", "LLM"
    EV = "ev", "Expected value"


class RouteDecision(TimeStamped):
    assessment = models.OneToOneField(
        "grading.GradingAssessment",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="route_decision",
    )
    order = models.ForeignKey(
        "marketplace.Order", on_delete=models.CASCADE, related_name="route_decisions"
    )
    unit = models.ForeignKey(
        "catalog.ItemUnit", on_delete=models.CASCADE, related_name="route_decisions"
    )
    status = models.CharField(
        max_length=10, choices=DecisionStatus.choices, default=DecisionStatus.PENDING
    )

    # Final decision (LLM authoritative, EV fallback).
    route = models.CharField(max_length=10, choices=RouteChoices.choices, blank=True)
    decided_by = models.CharField(
        max_length=8, choices=StrategyKinds.choices, blank=True
    )
    confidence = models.FloatField(blank=True, null=True)
    reasoning = models.TextField(blank=True)

    # What each strategy picked (kept for audit/explainability).
    ev_route = models.CharField(max_length=10, choices=RouteChoices.choices, blank=True)
    llm_route = models.CharField(max_length=10, choices=RouteChoices.choices, blank=True)

    # Deterministic per-route profit breakdown + the inputs that produced it.
    costs = models.JSONField(default=dict, blank=True)
    context = models.JSONField(default=dict, blank=True)

    error = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["order", "status"]),
            models.Index(fields=["-created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"RouteDecision #{self.pk} order={self.order_id} {self.route or '?'}"


class OfferStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    ACCEPTED = "ACCEPTED", "Accepted"
    DECLINED = "DECLINED", "Declined"


class ReturnOffer(TimeStamped):
    decision = models.OneToOneField(
        RouteDecision, on_delete=models.CASCADE, related_name="offer"
    )
    order = models.ForeignKey(
        "marketplace.Order", on_delete=models.CASCADE, related_name="return_offers"
    )
    status = models.CharField(
        max_length=10, choices=OfferStatus.choices, default=OfferStatus.PENDING
    )

    cash_refund = models.PositiveIntegerField(default=0, help_text="₹")
    green_credits = models.PositiveIntegerField(default=0)
    expected_loss = models.PositiveIntegerField(default=0, help_text="₹ loss avoided")
    company_cost = models.PositiveIntegerField(default=0, help_text="₹ cost to company")
    message = models.CharField(max_length=300, blank=True)

    responded_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        indexes = [models.Index(fields=["order", "status"])]
        ordering = ["-created_at"]

    def __str__(self):
        return f"ReturnOffer #{self.pk} order={self.order_id} {self.status}"
