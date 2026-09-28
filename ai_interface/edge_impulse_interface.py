def identify_pill(image_path):
    """
    Temporary mock AI Function.
    Later, this function will send the image to the Edge Impulse Model.
    """

    result = {
        "pill_id": 4,
        "confidence": 0.96,
        "pill_count": 1
    }

    return result


def evaluate_prediction(result):
    confidence = result["confidence"]
    pill_count = result["pill_count"]
    pill_id = result["pill_id"]

    if pill_count != 1:
        return {
            "decision": "REJECT",
            "reason": "Incorrect number of pills detected"
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
