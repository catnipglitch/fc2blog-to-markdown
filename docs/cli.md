# コマンドラインでの使い方

`run-convert.ps1` を使わず、コマンドで直接変換する方法をまとめます。macOS と Linux ではこの方法を使います。Windows でスクリプトから実行する手順は [README](../README.md) を参照してください。

## 準備

1 FC2 ブログの管理画面で [ツール] → [データのバックアップ] を開き、記事データをエクスポートしてテキストファイルとして保存します。

2 [uv](https://docs.astral.sh/uv/) をインストールします。Python 本体は uv が用意するため、個別にインストールする必要はありません。

```powershell
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3 このリポジトリを `git clone` するか、ZIP をダウンロードして展開します。

## 変換する

リポジトリのフォルダーで次を実行すると、`output/` に変換結果を書き出します。

```bash
uv run fc2md convert エクスポートファイル.txt
```

同梱のサンプルデータで動作を確認できます。

```bash
uv run fc2md convert sample/sample-fc2-export.txt
```

## カテゴリーを調べる

エクスポートファイルに含まれるカテゴリーと記事数を表示します。左が記事数、右がカテゴリー名です。

```bash
uv run fc2md categories エクスポートファイル.txt
```

## オプション

特定のカテゴリーだけを、画像のダウンロード付きで変換する例です。

```bash
uv run fc2md convert エクスポートファイル.txt -o output --category 猫日記 --download-images
```

| オプション | 説明 |
| --- | --- |
| `-o`, `--output` | 出力先ディレクトリー（既定: `output`） |
| `--category NAME` | 指定したカテゴリーの記事だけを変換します。複数指定でき、カテゴリー名は完全一致で判定します |
| `--download-images` | 本文中の FC2 画像をダウンロードし、参照をローカルパスへ書き換えます |

`--category` は記事の `CATEGORY:` 行と照合します。`CATEGORY:` 行を持たない記事は `PRIMARY CATEGORY:` の値と照合します。

## 出力されるファイル

```text
output/
├── posts/
│   ├── 2009/
│   │   └── 2009-03-10-01.md   # 日付 + 同じ日の連番
│   └── unknown/
│       └── undated-01.md      # DATE 行を読み取れなかった記事
└── images/                     # --download-images 指定時のみ
    └── tama.jpg
```

記事ファイルは `output/posts/<年>/<日付>-<連番>.md`、画像は `output/images/` に置きます。記事から画像への参照は `../../images/` で始まる相対パスです。この 2 つのフォルダーの位置関係を変えると、画像の参照が切れます。

ファイルの文字コードは UTF-8、改行コードは LF です。

## .md ファイルの中身

先頭に YAML frontmatter が付きます。

```markdown
---
title: "はじめまして、タマです。"
date: 2009-03-10T21:15:30
categories:
  - "猫日記"
tags:
  - "自己紹介"
draft: true
---
```

| 項目 | 内容 |
| --- | --- |
| `title` | `TITLE:` の値 |
| `date` | `DATE:` を ISO 8601 形式へ変換した値。日付を読み取れない記事では出力しません |
| `categories` | `CATEGORY:` の値。持たない記事では `PRIMARY CATEGORY:` の値 |
| `tags` | `KEYWORDS:` をカンマまたは読点で分割した値 |
| `draft` | `STATUS:` が `Publish` 以外の記事にだけ `true` を出力します |

frontmatter の後に本文が続きます。追記（`EXTENDED BODY:`）を持つ記事では、本文と追記の間に `<!--more-->` を挟みます。コメントが付いている記事では、末尾に `## コメント` 見出しで投稿者名・投稿日時・本文を出力します。コメント投稿者のメールアドレスと IP アドレスは出力しません。

本文の HTML は次のように変換します。

| 元の HTML | 変換後 |
| --- | --- |
| 生の改行 | Markdown の強制改行（行末の半角スペース 2 個） |
| サムネイル画像へのリンク | 原寸画像の `<img>` を展開した Markdown の画像記法 |
| `iframe` / `object` / `embed` | `> [埋め込みコンテンツ: URL]` の引用行 |
| `script` / `noscript` / `style` | 削除 |
| `th` を持たない表 | 先頭行をヘッダー行として GFM のテーブルへ変換 |

## 画像のダウンロード

`--download-images` を付けると、本文中の `blog-imgs-NN.fc2.com` にある画像を取得します。他のサーバーにある画像は取得せず、URL のまま残します。

- 取得先へ負荷をかけないよう、0.5 秒間隔で 1 枚ずつ取得します
- ファイル名は URL の末尾を使います。別々の URL でファイル名が重なる場合は、URL の SHA-1 の先頭 8 桁を前に付けます
- 同じ名前のファイルが `output/images/` に既にある場合は、ダウンロードを飛ばします。中断した変換をやり直しても、取得済みの画像は再取得しません
- 取得に失敗した URL は、実行の最後に一覧で表示します

ブログを削除すると FC2 上の画像も取得できなくなります。画像のダウンロードは、ブログを閉鎖する前に実行してください。

## 内部構造を知りたい場合

コードの構成と FC2 エクスポート形式の仕様は [ARCHITECTURE.md](ARCHITECTURE.md) にまとめています。
