import os
import pytest
from unittest import mock
import openai


def test_generate_llm_reasoning_no_api_key(monkeypatch):
    # Ensure the API key is not set
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    context = {
        "location": "Test Location",
        "recommended_price": 1000000,
        "occupancy_pct": 0.85,
        "breakeven_occupancy_pct": 0.75,
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
        "occupancy_pct": 0.85,
        "breakeven_occupancy_pct": 0.75,
        "published_price": 950000,
    }
    # Mock openai.ChatCompletion.create
    with mock.patch("openai.ChatCompletion.create") as mock_create:
        mock_create.return_value.choices = [
            mock.Mock(message={"content": "This is a test reasoning."})
        ]
        result = generate_llm_reasoning(context)
        assert result == "This is a test reasoning."


def generate_llm_reasoning(context: dict) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "[LLM reasoning unavailable: OPENAI_API_KEY not set]"

    client = openai.OpenAI(api_key=api_key)
    location = context.get("location")
    recommended_price = context.get("recommended_price")
    occupancy = context.get("occupancy_pct")
    breakeven = context.get("breakeven_occupancy_pct")
    published_price = context.get("published_price")

    # Calculate price differential percentage
    price_diff_pct = ((recommended_price - published_price) / published_price) * 100

    prompt = (
        f"You are an expert flexible office space pricing analyst.\n\n"
        f"Property Analysis:\n"
        f"- Location: {location}\n"
        f"- Recommended Price: ${recommended_price:,.2f}\n"
        f"- Current Published Price: ${published_price:,.2f}\n"
        f"- Price Differential: {price_diff_pct:+.1f}%\n\n"
        f"Performance Metrics:\n"
        f"- Current Occupancy Rate: {occupancy:.1%}\n"
        f"- Breakeven Occupancy Target: {breakeven:.1%}\n\n"
        f"Please provide a detailed pricing analysis addressing:\n"
        f"1. Whether the recommended price change is justified\n"
        f"2. Impact on occupancy and revenue\n"
        f"3. Risks and opportunities\n"
        f"4. Clear action recommendations\n\n"
        f"Explain your analysis in clear, actionable language with specific reference to the metrics provided."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert flexible office space pricing analyst specializing in revenue optimization and occupancy management. Provide clear, data-driven recommendations.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=250,  # Increased for more detailed analysis
            temperature=0.4,  # Reduced for more consistent, analytical responses
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[LLM reasoning unavailable: {e}]"
