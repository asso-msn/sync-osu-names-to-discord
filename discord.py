import httpx

INTENTS = ("GUILD_MEMBERS",)


class API:
    BASE_URL = "https://discord.com/api/v10"

    def __init__(self, bot_token: str):
        self._client = httpx.Client(
            headers={
                "Authorization": f"Bot {bot_token}",
                "User-Agent": "SyncOsuNamesToDiscordBot (https://github.com/asso-msn/sync-osu-names-to-discord)",
            }
        )

    def call(
        self, url: str, method="GET", reason=None, **kwargs
    ) -> httpx.Response:
        headers = {}
        if reason is not None:
            headers["X-Audit-Log-Reason"] = reason
        if url.startswith("/"):
            url = self.BASE_URL + url
        response = self._client.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()
        return response

    def iter_server_members(self, server_id: str):
        limit = 1000
        after = None
        while True:
            url = f"/guilds/{server_id}/members" f"?limit={limit}"
            if after is not None:
                url += f"&after={after}"
            members = self.call(url).json()
            yield from members
            if len(members) < limit:
                break
            after = members[-1]["user"]["id"]

    def set_user_nick(
        self,
        server_id: str,
        user_id: str,
        nick: str | None,
        reason: str | None = None,
    ):
        url = f"/guilds/{server_id}/members/{user_id}"
        self.call(url, method="PATCH", reason=reason, json={"nick": nick})


if __name__ == "__main__":
    from config import config

    api = API(config.DISCORD_BOT_TOKEN)

    # def print_user(user: dict):
    #     print({k: user[k] for k in ("id", "username")})

    # for result in api.call(
    #     f"/guilds/{config.DISCORD_SERVER_ID}/members?limit=50",
    # ).json():
    #     print_user(result["user"])
    # for result in api.iter_server_members(config.DISCORD_SERVER_ID):
    #     print_user(result["user"])
    api.set_user_nick(
        config.DISCORD_SERVER_ID,
        "1428095421506523177",
        "test",
        reason="test",
    )
