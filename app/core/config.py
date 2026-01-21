from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class BasicConfig(BaseSettings):
    ENV_SCOPE: str | None = None
    APP_NAME: str = "Sports Program API"
    DEBUG: bool = True

    SLACK_BOT_TOKEN: str = ""
    SLACK_SIGNING_SECRET: str = ""
    SLACK_CLIENT_ID: str = ""
    SLACK_CLIENT_SECRET: str = ""
    SLACK_SCOPES: str = "commands,chat:write"
    SLACK_INSTALL_PATH: str = "/slack/install"
    SLACK_REDIRECT_URI_PATH: str = "/slack/oauth_redirect"
    SLACK_STATE_EXPIRATION_SECONDS: int = 600
    DEBUG: bool = True
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class GlobalConfig(BasicConfig):
    DATABASE_URL: str | None = None


class DevConfig(GlobalConfig):
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite+aiosqlite:///./sports_program.db"


class TestConfig(GlobalConfig):
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"


class ProdConfig(GlobalConfig):
    DEBUG: bool = False

    @field_validator(
        "DATABASE_URL",
        "SLACK_SIGNING_SECRET",
        "SLACK_CLIENT_ID",
        "SLACK_CLIENT_SECRET",
    )
    @classmethod
    def check_must_be_set(cls, v: str | None) -> str:
        if not v:
            raise ValueError(
                "Required configuration missing for production environment"
            )
        return v


def get_configs(scope: str | None):
    configs = {"dev": DevConfig, "test": TestConfig, "prod": ProdConfig}
    config_class = configs.get(scope, DevConfig)
    return config_class()


settings = get_configs(BasicConfig().ENV_SCOPE)
