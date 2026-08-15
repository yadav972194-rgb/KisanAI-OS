"""
KisanAI OS
Location API Routes
Provides country/state/district/block hierarchy for farmer profiles.
"""

from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.orm import Session

from config.core.database import get_db
from config.core.data.india_locations import (
    COUNTRIES,
    STATES,
    STATES_DISTRICTS,
    DISTRICT_BLOCKS,
)


router = APIRouter(prefix="/api/locations", tags=["locations"])


def _districts_for_state(state: str) -> list[str]:
    """Return the curated district list for *state*, or a small fallback."""
    return STATES_DISTRICTS.get(state, []) or []


def _blocks_for_district(district: str) -> list[str]:
    """Return the curated block list for *district*, or fallback."""
    return DISTRICT_BLOCKS.get(district, DISTRICT_BLOCKS.get("default", []) or [])


@router.get("/countries", response_model=list[str])
def get_countries():
    """Return the list of supported countries."""
    return COUNTRIES


@router.get("/states", response_model=list[str])
def get_states():
    """Return the list of supported Indian states/UTs."""
    return STATES


@router.get("/districts", response_model=list[str])
def get_districts(state: str = Query(..., description="Indian state name")):
    """Return the districts for the given state.

    If the state is not recognised, a small generic list is returned
    so the UI never crashes.
    """
    districts = _districts_for_state(state)
    if not districts:
        # Fallback: return a few common districts so the UI is not empty.
        districts = ["District 1", "District 2", "District 3"]
    return districts


@router.get("/blocks", response_model=list[str])
def get_blocks(district: str = Query(..., description="District name")):
    """Return the blocks/tehsils for the given district.

    If no blocks are configured for this district the UI can fall back
    to showing the district name itself.
    """
    blocks = _blocks_for_district(district)
    if not blocks:
        # Fallback: return the district name so the UI always has an option.
        return [district]
    return blocks