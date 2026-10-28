import cv2
from edge_impulse_linux.image import ImageImpulseRunner

TOP_MODEL_PATH = "models/rxsort-pill-identification-(top)-linux-aarch64-v13-impulse-#1.eim"
BOTTOM_MODEL_PATH = "models/rxsort-pill-identification-(bottom)-linux-aarch64-v6-impulse-#1.eim"

LABEL_TO_PILL_ID = {
    "Ibuprofen": 3,
    "Simvastatin": 4,
    "Amlodipine Besylate & Benazepril Hydrochloride": 5,
    "Fexofenadine Hydrochloride": 6,
    "Mucinex": 7,
    "Hydrochlorothiazide & Losartan Potassium": 8,
    "Prazosin Hydrochloride": 9,
    "Propranolol Hydrochloride": 10,
    "Acetaminophen Guaifenesin": 11,
    "Dexamethasone": 12,
    "Benadryl Allergy Ultratab Diphenhydramine": 13,
    "Imodium Advanced": 14,
    "Labetalol Hydrochloride": 15,
    "Acetaminophen (Tylenol)": 16,
    "Famotidine": 17,
    "Nothing": 18
}


def identify_pill(image_path, model_path):
    with ImageImpulseRunner(model_path) as runner:
        model_info = runner.init()

        image = cv2.imread(image_path)

        if image is None:
            raise ValueError(f"Could not open image: {image_path}")

        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        features, cropped = runner.get_features_from_image(image)

        result = runner.classify(features)

        predictions = result["result"]["classification"]

        best_label = max(predictions, key=predictions.get)
        confidence = predictions[best_label]

        pill_id = LABEL_TO_PILL_ID.get(best_label)

        return {
            "pill_id": pill_id,
            "label": best_label,
            "confidence": confidence,
            "pill_count": 1,
            "all_predictions": predictions
        }


def identify_top_pill(image_path):
    return identify_pill(image_path, TOP_MODEL_PATH)


def identify_bottom_pill(image_path):
    return identify_pill(image_path, BOTTOM_MODEL_PATH)


def evaluate_prediction(result):
    confidence = result["confidence"]
    pill_count = result["pill_count"]
    pill_id = result["pill_id"]

    if pill_count != 1:
        return {
            "decision": "REJECT",
            "reason": "Incorrect number of pills detected"
        }

    if pill_id is None:
        return {
            "decision": "REJECT",
            "reason": "Medication not mapped to database"
        }

    if confidence < 0.80:
        return {
            "decision": "REJECT",
            "reason": "Confidence too low"
        }

    return {
        "decision": "SORT",
        "pill_id": pill_id,
        "confidence": confidence
    }
