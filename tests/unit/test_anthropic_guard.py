import pytest

from app.providers.anthropic import AnthropicProvider


def test_live_calls_stay_disabled():
    with pytest.raises(RuntimeError, match="disabled"):
        AnthropicProvider()
