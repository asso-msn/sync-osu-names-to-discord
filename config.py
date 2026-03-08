from pydantic_settings import BaseSettings


class Config(
    BaseSettings, env_file=".env", cli_parse_args=True, cli_kebab_case=True
):
    # Server in which the nicknames must sync
    DISCORD_SERVER_ID: str

    # Token from a bot that can read members and change nicknames on the server
    DISCORD_BOT_TOKEN: str

    # Webhook URL to send the report to
    DISCORD_WEBHOOK: str | None = None

    # Path to the JSON file in which the data is stored
    DB_PATH: str = "save.json"

    # Whether to apply the nickname changes on Discord or just report them
    APPLY_NICKNAME: bool = True

    # If > 0, the program will run in a loop and repeat the process every given
    # minutes
    LOOP_MINUTES: float = 0

    # Whether to send a status report or just do the actions without reporting
    SEND_REPORT: bool = True


config = Config()  # type: ignore[call-arg]
