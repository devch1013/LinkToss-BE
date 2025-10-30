from rest_framework import serializers

from api.deck.models.deck import Deck


class BreadcrumbSerializer(serializers.ModelSerializer):
    """Breadcrumb 정보용 Serializer"""

    class Meta:
        model = Deck
        fields = ["id", "name"]
