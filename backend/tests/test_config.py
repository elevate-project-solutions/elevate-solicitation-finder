import pytest
from pydantic import ValidationError

from app.config import Settings


def test_default_settings():
    settings = Settings(
        _env_file=None,
        _env_prefix="ELEVATE_TEST_",
    )

    assert settings.min_days_until_deadline == 30
    assert settings.debug is False


def test_invalid_deadline_setting():
    with pytest.raises(ValidationError):
        Settings(
            min_days_until_deadline=-1,
            _env_file=None,
            _env_prefix="ELEVATE_TEST_",
        )
