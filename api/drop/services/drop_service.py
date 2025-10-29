from typing import List, Optional
from uuid import UUID

from django.db import transaction
from django.db.models import QuerySet

from api.deck.models.deck import Deck
from api.drop.models.drop import Drop
from api.drop.models.tag import Tag, TagDropMapping
from api.user.models.user import User


class DropService:
    @classmethod
    def get_deck_drops(cls, deck_id: UUID, user: User) -> QuerySet[Drop]:
        """특정 deck의 drop 목록 조회"""
        return Drop.objects.filter(
            deck_id=deck_id, user=user, deleted_at__isnull=True
        ).prefetch_related("tag_drop_mappings__tag")

    @classmethod
    def get_drop_by_id(cls, drop_id: UUID, user: User) -> Optional[Drop]:
        """drop ID로 단일 조회"""
        try:
            return Drop.objects.prefetch_related("tag_drop_mappings__tag").get(
                id=drop_id, user=user, deleted_at__isnull=True
            )
        except Drop.DoesNotExist:
            return None

    @classmethod
    def search_drops(
        cls, user: User, query: Optional[str] = None, tag_names: Optional[List[str]] = None
    ) -> QuerySet[Drop]:
        """drop 검색 (제목, 내용, 메모, 태그로 검색)"""
        drops = Drop.objects.filter(user=user, deleted_at__isnull=True)

        if query:
            from django.db.models import Q

            drops = drops.filter(
                Q(title__icontains=query)
                | Q(content__icontains=query)
                | Q(memo__icontains=query)
            )

        if tag_names:
            # 태그로 필터링
            for tag_name in tag_names:
                drops = drops.filter(
                    tag_drop_mappings__tag__name__iexact=tag_name
                ).distinct()

        return drops.prefetch_related("tag_drop_mappings__tag")

    @classmethod
    @transaction.atomic
    def create_drop(
        cls,
        user: User,
        deck_id: UUID,
        title: str,
        url: str,
        content: Optional[str] = None,
        memo: Optional[str] = None,
        tag_names: Optional[List[str]] = None,
    ) -> Drop:
        """새로운 drop 생성 (태그 포함)"""
        # deck 존재 확인
        try:
            deck = Deck.objects.get(id=deck_id, user=user, deleted_at__isnull=True)
        except Deck.DoesNotExist:
            raise ValueError(f"Deck with id {deck_id} not found")

        drop = Drop.objects.create(
            user=user,
            deck=deck,
            title=title,
            url=url,
            content=content,
            memo=memo,
        )

        # 태그 처리
        if tag_names:
            cls._attach_tags(drop, tag_names)

        return drop

    @classmethod
    @transaction.atomic
    def update_drop(
        cls,
        drop_id: UUID,
        user: User,
        title: Optional[str] = None,
        content: Optional[str] = None,
        url: Optional[str] = None,
        memo: Optional[str] = None,
        deck_id: Optional[UUID] = None,
        tag_names: Optional[List[str]] = None,
    ) -> Optional[Drop]:
        """drop 수정"""
        drop = cls.get_drop_by_id(drop_id, user)
        if not drop:
            return None

        if title is not None:
            drop.title = title
        if content is not None:
            drop.content = content
        if url is not None:
            drop.url = url
        if memo is not None:
            drop.memo = memo

        # deck 변경
        if deck_id is not None:
            try:
                deck = Deck.objects.get(id=deck_id, user=user, deleted_at__isnull=True)
                drop.deck = deck
            except Deck.DoesNotExist:
                raise ValueError(f"Deck with id {deck_id} not found")

        drop.save()

        # 태그 업데이트 (기존 태그 모두 삭제 후 재생성)
        if tag_names is not None:
            TagDropMapping.objects.filter(drop=drop).delete()
            cls._attach_tags(drop, tag_names)

        return drop

    @classmethod
    @transaction.atomic
    def delete_drop(cls, drop_id: UUID, user: User) -> bool:
        """drop soft delete"""
        drop = cls.get_drop_by_id(drop_id, user)
        if not drop:
            return False

        drop.delete()  # SoftDeleteModel의 delete 사용
        return True

    @classmethod
    def get_drop_tags(cls, drop: Drop) -> List[str]:
        """drop의 태그 목록 조회"""
        return list(
            drop.tag_drop_mappings.filter(tag__deleted_at__isnull=True).values_list(
                "tag__name", flat=True
            )
        )

    # Internal helper methods

    @classmethod
    def _attach_tags(cls, drop: Drop, tag_names: List[str]):
        """drop에 태그 연결 (없으면 생성)"""
        for tag_name in tag_names:
            tag_name = tag_name.strip()
            if not tag_name:
                continue

            # 태그 가져오기 또는 생성
            tag, _ = Tag.objects.get_or_create(
                name=tag_name, defaults={"name": tag_name}
            )

            # 매핑 생성 (중복 방지)
            TagDropMapping.objects.get_or_create(tag=tag, drop=drop)
