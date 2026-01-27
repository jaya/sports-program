from datetime import UTC, datetime

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_close_cycle_success(async_client: AsyncClient):
    # 1. Create a User
    user_payload = {"slack_id": "U_CYCLE_001", "display_name": "User Cycle"}
    response = await async_client.post("/users", json=user_payload)
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["slack_id"] == "U_CYCLE_001"

    # 2. Create a Program
    now = datetime.now(UTC)
    current_year = now.year
    current_month = now.month

    cycle_ref = f"{current_year}-{current_month:02d}"

    program_payload = {
        "name": "Cycle Challenge",
        "slack_channel": "C_CYCLE_001",
        "start_date": datetime(current_year, current_month, 1, tzinfo=UTC).isoformat(),
    }
    resp = await async_client.post("/programs", json=program_payload)
    assert resp.status_code == 201

    # 3. Create Activities
    headers = {"x-slack-user-id": "U_CYCLE_001"}

    for day in range(1, 13):
        activity_date = datetime(current_year, current_month, day, 12, 0, 0, tzinfo=UTC)

        payload = {
            "description": f"Run day {day}",
            "evidence_url": "http://evidence.com",
            "performed_at": activity_date.isoformat(),
        }

        resp = await async_client.post(
            "/programs/C_CYCLE_001/activities", json=payload, headers=headers
        )
        assert resp.status_code == 201, (
            f"Failed to create activity for day {day}: {resp.text}"
        )

    # 4. Close the Cycle
    close_resp = await async_client.post(
        f"/programs/Cycle Challenge/close-cycle/{cycle_ref}"
    )

    assert close_resp.status_code == 200
    close_data = close_resp.json()

    assert close_data["total_created"] == 1
    assert close_data["program_name"] == "Cycle Challenge"
    assert "User Cycle" in close_data["users"]
