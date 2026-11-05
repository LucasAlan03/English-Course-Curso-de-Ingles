import pytest

from app.routes import media
from app.routes.media import youtube_video_url

CANONICAL = "https://www.youtube.com/watch?v=3bh6Gb0oBN0"


@pytest.mark.parametrize("url", [
    "https://www.youtube.com/watch?v=3bh6Gb0oBN0",
    "https://m.youtube.com/watch?v=3bh6Gb0oBN0&t=10s",
    "https://youtu.be/3bh6Gb0oBN0?si=abc",
    "https://www.youtube.com/shorts/3bh6Gb0oBN0",
    "youtube.com/watch?feature=share&v=3bh6Gb0oBN0",
])
def test_youtube_shapes_map_to_the_canonical_url(url):
    assert youtube_video_url(url) == CANONICAL


@pytest.mark.parametrize("url", ["https://vimeo.com/123", "not a url", "", "https://www.youtube.com/"])
def test_other_urls_are_not_youtube(url):
    assert youtube_video_url(url) is None


def test_non_youtube_url_returns_null_without_network(app_client, monkeypatch):
    calls = []
    monkeypatch.setattr(media, "fetch_oembed", lambda url: calls.append(url) or {"title": "x"})
    r = app_client.get("/media/youtube-title", params={"url": "https://vimeo.com/1"})
    assert r.json() == {"title": None} and calls == []


def test_network_error_returns_null(app_client, monkeypatch):
    def boom(url):
        raise OSError("offline")

    monkeypatch.setattr(media, "fetch_oembed", boom)
    assert app_client.get("/media/youtube-title", params={"url": CANONICAL}).json() == {"title": None}


def test_title_is_returned(app_client, monkeypatch):
    seen = []
    monkeypatch.setattr(media, "fetch_oembed", lambda url: seen.append(url) or {"title": "How I Went From Zero"})
    r = app_client.get("/media/youtube-title", params={"url": "https://youtu.be/3bh6Gb0oBN0"})
    assert r.json() == {"title": "How I Went From Zero"} and seen == [CANONICAL]
