"""
KisanAI OS - real local ONNX prediction-engine provider tests.

Proves the settings-driven factory wires in a real local model provider
when a model file + labels exist, that the provider returns a genuine
prediction from structured context (feature-based, no image decoding),
and that every missing/broken configuration degrades safely to the
honest ``MODEL_NOT_CONFIGURED`` result instead of crashing or
fabricating a prediction.

``onnxruntime`` is stubbed in-process so these tests run without a real
model file, while the ``corrupt model`` test exercises the real loader's
error path.
"""

import sys
import types

import pytest

from config.core.providers import get_prediction_provider
from config.core.providers.prediction_provider import (
    OnnxPredictionProvider,
    UnavailablePredictionProvider,
)
from config.settings import settings

FULL_CONTEXT = {
    "crop_name": "Wheat",
    "soil": {
        "ph": 6.5,
        "moisture": 30.0,
        "nitrogen": 40,
        "phosphorus": 25,
        "potassium": 30,
    },
    "weather": {
        "temperature": 28.0,
        "humidity": 60,
        "wind_speed": 8.0,
    },
}


def _write_model_and_labels(tmp_path, labels=None):
    model = tmp_path / "yield.onnx"
    model.write_bytes(b"\x00fake-onnx-model-bytes")
    labels_path = None
    if labels is not None:
        labels_file = tmp_path / "yield.txt"
        labels_file.write_text("\n".join(labels) + "\n", encoding="utf-8")
        labels_path = str(labels_file)
    return str(model), labels_path


class _FakeInput:
    def __init__(self, name, shape):
        self.name = name
        self.shape = shape


class _FakeOutput:
    def __init__(self, shape):
        self.shape = shape


class _FakeSession:
    """Stands in for onnxruntime.InferenceSession."""

    def __init__(
        self,
        path,
        providers=None,
        logits=(4.2,),
        input_shape=None,
        output_shape=None,
    ):
        self._logits = list(logits)
        self.input_shape = input_shape or [1, 8]
        self.output_shape = output_shape or [1, len(self._logits)]

    def get_inputs(self):
        return [_FakeInput("input", self.input_shape)]

    def get_outputs(self):
        return [_FakeOutput(self.output_shape)]

    def run(self, output_names, input_feed):
        return [self._logits]


def _install_fake_onnxruntime(monkeypatch, session=None):
    module = types.ModuleType("onnxruntime")
    module.InferenceSession = session or _FakeSession
    monkeypatch.setitem(sys.modules, "onnxruntime", module)


# ==========================================================
# Factory wiring (settings -> provider)
# ==========================================================

def test_factory_unconfigured_path_returns_unavailable(monkeypatch):
    monkeypatch.setattr(settings, "PREDICTION_MODEL_PATH", "")
    monkeypatch.setattr(settings, "PREDICTION_MODEL_LABELS", "")
    assert isinstance(
        get_prediction_provider(), UnavailablePredictionProvider
    )


def test_factory_missing_model_file_returns_unavailable(monkeypatch):
    monkeypatch.setattr(
        settings, "PREDICTION_MODEL_PATH", "models/does-not-exist.onnx"
    )
    assert isinstance(
        get_prediction_provider(), UnavailablePredictionProvider
    )


def test_factory_existing_model_returns_real_provider(monkeypatch, tmp_path):
    model, labels = _write_model_and_labels(tmp_path, labels=("Class A",))
    monkeypatch.setattr(settings, "PREDICTION_MODEL_PATH", model)
    monkeypatch.setattr(settings, "PREDICTION_MODEL_LABELS", labels)
    provider = get_prediction_provider()
    assert isinstance(provider, OnnxPredictionProvider)
    assert provider.model_id == "onnx:yield.onnx"
    assert provider.labels_path == labels


# ==========================================================
# Provider behaviour (session stubbed)
# ==========================================================

def test_provider_returns_real_regression_prediction(monkeypatch, tmp_path):
    _install_fake_onnxruntime(
        monkeypatch,
        session=lambda *a, **k: _FakeSession(*a, **k, logits=(4.2,)),
    )
    model, _ = _write_model_and_labels(tmp_path)
    provider = OnnxPredictionProvider(model)

    result = provider.predict("crop_yield", FULL_CONTEXT)

    assert result["status"] == "COMPLETE"
    # float32 inference introduces tiny precision error -> approx.
    assert result["result"]["yield_tons_per_hectare"] == pytest.approx(4.2)
    assert result["confidence"] is None
    assert result["model"] == "onnx:yield.onnx"
    assert result["metadata"]["type"] == "crop_yield"
    assert result["metadata"]["features_used"]["ph"] is True


def test_provider_classification_prediction_with_labels(monkeypatch, tmp_path):
    _install_fake_onnxruntime(
        monkeypatch,
        session=lambda *a, **k: _FakeSession(*a, **k, logits=(0.1, 0.85, 0.05)),
    )
    model, labels = _write_model_and_labels(
        tmp_path, labels=("Healthy", "Leaf Blight", "Rust")
    )
    provider = OnnxPredictionProvider(model, labels_path=labels)

    result = provider.predict("soil_analysis", FULL_CONTEXT)

    assert result["status"] == "COMPLETE"
    assert result["result"] == {"prediction": "Leaf Blight"}
    # softmax([0.1, 0.85, 0.05]) -> argmax is class 1 at ~0.5204
    assert result["confidence"] == pytest.approx(0.5204, abs=0.001)
    assert result["metadata"]["class_index"] == 1


def test_provider_handles_1d_input_shape(monkeypatch, tmp_path):
    _install_fake_onnxruntime(
        monkeypatch,
        session=lambda *a, **k: _FakeSession(
            *a, **k, logits=(3.7,), input_shape=[8]
        ),
    )
    model, _ = _write_model_and_labels(tmp_path)
    provider = OnnxPredictionProvider(model)

    result = provider.predict("crop_yield", FULL_CONTEXT)
    assert result["status"] == "COMPLETE"
    assert result["result"]["yield_tons_per_hectare"] == pytest.approx(3.7)


def test_provider_missing_labels_returns_not_configured(monkeypatch, tmp_path):
    """Classification output without a labels file must not fabricate."""
    _install_fake_onnxruntime(
        monkeypatch,
        session=lambda *a, **k: _FakeSession(*a, **k, logits=(0.1, 0.85, 0.05)),
    )
    model, _ = _write_model_and_labels(tmp_path, labels=None)
    provider = OnnxPredictionProvider(model)

    result = provider.predict("soil_analysis", FULL_CONTEXT)
    assert result["status"] == "MODEL_NOT_CONFIGURED"
    assert result["result"] is None
    assert result["confidence"] is None
    assert "labels" in result["message"]


def test_provider_labels_count_mismatch_not_configured(monkeypatch, tmp_path):
    _install_fake_onnxruntime(
        monkeypatch,
        session=lambda *a, **k: _FakeSession(*a, **k, logits=(0.1, 0.85, 0.05)),
    )
    model, labels = _write_model_and_labels(
        tmp_path, labels=("Healthy", "Rust")
    )
    provider = OnnxPredictionProvider(model, labels_path=labels)

    result = provider.predict("soil_analysis", FULL_CONTEXT)
    assert result["status"] == "MODEL_NOT_CONFIGURED"
    assert "does not match" in result["message"]


def test_provider_corrupt_model_never_crashes(monkeypatch, tmp_path):
    """A real load attempt on garbage bytes must degrade, not 5xx."""
    model = tmp_path / "broken.onnx"
    model.write_bytes(b"not a real onnx file at all")
    provider = OnnxPredictionProvider(str(model))

    result = provider.predict("crop_yield", FULL_CONTEXT)
    assert result["status"] == "MODEL_NOT_CONFIGURED"
    assert result["result"] is None
    assert result["confidence"] is None


def test_provider_without_onnxruntime_not_configured(monkeypatch, tmp_path):
    # A missing onnxruntime module must degrade gracefully (None in
    # sys.modules makes `import onnxruntime` raise ImportError).
    monkeypatch.setitem(sys.modules, "onnxruntime", None)
    model, _ = _write_model_and_labels(tmp_path)
    provider = OnnxPredictionProvider(model)

    result = provider.predict("crop_yield", FULL_CONTEXT)
    assert result["status"] == "MODEL_NOT_CONFIGURED"


def test_provider_missing_context_defaults_to_zero(monkeypatch, tmp_path):
    """Absent context fields must never block inference or be guessed:
    they default to 0.0 and are reported as not-present in metadata."""
    _install_fake_onnxruntime(
        monkeypatch,
        session=lambda *a, **k: _FakeSession(*a, **k, logits=(2.5,)),
    )
    model, _ = _write_model_and_labels(tmp_path)
    provider = OnnxPredictionProvider(model)

    result = provider.predict("crop_yield", {})

    assert result["status"] == "COMPLETE"
    assert result["result"] == {"yield_tons_per_hectare": 2.5}
    used = result["metadata"]["features_used"]
    assert all(flag is False for flag in used.values())


# ==========================================================
# End-to-end through the real API
# ==========================================================

def test_api_returns_real_prediction_when_model_configured(
    client, user_headers, monkeypatch, tmp_path
):
    _install_fake_onnxruntime(
        monkeypatch,
        session=lambda *a, **k: _FakeSession(*a, **k, logits=(4.2,)),
    )
    model, _ = _write_model_and_labels(tmp_path)
    monkeypatch.setattr(settings, "PREDICTION_MODEL_PATH", model)
    monkeypatch.setattr(settings, "PREDICTION_MODEL_LABELS", "")

    payload = {
        "prediction_type": "crop_yield",
        "crop_name": "Wheat",
        "soil": {"ph": 6.5, "moisture": 30.0},
        "weather": {"temperature": 28.0, "humidity": 60},
    }
    response = client.post(
        "/api/predictions", json=payload, headers=user_headers
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "COMPLETE"
    assert body["result"]["yield_tons_per_hectare"] == pytest.approx(4.2)
    assert body["model"] == "onnx:yield.onnx"
    assert body["prediction_type"] == "crop_yield"


def test_api_stays_not_configured_without_model(
    client, user_headers, monkeypatch
):
    monkeypatch.setattr(settings, "PREDICTION_MODEL_PATH", "")
    payload = {
        "prediction_type": "crop_yield",
        "crop_name": "Wheat",
    }
    response = client.post(
        "/api/predictions", json=payload, headers=user_headers
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "MODEL_NOT_CONFIGURED"
    assert body["result"] is None
    assert body["confidence"] is None
