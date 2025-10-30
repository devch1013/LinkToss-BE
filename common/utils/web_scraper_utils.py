import io
import re
from typing import Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from PIL import Image


class WebScraperUtil:
    """웹페이지에서 메타 정보를 추출하는 유틸리티"""

    @classmethod
    def fetch_page_metadata(
        cls, url: str, timeout: int = 10
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        웹페이지에서 favicon, screenshot, meta 이미지 URL을 추출합니다.

        Args:
            url: 대상 웹페이지 URL
            timeout: 요청 타임아웃 (초)

        Returns:
            Tuple[Optional[str], Optional[str], Optional[str]]:
                (favicon_url, screenshot_url, meta_image_url)
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")
            parsed_url = urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

            # Favicon 추출
            favicon_url = cls._extract_favicon(soup, base_url, url)

            # Meta 이미지 추출 (og:image, twitter:image 등)
            meta_image_url = cls._extract_meta_image(soup, base_url)

            # Screenshot은 meta 이미지와 동일하게 처리
            # 실제 스크린샷을 찍으려면 Playwright나 Selenium이 필요하므로
            # 여기서는 meta 이미지를 대신 사용
            screenshot_url = meta_image_url

            return favicon_url, screenshot_url, meta_image_url

        except Exception as e:
            print(f"Error fetching metadata from {url}: {str(e)}")
            return None, None, None

    @classmethod
    def _extract_favicon(
        cls, soup: BeautifulSoup, base_url: str, page_url: str
    ) -> Optional[str]:
        """HTML에서 favicon URL을 추출합니다."""
        # <link rel="icon" ...> 또는 <link rel="shortcut icon" ...>
        favicon_link = soup.find(
            "link", rel=lambda x: x and ("icon" in x.lower() if isinstance(x, str) else any("icon" in r.lower() for r in x))
        )

        if favicon_link and favicon_link.get("href"):
            href = favicon_link["href"]
            # 절대 URL로 변환
            if href.startswith("data:"):
                # data URI는 그대로 반환 (퍼블릭 URL)
                return href
            elif href.startswith("//"):
                parsed = urlparse(page_url)
                return f"{parsed.scheme}:{href}"
            elif href.startswith("http"):
                return href
            else:
                return urljoin(base_url, href)

        # 기본 favicon 경로 시도
        default_favicon = f"{base_url}/favicon.ico"
        try:
            response = requests.head(default_favicon, timeout=5)
            if response.status_code == 200:
                return default_favicon
        except Exception:
            pass

        return None

    @classmethod
    def _extract_meta_image(cls, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """HTML에서 meta 이미지 URL을 추출합니다 (og:image, twitter:image 등)."""
        # Open Graph 이미지
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            return cls._normalize_image_url(og_image["content"], base_url)

        # Twitter 카드 이미지
        twitter_image = soup.find("meta", attrs={"name": "twitter:image"})
        if twitter_image and twitter_image.get("content"):
            return cls._normalize_image_url(twitter_image["content"], base_url)

        # 일반 meta 이미지
        meta_image = soup.find("meta", attrs={"name": "image"})
        if meta_image and meta_image.get("content"):
            return cls._normalize_image_url(meta_image["content"], base_url)

        return None

    @classmethod
    def _normalize_image_url(cls, url: str, base_url: str) -> str:
        """이미지 URL을 절대 URL로 정규화합니다."""
        if url.startswith("data:"):
            return url
        elif url.startswith("//"):
            return f"https:{url}"
        elif url.startswith("http"):
            return url
        else:
            return urljoin(base_url, url)

    @classmethod
    def is_data_uri(cls, url: Optional[str]) -> bool:
        """URL이 data URI 형태인지 확인합니다."""
        return url is not None and url.startswith("data:")

    @classmethod
    def download_image(cls, url: str, timeout: int = 10) -> Optional[bytes]:
        """
        이미지 URL에서 이미지 데이터를 다운로드합니다.

        Args:
            url: 이미지 URL
            timeout: 요청 타임아웃 (초)

        Returns:
            Optional[bytes]: 이미지 바이트 데이터, 실패시 None
        """
        try:
            if cls.is_data_uri(url):
                # data URI는 이미 인코딩된 데이터이므로 다운로드 불필요
                return None

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()

            # 이미지인지 검증
            content_type = response.headers.get("content-type", "")
            if not content_type.startswith("image/"):
                print(f"URL is not an image: {url} (content-type: {content_type})")
                return None

            return response.content

        except Exception as e:
            print(f"Error downloading image from {url}: {str(e)}")
            return None

    @classmethod
    def get_content_type_from_url(cls, url: str) -> str:
        """URL에서 Content-Type을 추출하거나 확장자로 추정합니다."""
        # 확장자로 추정
        if url.lower().endswith(".png"):
            return "image/png"
        elif url.lower().endswith(".jpg") or url.lower().endswith(".jpeg"):
            return "image/jpeg"
        elif url.lower().endswith(".gif"):
            return "image/gif"
        elif url.lower().endswith(".webp"):
            return "image/webp"
        elif url.lower().endswith(".svg"):
            return "image/svg+xml"
        elif url.lower().endswith(".ico"):
            return "image/x-icon"

        return "image/jpeg"  # 기본값
