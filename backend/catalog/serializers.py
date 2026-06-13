from rest_framework import serializers
from django.core.files.storage import default_storage

from .models import ItemUnit, Product, UnitEvent
from marketplace.models import ListingStates, Listing


class ProductSerializer(serializers.ModelSerializer):
    seller_name = serializers.CharField(source="seller.username", read_only=True)
    image_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id", "title", "description", "category", "mrp",
            "image_url", "thumbnail_url", "seller_name", "created_at",
            "attributes",
        ]

    def get_image_url(self, obj):
        return obj.image.url if obj.image else None

    def get_thumbnail_url(self, obj):
        # Prefer product image
        if obj.image:
            return obj.image.url
        # Fallback: first photo from an ACTIVE listing for this product
        try:
            listing = Listing.objects.filter(unit__product=obj, state=ListingStates.ACTIVE).order_by('-created_at').first()
            if listing and listing.photos:
                # listing.photos is a list of relative paths
                first = listing.photos[0]
                try:
                    return default_storage.url(first)
                except Exception:
                    return None
        except Exception:
            return None
        return None


class UnitEventSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source="actor.username", read_only=True)

    class Meta:
        model = UnitEvent
        fields = ["id", "type", "payload", "actor_name", "created_at"]


class ItemUnitSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    events = UnitEventSerializer(many=True, read_only=True)
    routing_recommendation = serializers.SerializerMethodField()

    class Meta:
        model = ItemUnit
        fields = [
            "id", "product", "state", "grade", "grade_confidence", "untouched",
            "est_value", "arrived_at_facility", "storage_cost_accrued",
            "events", "created_at", "routing_recommendation",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # The AI disposition recommendation is facility-only. Drop the field
        # entirely when the caller opts out — e.g. the public buyer-facing
        # Health Card — so buyers never see internal routing info.
        if self.context.get("include_routing") is False:
            self.fields.pop("routing_recommendation", None)

    def get_routing_recommendation(self, obj):
        try:
            from rerouting.services import recommendation_for

            return recommendation_for(obj)
        except Exception:
            return None
