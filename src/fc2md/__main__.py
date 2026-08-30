"""fc2md CLI エントリーポイント。"""

from __future__ import annotations

import argparse
import logging
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

from . import converter, images, parser, writer

logger = logging.getLogger("fc2md")


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "convert":
            return _cmd_convert(args)
        if args.command == "categories":
            return _cmd_categories(args)
    except (OSError, ValueError) as exc:
        logger.error("エラー: %s", exc)
        return 1
    return 1


def _build_parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="fc2md",
        description="FC2ブログのエクスポートファイルを日付別のMarkdownに変換します。",
    )
    sub = root.add_subparsers(dest="command", required=True)

    convert = sub.add_parser("convert", help="エクスポートファイルをMarkdownへ変換する")
    convert.add_argument("input", type=Path, help="FC2からエクスポートしたテキストファイル")
    convert.add_argument(
        "-o", "--output", type=Path, default=Path("output"), help="出力先ディレクトリ（既定: output）"
    )
    convert.add_argument(
        "--category",
        action="append",
        metavar="NAME",
        help="このカテゴリの記事だけ変換する（複数指定可・完全一致）",
    )
    convert.add_argument(
        "--download-images",
        action="store_true",
        help="本文中のFC2画像をダウンロードし、参照をローカルパスへ書き換える",
    )

    categories = sub.add_parser("categories", help="エクスポート内のカテゴリ一覧と記事数を表示する")
    categories.add_argument("input", type=Path, help="FC2からエクスポートしたテキストファイル")
    return root


def _cmd_convert(args: argparse.Namespace) -> int:
    entries = parser.parse_export(parser.read_export_file(args.input))
    logger.info("%d 件の記事を読み込みました", len(entries))

    if args.category:
        wanted = set(args.category)
        entries = [e for e in entries if wanted & set(e.categories or [e.primary_category])]
        logger.info("カテゴリ絞り込み後: %d 件", len(entries))

    entries.sort(key=lambda e: e.date or datetime.min)

    converted: list[tuple[Path, str]] = []
    image_urls: list[str] = []
    seq_by_day: Counter[str] = Counter()
    for entry in entries:
        body_md, body_urls = converter.convert_html(entry.body)
        extended_md, extended_urls = converter.convert_html(entry.extended_body)
        markdown = writer.build_markdown(entry, body_md, extended_md)
        for url in body_urls + extended_urls:
            if url not in image_urls:
                image_urls.append(url)
        day = f"{entry.date:%Y-%m-%d}" if entry.date else "undated"
        seq_by_day[day] += 1
        converted.append((writer.output_path(entry, args.output, seq_by_day[day]), markdown))

    failed_urls: list[str] = []
    if args.download_images and image_urls:
        logger.info("%d 件の画像をダウンロードします", len(image_urls))
        mapping, failed_urls = images.download_images(image_urls, args.output / writer.IMAGES_DIR)
        converted = [
            (path, _rewrite_image_urls(markdown, mapping)) for path, markdown in converted
        ]

    for path, markdown in converted:
        writer.write_markdown(path, markdown)

    logger.info("完了: %d 件の記事を %s に書き出しました", len(converted), args.output)
    if failed_urls:
        logger.warning("ダウンロードに失敗した画像が %d 件あります:", len(failed_urls))
        for url in failed_urls:
            logger.warning("  %s", url)
    return 0


def _rewrite_image_urls(markdown: str, mapping: dict[str, str]) -> str:
    for url, name in mapping.items():
        markdown = markdown.replace(url, f"{writer.RELATIVE_IMAGES_PREFIX}/{name}")
    return markdown


def _cmd_categories(args: argparse.Namespace) -> int:
    entries = parser.parse_export(parser.read_export_file(args.input))
    counts: Counter[str] = Counter()
    for entry in entries:
        for category in entry.categories or [entry.primary_category]:
            if category:
                counts[category] += 1
    for category, count in counts.most_common():
        print(f"{count:4d}  {category}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
