import pytest


def test_reminder_times_default_to_19_and_21(app_client):
    assert app_client.get("/settings/reminders").json() == {"times": ["19:00", "21:00"]}


def test_reminder_times_can_be_changed(app_client):
    r = app_client.put("/settings/reminders", json={"times": ["07:30", "20:00"]})
    assert r.status_code == 200 and r.json() == {"times": ["07:30", "20:00"]}
    assert app_client.get("/settings/reminders").json() == {"times": ["07:30", "20:00"]}


@pytest.mark.parametrize("times", [["25:00"], ["7:30"], ["aa:bb"], ["08:00"] * 5])
def test_invalid_reminder_times_are_rejected(app_client, times):
    assert app_client.put("/settings/reminders", json={"times": times}).status_code == 422
