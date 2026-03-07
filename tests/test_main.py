import json
import os
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Provide required env vars before importing modules that load config at import time
os.environ.setdefault("DISCORD_SERVER_ID", "test_server")
os.environ.setdefault("DISCORD_BOT_TOKEN", "test_token")

import pytest

import main


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_member(discord_id: str, nick: str | None = None, username: str = "user"):
    return {"user": {"id": discord_id, "username": username}, "nick": nick}


# ---------------------------------------------------------------------------
# load_save / save_data
# ---------------------------------------------------------------------------

class TestLoadSave:
    def test_returns_empty_list_when_file_missing(self, tmp_path):
        assert main.load_save(str(tmp_path / "missing.json")) == []

    def test_returns_data_from_file(self, tmp_path):
        data = [{"discord_id": "1", "osu_id": 42, "match": True}]
        path = tmp_path / "save.json"
        path.write_text(json.dumps(data))
        assert main.load_save(str(path)) == data


class TestSaveData:
    def test_writes_json(self, tmp_path):
        data = [{"discord_id": "1", "osu_id": 42, "match": True}]
        path = tmp_path / "save.json"
        main.save_data(str(path), data)
        assert json.loads(path.read_text()) == data


# ---------------------------------------------------------------------------
# find_user
# ---------------------------------------------------------------------------

class TestFindUser:
    def test_finds_existing_user(self):
        data = [{"discord_id": "1", "osu_id": 10, "match": True}]
        assert main.find_user(data, "1") == data[0]

    def test_returns_none_for_missing_user(self):
        data = [{"discord_id": "1", "osu_id": 10, "match": True}]
        assert main.find_user(data, "99") is None


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------

class TestMain:
    """Tests for the main() routine."""

    def _run_main(self, members, save_data, tmp_path):
        """Helper: patch dependencies and run main()."""
        db_path = str(tmp_path / "save.json")
        if save_data:
            (tmp_path / "save.json").write_text(json.dumps(save_data))

        mock_discord_api = MagicMock()
        mock_discord_api.iter_server_members.return_value = iter(members)

        with (
            patch("main.DiscordAPI", return_value=mock_discord_api),
            patch("main.config") as mock_config,
        ):
            mock_config.DISCORD_BOT_TOKEN = "token"
            mock_config.DISCORD_SERVER_ID = "server"
            mock_config.DB_PATH = db_path
            main.main()

        with open(db_path) as f:
            return json.load(f)

    # -- New user: match found in osu! -----------------------------------

    def test_new_user_with_osu_match_is_saved(self, tmp_path):
        members = [_make_member("100", nick="peppy")]
        with patch("main.osu.get_user_id_from_username", return_value=2):
            result = self._run_main(members, [], tmp_path)

        assert result == [{"discord_id": "100", "osu_id": 2, "match": True}]

    # -- New user: no match in osu! --------------------------------------

    def test_new_user_without_osu_match_is_not_saved(self, tmp_path):
        members = [_make_member("100", nick="nobody")]
        with patch(
            "main.osu.get_user_id_from_username", side_effect=ValueError("no match")
        ):
            result = self._run_main(members, [], tmp_path)

        assert result == []

    # -- New user: nick is None, falls back to username ------------------

    def test_new_user_no_nick_uses_username(self, tmp_path):
        members = [_make_member("100", nick=None, username="peppy")]
        with patch("main.osu.get_user_id_from_username", return_value=2) as mock_lookup:
            result = self._run_main(members, [], tmp_path)

        mock_lookup.assert_called_once_with("peppy")
        assert result[0]["osu_id"] == 2

    # -- Existing user, match=True, username still matches ---------------

    def test_existing_user_match_true_same_username_unchanged(self, tmp_path):
        save = [{"discord_id": "100", "osu_id": 2, "match": True}]
        members = [_make_member("100", nick="peppy")]
        with patch("main.osu.get_username_from_user_id", return_value="peppy"):
            result = self._run_main(members, save, tmp_path)

        assert result == [{"discord_id": "100", "osu_id": 2, "match": True}]

    # -- Existing user, match=True, username changed ---------------------

    def test_existing_user_match_true_different_username_sets_false(self, tmp_path):
        save = [{"discord_id": "100", "osu_id": 2, "match": True}]
        members = [_make_member("100", nick="new_name")]
        with patch("main.osu.get_username_from_user_id", return_value="peppy"):
            result = self._run_main(members, save, tmp_path)

        assert result == [{"discord_id": "100", "osu_id": 2, "match": False}]

    # -- Existing user, match=False, skip --------------------------------

    def test_existing_user_match_false_is_skipped(self, tmp_path):
        save = [{"discord_id": "100", "osu_id": 2, "match": False}]
        members = [_make_member("100", nick="some_nick")]
        with patch("main.osu.get_username_from_user_id") as mock_lookup:
            result = self._run_main(members, save, tmp_path)

        mock_lookup.assert_not_called()
        assert result == [{"discord_id": "100", "osu_id": 2, "match": False}]

    # -- Username comparison is case-insensitive -------------------------

    def test_username_comparison_is_case_insensitive(self, tmp_path):
        save = [{"discord_id": "100", "osu_id": 2, "match": True}]
        members = [_make_member("100", nick="Peppy")]
        with patch("main.osu.get_username_from_user_id", return_value="peppy"):
            result = self._run_main(members, save, tmp_path)

        assert result[0]["match"] is True

    # -- Multiple members processed correctly ----------------------------

    def test_multiple_members(self, tmp_path):
        save = [{"discord_id": "200", "osu_id": 5, "match": True}]
        members = [
            _make_member("100", nick="peppy"),     # new, found
            _make_member("200", nick="old_nick"),  # existing, mismatch
            _make_member("300", nick="ghost"),     # new, not found
        ]

        def fake_get_id(name):
            if name == "peppy":
                return 2
            raise ValueError("not found")

        def fake_get_username(osu_id):
            if osu_id == 5:
                return "new_name"
            raise ValueError("not found")

        with (
            patch("main.osu.get_user_id_from_username", side_effect=fake_get_id),
            patch("main.osu.get_username_from_user_id", side_effect=fake_get_username),
        ):
            result = self._run_main(members, save, tmp_path)

        by_id = {u["discord_id"]: u for u in result}
        assert by_id["100"] == {"discord_id": "100", "osu_id": 2, "match": True}
        assert by_id["200"] == {"discord_id": "200", "osu_id": 5, "match": False}
        assert "300" not in by_id
