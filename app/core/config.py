from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Sports Program API"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./sports_program.db"

    # Slack
    SLACK_BOT_TOKEN: str = ""
    SLACK_SIGNING_SECRET: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
