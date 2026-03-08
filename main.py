import json
import os
import time
import traceback

import osu
from config import config
from discord import API as DiscordAPI


def load_save(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)


def save_data(path: str, data: dict):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def main():
    discord = DiscordAPI(config.DISCORD_BOT_TOKEN)
    data = load_save(config.DB_PATH)

    discord_server_member_ids = set()

    report = {
        "new_matches": [],
        "old_mismatches": [],
        "new_mismatches": [],
        "no_osu_user": [],
        "fixed_new_mismatches": [],
        "fixed_old_mismatches": [],
        "removed": [],
        "errors": [],
    }

    for member in discord.iter_server_members(config.DISCORD_SERVER_ID):
        discord_id = member["user"]["id"]
        nick = member.get("nick") or member["user"]["username"]

        discord_server_member_ids.add(discord_id)
        user = data.get(discord_id)

        if user is None:
            try:
                osu_id = osu.get_user_id_from_username(nick)

                if osu_id is None:
                    print(f"No osu! page exists for {nick=} {discord_id=}")
                    report["no_osu_user"].append(f"{nick=} {discord_id=}")
                    continue

                data[discord_id] = {"osu_id": osu_id, "match": True}
                print(f"Linked osu! user for {nick=} {osu_id=} {discord_id=}")
                report["new_matches"].append(f"{nick=} {osu_id=} {discord_id=}")

            except Exception as e:
                msg = (
                    f"Unexpected error while looking up osu! user for {nick=}"
                    f" {discord_id=}: {e}"
                )
                print(msg)
                report["errors"].append(msg)
                traceback.print_exc()
            continue

        osu_id = user["osu_id"]
        try:
            osu_username = osu.get_username_from_user_id(osu_id)
        except Exception as e:
            msg = (
                f"Unexpected error while looking up osu! username for"
                f" {nick=} {osu_id=} {discord_id=}: {e}"
            )
            print(msg)
            report["errors"].append(msg)
            traceback.print_exc()
            continue

        matching = osu_username.lower() == nick.lower()
        if matching and user["match"]:
            # everything is already fine with this user
            continue

        if matching and not user["match"]:
            # now matching, was previously not
            print(
                f"New username match for {nick=} {osu_username=}"
                f" {discord_id=}, was previously mismatching"
            )
            report["new_matches"].append(
                f"{nick=} {osu_username=} {discord_id=}"
            )
            user["match"] = True
            continue

        if not matching:
            if not config.APPLY_NICKNAME:
                if user["match"]:
                    print(
                        f"New username mismatch for {nick=} {osu_username=}"
                        f" {discord_id=}, was previously matching"
                    )
                    report["new_mismatches"].append(
                        f"{nick=} {osu_username=} {discord_id=}"
                    )
                if not user["match"]:
                    print(
                        f"Old username mismatch for {nick=} {osu_username=}"
                        f" {discord_id=}, was already mismatching"
                    )
                    report["old_mismatches"].append(
                        f"{nick=} {osu_username=} {discord_id=}"
                    )
                user["match"] = False
                continue

            print(
                f"Applying osu! username as nickname for {discord_id=}"
                f" {nick=} {osu_username=}"
            )

            try:
                discord.set_user_nick(
                    config.DISCORD_SERVER_ID,
                    discord_id,
                    nick=osu_username,
                    reason="Syncing osu! username to Discord nickname",
                )
            except Exception as e:
                msg = (
                    f"Unexpected error while setting nickname for"
                    f" {nick=} {osu_username=} {discord_id=}: {e}"
                )
                print(msg)
                report["errors"].append(msg)
                traceback.print_exc()

                if not user["match"]:
                    print(
                        f"{nick=} {osu_username=} {discord_id=} stays"
                        " mismatching due to error while applying nickname"
                    )
                    report["old_mismatches"].append(
                        f"{nick=} {osu_username=} {discord_id=}"
                    )
                if user["match"]:
                    print(
                        f"{nick=} {osu_username=} {discord_id=} is a new"
                        " mismatch that could not be fixed due to an error"
                        " while applying nickname"
                    )
                    report["new_mismatches"].append(
                        f"{nick=} {osu_username=} {discord_id=}"
                    )
                user["match"] = False
                continue

            if user["match"]:
                print(
                    f"Fixed new mismatch for {discord_id=}:"
                    f" {osu_username=}, {nick=}"
                )
                report["fixed_new_mismatches"].append(
                    f"{nick=} {osu_username=} {discord_id=}"
                )
            if not user["match"]:
                print(
                    f"Fixed old mismatch for {discord_id=}:"
                    f" {osu_username=}, {nick=}"
                )
                report["fixed_old_mismatches"].append(
                    f"{nick=} {osu_username=} {discord_id=}"
                )
            user["match"] = True

    for discord_id in data:
        if discord_id not in discord_server_member_ids:
            osu_id = data[discord_id]["osu_id"]
            print(
                f"Removing {discord_id=} {osu_id=} from data, because they are"
                " no longer in the server"
            )
            report["removed"].append(f"{discord_id=} {osu_id=}")
            del data[discord_id]

    save_data(config.DB_PATH, data)

    if config.SEND_REPORT:
        titles = {
            "new_matches": (
                "Newly matched user, were not in data before, is matching with"
                " osu!"
            ),
            "no_osu_user": (
                "These users have usernames that do not exist on osu!, and they"
                " were never linked to an osu! account before"
            ),
            "old_mismatches": (
                "Old mismatches, were already not in sync, still not in sync"
            ),
            "new_mismatches": (
                "New mismatches, were in sync before, now are mismatching"
            ),
            "fixed_new_mismatches": (
                "Fixed new mismatches, were matching before, but were not"
                " matching now, fixed by the script"
            ),
            "fixed_old_mismatches": (
                "Fixed old mismatches, were not matching last time, got fixed"
                " now"
            ),
            "removed": "Left the server",
            "errors": "Errors that happened during the run",
        }

        msg = ""
        for key, title in titles.items():
            if len(report[key]) == 0:
                continue
            msg += f"{title}:\n"
            msg += "\n".join(f"- {entry}" for entry in report[key])
            msg += "\n\n"
        if msg:
            sep = "-" * 10
            print(f"{sep}\n{msg}{sep}")
            if config.DISCORD_WEBHOOK:
                discord.send_webhook_message(config.DISCORD_WEBHOOK, msg)


if __name__ == "__main__":
    while True:
        main()
        if config.LOOP_MINUTES > 0:
            time.sleep(config.LOOP_MINUTES * 60)
        else:
            break
