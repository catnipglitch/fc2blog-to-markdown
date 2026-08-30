"""Movable Type 互換形式（FC2 エクスポート）のパーサ。"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

ENTRY_SEPARATOR = "--------"
SECTION_SEPARATOR = "-----"
# FC2 のエクスポートは通常 UTF-8 だが、古い設定では CP932 / EUC-JP の場合がある
ENCODINGS = ("utf-8", "cp932", "euc-jp")
DATE_FORMAT = "%m/%d/%Y %H:%M:%S"

_COMMENT_KEYS = {"AUTHOR", "EMAIL", "URL", "IP", "DATE"}


@dataclass
class Comment:
    author: str = ""
    email: str = ""
    url: str = ""
    ip: str = ""
    date: datetime | None = None
    body: str = ""


@dataclass
class Entry:
    author: str = ""
    title: str = ""
    status: str = "Publish"
    primary_category: str = ""
    categories: list[str] = field(default_factory=list)
    date: datetime | None = None
    body: str = ""
    extended_body: str = ""
    excerpt: str = ""
    keywords: list[str] = field(default_factory=list)
    comments: list[Comment] = field(default_factory=list)

    @property
    def is_draft(self) -> bool:
        return self.status.lower() != "publish"


def read_export_file(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ENCODINGS:
        try:
            text = data.decode(encoding)
        except UnicodeDecodeError:
            continue
        logger.debug("エンコーディング %s で読み込みました", encoding)
        return text
    raise ValueError(f"エンコーディングを判定できませんでした: {path}")


def parse_export(text: str) -> list[Entry]:
    entries: list[Entry] = []
    chunk: list[str] = []
    for line in text.replace("\r\n", "\n").split("\n"):
        if line == ENTRY_SEPARATOR:
            if any(l.strip() for l in chunk):
                entries.append(_parse_entry(chunk))
            chunk = []
        else:
            chunk.append(line)
    if any(l.strip() for l in chunk):
        entries.append(_parse_entry(chunk))
    return entries


def _parse_entry(lines: list[str]) -> Entry:
    entry = Entry()
    i = 0
    while i < len(lines) and lines[i] != SECTION_SEPARATOR:
        line = lines[i]
        i += 1
        if not line.strip():
            continue
        key, _, value = line.partition(":")
        key = key.strip().upper()
        value = value.strip()
        if key == "AUTHOR":
            entry.author = value
        elif key == "TITLE":
            entry.title = value
        elif key == "STATUS":
            entry.status = value
        elif key == "PRIMARY CATEGORY":
            entry.primary_category = value
        elif key == "CATEGORY":
            if value and value not in entry.categories:
                entry.categories.append(value)
        elif key == "DATE":
            entry.date = _parse_date(value)
        # ALLOW COMMENTS / CONVERT BREAKS / ALLOW PINGS は変換結果に影響しないため無視
    i += 1

    while i < len(lines):
        name_line = lines[i]
        i += 1
        if not name_line.strip():
            continue
        if not name_line.endswith(":"):
            logger.warning("不明な行をスキップしました: %r", name_line)
            continue
        name = name_line[:-1].upper()
        content_lines: list[str] = []
        while i < len(lines) and lines[i] != SECTION_SEPARATOR:
            content_lines.append(lines[i])
            i += 1
        i += 1
        content = "\n".join(content_lines).strip("\n")
        if name == "BODY":
            entry.body = content
        elif name == "EXTENDED BODY":
            entry.extended_body = content
        elif name == "EXCERPT":
            entry.excerpt = content
        elif name == "KEYWORDS":
            entry.keywords = [k.strip() for k in content.replace("、", ",").split(",") if k.strip()]
        elif name == "COMMENT":
            entry.comments.append(_parse_comment(content_lines))
        # PING などその他のセクションは保存対象外

    return entry


def _parse_comment(lines: list[str]) -> Comment:
    comment = Comment()
    body_start = 0
    for idx, line in enumerate(lines):
        key, sep, value = line.partition(":")
        key = key.strip().upper()
        if not sep or key not in _COMMENT_KEYS:
            break
        value = value.strip()
        if key == "AUTHOR":
            comment.author = value
        elif key == "EMAIL":
            comment.email = value
        elif key == "URL":
            comment.url = value
        elif key == "IP":
            comment.ip = value
        elif key == "DATE":
            comment.date = _parse_date(value)
        body_start = idx + 1
    comment.body = "\n".join(lines[body_start:]).strip("\n")
    return comment


def _parse_date(value: str) -> datetime | None:
    try:
        return datetime.strptime(value, DATE_FORMAT)
    except ValueError:
        logger.warning("日付を解釈できませんでした: %r", value)
        return None
