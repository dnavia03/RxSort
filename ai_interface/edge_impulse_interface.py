from pathlib import Path
import cv2

from edge_impulse_linux.image import ImageImpulseRunner


# ==========================================================
# PROJECT PATHS
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_FOLDER = PROJECT_ROOT / "models"


# ==========================================================
# MODEL FILES
# ==========================================================
#
# These are the model filenames shown in your terminal.
# If you export another version later, update these names.
# ==========================================================

TOP_MODEL_PATH = (
    MODELS_FOLDER
    / "rxsort-pill-identification-(top)-linux-aarch64-v23-impulse-#1.eim"
)

BOTTOM_MODEL_PATH = (
    MODELS_FOLDER
    / "rxsort-pill-identification-(bottom)-linux-aarch64-v16-impulse-#1.eim"
)


# ==========================================================
# EDGE IMPULSE LABEL -> DATABASE PILL ID
# ==========================================================
#
# IMPORTANT:
# The text on the LEFT must match the Edge Impulse class
# label EXACTLY.
#
# The number on the RIGHT is the RxSort database pill ID.
# ==========================================================

LABEL_TO_PILL_ID = {

    "Ibuprofen": 3,

    "Simvastatin": 4,

    "Amlodipine Besylate & Benazepril Hydrochloride": 5,

    # Pill ID 6
    "Fexofenadine Hydrochloride": 6,

    "Mucinex": 7,

    "Hydrochlorothiazide & Losartan Potassium": 8,

    "Dexamethasone": 12,

    "Benadryl Allergy Ultratab Diphenhydramine": 13,

    "Labetalol Hydrochloride": 15,

    "Acetaminophen (Tylenol)": 16,

    # Empty chamber class
    "Nothing": 18,

    # New pills
    "Advil": 19,

    "Loperamide HCI": 20,
}


# ==========================================================
# NORMALIZE LABEL
# ==========================================================

def normalize_label(label):

    return str(label).strip()


# ==========================================================
# CLASSIFY ONE IMAGE
# ==========================================================

def identify_pill(image_path, model_path):

    image_path = Path(image_path)
    model_path = Path(model_path)

    # ------------------------------------------------------
    # VERIFY FILES
    # ------------------------------------------------------

    if not image_path.exists():

        print(
            f"ERROR: Image not found: {image_path}"
        )

        return None

    if not model_path.exists():

        print(
            f"ERROR: Model not found: {model_path}"
        )

        return None

    runner = None

    try:

        # ==================================================
        # START MODEL
        # ==================================================

        print(
            f"\nLoading model: {model_path.name}"
        )

        runner = ImageImpulseRunner(
            str(model_path)
        )

        # Debug can be changed to True later if needed.
        model_info = runner.init()

        print(
            "Model loaded successfully."
        )

        # ==================================================
        # GET MODEL LABELS
        # ==================================================

        model_parameters = model_info.get(
            "model_parameters",
            {}
        )

        labels = model_parameters.get(
            "labels",
            []
        )

        print(
            f"Model labels: {labels}"
        )

        if not labels:

            print(
                "ERROR: No labels found in model."
            )

            return None

        # ==================================================
        # LOAD IMAGE
        # ==================================================

        image = cv2.imread(
            str(image_path)
        )

        if image is None:

            print(
                f"ERROR: Could not read image: "
                f"{image_path}"
            )

            return None

        print(
            f"Original image size: "
            f"{image.shape[1]} x {image.shape[0]}"
        )

        # ==================================================
        # CONVERT BGR -> RGB
        # ==========================================================
        #
        # cv2.imread() returns BGR.
        # Edge Impulse expects RGB.
        # ==================================================

        image_rgb = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2RGB
        )

        # ==================================================
        # EDGE IMPULSE PREPROCESSING
        # ==========================================================
        #
        # This is the official Linux SDK image helper.
        # It handles resizing/cropping for the impulse.
        # ==================================================

        print(
            "Preparing image for Edge Impulse..."
        )

        features, cropped = (
            runner.get_features_from_image(
                image_rgb
            )
        )

        print(
            "Image preprocessing successful."
        )

        # ==================================================
        # OPTIONAL DEBUG IMAGE
        # ==========================================================
        #
        # This saves exactly what Edge Impulse passed to
        # the classifier, which is extremely useful when
        # checking framing.
        # ==================================================

        debug_path = (
            PROJECT_ROOT
            / "edge_impulse_debug.jpg"
        )

        cv2.imwrite(
            str(debug_path),
            cv2.cvtColor(
                cropped,
                cv2.COLOR_RGB2BGR
            )
        )

        print(
            f"Debug image saved: {debug_path}"
        )

        # ==================================================
        # RUN CLASSIFICATION
        # ==================================================

        print(
            "Running inference..."
        )

        result = runner.classify(
            features
        )

        # ==================================================
        # VERIFY RESULT
        # ==================================================

        if "result" not in result:

            print(
                "ERROR: Edge Impulse returned no result."
            )

            print(
                result
            )

            return None

        if "classification" not in result["result"]:

            print(
                "ERROR: Model did not return "
                "classification output."
            )

            print(
                "Raw result:"
            )

            print(
                result
            )

            return None

        classification = result[
            "result"
        ][
            "classification"
        ]

        # ==================================================
        # DISPLAY ALL SCORES
        # ==================================================

        print(
            "\n================================"
        )

        print(
            "      CLASSIFICATION SCORES"
        )

        print(
            "================================"
        )

        for label in labels:

            clean_label = normalize_label(
                label
            )

            confidence = classification.get(
                label,
                classification.get(
                    clean_label,
                    0.0
                )
            )

            print(
                f"{clean_label}: "
                f"{confidence * 100:.2f}%"
            )

        # ==================================================
        # FIND BEST RESULT
        # ==================================================

        best_raw_label = max(
            classification,
            key=classification.get
        )

        best_label = normalize_label(
            best_raw_label
        )

        best_confidence = classification[
            best_raw_label
        ]

        print(
            "\nBest match:"
        )

        print(
            f"{best_label}"
        )

        print(
            f"Confidence: "
            f"{best_confidence * 100:.2f}%"
        )

        # ==================================================
        # DATABASE ID LOOKUP
        # ==================================================

        pill_id = LABEL_TO_PILL_ID.get(
            best_label
        )

        if pill_id is None:

            print(
                "\nWARNING:"
            )

            print(
                f"'{best_label}' is not currently "
                f"mapped to an RxSort database ID."
            )

            print(
                "\nCurrent mapping:"
            )

            for label, mapped_id in (
                LABEL_TO_PILL_ID.items()
            ):

                print(
                    f"  {label} -> {mapped_id}"
                )

        else:

            print(
                f"Database Pill ID: {pill_id}"
            )

        # ==================================================
        # TIMING
        # ==================================================

        if "timing" in result:

            timing = result[
                "timing"
            ]

            print(
                "\nInference timing:"
            )

            for key, value in timing.items():

                print(
                    f"  {key}: {value} ms"
                )

        # ==================================================
        # RETURN RESULT TO DUAL CAMERA TEST
        # ==================================================

        return {

            "label":
                best_label,

            "confidence":
                best_confidence,

            "pill_id":
                pill_id

        }

    except IndexError as error:

        print(
            "\n================================"
        )

        print(
            "EDGE IMPULSE INDEX ERROR"
        )

        print(
            "================================"
        )

        print(
            error
        )

        print(
            "\nThe model loaded, but the Edge Impulse "
            "image helper failed while preprocessing."
        )

        print(
            "This usually points to an incompatibility "
            "between the exported EIM and the installed "
            "edge_impulse_linux SDK."
        )

        return None

    except Exception as error:

        print(
            "\n================================"
        )

        print(
            "EDGE IMPULSE ERROR"
        )

        print(
            "================================"
        )

        print(
            type(error).__name__,
            ":",
            error
        )

        return None

    finally:

        if runner is not None:

            try:

                runner.stop()

            except Exception:

                pass


# ==========================================================
# TOP MODEL
# ==========================================================

def identify_top_pill(image_path):

    return identify_pill(
        image_path,
        TOP_MODEL_PATH
    )


# ==========================================================
# BOTTOM MODEL
# ==========================================================

def identify_bottom_pill(image_path):

    return identify_pill(
        image_path,
        BOTTOM_MODEL_PATH
    )
