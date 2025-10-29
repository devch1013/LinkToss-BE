from typing import Any, Dict, List

from django.db.models import QuerySet

from api.deck.models.deck import Deck
from api.drop.models.drop import Drop
from api.drop.models.tag import Tag
from api.user.models.user import User


class DashboardService:
    @classmethod
    def get_user_dashboard(cls, user: User) -> Dict[str, Any]:
        """사용자의 대시보드 전체 정보 조회"""
        overview = cls._get_overview(user)
        recent_drops = cls._get_recent_drops(user, limit=10)
        frequent_decks = cls._get_frequent_decks(user, limit=5)

        return {
            "overview": overview,
            "recent_drops": recent_drops,
            "frequent_decks": frequent_decks,
        }

    @classmethod
    def _get_overview(cls, user: User) -> Dict[str, int]:
        """대시보드 통계 정보"""
        return {
            "deck_count": cls._get_deck_count(user),
            "drop_count": cls._get_drop_count(user),
            "public_deck_count": cls._get_public_deck_count(user),
            "tag_count": cls._get_tag_count(user),
        }

    @classmethod
    def _get_recent_drops(cls, user: User, limit: int = 10) -> QuerySet[Drop]:
        """최근 생성된 drop 목록"""
        return (
            Drop.objects.filter(user=user, deleted_at__isnull=True)
            .prefetch_related("tag_drop_mappings__tag")
            .order_by("-created_at")[:limit]
        )

    @classmethod
    def _get_frequent_decks(cls, user: User, limit: int = 5) -> QuerySet[Deck]:
        """최근 업데이트된 deck 목록 (최근 drop이 추가된 deck 기준)"""
        # 최근 업데이트된 deck ID 추출
        recent_deck_ids = (
            Drop.objects.filter(user=user, deleted_at__isnull=True)
            .values_list("deck_id", flat=True)
            .order_by("-updated_at")
            .distinct()[:limit]
        )

        # deck 조회 (최근 업데이트 순서 유지)
        decks = Deck.objects.filter(
            id__in=list(recent_deck_ids), deleted_at__isnull=True
        )

        # 원래 순서대로 정렬
        deck_dict = {deck.id: deck for deck in decks}
        return [deck_dict[deck_id] for deck_id in recent_deck_ids if deck_id in deck_dict]

    # Internal helper methods

    @classmethod
    def _get_deck_count(cls, user: User) -> int:
        """사용자의 전체 deck 개수"""
        return Deck.objects.filter(user=user, deleted_at__isnull=True).count()

    @classmethod
    def _get_drop_count(cls, user: User) -> int:
        """사용자의 전체 drop 개수"""
        return Drop.objects.filter(user=user, deleted_at__isnull=True).count()

    @classmethod
    def _get_public_deck_count(cls, user: User) -> int:
        """사용자의 공개 deck 개수"""
        return Deck.objects.filter(
            user=user, is_public=True, deleted_at__isnull=True
        ).count()

    @classmethod
    def _get_tag_count(cls, user: User) -> int:
        """사용자가 사용한 고유 tag 개수"""
        # 사용자의 drop들이 가지고 있는 고유한 태그 개수
        tag_ids = (
            Drop.objects.filter(user=user, deleted_at__isnull=True)
            .values_list("tag_drop_mappings__tag_id", flat=True)
            .distinct()
        )
        return Tag.objects.filter(id__in=tag_ids, deleted_at__isnull=True).count()
