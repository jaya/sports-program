import os

from app.core.config import get_configs


def run_config_check(scope, env_vars=None):
    print(f"\n--- Testing with SCOPE: {scope} ---")
    if env_vars:
        for k, v in env_vars.items():
            os.environ[k] = v

    try:
        # Force reload or get a new instance
        cfg = get_configs(scope)
        print(f"Class: {cfg.__class__.__name__}")
        print(f"DEBUG: {cfg.DEBUG}")
        print(f"DATABASE_URL: {cfg.DATABASE_URL}")
        print(f"SLACK_BOT_TOKEN: {'defined' if cfg.SLACK_BOT_TOKEN else 'empty'}")
        return cfg
    except Exception as e:
        print(f"Error loading config: {e}")
        raise e
    finally:
        if env_vars:
            for k in env_vars.keys():
                del os.environ[k]


def test_prod_config_validation():
    import pytest
    from pydantic import ValidationError

    # To test validation, let's try to overwrite with empty values in prod.
    with pytest.raises(ValidationError):
        run_config_check(
            "prod",
            {"DATABASE_URL": "", "SLACK_BOT_TOKEN": "", "SLACK_SIGNING_SECRET": ""},
        )


def test_prod_config_success():
    cfg = run_config_check(
        "prod",
        {
            "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost/db",
            "DEBUG": "True",
            "SLACK_BOT_TOKEN": "xoxb-prod-token",
            "SLACK_SIGNING_SECRET": "secret",
        },
    )
    assert cfg.DEBUG is True
    assert cfg.DATABASE_URL == "postgresql+asyncpg://user:pass@localhost/db"


def test_dev_config_default():
    cfg = run_config_check(None)
    assert cfg.__class__.__name__ == "DevConfig"


if __name__ == "__main__":
    # 1. Simulate production without environment variables set (but requesting prod)
    try:
        run_config_check(
            "prod",
            {"DATABASE_URL": "", "SLACK_BOT_TOKEN": "", "SLACK_SIGNING_SECRET": ""},
        )
    except Exception:
        pass

    # 2. Simulate production with environment variables (DEBUG should work now)
    run_config_check(
        "prod",
        {
            "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost/db",
            "DEBUG": "True",
            "SLACK_BOT_TOKEN": "xoxb-prod-token",
            "SLACK_SIGNING_SECRET": "secret",
        },
    )

    # 3. Simulate null scope (current default behavior)
    run_config_check(None)
