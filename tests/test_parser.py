from datetime import datetime

from fc2md.parser import parse_export


def test_parses_all_entries(sample_text):
    entries = parse_export(sample_text)
    assert len(entries) == 6


def test_header_fields(sample_text):
    entry = parse_export(sample_text)[0]
    assert entry.author == "sampleuser"
    assert entry.title == "はじめまして、タマです。"
    assert entry.status == "Publish"
    assert entry.primary_category == "猫日記"
    assert entry.categories == ["猫日記"]
    assert entry.date == datetime(2009, 3, 10, 21, 15, 30)
    assert not entry.is_draft


def test_multiple_categories_and_keywords(sample_text):
    entry = parse_export(sample_text)[4]
    assert entry.title == "ブログ開設一周年"
    assert entry.categories == ["日常", "猫日記"]
    assert entry.keywords == ["記念", "雑記"]
    assert "ここからは追記です。" in entry.extended_body


def test_comments(sample_text):
    comments = parse_export(sample_text)[4].comments
    assert len(comments) == 2
    assert comments[0].author == "通りすがりの猫好き"
    assert comments[0].date == datetime(2010, 8, 8, 10, 12, 34)
    assert "一周年おめでとうございます！" in comments[0].body
    assert comments[1].url == "http://sampleblog.blog99.fc2.com/"


def test_draft_status(sample_text):
    entry = parse_export(sample_text)[5]
    assert entry.status == "Draft"
    assert entry.is_draft


def test_body_preserves_blank_lines(sample_text):
    entry = parse_export(sample_text)[1]
    assert "夕方の空がきれいだったので思わず撮影。\n\n明日は晴れるといいなぁ。" in entry.body
