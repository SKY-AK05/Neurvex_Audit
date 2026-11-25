from unittest.mock import MagicMock
import pytest
from app.services.settings_service import get_settings, ensure_settings_row, update_settings, get_sender_for_send


def test_get_settings_table_not_exists():
    # Reset the cached table existence status for a clean test
    import app.services.settings_service
    app.services.settings_service._settings_cache = None
    app.services.settings_service._app_settings_table_exists = None

    mock_cur = MagicMock()
    # 1. First _fetch returns None
    # 2. ensure_settings_table checks table exists -> returns (False,)
    # 3. Second _fetch after ensure_settings_row returns None
    mock_cur.fetchone.side_effect = [None, (False,), None]

    settings = get_settings(mock_cur)

    # Verify standard defaults are returned
    assert settings["notifications_enabled"] is False
    assert settings["support_email"] == "aakash.padyachi@rochvate.com"
    # Ensure insert was called (table check + insert + select)
    assert mock_cur.execute.call_count >= 2


def test_get_settings_table_exists():
    import app.services.settings_service
    app.services.settings_service._settings_cache = None
    app.services.settings_service._app_settings_table_exists = None

    mock_cur = MagicMock()
    
    # 1st call to _fetch: returns existing settings row directly
    mock_cur.fetchone.side_effect = [
        (
            "Custom Sender",
            "custom@orchvate.com",
            "admin@orchvate.com",
            "admin-cc@orchvate.com",
            True,
            "custom-support@orchvate.com",
            None,
            False,
            "",
            50
        )
    ]

    settings = get_settings(mock_cur)

    assert settings["sender_name"] == "Custom Sender"
    assert settings["sender_address"] == "custom@orchvate.com"
    assert settings["notification_email"] == "admin@orchvate.com"
    assert settings["notification_cc_email"] == "admin-cc@orchvate.com"
    assert settings["notifications_enabled"] is True
    assert settings["support_email"] == "custom-support@orchvate.com"
    assert settings["crm_sync_enabled"] is False
    assert settings["hubspot_api_key"] == ""
    assert settings["low_visibility_threshold"] == 50
    assert settings["draft_reminder_hours"] == 2
    assert settings["draft_reminder_value"] == 2
    assert settings["draft_reminder_unit"] == "hours"


def test_update_draft_reminder_hours():
    import app.services.settings_service
    app.services.settings_service._settings_cache = None
    app.services.settings_service._app_settings_table_exists = True

    mock_cur = MagicMock()
    # 1. get_settings calls _fetch
    # 2. update_settings execute runs
    # 3. get_settings after update calls _fetch
    mock_cur.fetchone.side_effect = [
        (
            "Orchvate",
            "info@orchvate.com",
            "admin@orchvate.com",
            "",
            False,
            "support@orchvate.com",
            None,
            False,
            "",
            50,
            2,
            2,
            "hours"
        ),
        (
            "Orchvate",
            "info@orchvate.com",
            "admin@orchvate.com",
            "",
            False,
            "support@orchvate.com",
            None,
            False,
            "",
            50,
            6,
            6,
            "hours"
        )
    ]

    res = update_settings(mock_cur, {"draft_reminder_hours": 6})
    assert res["draft_reminder_hours"] == 6
    assert res["draft_reminder_value"] == 6
    assert res["draft_reminder_unit"] == "hours"
    # Verify execute called UPDATE with 6
    update_call_args = [call for call in mock_cur.execute.call_args_list if "UPDATE app_settings SET" in call[0][0]]
    assert len(update_call_args) == 1
    params = update_call_args[0][0][1]
    assert params[9] == 6   # draft_reminder_hours param
    assert params[10] == 6  # draft_reminder_value param
    assert params[11] == "hours"  # draft_reminder_unit param

    # Invalidate cache for subsequent tests
    app.services.settings_service._settings_cache = None
    app.services.settings_service._settings_cache_time = 0.0


def test_update_draft_reminder_seconds_and_minutes():
    import app.services.settings_service
    app.services.settings_service._settings_cache = None
    app.services.settings_service._app_settings_table_exists = True

    mock_cur = MagicMock()
    mock_cur.fetchone.side_effect = [
        (
            "Orchvate",
            "info@orchvate.com",
            "admin@orchvate.com",
            "",
            False,
            "support@orchvate.com",
            None,
            False,
            "",
            50,
            2,
            2,
            "hours"
        ),
        (
            "Orchvate",
            "info@orchvate.com",
            "admin@orchvate.com",
            "",
            False,
            "support@orchvate.com",
            None,
            False,
            "",
            50,
            1,
            45,
            "seconds"
        )
    ]

    res = update_settings(mock_cur, {"draft_reminder_value": 45, "draft_reminder_unit": "seconds"})
    assert res["draft_reminder_value"] == 45
    assert res["draft_reminder_unit"] == "seconds"

    update_call_args = [call for call in mock_cur.execute.call_args_list if "UPDATE app_settings SET" in call[0][0]]
    assert len(update_call_args) == 1
    params = update_call_args[0][0][1]
    assert params[10] == 45  # draft_reminder_value param
    assert params[11] == "seconds"  # draft_reminder_unit param

    app.services.settings_service._settings_cache = None
    app.services.settings_service._settings_cache_time = 0.0

