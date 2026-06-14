"""Tests for FitFindr tool functions."""

from unittest.mock import patch

from tools import create_fit_card, search_listings, suggest_outfit
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

OUTFIT_SUGGESTION = (
    "Pair this with your baggy straight-leg jeans and chunky white sneakers "
    "for an easy streetwear look."
)

LISTING_FIELDS = {
    "id",
    "title",
    "description",
    "category",
    "style_tags",
    "size",
    "condition",
    "price",
    "colors",
    "brand",
    "platform",
}


# ── search_listings ───────────────────────────────────────────────────────────


def test_search_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) > 0
    assert LISTING_FIELDS.issubset(results[0].keys())


def test_search_empty_results():
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []


def test_search_price_filter():
    results = search_listings("jacket", size=None, max_price=10)
    assert all(item["price"] <= 10 for item in results)


# ── suggest_outfit ────────────────────────────────────────────────────────────


def test_suggest_outfit_empty_wardrobe_uses_fallback():
    """Empty wardrobe: returns informative advice, never crashes or returns ''."""
    with patch("tools._call_groq_llm", return_value=""):
        result = suggest_outfit(BAND_TEE, get_empty_wardrobe())

    assert isinstance(result, str)
    assert result.strip()
    assert "wardrobe is empty" in result.lower()


def test_suggest_outfit_empty_wardrobe_with_llm_advice():
    """Empty wardrobe: LLM general styling advice is returned when available."""
    mock_advice = (
        "Pair this vintage tee with relaxed denim and chunky sneakers "
        "for a classic grunge look."
    )
    with patch("tools._call_groq_llm", return_value=mock_advice):
        result = suggest_outfit(BAND_TEE, get_empty_wardrobe())

    assert result == mock_advice


@patch(
    "tools._call_groq_llm",
    return_value=(
        "Pair this with your baggy straight-leg jeans and chunky white sneakers. "
        "Roll the sleeves once for shape."
    ),
)
def test_suggest_outfit_with_wardrobe(mock_llm):
    result = suggest_outfit(BAND_TEE, get_example_wardrobe())

    assert isinstance(result, str)
    assert len(result) > 0
    mock_llm.assert_called_once()


# ── create_fit_card ───────────────────────────────────────────────────────────


def test_create_fit_card_empty_outfit():
    result = create_fit_card("", BAND_TEE)

    assert isinstance(result, str)
    assert "couldn't generate" in result.lower()
    assert "incomplete" in result.lower()


def test_create_fit_card_whitespace_outfit():
    result = create_fit_card("   ", BAND_TEE)

    assert isinstance(result, str)
    assert "couldn't generate" in result.lower()


def test_create_fit_card_missing_listing_fields():
    result = create_fit_card(OUTFIT_SUGGESTION, {"title": "Vintage Band Tee"})

    assert isinstance(result, str)
    assert "missing price or platform" in result.lower()


@patch(
    "tools._call_groq_llm",
    return_value=(
        "thrifted this faded band tee off depop for $19 and honestly "
        "it was made for my baggy jeans 🖤"
    ),
)
def test_create_fit_card_returns_caption(mock_llm):
    result = create_fit_card(OUTFIT_SUGGESTION, BAND_TEE)

    assert isinstance(result, str)
    assert "depop" in result.lower()
    mock_llm.assert_called_once()
