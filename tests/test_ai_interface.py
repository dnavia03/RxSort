from ai_interface.edge_impulse_interface import identify_pill, evaluate_prediction
from database.database_manager import get_pill_by_id

result = identify_pill("test_image.jpg")

print("AI Result:")
print(result)

pill_id = result["pill_id"]

pill = get_pill_by_id(pill_id)

print("\nDatabase Result:")
print(pill)

print("\n--- Decision Tests ---")

good_result = {
    "pill_id": 4,
    "confidence": 0.96,
    "pill_count": 1
}

print("Good prediction:")
print(evaluate_prediction(good_result))

low_confidence_result = {
    "pill_id": 4,
    "confidence": 0.65,
    "pill_count": 2
}

print("\nLow confidence:")
print(evaluate_prediction(low_confidence_result))

multiple_pills_result = {
    "pill_id": 4,
    "confidence": 0.95,
    "pill_count": 2
}

print("\nMultiple pills:")
print(evaluate_prediction(multiple_pills_result))
