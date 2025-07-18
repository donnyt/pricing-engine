from src.llm_reasoning import generate_llm_reasoning

context = {
    "location": "Pacific Place",
    "recommended_price": 12000000,
    "occupancy_pct": 92.0,
    "breakeven_occupancy_pct": 80.0,
    "published_price": 11500000,
}

print(generate_llm_reasoning(context))
