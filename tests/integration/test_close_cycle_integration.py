from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from httpx import AsyncClient

SAO_PAULO = ZoneInfo("America/Sao_Paulo")


@pytest.mark.asyncio
async def test_close_cycle_success(async_client: AsyncClient):
    # 1. Create a User
    user_payload = {"slack_id": "U_CYCLE_001", "display_name": "User Cycle"}
    response = await async_client.post("/users", json=user_payload)
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["slack_id"] == "U_CYCLE_001"

    # 2. Create a Program
    now = datetime.now(SAO_PAULO)
    if now.month == 1:
        test_year = now.year - 1
        test_month = 12
    else:
        test_year = now.year
        test_month = now.month - 1

    cycle_ref = f"{test_year}-{test_month:02d}"

    start_dt = datetime(test_year, test_month, 1, 0, 0, 1, tzinfo=SAO_PAULO)
    program_payload = {
        "name": "Cycle Challenge",
        "slack_channel": "C_CYCLE_001",
        "start_date": start_dt.isoformat(),
    }
    resp = await async_client.post("/programs", json=program_payload)
    assert resp.status_code == 201
    program_data = resp.json()
    program_id = program_data["id"]

    # 3. Create Activities
    headers = {"x-slack-user-id": "U_CYCLE_001"}

    for day in range(2, 15):
        activity_date = datetime(
            test_year, test_month, day, 12, 0, 0, tzinfo=SAO_PAULO)

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

    # 4. Verify activities were created by checking user's activities
    activities_resp = await async_client.get(
        f"/programs/C_CYCLE_001/activities?reference_date={cycle_ref}",
        headers=headers
    )
    assert activities_resp.status_code == 200
    activities = activities_resp.json()
    assert len(
        activities) == 13, f"Expected 13 activities, got {len(activities)}"

    # 5. Close the Cycle
    close_resp = await async_client.post(
        f"/programs/{program_id}/close-cycle/{cycle_ref}"
    )

    assert close_resp.status_code == 200, f"Close cycle failed: {close_resp.text}"
    close_data = close_resp.json()

    assert close_data is not None, "close_cycle returned None"
    assert close_data["total_created"] == 0, (
        f"Expected 0, got {close_data.get('total_created', 'N/A')}"
    )
    assert close_data["program_name"] == "Cycle Challenge"
