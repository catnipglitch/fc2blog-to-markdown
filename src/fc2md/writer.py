"""frontmatter 付き Markdown ファイルの組み立てと書き出し。"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from .parser import Comment, Entry

logger = logging.getLogger(__name__)

POSTS_DIR = "posts"
IMAGES_DIR = "images"
# 出力構成は output/posts/YYYY/*.md と output/images/ で固定のため、
# 記事から見た画像ディレクトリへの相対パスは常に 2 階層上になる
RELATIVE_IMAGES_PREFIX = f"../../{IMAGES_DIR}"
UNDATED_DIR = "unknown"


def build_markdown(entry: Entry, body_md: str, extended_md: str = "") -> str:
    parts = [_frontmatter(entry)]
    if body_md:
        parts.append(body_md)
    if extended_md:
        parts.append("<!--more-->")
        parts.append(extended_md)
    if entry.comments:
        parts.append(_comments_section(entry.comments))
    return "\n\n".join(parts) + "\n"


def output_path(entry: Entry, out_dir: Path, seq: int) -> Path:
    if entry.date is None:
        return out_dir / POSTS_DIR / UNDATED_DIR / f"undated-{seq:02d}.md"
    return out_dir / POSTS_DIR / f"{entry.date:%Y}" / f"{entry.date:%Y-%m-%d}-{seq:02d}.md"


def write_markdown(path: Path, markdown: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown, encoding="utf-8", newline="\n")
    logger.info("書き出し: %s", path)


def _yaml_str(value: str) -> str:
    # JSON のダブルクォート文字列は YAML としても妥当なので、エスケープを json に任せる
    return json.dumps(value, ensure_ascii=False)


def _frontmatter(entry: Entry) -> str:
    lines = ["---", f"title: {_yaml_str(entry.title)}"]
    if entry.date is not None:
        lines.append(f"date: {entry.date.isoformat()}")
    categories = entry.categories or ([entry.primary_category] if entry.primary_category else [])
    if categories:
        lines.append("categories:")
        lines.extend(f"  - {_yaml_str(c)}" for c in categories)
    if entry.keywords:
        lines.append("tags:")
        lines.extend(f"  - {_yaml_str(k)}" for k in entry.keywords)
    if entry.is_draft:
        lines.append("draft: true")
    lines.append("---")
    return "\n".join(lines)


def _comments_section(comments: list[Comment]) -> str:
    lines = ["## コメント"]
    for comment in comments:
        author = comment.author or "（名無し）"
        heading = f"**{author}**"
        if comment.date is not None:
            heading += f"（{comment.date:%Y-%m-%d %H:%M}）"
        lines.extend(["", heading, "", _with_hard_breaks(comment.body)])
    return "\n".join(lines)


def _with_hard_breaks(text: str) -> str:
    """本文と同様に、コメント内の改行も Markdown の強制改行（行末 2 スペース）にする。"""
    lines = text.split("\n")
    result = []
    for idx, line in enumerate(lines):
        has_next_text = idx + 1 < len(lines) and lines[idx + 1].strip()
        result.append(f"{line}  " if line.strip() and has_next_text else line)
    return "\n".join(result)
