from unittest.mock import MagicMock
import pytest
from app.services.settings_service import get_settings, ensure_settings_row, update_settings, get_sender_for_send


def test_get_settings_table_not_exists():
    # Reset the cached table existence status for a clean test
    import app.services.settings_service
    app.services.settings_service._app_settings_table_exists = None

    mock_cur = MagicMock()
    # Mock information_schema check returning False, then select returning None
    mock_cur.fetchone.side_effect = [(False,), None]

    settings = get_settings(mock_cur)

    # Verify standard defaults are returned
    assert settings["notifications_enabled"] is False
    assert settings["support_email"] == "aakash.padyachi@rochvate.com"
    # Ensure insert was called (table check + insert + select)
    assert mock_cur.execute.call_count >= 2


def test_get_settings_table_exists():
    import app.services.settings_service
    app.services.settings_service._app_settings_table_exists = None

    mock_cur = MagicMock()
    
    # 1st call to execute check: table exists
    # 2nd call to execute in ensure_settings_row: insert
    # 3rd call to execute in get_settings: select
    mock_cur.fetchone.side_effect = [
        (True,),  # check table exists
        (
            "Custom Sender",
            "custom@orchvate.com",
            "admin@orchvate.com",
            True,
            "custom-support@orchvate.com",
            None,
        )  # select settings row
    ]

    settings = get_settings(mock_cur)

    assert settings["sender_name"] == "Custom Sender"
    assert settings["sender_address"] == "custom@orchvate.com"
    assert settings["notification_email"] == "admin@orchvate.com"
    assert settings["notifications_enabled"] is True
    assert settings["support_email"] == "custom-support@orchvate.com"
