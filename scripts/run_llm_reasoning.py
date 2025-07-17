from src.llm_reasoning import generate_llm_reasoning

context = {
    "location": "Pacific Place",
    "recommended_price": 12000000,
    "occupancy_pct": 0.92,
    "breakeven_occupancy_pct": 0.80,
    "published_price": 11500000,
}

print(generate_llm_reasoning(context))
