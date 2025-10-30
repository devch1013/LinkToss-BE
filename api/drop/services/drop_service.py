from typing import List, Optional
from uuid import UUID

from django.db import transaction
from django.db.models import QuerySet

from api.deck.models.deck import Deck
from api.drop.models.drop import Drop
from api.drop.models.tag import Tag, TagDropMapping
from api.user.models.user import User
from common.utils.s3_utils import S3KeyPrefix, S3UploadUtil
from common.utils.web_scraper_utils import WebScraperUtil


class DropService:
    @classmethod
    def get_deck_drops(cls, deck_id: UUID, user: User) -> QuerySet[Drop]:
        """특정 deck의 drop 목록 조회"""
        return Drop.objects.filter(
            deck_id=deck_id, user=user, is_deleted=False
        ).prefetch_related("tag_drop_mappings__tag")

    @classmethod
    def get_drop_by_id(cls, drop_id: UUID, user: User) -> Optional[Drop]:
        """drop ID로 단일 조회"""
        try:
            return Drop.objects.prefetch_related("tag_drop_mappings__tag").get(
                id=drop_id, user=user, is_deleted=False
            )
        except Drop.DoesNotExist:
            return None

    @classmethod
    def search_drops(
        cls,
        user: User,
        query: Optional[str] = None,
        tag_names: Optional[List[str]] = None,
    ) -> QuerySet[Drop]:
        """drop 검색 (제목, 내용, 메모, 태그로 검색)"""
        drops = Drop.objects.filter(user=user, is_deleted=False)

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
            deck = Deck.objects.get(id=deck_id, user=user, is_deleted=False)
        except Deck.DoesNotExist:
            raise ValueError(f"Deck with id {deck_id} not found")

        # 웹페이지 메타데이터 가져오기
        favicon_url, screenshot_url, meta_image_url = (
            WebScraperUtil.fetch_page_metadata(url)
        )

        # 이미지 URL 처리 (data URI나 public URL이 아닌 경우 S3에 업로드)
        favicon_final_url = cls._process_image_url(
            favicon_url, drop_id=None, prefix=S3KeyPrefix.DROP_FAVICON
        )
        screenshot_final_url = cls._process_image_url(
            screenshot_url, drop_id=None, prefix=S3KeyPrefix.DROP_SCREENSHOT
        )
        meta_image_final_url = cls._process_image_url(
            meta_image_url, drop_id=None, prefix=S3KeyPrefix.DROP_META_IMAGE
        )

        drop = Drop.objects.create(
            user=user,
            deck=deck,
            title=title,
            url=url,
            content=content,
            memo=memo,
            favicon_url=favicon_final_url,
            screenshot_url=screenshot_final_url,
            meta_image_url=meta_image_final_url,
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
                deck = Deck.objects.get(id=deck_id, user=user, is_deleted=False)
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
            drop.tag_drop_mappings.filter(tag__is_deleted=False).values_list(
                "tag__name", flat=True
            )
        )

    @classmethod
    def get_recent_drops(cls, user: User, limit: int = 10) -> QuerySet[Drop]:
        """사용자의 최근 drop 목록 조회 (시간순)"""
        return (
            Drop.objects.filter(user=user, is_deleted=False)
            .prefetch_related("tag_drop_mappings__tag")
            .order_by("-created_at")[:limit]
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

    @classmethod
    def _process_image_url(
        cls,
        image_url: Optional[str],
        drop_id: Optional[UUID],
        prefix: S3KeyPrefix,
    ) -> Optional[str]:
        """
        이미지 URL을 처리합니다.
        - data URI나 public URL은 그대로 반환
        - 그 외의 경우 이미지를 다운로드하여 S3에 업로드

        Args:
            image_url: 원본 이미지 URL
            drop_id: Drop ID (S3 키 생성용, None인 경우 임시 UUID 생성)
            prefix: S3 키 프리픽스

        Returns:
            최종 이미지 URL (S3 URL 또는 원본 URL)
        """
        if not image_url:
            return None

        # data URI는 그대로 반환 (퍼블릭 URL)
        if WebScraperUtil.is_data_uri(image_url):
            return image_url

        # 일반 HTTP/HTTPS URL인 경우
        if image_url.startswith("http://") or image_url.startswith("https://"):
            # 이미지를 다운로드하여 S3에 업로드
            try:
                image_data = WebScraperUtil.download_image(image_url)
                if not image_data:
                    # 다운로드 실패시 원본 URL 반환
                    return image_url

                # S3에 업로드
                import uuid as uuid_module

                file_id = drop_id if drop_id else uuid_module.uuid4()

                # 확장자 추출
                from urllib.parse import urlparse
                import os

                parsed = urlparse(image_url)
                ext = os.path.splitext(parsed.path)[1]
                if not ext or len(ext) > 10:
                    ext = ".jpg"  # 기본 확장자

                file_name = f"image{ext}"
                content_type = WebScraperUtil.get_content_type_from_url(image_url)

                _, s3_url = S3UploadUtil.upload_bytes(
                    file_id=file_id,
                    file_data=image_data,
                    prefix=prefix,
                    file_name=file_name,
                    content_type=content_type,
                )

                # S3 업로드 성공시 S3 URL 반환, 실패시 원본 URL 반환
                return s3_url if s3_url else image_url

            except Exception as e:
                print(f"Error processing image URL {image_url}: {str(e)}")
                # 에러 발생시 원본 URL 반환
                return image_url

        # 그 외의 경우 원본 URL 반환
        return image_url
