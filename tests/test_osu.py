import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import httpx
import pytest

import osu


class ChunkedStream(httpx.SyncByteStream):
    def __init__(self, *chunks: str):
        self._chunks = [c.encode() for c in chunks]

    def __iter__(self):
        yield from self._chunks


class TestGetUserIdFromUsername:
    def test_returns_user_id(self, httpx_mock):
        id = 2
        username = "peppy"
        httpx_mock.add_response(
            method="HEAD",
            url=f"http://osu.ppy.sh/users/{username}",
            headers={"Location": f"http://osu.ppy.sh/users/{id}"},
        )
        assert osu.get_user_id_from_username(username) == id

    def test_raises_when_no_redirect(self, httpx_mock):
        username = "should not exist"
        httpx_mock.add_response(
            method="HEAD",
            url=f"http://osu.ppy.sh/users/{username}",
            status_code=404,
        )
        with pytest.raises(ValueError, match="redirect"):
            osu.get_user_id_from_username("should not exist")


class TestGetUsernameFromUserId:
    def test_returns_username(self, httpx_mock):
        id = 2
        username = "peppy"
        httpx_mock.add_response(
            url=f"http://osu.ppy.sh/users/{id}",
            text=(
                f"<html><head><title>{username}\u202c · player info\u202c | \u202c"
                " osu!</title></head></html>"
            ),
        )
        assert osu.get_username_from_user_id(id) == username

    def test_raises_when_no_title(self, httpx_mock):
        id = 99999999999
        httpx_mock.add_response(
            url=f"http://osu.ppy.sh/users/{id}",
            text="<html><head><title>osu!</title></head></html>",
            status_code=404,
        )
        with pytest.raises(ValueError, match="username"):
            osu.get_username_from_user_id(id)

    def test_handles_chunked_title(self, httpx_mock):
        httpx_mock.add_response(
            url="http://osu.ppy.sh/users/2",
            stream=ChunkedStream(
                "<titl", "e>pepp", "y\u202c · playe", "r info</ti", "tle>"
            ),
        )
        assert osu.get_username_from_user_id(2) == "peppy"
