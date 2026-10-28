"""Fixtures för Home Assistant-tester (pytest-homeassistant-custom-component)."""

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Låt Home Assistant hitta custom_components."""
    yield
