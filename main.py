import json
import os
import traceback

from config import config
from discord import API as DiscordAPI
import osu


def load_save(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return json.load(f)


def save_data(path: str, data: list[dict]):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def find_user(data: list[dict], discord_id: str) -> dict | None:
    for user in data:
        if user["discord_id"] == discord_id:
            return user
    return None


def main():
    discord = DiscordAPI(config.DISCORD_BOT_TOKEN)
    data = load_save(config.DB_PATH)

    for member in discord.iter_server_members(config.DISCORD_SERVER_ID):
        discord_id = member["user"]["id"]
        nick = member.get("nick") or member["user"]["username"]

        user = find_user(data, discord_id)

        if user is None:
            try:
                osu_id = osu.get_user_id_from_username(nick)
                data.append({"discord_id": discord_id, "osu_id": osu_id, "match": True})
                print(f"Linked osu! user for discord_id={discord_id} nick={nick!r}: osu_id={osu_id}")
            except ValueError:
                pass  # No osu! user found for this nick — expected
            except Exception:
                print(f"Unexpected error looking up osu! user for nick={nick!r}")
                traceback.print_exc()
        else:
            if not user["match"]:
                continue
            try:
                osu_username = osu.get_username_from_user_id(user["osu_id"])
                if osu_username.lower() != nick.lower():
                    print(
                        f"Username mismatch for discord_id={discord_id}:"
                        f" osu={osu_username!r}, nick={nick!r} — setting match=False"
                    )
                    user["match"] = False
            except Exception:
                traceback.print_exc()

    save_data(config.DB_PATH, data)


if __name__ == "__main__":
    main()
