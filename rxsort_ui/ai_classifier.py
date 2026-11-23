"""
ai_classifier.py
-----------------
Pill identification. Mirrors the pipeline described in the RxSort README:

    Camera Image -> Image Preprocessing -> TFLite Model -> Class Prediction

...run once for the top camera and once for the bottom camera, since testing
showed the two views produce different confidence behavior (see report
section F-2). The decision logic then requires both predictions to agree
and both confidences to clear the threshold before accepting the result,
exactly as shown in the "Compare Predictions" block of the system diagram.

Two classifier implementations are provided:

* ``DemoClassifier``  - simulates a capture + inference cycle with randomized
  but plausible results, including occasional low-confidence / disagreement
  cases so the reject flow can be demonstrated without real hardware.

* ``RealClassifier``  - a documented stub showing where to plug in Picamera2
  capture and a local LiteRT/TFLite interpreter, loading the two exported
  Edge Impulse models referenced in the RxSort report. This class is not
  exercised unless config.DEMO_MODE is False and the optional hardware
  dependencies are installed.

Swap which one is used by changing ``config.DEMO_MODE``; the UI only ever
talks to the common ``ClassificationResult`` object returned by ``classify()``.
"""

import random
from dataclasses import dataclass
from typing import Optional

import config
import database


@dataclass
class ClassificationResult:
    accepted: bool                      # True -> SORT, False -> REJECT
    pill: Optional[database.Pill]       # None when unidentified
    top_confidence: float
    bottom_confidence: float
    top_class_id: Optional[int]
    bottom_class_id: Optional[int]
    reason: str                         # human-readable explanation for the UI/log


class BaseClassifier:
    def classify(self) -> ClassificationResult:
        raise NotImplementedError


class DemoClassifier(BaseClassifier):
    """
    Simulates the top/bottom camera capture + dual-model inference cycle.

    Roughly 75% of simulated attempts return a confident, agreeing
    identification; the remainder simulate the two main rejection causes
    actually documented in the RxSort report: low confidence, and
    disagreement between the top and bottom camera models.
    """

    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)
        self._forced = None  # None (random), an int class_id, or "reject"

    def force_next(self, forced) -> None:
        """Make the next classify() call return a specific outcome instead of
        a random one: pass a pill's class_id to force that identification,
        "reject" to force an unidentified/low-confidence result, or None to
        go back to normal random behavior. Used by the Manual Control
        screen's scan simulator so a specific medication (and its photos,
        if any) can be tested on demand instead of waiting on random luck.
        The override applies to exactly one call and then clears itself.
        """
        self._forced = forced

    def classify(self) -> ClassificationResult:
        if self._forced is not None:
            forced, self._forced = self._forced, None  # one-shot
            if forced == "reject":
                return ClassificationResult(
                    accepted=False, pill=None, top_confidence=0.45, bottom_confidence=0.40,
                    top_class_id=None, bottom_class_id=None,
                    reason="Forced rejection (manual test trigger).",
                )
            pill = database.get_pill_by_class_id(forced)
            if pill is not None:
                return ClassificationResult(
                    accepted=True, pill=pill, top_confidence=0.97, bottom_confidence=0.95,
                    top_class_id=pill.class_id, bottom_class_id=pill.class_id,
                    reason="Forced identification (manual test trigger).",
                )
            # Unknown class_id requested: fall through to normal random behavior.

        known_pills = database.get_all_pills()
        chosen = self._rng.choice(known_pills)
        outcome = self._rng.random()

        if outcome < 0.75:
            # Confident, agreeing identification.
            top_conf = round(self._rng.uniform(0.90, 0.99), 3)
            bottom_conf = round(self._rng.uniform(0.85, 0.98), 3)
            return ClassificationResult(
                accepted=True,
                pill=chosen,
                top_confidence=top_conf,
                bottom_confidence=bottom_conf,
                top_class_id=chosen.class_id,
                bottom_class_id=chosen.class_id,
                reason="Top and bottom camera models agreed with high confidence.",
            )

        elif outcome < 0.90:
            # Low confidence on one or both cameras.
            top_conf = round(self._rng.uniform(0.30, 0.79), 3)
            bottom_conf = round(self._rng.uniform(0.30, 0.79), 3)
            return ClassificationResult(
                accepted=False,
                pill=None,
                top_confidence=top_conf,
                bottom_confidence=bottom_conf,
                top_class_id=chosen.class_id,
                bottom_class_id=chosen.class_id,
                reason=f"Confidence below the {int(config.CONFIDENCE_THRESHOLD * 100)}% "
                       f"threshold required to accept an identification.",
            )

        else:
            # Top/bottom camera disagreement.
            other = self._rng.choice([p for p in known_pills if p.class_id != chosen.class_id])
            top_conf = round(self._rng.uniform(0.85, 0.97), 3)
            bottom_conf = round(self._rng.uniform(0.85, 0.97), 3)
            return ClassificationResult(
                accepted=False,
                pill=None,
                top_confidence=top_conf,
                bottom_confidence=bottom_conf,
                top_class_id=chosen.class_id,
                bottom_class_id=other.class_id,
                reason="Top camera and bottom camera predictions did not match.",
            )


class RealClassifier(BaseClassifier):
    """
    Stub for the real on-device pipeline. Not used while config.DEMO_MODE
    is True. To bring this online on the Raspberry Pi:

      1. pip install tflite-runtime picamera2
      2. Export the two trained models from the Edge Impulse projects linked
         in the RxSort report and place them at config.TOP_CAMERA_MODEL_PATH
         and config.BOTTOM_CAMERA_MODEL_PATH.
      3. Fill in _capture_image() and _run_model() below.
      4. Set config.DEMO_MODE = False.

    The method bodies are intentionally left as guidance rather than being
    wired up automatically, since they depend on camera hardware and model
    files that only exist on the physical RxSort unit.
    """

    def __init__(self):
        self._top_interpreter = None
        self._bottom_interpreter = None
        # Example (uncomment once tflite-runtime is installed):
        #
        # from tflite_runtime.interpreter import Interpreter
        # self._top_interpreter = Interpreter(model_path=config.TOP_CAMERA_MODEL_PATH)
        # self._top_interpreter.allocate_tensors()
        # self._bottom_interpreter = Interpreter(model_path=config.BOTTOM_CAMERA_MODEL_PATH)
        # self._bottom_interpreter.allocate_tensors()

    def _capture_image(self, camera_index: int):
        """Capture a still frame from the top (0) or bottom (1) camera."""
        # Example using Picamera2 (two cameras, or one camera + a mirror/second
        # chamber position depending on the final imaging-chamber hardware):
        #
        # from picamera2 import Picamera2
        # picam = Picamera2(camera_num=camera_index)
        # picam.start()
        # frame = picam.capture_array()
        # picam.stop()
        # return frame
        raise NotImplementedError("Wire up Picamera2 capture here.")

    def _run_model(self, interpreter, image) -> (int, float):
        """Run inference and return (class_id, confidence)."""
        # Example:
        #
        # preprocessed = preprocess(image)  # resize/normalize to match training
        # input_details = interpreter.get_input_details()
        # output_details = interpreter.get_output_details()
        # interpreter.set_tensor(input_details[0]['index'], preprocessed)
        # interpreter.invoke()
        # output = interpreter.get_tensor(output_details[0]['index'])
        # class_id = int(output.argmax())
        # confidence = float(output.max())
        # return class_id, confidence
        raise NotImplementedError("Wire up TFLite inference here.")

    def classify(self) -> ClassificationResult:
        top_image = self._capture_image(0)
        bottom_image = self._capture_image(1)
        top_class_id, top_conf = self._run_model(self._top_interpreter, top_image)
        bottom_class_id, bottom_conf = self._run_model(self._bottom_interpreter, bottom_image)

        agree = (top_class_id == bottom_class_id) or not config.REQUIRE_CAMERA_AGREEMENT
        confident = (top_conf >= config.CONFIDENCE_THRESHOLD
                     and bottom_conf >= config.CONFIDENCE_THRESHOLD)

        if agree and confident:
            pill = database.get_pill_by_class_id(top_class_id)
            return ClassificationResult(
                accepted=pill is not None,
                pill=pill,
                top_confidence=top_conf,
                bottom_confidence=bottom_conf,
                top_class_id=top_class_id,
                bottom_class_id=bottom_class_id,
                reason="Top and bottom camera models agreed with high confidence."
                       if pill else "Predicted class has no matching database entry.",
            )

        reason = ("Top camera and bottom camera predictions did not match."
                  if not agree else
                  f"Confidence below the {int(config.CONFIDENCE_THRESHOLD * 100)}% threshold.")
        return ClassificationResult(
            accepted=False, pill=None, top_confidence=top_conf, bottom_confidence=bottom_conf,
            top_class_id=top_class_id, bottom_class_id=bottom_class_id, reason=reason,
        )


def get_classifier() -> BaseClassifier:
    """Factory used by the UI so screens never import a concrete class directly."""
    if config.DEMO_MODE:
        return DemoClassifier()
    return RealClassifier()
