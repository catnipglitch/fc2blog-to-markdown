# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクトのゴール

FC2 ブログからエクスポートしたファイルを日付別の Markdown へ変換し、Astro などの別ブログシステムへ移転しやすくするツール。

- 目的: FC2 ブログのクローズに向けた記事のバックアップと、一部カテゴリの
  Astro 等への移転準備（移転そのものはスコープ外）
- 出力は移転先（Astro Content Collections 等）でそのまま使える形を目標にする:
  日付ベースのファイル名・ディレクトリ構成と、`title` / `date` / `tags` などの
  YAML frontmatter を持つ .md ファイル
- カテゴリによる絞り込み（一部カテゴリだけ移転）を想定した設計にする
- 最終的に GitHub でツールとして公開する。非エンジニアでも実行しやすい形を目指す

## 最重要の制約（秘匿データ）

- `tmp/fc2blog-data.txt` はユーザーのテストデータ。
  **絶対に GitHub（コミット・PR・サンプル・テストフィクスチャ）へ含めてはならない**
- 実データの中身（記事タイトル・画像 URL・コメント投稿者）を、
  ドキュメント・コミットメッセージ・Issue へ引用してはならない
- 開発は同一形式で自作したサンプルテキスト（架空の記事）を中心に行う。
  実データでの変換はユーザー自身が実行する
- `tmp/` 全体を .gitignore で除外すること

## 作業前に読むドキュメント

技術情報は docs/ に置いてある。README はツールを使う人（非エンジニア）向けの入口であり、
技術的な詳細を README へ書き戻さない。

- コード構成・処理の流れ・FC2 エクスポート形式の仕様 → [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- CLI の仕様・出力ファイルの形式・開発用コマンド → [docs/cli.md](docs/cli.md) と
  [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **`run-convert.ps1` を編集する前に、docs/ARCHITECTURE.md の「変更時に壊しやすい箇所」を必ず読む**
  （UTF-8 BOM 付きで保存する・Windows PowerShell 5.1 互換で書く。破ると日本語が文字化けする）
