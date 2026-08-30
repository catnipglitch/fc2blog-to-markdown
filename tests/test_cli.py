from pathlib import Path

from fc2md.__main__ import main

SAMPLE = str(Path(__file__).parent.parent / "sample" / "sample-fc2-export.txt")


def _run_convert(tmp_path, *extra):
    assert main(["convert", SAMPLE, "-o", str(tmp_path), *extra]) == 0
    return sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*.md"))


def test_convert_writes_dated_files(tmp_path):
    files = _run_convert(tmp_path)
    assert files == [
        "posts/2009/2009-03-10-01.md",
        "posts/2009/2009-03-10-02.md",
        "posts/2009/2009-05-02-01.md",
        "posts/2010/2010-01-15-01.md",
        "posts/2010/2010-08-07-01.md",
        "posts/2011/2011-02-20-01.md",
    ]


def test_frontmatter_and_sections(tmp_path):
    _run_convert(tmp_path)
    text = (tmp_path / "posts/2010/2010-08-07-01.md").read_text(encoding="utf-8")
    assert text.startswith("---\n")
    assert 'title: "ブログ開設一周年"' in text
    assert "date: 2010-08-07T19:00:00" in text
    assert '  - "日常"' in text
    assert '  - "猫日記"' in text
    assert '  - "記念"' in text
    assert "<!--more-->" in text
    assert "## コメント" in text
    assert "**通りすがりの猫好き**（2010-08-08 10:12）" in text


def test_draft_flag(tmp_path):
    _run_convert(tmp_path)
    text = (tmp_path / "posts/2011/2011-02-20-01.md").read_text(encoding="utf-8")
    assert "draft: true" in text


def test_embed_note_and_script_removal(tmp_path):
    _run_convert(tmp_path)
    text = (tmp_path / "posts/2010/2010-01-15-01.md").read_text(encoding="utf-8")
    assert "> [埋め込みコンテンツ: http://video.example.jp/embed.do?movieId=123456" in text
    assert "analyzer99" not in text


def test_category_filter(tmp_path):
    files = _run_convert(tmp_path, "--category", "カメラ")
    assert files == [
        "posts/2009/2009-05-02-01.md",
        "posts/2011/2011-02-20-01.md",
    ]


def test_categories_command(capsys):
    assert main(["categories", SAMPLE]) == 0
    output = capsys.readouterr().out
    assert "猫日記" in output
    assert "カメラ" in output
