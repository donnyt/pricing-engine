import os
import pytest
from unittest import mock
import openai
from src.pricing.reasoning import generate_llm_reasoning


def test_generate_llm_reasoning_no_api_key(monkeypatch):
    # Ensure the API key is not set
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    context = {
        "location": "Test Location",
        "recommended_price": 1000000,
        "occupancy_pct": 85.0,
        "breakeven_occupancy_pct": 75.0,
        "published_price": 950000,
    }
    result = generate_llm_reasoning(context)
    assert "OPENAI_API_KEY not set" in result


def test_generate_llm_reasoning_with_mock(monkeypatch):
    # Set a dummy API key
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    context = {
        "location": "Test Location",
        "recommended_price": 1000000,
        "occupancy_pct": 85.0,
        "breakeven_occupancy_pct": 75.0,
        "published_price": 950000,
    }
    # Mock the OpenAI client's chat completions create method
    with mock.patch("openai.OpenAI") as mock_openai:
        mock_client = mock.Mock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value.choices = [
            mock.Mock(message=mock.Mock(content="This is a test reasoning."))
        ]
        result = generate_llm_reasoning(context)
        assert result == "This is a test reasoning."
