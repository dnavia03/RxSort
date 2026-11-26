import sys
import cv2

from edge_impulse_linux.image import ImageImpulseRunner


def main():

    print("\nEfficientNet standalone test starting...")

    if len(sys.argv) != 3:

        print(
            "Usage:\n"
            "python -m ai_interface.test_efficientnet "
            "<model.eim> <image.jpg>"
        )

        return

    model_path = sys.argv[1]
    image_path = sys.argv[2]

    print(f"\nModel: {model_path}")
    print(f"Image: {image_path}")

    runner = ImageImpulseRunner(
        model_path
    )

    try:

        print(
            "\nInitializing model..."
        )

        model_info = runner.init()

        print(
            "Model loaded successfully."
        )

        print(
            "Labels:",
            model_info["model_parameters"]["labels"]
        )

        print(
            "\nLoading image..."
        )

        image = cv2.imread(
            image_path
        )

        if image is None:

            print(
                "ERROR: Could not open image."
            )

            return

        print(
            f"Image size: "
            f"{image.shape[1]} x "
            f"{image.shape[0]}"
        )

        image = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2RGB
        )

        print(
            "\nRunning image preprocessing..."
        )

        features, cropped = (
            runner.get_features_from_image(
                image
            )
        )

        print(
            "Preprocessing successful."
        )

        print(
            "\nRunning inference..."
        )

        result = runner.classify(
            features
        )

        print(
            "\nInference successful."
        )

        print(
            "\nResult:"
        )

        print(
            result
        )

    except Exception as error:

        print(
            "\nERROR:"
        )

        print(
            type(error).__name__,
            ":",
            error
        )

    finally:

        try:

            runner.stop()

        except Exception:

            pass


if __name__ == "__main__":

    main()
