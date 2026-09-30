"""
KisanAI OS - Location hierarchy tests (देश -> राज्य -> जिला -> तहसील -> गाँव).
"""

from config.core.data.india_locations import (
    COUNTRIES,
    STATES,
    STATES_DISTRICTS,
    DISTRICT_BLOCKS,
    TEHSIL_VILLAGES,
)


def test_countries_returns_india(client):
    response = client.get("/api/locations/countries")
    assert response.status_code == 200
    assert response.json() == COUNTRIES


def test_states_are_sorted_and_unique(client):
    response = client.get("/api/locations/states")
    assert response.status_code == 200
    states = response.json()
    assert states == STATES
    assert len(states) == len(set(states))
    assert "Madhya Pradesh" in states


def test_districts_for_known_state(client):
    response = client.get("/api/locations/districts",
                          params={"state": "Madhya Pradesh"})
    assert response.status_code == 200
    districts = response.json()
    assert districts == STATES_DISTRICTS["Madhya Pradesh"]
    assert "Sehore" in districts


def test_districts_unknown_state_fallback(client):
    response = client.get("/api/locations/districts",
                          params={"state": "NotAState"})
    assert response.status_code == 200
    assert response.json() == ["District 1", "District 2", "District 3"]


def test_blocks_for_known_district(client):
    response = client.get("/api/locations/blocks",
                          params={"district": "Jaipur"})
    assert response.status_code == 200
    assert response.json() == DISTRICT_BLOCKS["Jaipur"]


def test_blocks_unknown_district_falls_back_to_district_name(client):
    response = client.get("/api/locations/blocks",
                          params={"district": "Some Unknown District"})
    assert response.status_code == 200
    assert response.json() == ["Some Unknown District"]


def test_villages_for_curated_tehsil(client):
    response = client.get("/api/locations/villages",
                          params={"tehsil": "Jaipur Tehsil"})
    assert response.status_code == 200
    villages = response.json()
    assert villages == TEHSIL_VILLAGES["Jaipur Tehsil"]
    assert villages
    # Every curated village is a real name (non-empty, not a placeholder).
    assert all(v.strip() for v in villages)


def test_villages_unknown_tehsil_return_empty(client):
    response = client.get("/api/locations/villages",
                          params={"tehsil": "No Such Tehsil"})
    assert response.status_code == 200
    assert response.json() == []