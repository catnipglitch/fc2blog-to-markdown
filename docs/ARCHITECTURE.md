# アーキテクチャ

`fc2md` のコード構成、FC2 エクスポート形式の仕様、実装上の制約をまとめます。コードを読む人と改修する人向けの資料です。使い方は [cli.md](cli.md) を参照してください。

## 開発環境

Python 3.13 と uv を使うプロジェクトです。依存は beautifulsoup4 / markdownify / requests、開発用の依存は pytest です。

```bash
uv sync                                                # 依存の取得
uv run pytest                                          # テスト実行
uv run pytest tests/test_converter.py -k table         # 単一テスト
uv run fc2md convert sample/sample-fc2-export.txt      # サンプルで変換（output/ へ出力）
uv run fc2md categories sample/sample-fc2-export.txt   # カテゴリー一覧
```

## 処理の流れ

`__main__.py`（CLI）から `parser.py` → `converter.py` → `writer.py` の順に処理します。`--download-images` を指定した場合だけ、`writer.py` の手前に `images.py` が入ります。

```text
エクスポート .txt
  └ parser.read_export_file / parse_export      Entry / Comment のリスト
      └ converter.convert_html                  (Markdown, FC2 画像 URL 一覧)
          └ images.download_images              URL → ローカルファイル名の対応表（任意）
              └ writer.build_markdown           frontmatter + 本文 + コメント
                  └ writer.write_markdown       posts/YYYY/YYYY-MM-DD-NN.md
```

画像の URL 書き換えは `__main__.py` の `_rewrite_image_urls` が担当します。Markdown を組み立てた後に、URL の文字列を相対パスへ置換します。

## モジュールの責務

| モジュール | 責務 |
| --- | --- |
| `src/fc2md/__main__.py` | CLI の引数解析、`convert` / `categories` サブコマンド、カテゴリー絞り込み、同じ日の連番付与、画像 URL の書き換え |
| `src/fc2md/parser.py` | Movable Type 形式を `Entry` / `Comment` dataclass へパース。ファイルの読み込みとエンコーディング判定 |
| `src/fc2md/converter.py` | 本文 HTML を Markdown へ変換し、本文中の FC2 画像 URL 一覧を返す |
| `src/fc2md/writer.py` | frontmatter の組み立て、コメントセクションの生成、出力パスの決定、ファイル書き出し |
| `src/fc2md/images.py` | 画像のダウンロードと、URL からローカルファイル名への対応付け |
| `run-convert.ps1` | 非エンジニア向けのラッパー。uv の自動インストール、`uv sync`、対話形式での `fc2md convert` 実行 |

## 実装上の判断

- エンコーディングは UTF-8 → CP932 → EUC-JP の順に試します。FC2 のエクスポートは通常 UTF-8 ですが、古い設定では他の 2 つになる場合があります
- 本文 HTML は、生の改行を `<br/>` へ置換してから BeautifulSoup と markdownify にかけます。FC2 の `CONVERT BREAKS: default` と同じ表示結果にするためです
- `table` / `tr` / `ul` / `ol` の直下に入った `<br>` は削除します。残すと Markdown のテーブルとリストの構造が壊れます
- frontmatter の YAML 文字列は `json.dumps` でエスケープします。JSON のダブルクォート文字列は YAML としても妥当なためです
- コメントの `EMAIL` と `IP` はパースしますが、出力には含めません

## 変更時に壊しやすい箇所

- `run-convert.ps1` は **UTF-8 BOM 付き**で保存します。BOM が無いと Windows PowerShell 5.1 で日本語が文字化けします。ヒアドキュメントによる全文の書き換えは BOM を落とすため、編集後に先頭 3 バイトが `EF BB BF` であることを確認してください
- `run-convert.ps1` は Windows PowerShell 5.1 互換で書きます。pwsh 専用の構文（`&&`、三項演算子）は使えません
- 非エンジニア向けのラッパーは .ps1 の 1 本だけとし、.bat ランチャーは置きません。実行ポリシーの回避は README が案内する `powershell -NoProfile -ExecutionPolicy Bypass -File` の 1 行で行います
- `writer.py` の `RELATIVE_IMAGES_PREFIX`（`../../images`）は、記事を `posts/YYYY/` に、画像を `images/` に置く出力構成が前提です。出力構成を変えるときは、この定数も合わせて変更します

## テストの方針

テストは `sample/sample-fc2-export.txt`（架空データ）を基準にしたプロパティ検証です。形式のエッジケースを増やすときは、サンプルへ架空の記事を追加します。実際のブログデータをテストフィクスチャへ持ち込むことは禁止です。

## FC2 エクスポート形式

FC2 ブログのエクスポートは、Movable Type 互換のテキスト形式 1 ファイルです。

- 記事間の区切りはハイフン 8 個の `--------`、セクション間の区切りはハイフン 5 個の `-----` です
- 記事の前半は `AUTHOR:` `TITLE:` `STATUS:` `PRIMARY CATEGORY:` `CATEGORY:` `DATE:` のヘッダー行です。`CATEGORY:` は複数行になることがあります
- 記事の後半は `BODY:` `EXTENDED BODY:` `EXCERPT:` `KEYWORDS:` `COMMENT:` のセクションです。`COMMENT:` は記事 1 件につき複数現れます
- `DATE:` は `MM/DD/YYYY HH:MM:SS` 形式です。ファイル名と frontmatter の日付はこの値を基準にします
- `STATUS:` が `Publish` 以外の記事は下書きです
- `CONVERT BREAKS: default` の記事の本文は、生の改行を持つ HTML 断片です
- `ALLOW COMMENTS` / `ALLOW PINGS` / `PING` は変換結果に影響しないため無視します
- 画像は本文に含まれず、`http://blog-imgs-NN.fc2.com/...` の URL として `<a>` タグと `<img>` タグに埋め込まれています。サムネイル（`...s.jpg`）から原寸（`...jpg`）へリンクする構造があります

`COMMENT:` セクションは、先頭に `AUTHOR:` `EMAIL:` `URL:` `IP:` `DATE:` の行が並び、それ以降が本文です。既知のキー以外の行が現れた時点で、本文の開始と判断します。
