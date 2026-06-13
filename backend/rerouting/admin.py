from django.contrib import admin

from .models import ReturnOffer, RouteDecision


@admin.register(RouteDecision)
class RouteDecisionAdmin(admin.ModelAdmin):
    list_display = (
        "id", "order", "unit", "status", "route", "decided_by",
        "ev_route", "llm_route", "created_at",
    )
    list_filter = ("status", "route", "decided_by")
    search_fields = ("order__id", "unit__id")
    readonly_fields = ("costs", "context", "created_at", "updated_at")


@admin.register(ReturnOffer)
class ReturnOfferAdmin(admin.ModelAdmin):
    list_display = (
        "id", "order", "status", "cash_refund", "green_credits",
        "expected_loss", "company_cost", "created_at",
    )
    list_filter = ("status",)
    search_fields = ("order__id",)
    readonly_fields = ("created_at", "updated_at", "responded_at")
