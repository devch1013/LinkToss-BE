from rest_framework import serializers

from api.deck.serializers import DeckSerializer
from api.drop.serializers import DropSerializer


class DashboardOverviewSerializer(serializers.Serializer):
    """Dashboard 통계 정보 Serializer"""

    deck_count = serializers.IntegerField(help_text="전체 deck 개수")
    drop_count = serializers.IntegerField(help_text="전체 drop 개수")
    public_deck_count = serializers.IntegerField(help_text="공개 deck 개수")
    tag_count = serializers.IntegerField(help_text="사용한 고유 tag 개수")


class DashboardSerializer(serializers.Serializer):
    """Dashboard 전체 정보 Serializer"""

    overview = DashboardOverviewSerializer(help_text="통계 정보")
    recent_drops = DropSerializer(many=True, help_text="최근 drop 10개")
    frequent_decks = DeckSerializer(many=True, help_text="최근 조회한 deck 5개")
