"""FC2 画像のダウンロード。"""

from __future__ import annotations

import hashlib
import logging
import time
from pathlib import Path
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)

REQUEST_INTERVAL_SECONDS = 0.5
TIMEOUT_SECONDS = 30
USER_AGENT = "fc2blog-to-markdown/0.1"


def download_images(urls: list[str], images_dir: Path) -> tuple[dict[str, str], list[str]]:
    """画像をダウンロードし、(URL → ローカルファイル名の対応表, 失敗した URL 一覧) を返す。"""
    images_dir.mkdir(parents=True, exist_ok=True)
    mapping: dict[str, str] = {}
    failed: list[str] = []
    name_owner: dict[str, str] = {}
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT

    for url in urls:
        name = _local_name(url, name_owner)
        dest = images_dir / name
        if dest.exists():
            logger.info("スキップ（取得済み）: %s", name)
            mapping[url] = name
            continue
        try:
            response = session.get(url, timeout=TIMEOUT_SECONDS)
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("取得失敗: %s (%s)", url, exc)
            failed.append(url)
        else:
            dest.write_bytes(response.content)
            mapping[url] = name
            logger.info("保存: %s (%d bytes)", name, len(response.content))
        time.sleep(REQUEST_INTERVAL_SECONDS)

    return mapping, failed


def _local_name(url: str, name_owner: dict[str, str]) -> str:
    """URL からローカルファイル名を決める。別 URL と名前が衝突したらハッシュを前置する。"""
    name = Path(urlparse(url).path).name or "image"
    if name_owner.get(name, url) != url:
        digest = hashlib.sha1(url.encode()).hexdigest()[:8]
        name = f"{digest}-{name}"
    name_owner[name] = url
    return name
