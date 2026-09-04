"""
KisanAI OS
ONNX Crop Growth Stage Detection Provider

Runs a real, local, free crop growth-stage image classifier from an
ONNX model file. No external API and no paid service.

Mirrors the proven disease-detection, pest-detection, weed-detection
and nutrient-deficiency providers exactly (same loading, preprocessing
and honesty contract).

Runtime requirements (all free / open source):
  - ``onnxruntime``: CPU inference runtime.
  - ``Pillow``:      image decode + preprocessing.
  - ``GROWTH_STAGE_MODEL_PATH``: a ``.onnx`` model exporting one image
    input tensor and one score/logit output tensor.
  - a labels file (one class name per line, in the model's output
    order) - either ``<model>.txt`` next to the model or the
    ``GROWTH_STAGE_MODEL_LABELS`` setting.

The provider never fabricates a crop growth stage. If the model file is
missing/corrupt, the runtime is unavailable, the labels file is missing
or the output shape does not match the labels, it returns the
controlled ``MODEL_NOT_CONFIGURED`` result so the API and the app stay
honest (never confused with "no stage" or a real growth-stage
identification).
"""

import os

import numpy as np

from config.core.logger import logger
from config.core.providers.base import (
    RESULT_CONFIDENCE,
    RESULT_CROP,
    RESULT_GROWTH_STAGE,
    RESULT_MESSAGE,
    RESULT_MODEL,
    RESULT_STATUS,
    STATUS_GROWTH_STAGE_DETECTED,
    STATUS_MODEL_NOT_CONFIGURED,
    GrowthStageProvider,
)


def _softmax(scores: np.ndarray) -> np.ndarray:
    """Stable softmax over the last axis (class scores)."""
    shifted = scores - np.max(scores, axis=-1, keepdims=True)
    exp = np.exp(shifted)
    return exp / np.sum(exp, axis=-1, keepdims=True)


def _default_labels_path(model_path):
    """Labels live next to the model: ``<model>.txt``."""
    return os.path.splitext(model_path)[0] + ".txt"


def _read_labels(labels_path):
    """Read one class name per line. None when unreadable."""
    if not labels_path or not os.path.isfile(labels_path):
        return None
    try:
        with open(labels_path, "r", encoding="utf-8") as handle:
            labels = [
                line.strip()
                for line in handle
                if line.strip()
            ]
        return labels or None
    except OSError:
        return None


def _preprocess(image_path: str, input_size: int, layout: str):
    """Decode + resize + normalise the stored image for the model.

    ``image_path`` is the server-side absolute path produced by the
    secure upload layer - never client input. Returns a float32 tensor
    shaped ``[1, H, W, 3]`` (NHWC) or ``[1, 3, H, W]`` (NCHW).
    """
    from PIL import Image

    with Image.open(image_path) as img:
        img = img.convert("RGB")
        img = img.resize((input_size, input_size), Image.BILINEAR)
        arr = np.asarray(img, dtype=np.float32) / 255.0  # [H, W, 3]

    if layout == "NCHW":
        arr = np.transpose(arr, (2, 0, 1))

    return arr[np.newaxis, ...]


class OnnxGrowthStageProvider(GrowthStageProvider):
    """Real local crop growth-stage classifier backed by an ONNX model."""

    def __init__(self, model_path, labels_path=None, input_size=224):
        self.model_path = model_path
        self.labels_path = labels_path or _default_labels_path(model_path)
        self.input_size = int(input_size or 224)
        self._session = None
        self._input_name = None
        self._layout = None
        self._num_classes = None
        self._labels = None
        self._load_error = None

    @property
    def model_id(self):
        return "onnx:%s" % os.path.basename(self.model_path)

    def _ensure_loaded(self):
        """Load the model + labels once. Returns an error string on
        failure (so detect() can answer MODEL_NOT_CONFIGURED safely),
        or None when ready."""
        if self._session is not None:
            return None
        if self._load_error is not None:
            return self._load_error

        try:
            import onnxruntime as ort
        except Exception as error:  # runtime not installed
            logger.warning(
                "onnxruntime unavailable; crop growth stage detection "
                "not configured (%s)",
                error,
            )
            self._load_error = (
                "Crop growth stage model is not configured"
            )
            return self._load_error

        try:
            self._session = ort.InferenceSession(
                self.model_path, providers=["CPUExecutionProvider"]
            )

            inputs = self._session.get_inputs()
            if not inputs:
                return self._fail("ONNX model exposes no image input")

            self._input_name = inputs[0].name
            shape = list(inputs[0].shape)
            # [1, 224, 224, 3] -> NHWC ; [1, 3, 224, 224] -> NCHW
            self._layout = (
                "NHWC"
                if len(shape) == 4 and shape[-1] in (1, 3)
                else "NCHW"
            )

            outputs = self._session.get_outputs()
            out_shape = list(outputs[0].shape) if outputs else []
            self._num_classes = out_shape[-1] if out_shape and out_shape[-1] else None

            self._labels = _read_labels(self.labels_path)
            if not self._labels:
                return self._fail(
                    "Crop growth stage labels file is missing or empty: "
                    "%s" % self.labels_path
                )

            if self._num_classes and len(self._labels) != self._num_classes:
                return self._fail(
                    "Crop growth stage labels count (%d) does not match "
                    "the model output (%d)"
                    % (len(self._labels), self._num_classes)
                )

            logger.info(
                "Crop growth stage model loaded: %s (%s, %d classes)",
                self.model_path,
                self._layout,
                len(self._labels),
            )
            return None
        except Exception as error:  # corrupt / unsupported model
            logger.warning(
                "Failed to load crop growth stage model %s: %s",
                self.model_path,
                error,
            )
            self._load_error = (
                "Crop growth stage model is not configured"
            )
            return self._load_error

    def _fail(self, message):
        self._load_error = message
        logger.warning(message)
        return message

    def detect(self, image_path: str, crop_name: str | None = None) -> dict:
        error = self._ensure_loaded()
        if error is not None:
            return {
                RESULT_STATUS: STATUS_MODEL_NOT_CONFIGURED,
                RESULT_CROP: crop_name,
                RESULT_GROWTH_STAGE: None,
                RESULT_CONFIDENCE: None,
                RESULT_MODEL: None,
                RESULT_MESSAGE: error,
            }

        tensor = _preprocess(image_path, self.input_size, self._layout)
        outputs = self._session.run(None, {self._input_name: tensor})
        scores = np.asarray(outputs[0], dtype=np.float32).reshape(-1)
        probs = _softmax(scores)
        top = int(np.argmax(probs))
        label = (
            self._labels[top]
            if self._labels and top < len(self._labels)
            else "Class %d" % top
        )
        confidence = float(probs[top])

        logger.info(
            "Crop growth stage detection: %s (crop=%s) -> %s @ %.2f",
            os.path.basename(image_path),
            crop_name,
            label,
            confidence,
        )

        return {
            RESULT_STATUS: STATUS_GROWTH_STAGE_DETECTED,
            RESULT_CROP: crop_name,
            RESULT_GROWTH_STAGE: label,
            RESULT_CONFIDENCE: confidence,
            RESULT_MODEL: self.model_id,
            RESULT_MESSAGE: "ok",
        }
