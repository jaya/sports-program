from datetime import UTC, datetime

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_retrieve_activity(async_client: AsyncClient):
    # 1. Create a Program
    program_payload = {
        "name": "Integration Challenge",
        "slack_channel": "C_TEST_001",
        "start_date": datetime.now(UTC).isoformat(),
    }
    response = await async_client.post("/programs", json=program_payload)
    assert response.status_code == 201
    program_data = response.json()
    assert program_data["slack_channel"] == "C_TEST_001"

    # 2. Create an Activity
    activity_payload = {
        "description": "Integration Run 5k",
        "evidence_url": "https://example.com/evidence.png",
    }

    headers = {"x-slack-user-id": "U_TEST_001"}

    response = await async_client.post(
        f"/programs/{program_data['slack_channel']}/activities",
        json=activity_payload,
        headers=headers,
    )
    assert response.status_code == 201
    activity_summary = response.json()
    assert activity_summary["id"] is not None

    # 3. Retrieve the Activity
    activity_id = activity_summary["id"]
    response = await async_client.get(f"/activities/{activity_id}", headers=headers)
    assert response.status_code == 200
    activity_detail = response.json()

    assert activity_detail["description"] == "Integration Run 5k"
    assert activity_detail["user"]["slack_id"] == "U_TEST_001"
    assert activity_detail["program"]["slack_channel"] == "C_TEST_001"
