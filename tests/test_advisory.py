"""
KisanAI OS - Phase 5.6 Advisory module tests.

The advisory module is a stateless rule-based generator with no DB
persistence. Tests cover authentication, required-field validation,
response shape and echo, the full rule matrix (soil/weather/disease),
string normalization (padded and whitespace-only inputs), and
idempotency (no persistence means duplicates are impossible).
"""

import pytest

from config.core.services.advisory_service import AdvisoryService


def _advisory_payload(**overrides):
    payload = {
        "crop_name": "Wheat",
        "soil_type": "Loamy",
        "ph": 6.8,
        "moisture": 45,
        "nitrogen": 50,
        "phosphorus": 25,
        "potassium": 30,
        "temperature": 30.3,
        "humidity": 60.0,
        "condition": "Overcast",
        "wind_speed": 6.0,
        "disease_name": "",
        "disease_severity": "",
    }
    payload.update(overrides)
    return payload


def _generate(**overrides):
    args = {
        "crop_name": "Wheat",
        "soil_type": "Loamy",
        "ph": 6.8,
        "moisture": 45,
        "nitrogen": 50,
        "phosphorus": 25,
        "potassium": 30,
        "temperature": 30.3,
        "humidity": 60.0,
        "condition": "Overcast",
        "wind_speed": 6.0,
        "disease_name": "",
        "disease_severity": "",
    }
    args.update(overrides)
    return AdvisoryService().generate_advisory(**args)


# ==========================================================
# A. Authentication (401)
# ==========================================================

def test_advisory_requires_auth(client):
    response = client.post("/api/advisory", json=_advisory_payload())
    assert response.status_code == 401


def test_advisory_any_authenticated_user_can_generate(client, user_headers):
    response = client.post(
        "/api/advisory", json=_advisory_payload(), headers=user_headers
    )
    assert response.status_code == 200
    assert response.json()["success"] is True


# ==========================================================
# B. Required-field validation (422)
# ==========================================================

@pytest.mark.parametrize(
    "field",
    [
        "crop_name",
        "soil_type",
        "ph",
        "moisture",
        "nitrogen",
        "phosphorus",
        "potassium",
        "temperature",
        "humidity",
        "condition",
        "wind_speed",
    ],
)
def test_advisory_required_field_422(client, user_headers, field):
    payload = _advisory_payload()
    payload.pop(field)

    response = client.post(
        "/api/advisory", json=payload, headers=user_headers
    )
    assert response.status_code == 422


# ==========================================================
# C. Response shape and echo
# ==========================================================

def test_advisory_response_shape(client, user_headers):
    response = client.post(
        "/api/advisory", json=_advisory_payload(), headers=user_headers
    )
    assert response.status_code == 200

    body = response.json()
    assert body["success"] is True
    assert body["service"] == "KisanAI Advisory Engine"
    assert "version" in body
    assert body["crop"] == "Wheat"

    assert set(body["soil"].keys()) == {
        "type", "ph", "moisture", "nitrogen", "phosphorus", "potassium"
    }
    assert set(body["weather"].keys()) == {
        "temperature", "humidity", "condition", "wind_speed"
    }
    assert set(body["disease"].keys()) == {"name", "severity"}

    assert isinstance(body["recommendations"], list)
    assert isinstance(body["warnings"], list)
    assert "generated_at" in body


def test_advisory_echoes_input(client, user_headers):
    response = client.post(
        "/api/advisory",
        json=_advisory_payload(
            crop_name="Rice",
            soil_type="Clay",
            ph=6.2,
            moisture=40,
            nitrogen=30,
            phosphorus=20,
            potassium=15,
            temperature=28.0,
            humidity=70.0,
            condition="Partly Cloudy",
            wind_speed=8.0,
            disease_name="Blast",
            disease_severity="High",
        ),
        headers=user_headers,
    )
    assert response.status_code == 200

    body = response.json()
    assert body["crop"] == "Rice"
    assert body["soil"]["type"] == "Clay"
    assert body["soil"]["ph"] == 6.2
    assert body["weather"]["condition"] == "Partly Cloudy"
    assert body["disease"]["name"] == "Blast"
    assert body["disease"]["severity"] == "High"


# ==========================================================
# D. Idempotency (advisory is never persisted -> no duplicates)
# ==========================================================

def test_advisory_repeated_request_identical(client, user_headers):
    payload = _advisory_payload()

    first = client.post("/api/advisory", json=payload, headers=user_headers)
    second = client.post("/api/advisory", json=payload, headers=user_headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["recommendations"] == second.json()["recommendations"]


# ==========================================================
# E. Soil rule matrix
# ==========================================================

def test_advisory_low_ph_rec(client):
    result = _generate(ph=5.0)
    assert any("lime" in r.lower() for r in result["recommendations"])


def test_advisory_high_ph_rec(client):
    result = _generate(ph=8.5)
    assert any("soil ph is high" in r.lower() for r in result["recommendations"])


def test_advisory_neutral_ph_rec(client):
    result = _generate(ph=6.8)
    assert any("suitable range" in r.lower() for r in result["recommendations"])


def test_advisory_low_moisture_rec(client):
    result = _generate(moisture=20)
    assert any("irrigation" in r.lower() for r in result["recommendations"])


def test_advisory_high_moisture_warning(client):
    result = _generate(moisture=90)
    assert any("avoid unnecessary irrigation" in w.lower() for w in result["warnings"])


def test_advisory_reasonable_moisture_rec(client):
    result = _generate(moisture=45)
    assert any("reasonable range" in r.lower() for r in result["recommendations"])


# ==========================================================
# F. Nutrient rule matrix
# ==========================================================

def test_advisory_low_nutrients_recs(client):
    result = _generate(nitrogen=10, phosphorus=10, potassium=10)
    recs = " ".join(result["recommendations"]).lower()
    assert "nitrogen" in recs
    assert "phosphorus" in recs
    assert "potassium" in recs


def test_advisory_adequate_nutrients_no_recs(client):
    result = _generate(nitrogen=80, phosphorus=40, potassium=50)
    recs = " ".join(result["recommendations"]).lower()
    assert "nitrogen level appears low" not in recs
    assert "phosphorus level appears low" not in recs
    assert "potassium level appears low" not in recs


# ==========================================================
# G. Weather rule matrix
# ==========================================================

def test_advisory_high_temperature_warning(client):
    result = _generate(temperature=38.0)
    assert any("heat stress" in w.lower() for w in result["warnings"])


def test_advisory_low_temperature_warning(client):
    result = _generate(temperature=5.0)
    assert any("cold stress" in w.lower() for w in result["warnings"])


def test_advisory_high_humidity_warning(client):
    result = _generate(humidity=85.0)
    assert any("fungal" in w.lower() for w in result["warnings"])


def test_advisory_rainy_condition_rec(client):
    result = _generate(condition="Moderate Rain")
    assert any("drainage" in r.lower() for r in result["recommendations"])


def test_advisory_cloudy_condition_rec(client):
    result = _generate(condition="Partly Cloudy")
    assert any("disease development" in r.lower() for r in result["recommendations"])


def test_advisory_overcast_condition_rec(client):
    result = _generate(condition="Overcast")
    assert any("disease development" in r.lower() for r in result["recommendations"])


def test_advisory_high_wind_warning(client):
    result = _generate(wind_speed=25.0)
    assert any("spraying" in w.lower() for w in result["warnings"])


def test_advisory_condition_match_case_insensitive(client):
    result = _generate(condition="MODERATE RAIN")
    assert any("drainage" in r.lower() for r in result["recommendations"])


# ==========================================================
# H. Disease rule matrix
# ==========================================================

def test_advisory_disease_high_severity(client):
    result = _generate(disease_name="Rust", disease_severity="High")
    assert any(
        "monitor the crop for symptoms of rust" in r.lower()
        for r in result["recommendations"]
    )
    assert any("severity is high" in w.lower() for w in result["warnings"])


def test_advisory_disease_medium_severity(client):
    result = _generate(disease_name="Blast", disease_severity="Medium")
    assert any("severity is medium" in r.lower() for r in result["recommendations"])


def test_advisory_no_disease_no_specific_rec(client):
    result = _generate(disease_name="", disease_severity="")
    assert not any(
        "monitor the crop for symptoms" in r.lower()
        for r in result["recommendations"]
    )


def test_advisory_padded_disease_input(client):
    result = _generate(
        disease_name="  Rust  ", disease_severity="  High  "
    )
    assert any(
        "monitor the crop for symptoms of rust" in r.lower()
        for r in result["recommendations"]
    )
    assert any("severity is high" in w.lower() for w in result["warnings"])
    assert result["disease"]["name"] == "Rust"
    assert result["disease"]["severity"] == "High"


def test_advisory_whitespace_only_disease_ignored(client):
    result = _generate(disease_name="   ", disease_severity="   ")
    assert not any(
        "monitor the crop for symptoms" in r.lower()
        for r in result["recommendations"]
    )
    assert result["disease"]["name"] == ""
    assert result["disease"]["severity"] == ""


# ==========================================================
# I. Crop handling / normalization
# ==========================================================

def test_advisory_crop_monitoring_rec(client):
    result = _generate(crop_name="Wheat")
    assert any("continue regular monitoring of wheat" in r.lower() for r in result["recommendations"])


def test_advisory_blank_crop_name_no_monitoring_rec(client):
    result = _generate(crop_name="")
    assert not any("continue regular monitoring of" in r.lower() for r in result["recommendations"])
    assert result["crop"] == ""


def test_advisory_padded_crop_name_normalized(client):
    result = _generate(crop_name="  Rice  ")
    assert any(
        "continue regular monitoring of rice" in r.lower()
        for r in result["recommendations"]
    )
    assert result["crop"] == "Rice"


def test_advisory_whitespace_only_crop_name_normalized(client):
    result = _generate(crop_name="   ")
    assert not any("continue regular monitoring of" in r.lower() for r in result["recommendations"])
    assert result["crop"] == ""


# ==========================================================
# J. Recommendations never empty
# ==========================================================

def test_advisory_recommendations_never_empty(client):
    result = _generate()
    assert len(result["recommendations"]) >= 1
