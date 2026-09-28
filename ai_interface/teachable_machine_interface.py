from ai_edge_litert.interpreter import Interpreter
from matplotlib import scale
import numpy as np
from PIL import Image

# --------------------------------------------------
# RxSort - Teachable Machine AI Interface
# --------------------------------------------------

MODEL_PATH = "models/vww_96_grayscale_quantized.tflite"
LABELS_PATH = "models/labels.txt"

# Teachable Machine class -> RxSort database pill_id
CLASS_TO_PILL_ID = {
    0: 3,  # Ibuprofen
    1: 5,  # Amlodipine
    2: 4  # Simvastatin
}


def load_model():
    """Load the trained TFLite model."""

    interpreter = Interpreter(MODEL_PATH)
    interpreter.allocate_tensors()

    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    return interpreter, input_details, output_details


def load_labels():
    """Load the class labels from the labels.txt file."""

    with open(LABELS_PATH, "r") as file:
        labels = []

        for line in file:
            parts = line.strip().split(" ", 1)

            if len(parts) == 2:
                labels.append(parts[1])
            else:
                labels.append(parts[0])

    return labels


def prepare_image(image_path, input_details):
    image = Image.open(image_path)
    image = image.convert("L")
    image = image.resize((96, 96))

    image_array = np .array(image, dtype=np.float32)

    image_array = (image_array / 127.5) - 1.0

    image_array = np.expand_dims(image_array, axis=0)
    image_array = np.expand_dims(image_array, axis=-1)

    return image_array


def identify_pill(image_path):
    """
Run a pill image through the trained model
and return the RxSort result.
"""

    interpreter, input_details, output_details = load_model()
    labels = load_labels()

    image_array = prepare_image(image_path, input_details)

    interpreter.set_tensor(input_details[0]["index"], image_array)
    interpreter.invoke()

    predictions = interpreter.get_tensor(output_details[0]["index"])[0]
    class_index = np.argmax(predictions)
    confidence = float(predictions[class_index])

    label = labels[class_index]

    pill_id = CLASS_TO_PILL_ID.get(class_index, None)

    result = {
        "label": label,
        "pill_id": pill_id,
        "confidence": confidence

    }

    return result


# --------------------------------------------------
# Test the model
# --------------------------------------------------

if __name__ == "__main__":

    test_image = "dataset/pill_003/top/image_001.jpg"

    print("\nRxSort AI Test")
    print("-------------------------")
    print("Testing image:", test_image)

    result = identify_pill(test_image)

    print("\nPrediction:")
    print("Medication:", result["label"])
    print("Database Pill ID:", result["pill_id"])
    print(
        "Confidence:",
        f'{result["confidence"] * 100:.2f}%'
    )
