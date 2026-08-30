from fc2md.images import _local_name


def test_local_name_uses_basename():
    assert _local_name("http://blog-imgs-99.fc2.com/s/a/m/sampleblog/tama.jpg", {}) == "tama.jpg"


def test_local_name_same_url_keeps_same_name():
    owner = {}
    url = "http://blog-imgs-99.fc2.com/s/a/m/sampleblog/tama.jpg"
    assert _local_name(url, owner) == _local_name(url, owner)


def test_local_name_collision_gets_hash_prefix():
    owner = {}
    first = _local_name("http://blog-imgs-1.fc2.com/a/b/c/blog1/tama.jpg", owner)
    second = _local_name("http://blog-imgs-2.fc2.com/x/y/z/blog2/tama.jpg", owner)
    assert first == "tama.jpg"
    assert second != "tama.jpg"
    assert second.endswith("-tama.jpg")
