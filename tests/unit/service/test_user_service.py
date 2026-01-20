from unittest.mock import AsyncMock, patch

import pytest

from app.exceptions.business import DatabaseError, DuplicateEntityError, ExternalServiceError
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import UserCreate
from app.services.user_service import UserService


@pytest.fixture
def mock_user_repo():
    return AsyncMock(spec=UserRepository)


@pytest.fixture
def mock_slack_client():
    return AsyncMock()


@pytest.fixture
def user_service(mock_user_repo):
    return UserService(user_repo=mock_user_repo)


@pytest.mark.anyio
async def test_user_service_create_success(user_service, mock_user_repo):
    user_create = UserCreate(slack_id="U123", display_name="Test User")
    mock_user_repo.find_by_slack_id.return_value = None

    expected_user = User(id=1, slack_id="U123", display_name="Test User")
    mock_user_repo.create.return_value = expected_user

    result = await user_service.create(user_create)

    mock_user_repo.find_by_slack_id.assert_called_once_with("U123")
    mock_user_repo.create.assert_called_once()
    assert result == expected_user


@pytest.mark.anyio
async def test_user_service_create_duplicate_error(user_service, mock_user_repo):
    user_create = UserCreate(slack_id="U123", display_name="Test User")
    mock_user_repo.find_by_slack_id.return_value = User(id=1, slack_id="U123")

    with pytest.raises(DuplicateEntityError):
        await user_service.create(user_create)

    mock_user_repo.create.assert_not_called()


@pytest.mark.anyio
async def test_user_service_create_database_error(user_service, mock_user_repo):
    user_create = UserCreate(slack_id="U123", display_name="Test User")
    mock_user_repo.find_by_slack_id.return_value = None
    mock_user_repo.create.side_effect = Exception("DB Fail")

    with pytest.raises(DatabaseError):
        await user_service.create(user_create)


@pytest.mark.anyio
async def test_user_service_find_all(user_service, mock_user_repo):
    users = [User(id=1), User(id=2)]
    mock_user_repo.get_all.return_value = users

    result = await user_service.find_all()

    mock_user_repo.get_all.assert_called_once()
    assert result == users


@pytest.mark.anyio
async def test_user_service_find_by_slack_id(user_service, mock_user_repo):
    user = User(id=1, slack_id="U123")
    mock_user_repo.find_by_slack_id.return_value = user

    result = await user_service.find_by_slack_id("U123")

    mock_user_repo.find_by_slack_id.assert_called_once_with("U123")
    assert result == user


@pytest.mark.anyio
async def test_get_slack_display_name_success_with_display_name(user_service):
    with patch("app.services.user_service.slack_app") as mock_slack:
        mock_slack.client.users_info = AsyncMock(return_value={
            "ok": True,
            "user": {
                "profile": {"display_name": "John Doe"},
                "real_name": "John D.",
                "name": "johndoe"
            }
        })

        result = await user_service.get_slack_display_name("U123ABC")

        assert result == "John Doe"
        mock_slack.client.users_info.assert_called_once_with(user="U123ABC")


@pytest.mark.anyio
async def test_get_slack_display_name_fallback_to_real_name(user_service):
    with patch("app.services.user_service.slack_app") as mock_slack:
        mock_slack.client.users_info = AsyncMock(return_value={
            "ok": True,
            "user": {
                "profile": {"display_name": ""},
                "real_name": "John D.",
                "name": "johndoe"
            }
        })

        result = await user_service.get_slack_display_name("U123ABC")

        assert result == "John D."


@pytest.mark.anyio
async def test_get_slack_display_name_fallback_to_name(user_service):
    with patch("app.services.user_service.slack_app") as mock_slack:
        mock_slack.client.users_info = AsyncMock(return_value={
            "ok": True,
            "user": {
                "profile": {"display_name": ""},
                "real_name": "",
                "name": "johndoe"
            }
        })

        result = await user_service.get_slack_display_name("U123ABC")

        assert result == "johndoe"


@pytest.mark.anyio
async def test_get_slack_display_name_api_error(user_service):
    with patch("app.services.user_service.slack_app") as mock_slack:
        mock_slack.client.users_info = AsyncMock(return_value={
            "ok": False,
            "error": "user_not_found"
        })

        with pytest.raises(ExternalServiceError) as exc_info:
            await user_service.get_slack_display_name("U123ABC")

        assert "Slack" in str(exc_info.value.message)
        assert "user_not_found" in str(exc_info.value.message)


@pytest.mark.anyio
async def test_get_slack_display_name_no_display_name(user_service):
    with patch("app.services.user_service.slack_app") as mock_slack:
        mock_slack.client.users_info = AsyncMock(return_value={
            "ok": True,
            "user": {
                "profile": {},
                "real_name": "",
                "name": ""
            }
        })

        with pytest.raises(ExternalServiceError) as exc_info:
            await user_service.get_slack_display_name("U123ABC")

        assert "has no display name" in str(exc_info.value.message)
