"""Tests for the FitFindr planning loop."""

from unittest.mock import patch

from agent import run_agent
from utils.data_loader import get_empty_wardrobe, get_example_wardrobe

BAND_TEE = {
    "id": "lst_033",
    "title": "Vintage Band Tee — Faded Grey",
    "description": "Faded grey band-style tee with distressed graphic.",
    "category": "tops",
    "style_tags": ["vintage", "grunge", "graphic tee"],
    "size": "L",
    "condition": "fair",
    "price": 19.0,
    "colors": ["grey", "charcoal"],
    "brand": None,
    "platform": "depop",
}

MOCK_OUTFIT = "Pair with baggy straight-leg jeans and chunky white sneakers."
MOCK_FIT_CARD = "thrifted this faded band tee off depop for $19 🖤"


def test_no_results_skips_downstream_tools():
    session = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )

    assert session["error"] is not None
    assert session["search_results"] == []
    assert session["selected_item"] is None
    assert session["outfit_suggestion"] is None
    assert session["fit_card"] is None


@patch("agent.create_fit_card", return_value=MOCK_FIT_CARD)
@patch("agent.suggest_outfit", return_value=MOCK_OUTFIT)
@patch("agent.search_listings", return_value=[BAND_TEE])
def test_state_passes_between_tools(mock_search, mock_outfit, mock_fit_card):
    wardrobe = get_example_wardrobe()
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=wardrobe,
    )

    mock_search.assert_called_once()
    mock_outfit.assert_called_once_with(new_item=BAND_TEE, wardrobe=wardrobe)
    mock_fit_card.assert_called_once_with(outfit=MOCK_OUTFIT, new_item=BAND_TEE)

    assert session["error"] is None
    assert session["selected_item"] == BAND_TEE
    assert session["outfit_suggestion"] == MOCK_OUTFIT
    assert session["fit_card"] == MOCK_FIT_CARD


@patch("agent.create_fit_card")
@patch("agent.suggest_outfit", return_value="General styling advice for an empty closet.")
@patch("agent.search_listings", return_value=[BAND_TEE])
def test_empty_wardrobe_skips_fit_card(mock_search, mock_outfit, mock_fit_card):
    session = run_agent(
        query="vintage graphic tee under $30",
        wardrobe=get_empty_wardrobe(),
    )

    mock_outfit.assert_called_once()
    mock_fit_card.assert_not_called()

    assert session["selected_item"] == BAND_TEE
    assert session["outfit_suggestion"] is not None
    assert session["fit_card"] is None
