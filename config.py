from pydantic_settings import BaseSettings


class Config(BaseSettings):
    DISCORD_SERVER_ID: str
    DISCORD_BOT_TOKEN: str
    DISCORD_WEBHOOK: str | None = None
    DB_PATH: str = "save.json"
    CHECK_INTERVAL_MINUTE: int = 5
    APPLY_NICKNAME: bool = True


config = Config()  # type: ignore[call-arg]
