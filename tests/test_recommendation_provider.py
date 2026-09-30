"""
KisanAI OS - real local ONNX recommendation-engine provider tests.

Proves the settings-driven factory wires in a real local model provider
when a model file + labels exist, that the provider returns a genuine,
traceable recommendation from structured context (feature-based, no image
decoding), and that every missing/broken configuration degrades safely to
the honest ``MODEL_NOT_CONFIGURED`` result instead of crashing or
fabricating a recommendation.

``onnxruntime`` is stubbed in-process so these tests run without a real
model file, while the ``corrupt model`` test exercises the real loader's
error path.
"""

import sys
import types

import pytest

from config.core.providers import get_recommendation_provider
from config.core.providers.recommendation_provider import (
    OnnxRecommendationProvider,
    UnavailableRecommendationProvider,
)
from config.settings import settings

FULL_CONTEXT = {
    "crop_name": "Wheat",
    "soil": {
        "ph": 6.5,
        "moisture": 45.0,
        "nitrogen": 50,
        "phosphorus": 25,
        "potassium": 30,
    },
    "weather": {
        "temperature": 28.0,
        "humidity": 60,
        "condition": "Partly Cloudy",
        "wind_speed": 8.0,
    },
}


def _write_model_and_labels(tmp_path, labels=None):
    model = tmp_path / "rec.onnx"
    model.write_bytes(b"\x00fake-onnx-model-bytes")
    labels_path = None
    if labels is not None:
        labels_file = tmp_path / "rec.txt"
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

def test_factory_ai_provider_without_model_path_returns_unavailable(monkeypatch):
    monkeypatch.setattr(settings, "RECOMMENDATION_PROVIDER", "ai")
    monkeypatch.setattr(settings, "RECOMMENDATION_MODEL_PATH", "")
    monkeypatch.setattr(settings, "RECOMMENDATION_MODEL_LABELS", "")
    assert isinstance(
        get_recommendation_provider(), UnavailableRecommendationProvider
    )


def test_factory_missing_model_file_returns_unavailable(monkeypatch):
    monkeypatch.setattr(settings, "RECOMMENDATION_PROVIDER", "ai")
    monkeypatch.setattr(
        settings, "RECOMMENDATION_MODEL_PATH", "models/does-not-exist.onnx"
    )
    assert isinstance(
        get_recommendation_provider(), UnavailableRecommendationProvider
    )


def test_factory_existing_model_returns_real_provider(monkeypatch, tmp_path):
    model, labels = _write_model_and_labels(tmp_path, labels=("irrigation",))
    monkeypatch.setattr(settings, "RECOMMENDATION_PROVIDER", "ai")
    monkeypatch.setattr(settings, "RECOMMENDATION_MODEL_PATH", model)
    monkeypatch.setattr(settings, "RECOMMENDATION_MODEL_LABELS", labels)
    provider = get_recommendation_provider()
    assert isinstance(provider, OnnxRecommendationProvider)
    assert provider.model_id == "onnx:rec.onnx"
    assert provider.labels_path == labels


# ==========================================================
# Provider behaviour (session stubbed)
# ==========================================================

def test_provider_returns_real_classification_recommendation(monkeypatch, tmp_path):
    _install_fake_onnxruntime(
        monkeypatch,
        session=lambda *a, **k: _FakeSession(*a, **k, logits=(0.1, 0.85, 0.05)),
    )
    model, labels = _write_model_and_labels(
        tmp_path, labels=("irrigation", "soil", "weather")
    )
    provider = OnnxRecommendationProvider(model, labels_path=labels)

    result = provider.recommend(FULL_CONTEXT)

    assert result["status"] == "RECOMMENDATION_AVAILABLE"
    assert result["model"] == "onnx:rec.onnx"
    assert result["provider"] == "onnx"
    assert len(result["recommendations"]) == 1
    item = result["recommendations"][0]
    assert item["category"] == "soil"
    assert item["source"] == "onnx"
    assert item["text"] == "Model-based recommendation: soil"
    assert "onnx:rec.onnx" in item["reason"]
    # softmax([0.1, 0.85, 0.05]) -> argmax is class 1 at ~0.5204
    assert result["confidence"] == pytest.approx(0.5204, abs=0.001)


def test_provider_returns_real_regression_recommendation(monkeypatch, tmp_path):
    _install_fake_onnxruntime(
        monkeypatch,
        session=lambda *a, **k: _FakeSession(*a, **k, logits=(4.2,)),
    )
    model, _ = _write_model_and_labels(tmp_path)
    provider = OnnxRecommendationProvider(model)

    result = provider.recommend(FULL_CONTEXT)

    assert result["status"] == "RECOMMENDATION_AVAILABLE"
    assert result["confidence"] is None
    assert result["model"] == "onnx:rec.onnx"
    assert len(result["recommendations"]) == 1
    item = result["recommendations"][0]
    assert item["category"] == "crop_care"
    assert item["source"] == "onnx"
    # float32 inference introduces tiny precision error -> approx.
    value = float(item["text"].split(": ")[-1])
    assert value == pytest.approx(4.2)


def test_provider_handles_1d_input_shape(monkeypatch, tmp_path):
    _install_fake_onnxruntime(
        monkeypatch,
        session=lambda *a, **k: _FakeSession(
            *a, **k, logits=(3.7,), input_shape=[8]
        ),
    )
    model, _ = _write_model_and_labels(tmp_path)
    provider = OnnxRecommendationProvider(model)

    result = provider.recommend(FULL_CONTEXT)
    assert result["status"] == "RECOMMENDATION_AVAILABLE"
    value = float(result["recommendations"][0]["text"].split(": ")[-1])
    assert value == pytest.approx(3.7)


def test_provider_missing_labels_returns_not_configured(monkeypatch, tmp_path):
    """Classification output without a labels file must not fabricate."""
    _install_fake_onnxruntime(
        monkeypatch,
        session=lambda *a, **k: _FakeSession(*a, **k, logits=(0.1, 0.85, 0.05)),
    )
    model, _ = _write_model_and_labels(tmp_path, labels=None)
    provider = OnnxRecommendationProvider(model)

    result = provider.recommend(FULL_CONTEXT)
    assert result["status"] == "MODEL_NOT_CONFIGURED"
    assert result["recommendations"] == []
    assert result["confidence"] is None
    assert "labels" in result["message"]


def test_provider_labels_count_mismatch_not_configured(monkeypatch, tmp_path):
    _install_fake_onnxruntime(
        monkeypatch,
        session=lambda *a, **k: _FakeSession(*a, **k, logits=(0.1, 0.85, 0.05)),
    )
    model, labels = _write_model_and_labels(
        tmp_path, labels=("irrigation", "soil")
    )
    provider = OnnxRecommendationProvider(model, labels_path=labels)

    result = provider.recommend(FULL_CONTEXT)
    assert result["status"] == "MODEL_NOT_CONFIGURED"
    assert "does not match" in result["message"]


def test_provider_corrupt_model_never_crashes(monkeypatch, tmp_path):
    """A real load attempt on garbage bytes must degrade, not 5xx."""
    model = tmp_path / "broken.onnx"
    model.write_bytes(b"not a real onnx file at all")
    provider = OnnxRecommendationProvider(str(model))

    result = provider.recommend(FULL_CONTEXT)
    assert result["status"] == "MODEL_NOT_CONFIGURED"
    assert result["recommendations"] == []
    assert result["confidence"] is None


def test_provider_without_onnxruntime_not_configured(monkeypatch, tmp_path):
    # A missing onnxruntime module must degrade gracefully (None in
    # sys.modules makes `import onnxruntime` raise ImportError).
    monkeypatch.setitem(sys.modules, "onnxruntime", None)
    model, _ = _write_model_and_labels(tmp_path)
    provider = OnnxRecommendationProvider(model)

    result = provider.recommend(FULL_CONTEXT)
    assert result["status"] == "MODEL_NOT_CONFIGURED"


def test_provider_missing_context_defaults_to_zero(monkeypatch, tmp_path):
    """Absent context fields must never block inference or be guessed:
    they default to 0.0 so the tensor is always complete."""
    _install_fake_onnxruntime(
        monkeypatch,
        session=lambda *a, **k: _FakeSession(*a, **k, logits=(2.5,)),
    )
    model, _ = _write_model_and_labels(tmp_path)
    provider = OnnxRecommendationProvider(model)

    result = provider.recommend({})

    assert result["status"] == "RECOMMENDATION_AVAILABLE"
    value = float(result["recommendations"][0]["text"].split(": ")[-1])
    assert value == pytest.approx(2.5)


# ==========================================================
# End-to-end through the real API
# ==========================================================

def test_api_returns_real_recommendation_when_model_configured(
    client, admin_headers, monkeypatch, tmp_path
):
    _install_fake_onnxruntime(
        monkeypatch,
        session=lambda *a, **k: _FakeSession(*a, **k, logits=(0.1, 0.85, 0.05)),
    )
    model, labels = _write_model_and_labels(
        tmp_path, labels=("irrigation", "soil", "weather")
    )
    monkeypatch.setattr(settings, "RECOMMENDATION_PROVIDER", "ai")
    monkeypatch.setattr(settings, "RECOMMENDATION_MODEL_PATH", model)
    monkeypatch.setattr(settings, "RECOMMENDATION_MODEL_LABELS", labels)

    payload = {
        "crop_name": "Wheat",
        "soil": {"ph": 6.5, "moisture": 45.0, "nitrogen": 50, "phosphorus": 25, "potassium": 30},
        "weather": {"temperature": 28.0, "humidity": 60, "condition": "Partly Cloudy", "wind_speed": 8.0},
    }
    response = client.post(
        "/api/recommendations", json=payload, headers=admin_headers
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "RECOMMENDATION_AVAILABLE"
    assert len(body["recommendations"]) == 1
    item = body["recommendations"][0]
    assert item["category"] == "soil"
    assert item["source"] == "onnx"
    assert body["model"] == "onnx:rec.onnx"
    assert body["provider"] == "onnx"
    assert body["confidence"] == pytest.approx(0.5204, abs=0.001)
    assert body["missing"] == []


def test_api_stays_not_configured_without_model(client, admin_headers, monkeypatch):
    monkeypatch.setattr(settings, "RECOMMENDATION_PROVIDER", "ai")
    monkeypatch.setattr(settings, "RECOMMENDATION_MODEL_PATH", "")
    payload = {
        "crop_name": "Wheat",
        "soil": {"ph": 6.5, "moisture": 45.0, "nitrogen": 50, "phosphorus": 25, "potassium": 30},
        "weather": {"temperature": 28.0, "humidity": 60, "condition": "Partly Cloudy", "wind_speed": 8.0},
    }
    response = client.post(
        "/api/recommendations", json=payload, headers=admin_headers
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "MODEL_NOT_CONFIGURED"
    assert body["recommendations"] == []
    assert body["confidence"] is None
