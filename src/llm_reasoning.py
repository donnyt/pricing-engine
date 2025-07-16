"""
llm_reasoning.py - Module for generating LLM-based reasoning for price recommendations.
"""

import os
import openai


def generate_llm_reasoning(context: dict) -> str:
    """
    Generate reasoning for price recommendations using OpenAI's GPT API.
    Args:
        context (dict): Contextual information about the pricing decision.
    Returns:
        str: LLM-generated reasoning or a fallback message.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "[LLM reasoning unavailable: OPENAI_API_KEY not set]"
    client = openai.OpenAI(api_key=api_key)
    location = context.get("location")
    recommended_price = context.get("recommended_price")
    occupancy = context.get("occupancy_pct")
    breakeven = context.get("breakeven_occupancy_pct")
    published_price = context.get("published_price")
    prompt = (
        f"You are an expert pricing analyst for flexible office space in Indonesia.\n"
        f"Location: {location}\n"
        f"Recommended Price: Rp {recommended_price:,.0f}\n"
        f"Published Price: Rp {published_price:,.0f}\n"
        f"Occupancy Rate: {occupancy:.0%}\n"
        f"Breakeven Occupancy: {breakeven:.0%}\n\n"
        f"Based on these metrics, provide a concise (max 6 sentences) reasoning for whether the recommended price is justified. "
        f"Address the occupancy, price difference, and impact on revenue. Respond in clear, practical business language."
    )
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful pricing assistant."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=250,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[LLM reasoning unavailable: {e}]"
