"""
KisanAI OS - real local ONNX crop-growth-stage detection provider tests.

Proves the settings-driven factory wires in a real local model provider
when a model file + labels exist, that the provider returns a genuine
``GROWTH_STAGE_DETECTED`` result with correct preprocessing/label
mapping, and that every missing/broken configuration degrades safely to
the honest ``MODEL_NOT_CONFIGURED`` result instead of crashing or
fabricating a crop growth stage.

``onnxruntime`` is stubbed in-process so these tests run without a real
model file, while the ``corrupt model`` test exercises the real loader's
error path.
"""

import sys
import types

import pytest

from config.core.providers import (
    get_growth_stage_provider,
)
from config.core.providers.base import UnavailableGrowthStageProvider
from config.settings import settings


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
        logits=(0.05, 0.85, 0.05, 0.03, 0.02),
        input_shape=None,
    ):
        self._logits = list(logits)
        self.input_shape = input_shape or [1, 224, 224, 3]

    def get_inputs(self):
        return [_FakeInput("input", self.input_shape)]

    def get_outputs(self):
        return [_FakeOutput([1, len(self._logits)])]

    def run(self, output_names, input_feed):
        return [self._logits]


def _install_fake_onnxruntime(monkeypatch, session=None):
    module = types.ModuleType("onnxruntime")
    module.InferenceSession = session or _FakeSession
    monkeypatch.setitem(sys.modules, "onnxruntime", module)


def _real_png_bytes():
    from PIL import Image
    import io

    buf = io.BytesIO()
    Image.new("RGB", (48, 48), (60, 120, 40)).save(buf, format="PNG")
    return buf.getvalue()


def _write_model_and_labels(tmp_path, labels=("Germination", "Vegetative", "Flowering", "Fruiting", "Maturity")):
    model = tmp_path / "growth.onnx"
    model.write_bytes(b"\x00fake-onnx-model-bytes")
    labels_file = tmp_path / "growth.txt"
    labels_file.write_text("\n".join(labels) + "\n", encoding="utf-8")
    return str(model), str(labels_file)


# ==========================================================
# Factory wiring (settings -> provider)
# ==========================================================

def test_unavailable_provider_returns_not_configured(monkeypatch):
    monkeypatch.setattr(settings, "GROWTH_STAGE_MODEL_PATH", "")
    monkeypatch.setattr(settings, "GROWTH_STAGE_MODEL_LABELS", "")
    provider = get_growth_stage_provider()
    assert isinstance(provider, UnavailableGrowthStageProvider)

    result = provider.detect("/nonexistent.png", "Wheat")
    assert result["status"] == "MODEL_NOT_CONFIGURED"
    assert result["growth_stage"] is None
    assert result["confidence"] is None
    assert result["model"] is None
    assert result["crop"] == "Wheat"


def test_provider_factory_returns_unavailable_when_no_path(monkeypatch):
    monkeypatch.setattr(
        settings, "GROWTH_STAGE_MODEL_PATH", "models/does-not-exist.onnx"
    )
    assert isinstance(
        get_growth_stage_provider(), UnavailableGrowthStageProvider
    )


def test_provider_factory_existing_model_returns_real_provider(monkeypatch, tmp_path):
    """A configured model path + labels build the real ONNX provider."""
    _install_fake_onnxruntime(monkeypatch)
    model, labels = _write_model_and_labels(tmp_path)
    monkeypatch.setattr(
        settings, "GROWTH_STAGE_MODEL_PATH", model
    )
    monkeypatch.setattr(
        settings, "GROWTH_STAGE_MODEL_LABELS", labels
    )

    from config.core.providers.growth_stage_provider import (
        OnnxGrowthStageProvider,
    )

    provider = get_growth_stage_provider()
    assert isinstance(provider, OnnxGrowthStageProvider)


# ==========================================================
# Provider behaviour (session stubbed)
# ==========================================================

def test_onnx_provider_loads_model_successfully(monkeypatch, tmp_path):
    """A valid model + labels load without error and the layout is
    resolved from the first input tensor."""
    _install_fake_onnxruntime(monkeypatch)
    model, labels = _write_model_and_labels(tmp_path)
    image = tmp_path / "plant.png"
    image.write_bytes(_real_png_bytes())

    from config.core.providers.growth_stage_provider import (
        OnnxGrowthStageProvider,
    )

    provider = OnnxGrowthStageProvider(model, labels_path=labels)
    result = provider.detect(str(image), "Wheat")
    assert result["status"] == "GROWTH_STAGE_DETECTED"
    assert provider._layout == "NHWC"
    assert provider._session is not None


def test_onnx_provider_successful_detection_returns_stage_confidence(
    monkeypatch, tmp_path
):
    _install_fake_onnxruntime(monkeypatch)
    model, labels = _write_model_and_labels(tmp_path)
    image = tmp_path / "plant.png"
    image.write_bytes(_real_png_bytes())

    from config.core.providers.growth_stage_provider import (
        OnnxGrowthStageProvider,
    )

    result = OnnxGrowthStageProvider(model, labels_path=labels).detect(
        str(image), "Wheat"
    )

    assert result["status"] == "GROWTH_STAGE_DETECTED"
    assert result["growth_stage"] == "Vegetative"
    # softmax([0.05, 0.85, 0.05, 0.03, 0.02]) -> argmax is class 1
    assert result["confidence"] == pytest.approx(0.3603, abs=0.001)
    assert result["model"] == "onnx:growth.onnx"
    assert result["crop"] == "Wheat"
    assert result["message"] == "ok"


def test_onnx_provider_missing_model_file_returns_not_configured(monkeypatch, tmp_path):
    _install_fake_onnxruntime(monkeypatch)
    labels = tmp_path / "growth.txt"
    labels.write_text("Germination\nVegetative\n", encoding="utf-8")
    image = tmp_path / "plant.png"
    image.write_bytes(_real_png_bytes())

    from config.core.providers.growth_stage_provider import (
        OnnxGrowthStageProvider,
    )

    result = OnnxGrowthStageProvider(
        str(tmp_path / "missing.onnx"), labels_path=str(labels)
    ).detect(str(image))
    assert result["status"] == "MODEL_NOT_CONFIGURED"
    assert result["growth_stage"] is None
    assert result["confidence"] is None


def test_onnx_provider_missing_labels_returns_not_configured(monkeypatch, tmp_path):
    _install_fake_onnxruntime(monkeypatch)
    # Model file only - no sibling .txt labels file.
    model = tmp_path / "growth.onnx"
    model.write_bytes(b"\x00fake-onnx-model-bytes")
    image = tmp_path / "plant.png"
    image.write_bytes(_real_png_bytes())

    from config.core.providers.growth_stage_provider import (
        OnnxGrowthStageProvider,
    )

    result = OnnxGrowthStageProvider(str(model)).detect(str(image))
    assert result["status"] == "MODEL_NOT_CONFIGURED"
    assert result["growth_stage"] is None
    assert result["confidence"] is None
    assert "labels" in result["message"]


def test_onnx_provider_label_count_mismatch_returns_not_configured(monkeypatch, tmp_path):
    _install_fake_onnxruntime(monkeypatch)
    model, _ = _write_model_and_labels(
        tmp_path, labels=("Germination", "Vegetative")
    )
    image = tmp_path / "plant.png"
    image.write_bytes(_real_png_bytes())

    from config.core.providers.growth_stage_provider import (
        OnnxGrowthStageProvider,
    )

    result = OnnxGrowthStageProvider(model).detect(str(image))
    assert result["status"] == "MODEL_NOT_CONFIGURED"
    assert "does not match" in result["message"]


def test_onnx_provider_corrupt_model_returns_not_configured(monkeypatch, tmp_path):
    """A real load attempt on garbage bytes must degrade, not 5xx."""
    model = tmp_path / "broken.onnx"
    model.write_bytes(b"not a real onnx file at all")
    labels = tmp_path / "broken.txt"
    labels.write_text("Germination\n", encoding="utf-8")
    image = tmp_path / "plant.png"
    image.write_bytes(_real_png_bytes())

    from config.core.providers.growth_stage_provider import (
        OnnxGrowthStageProvider,
    )

    provider = OnnxGrowthStageProvider(str(model), labels_path=str(labels))
    result = provider.detect(str(image))
    assert result["status"] == "MODEL_NOT_CONFIGURED"
    assert result["growth_stage"] is None
    assert result["confidence"] is None


def test_onnx_provider_invalid_image_path_returns_error(monkeypatch, tmp_path):
    """A missing image must not fabricate a growth stage."""
    _install_fake_onnxruntime(monkeypatch)
    model, labels = _write_model_and_labels(tmp_path)

    from config.core.providers.growth_stage_provider import (
        OnnxGrowthStageProvider,
    )

    with pytest.raises(Exception):
        OnnxGrowthStageProvider(
            model, labels_path=labels
        ).detect(str(tmp_path / "does-not-exist.png"))


def test_onnx_provider_nhwc_preprocessing(monkeypatch, tmp_path):
    _install_fake_onnxruntime(monkeypatch)
    model, labels = _write_model_and_labels(tmp_path)
    image = tmp_path / "plant.png"
    image.write_bytes(_real_png_bytes())

    from config.core.providers.growth_stage_provider import (
        OnnxGrowthStageProvider,
    )

    provider = OnnxGrowthStageProvider(model, labels_path=labels)
    assert provider._layout is None  # lazy: layout resolved on load
    result = provider.detect(str(image))
    assert result["status"] == "GROWTH_STAGE_DETECTED"
    assert provider._layout == "NHWC"


def test_onnx_provider_nchw_preprocessing(monkeypatch, tmp_path):
    _install_fake_onnxruntime(
        monkeypatch, session=lambda *a, **k: _FakeSession(
            *a, **k, input_shape=[1, 3, 224, 224]
        )
    )
    model, labels = _write_model_and_labels(tmp_path)
    image = tmp_path / "plant.png"
    image.write_bytes(_real_png_bytes())

    from config.core.providers.growth_stage_provider import (
        OnnxGrowthStageProvider,
    )

    provider = OnnxGrowthStageProvider(model, labels_path=labels)
    result = provider.detect(str(image))
    assert result["status"] == "GROWTH_STAGE_DETECTED"
    assert result["growth_stage"] == "Vegetative"
    assert provider._layout == "NCHW"
