"""記事本文の HTML を Markdown へ変換する。"""

from __future__ import annotations

import logging
import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from markdownify import MarkdownConverter

logger = logging.getLogger(__name__)

FC2_IMAGE_HOST_RE = re.compile(r"^blog-imgs-\d+\.fc2\.com$")
IMAGE_EXT_RE = re.compile(r"\.(jpe?g|png|gif|bmp|webp)$", re.IGNORECASE)
REMOVE_TAGS = ("script", "noscript", "style")
EMBED_TAGS = ("iframe", "object", "embed")
# <br> が入ると Markdown のテーブル・リスト構造が壊れる親要素
_NO_BR_PARENTS = {"table", "tbody", "thead", "tfoot", "tr", "ul", "ol"}


def convert_html(html: str) -> tuple[str, list[str]]:
    """HTML を Markdown に変換し、本文中の FC2 画像 URL 一覧も返す。"""
    if not html.strip():
        return "", []

    # CONVERT BREAKS 相当: エクスポート内の生の改行は表示上 <br> として扱われる
    normalized = html.replace("\r\n", "\n").replace("\n", "<br/>")
    soup = BeautifulSoup(normalized, "html.parser")

    for tag_name in REMOVE_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    for br in soup.find_all("br"):
        if br.parent is not None and br.parent.name in _NO_BR_PARENTS:
            br.decompose()

    _replace_embeds(soup)
    _unwrap_image_links(soup)
    _promote_table_headers(soup)
    image_urls = _collect_fc2_image_urls(soup)

    markdown = _Converter(
        heading_style="ATX",
        bullets="-",
        escape_asterisks=False,
        escape_underscores=False,
        escape_misc=False,
    ).convert_soup(soup)
    return _tidy(markdown), image_urls


class _Converter(MarkdownConverter):
    pass


def _replace_embeds(soup: BeautifulSoup) -> None:
    """死んでいる可能性の高い埋め込み (iframe/object/embed) を注記へ置換する。"""
    for tag in soup.find_all(EMBED_TAGS):
        if tag.parent is None:
            # 先に処理した object の内側にあった embed など、すでに切り離されたタグ
            continue
        url = _embed_url(tag)
        note = soup.new_tag("blockquote")
        note.string = f"[埋め込みコンテンツ: {url}]" if url else "[埋め込みコンテンツ]"
        tag.replace_with(note)


def _embed_url(tag) -> str:
    url = tag.get("src") or tag.get("data") or ""
    if not url and tag.name == "object":
        inner = tag.find("embed")
        if inner is not None:
            url = inner.get("src") or ""
        if not url:
            movie = tag.find("param", attrs={"name": "movie"})
            if movie is not None:
                url = movie.get("value") or ""
    return url


def _unwrap_image_links(soup: BeautifulSoup) -> None:
    """<a href="原寸"><img src="サムネ"></a> を原寸画像の <img> に置き換える。"""
    for anchor in soup.find_all("a"):
        href = anchor.get("href") or ""
        img = anchor.find("img")
        if img is None or not IMAGE_EXT_RE.search(urlparse(href).path):
            continue
        img["src"] = href
        anchor.replace_with(img)


def _promote_table_headers(soup: BeautifulSoup) -> None:
    """th を持たないテーブルの先頭行を th 化し、GFM テーブルのヘッダ行にする。"""
    for table in soup.find_all("table"):
        if table.find("th") is not None:
            continue
        first_row = table.find("tr")
        if first_row is None:
            continue
        for cell in first_row.find_all("td", recursive=False):
            cell.name = "th"


def _collect_fc2_image_urls(soup: BeautifulSoup) -> list[str]:
    urls: list[str] = []
    for img in soup.find_all("img"):
        src = img.get("src") or ""
        host = urlparse(src).hostname or ""
        if FC2_IMAGE_HOST_RE.match(host) and src not in urls:
            urls.append(src)
    return urls


def _tidy(markdown: str) -> str:
    """空白だけの行を空行に正規化し、連続空行と不要な強制改行を整理する。"""
    lines = [line if line.strip() else "" for line in markdown.split("\n")]

    collapsed: list[str] = []
    for line in lines:
        if line == "" and collapsed and collapsed[-1] == "":
            continue
        collapsed.append(line)

    result: list[str] = []
    for idx, line in enumerate(collapsed):
        next_line = collapsed[idx + 1] if idx + 1 < len(collapsed) else ""
        if line.endswith("  ") and next_line == "":
            # 段落末尾の強制改行 ("  ") は空行が続くなら不要
            line = line.rstrip()
        result.append(line)
    return "\n".join(result).strip("\n")
