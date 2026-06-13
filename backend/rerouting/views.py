from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from . import services
from .models import ReturnOffer


def _owned_offer(request, pk):
    """The offer with this id belonging to the requesting buyer, or None."""
    return (
        ReturnOffer.objects.filter(pk=pk, order__buyer=request.user)
        .select_related("order", "order__listing", "order__listing__unit")
        .first()
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def accept_offer(request, pk):
    offer = _owned_offer(request, pk)
    if offer is None:
        return Response({"detail": "Offer not found."}, status=404)
    return Response(services.accept_offer(offer, request.user))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def decline_offer(request, pk):
    offer = _owned_offer(request, pk)
    if offer is None:
        return Response({"detail": "Offer not found."}, status=404)
    return Response(services.decline_offer(offer, request.user))
