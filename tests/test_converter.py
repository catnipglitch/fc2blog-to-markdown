from fc2md.converter import convert_html


def test_thumbnail_link_becomes_full_size_image():
    html = (
        '<a href="http://blog-imgs-99.fc2.com/s/a/m/sampleblog/tama.jpg" target="_blank">'
        '<img src="http://blog-imgs-99.fc2.com/s/a/m/sampleblog/tamas.jpg" alt="タマの写真" /></a>'
    )
    markdown, urls = convert_html(html)
    assert markdown == "![タマの写真](http://blog-imgs-99.fc2.com/s/a/m/sampleblog/tama.jpg)"
    assert urls == ["http://blog-imgs-99.fc2.com/s/a/m/sampleblog/tama.jpg"]


def test_newlines_become_line_breaks_and_paragraphs():
    markdown, _ = convert_html("1行目\n2行目\n\n次の段落")
    assert markdown == "1行目  \n2行目\n\n次の段落"


def test_table_becomes_gfm_table():
    html = (
        "<table>\n<tr><td>項目</td><td>値</td></tr>\n"
        "<tr><td>重さ</td><td>280g</td></tr>\n</table>"
    )
    markdown, _ = convert_html(html)
    assert "| 項目 | 値 |" in markdown
    assert "| --- | --- |" in markdown
    assert "| 重さ | 280g |" in markdown
    assert "<table" not in markdown


def test_iframe_becomes_note():
    markdown, _ = convert_html('<iframe src="http://video.example.jp/embed?id=1"></iframe>')
    assert markdown == "> [埋め込みコンテンツ: http://video.example.jp/embed?id=1]"


def test_script_and_noscript_are_removed():
    html = (
        "本文です。\n"
        '<script type="text/javascript" src="http://analyzer99.example.com/a.js"></script>'
        '<noscript><img src="http://analyzer99.example.com/icon.php" alt="" /></noscript>'
    )
    markdown, urls = convert_html(html)
    assert "analyzer99" not in markdown
    assert markdown.startswith("本文です。")
    assert urls == []


def test_non_fc2_images_are_not_collected():
    markdown, urls = convert_html('<img src="http://example.com/pic.jpg" alt="外部画像" />')
    assert "![外部画像](http://example.com/pic.jpg)" in markdown
    assert urls == []


def test_empty_html():
    assert convert_html("") == ("", [])
