from typing import Optional
from uuid import UUID

from django.db import transaction
from django.db.models import QuerySet

from api.deck.models.deck import Deck
from api.user.models.user import User


class DeckService:
    @classmethod
    def get_user_decks(
        cls, user: User, parent: Optional[Deck] = None
    ) -> QuerySet[Deck]:
        """사용자의 deck 목록 조회 (특정 parent의 children만)"""
        return Deck.objects.filter(user=user, parent=parent, deleted_at__isnull=True)

    @classmethod
    def get_deck_by_id(cls, deck_id: UUID, user: User) -> Optional[Deck]:
        """deck ID로 단일 조회"""
        try:
            return Deck.objects.get(id=deck_id, user=user, deleted_at__isnull=True)
        except Deck.DoesNotExist:
            return None

    @classmethod
    @transaction.atomic
    def create_deck(
        cls,
        user: User,
        name: str,
        description: Optional[str] = None,
        color_hex: str = "#000000",
        parent_id: Optional[UUID] = None,
        is_public: bool = False,
    ) -> Deck:
        """새로운 deck 생성"""
        parent = None
        if parent_id:
            parent = cls._get_parent_deck(parent_id, user)

        # 같은 parent 아래 deck 개수로 order 설정
        order = cls._get_next_order(user, parent)

        deck = Deck.objects.create(
            user=user,
            name=name,
            description=description,
            color_hex=color_hex,
            parent=parent,
            order=order,
            is_public=is_public,
        )
        return deck

    @classmethod
    @transaction.atomic
    def update_deck(
        cls,
        deck_id: UUID,
        user: User,
        name: Optional[str] = None,
        description: Optional[str] = None,
        color_hex: Optional[str] = None,
        parent_id: Optional[UUID] = None,
        order: Optional[int] = None,
        is_public: Optional[bool] = None,
    ) -> Optional[Deck]:
        """deck 수정"""
        deck = cls.get_deck_by_id(deck_id, user)
        if not deck:
            return None

        if name is not None:
            deck.name = name
        if description is not None:
            deck.description = description
        if color_hex is not None:
            deck.color_hex = color_hex
        if is_public is not None:
            deck.is_public = is_public
        if order is not None:
            deck.order = order

        # parent 변경 처리
        if parent_id is not None:
            if str(deck.id) == str(parent_id):
                raise ValueError("Deck cannot be its own parent")

            new_parent = None
            if parent_id:
                new_parent = cls._get_parent_deck(parent_id, user)
                # 순환 참조 체크
                cls._check_circular_reference(deck, new_parent)

            deck.parent = new_parent

        deck.save()
        return deck

    @classmethod
    @transaction.atomic
    def delete_deck(cls, deck_id: UUID, user: User) -> bool:
        """deck soft delete (children도 함께 삭제)"""
        deck = cls.get_deck_by_id(deck_id, user)
        if not deck:
            return False

        cls._soft_delete_recursive(deck)
        return True

    @classmethod
    def get_deck_tree(cls, user: User, deck_id: Optional[UUID] = None) -> QuerySet:
        """deck의 하위 트리 구조 조회"""
        if deck_id:
            deck = cls.get_deck_by_id(deck_id, user)
            if not deck:
                return Deck.objects.none()
            return Deck.objects.filter(
                user=user, parent=deck, deleted_at__isnull=True
            )
        else:
            # root decks (parent가 None인 것들)
            return Deck.objects.filter(
                user=user, parent__isnull=True, deleted_at__isnull=True
            )

    # Internal helper methods

    @classmethod
    def _get_parent_deck(cls, parent_id: UUID, user: User) -> Deck:
        """parent deck 조회 (검증 포함)"""
        parent = cls.get_deck_by_id(parent_id, user)
        if not parent:
            raise ValueError(f"Parent deck with id {parent_id} not found")
        return parent

    @classmethod
    def _get_next_order(cls, user: User, parent: Optional[Deck]) -> int:
        """다음 order 값 계산"""
        last_deck = (
            Deck.objects.filter(user=user, parent=parent, deleted_at__isnull=True)
            .order_by("-order")
            .first()
        )
        return (last_deck.order + 1) if last_deck else 0

    @classmethod
    def _check_circular_reference(cls, deck: Deck, new_parent: Deck):
        """순환 참조 체크"""
        current = new_parent
        while current:
            if current.id == deck.id:
                raise ValueError("Circular reference detected")
            current = current.parent

    @classmethod
    def _soft_delete_recursive(cls, deck: Deck):
        """deck과 하위 children을 재귀적으로 soft delete"""
        children = Deck.objects.filter(parent=deck, deleted_at__isnull=True)
        for child in children:
            cls._soft_delete_recursive(child)

        deck.delete()  # SoftDeleteModel의 delete 사용
