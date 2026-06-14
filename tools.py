"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()

GROQ_MODEL = "llama-3.3-70b-versatile"
FIT_CARD_TEMPERATURE = 0.95


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


def _call_groq_llm(system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
    """Send a chat completion request to Groq and return the assistant reply."""
    client = _get_groq_client()
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
    )
    content = response.choices[0].message.content
    return content.strip() if content else ""


def _format_new_item(item: dict) -> str:
    """Format listing fields for LLM prompts."""
    return (
        f"Title: {item.get('title', 'Unknown')}\n"
        f"Category: {item.get('category', 'unknown')}\n"
        f"Style tags: {', '.join(item.get('style_tags', []))}\n"
        f"Colors: {', '.join(item.get('colors', []))}\n"
        f"Description: {item.get('description', '')}"
    )


def _format_wardrobe_items(items: list[dict]) -> str:
    """Format wardrobe items for LLM prompts."""
    lines = []
    for item in items:
        notes = item.get("notes")
        notes_text = f"\n  Notes: {notes}" if notes else ""
        lines.append(
            f"- {item.get('name', 'Unknown')} "
            f"({item.get('category', 'unknown')}, "
            f"colors: {', '.join(item.get('colors', []))}, "
            f"tags: {', '.join(item.get('style_tags', []))})"
            f"{notes_text}"
        )
    return "\n".join(lines)


def _get_wardrobe_items(wardrobe: dict | None) -> list[dict]:
    """Safely extract wardrobe items — treats missing or empty as no items."""
    if not wardrobe:
        return []
    items = wardrobe.get("items")
    return items if items else []


def _empty_wardrobe_styling_fallback(new_item: dict) -> str:
    """General styling advice when the wardrobe is empty and the LLM is unavailable."""
    category = new_item.get("category", "piece")
    return (
        "I found a great piece, but your wardrobe is empty — add what you already "
        "own so I can style around it. For now: pair this "
        f"{category} with relaxed denim and chunky sneakers for a classic casual look."
    )


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def _extract_keywords(description: str) -> list[str]:
    """Split a search description into lowercase keywords."""
    return [word.lower() for word in description.split() if word.strip()]


def _matches_size(listing_size: str, size_filter: str) -> bool:
    """Case-insensitive flexible size match (e.g. 'M' matches 'S/M')."""
    return size_filter.lower() in listing_size.lower()


def _relevance_score(listing: dict, keywords: list[str]) -> int:
    """Count keyword hits across title, description, and style_tags."""
    title = listing.get("title", "").lower()
    description = listing.get("description", "").lower()
    tags = " ".join(listing.get("style_tags", [])).lower()
    searchable = f"{title} {description} {tags}"

    return sum(1 for keyword in keywords if keyword in searchable)


def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    keywords = _extract_keywords(description)
    if not keywords:
        return []

    scored: list[tuple[int, dict]] = []

    for listing in load_listings():
        if max_price is not None and listing["price"] > max_price:
            continue
        if size is not None and not _matches_size(listing["size"], size):
            continue

        score = _relevance_score(listing, keywords)
        if score > 0:
            scored.append((score, listing))

    scored.sort(key=lambda item: (-item[0], item[1]["price"]))
    return [listing for _, listing in scored]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    items = _get_wardrobe_items(wardrobe)
    item_details = _format_new_item(new_item)

    if not items:
        system_prompt = (
            "You are FitFindr, a friendly secondhand fashion stylist. "
            "Give practical, concise styling advice in 2–4 sentences."
        )
        user_prompt = (
            "The user is considering buying this thrifted item:\n"
            f"{item_details}\n\n"
            "Their wardrobe is empty, so you cannot reference specific pieces they own. "
            "Give general styling advice for this item: what kinds of bottoms, shoes, "
            "and layers would pair well, what vibe it suits, and one practical styling tip. "
            "Do not pretend they already own specific items."
        )
        try:
            advice = _call_groq_llm(system_prompt, user_prompt)
        except Exception:
            advice = ""
        if advice.strip():
            return advice
        return _empty_wardrobe_styling_fallback(new_item)

    wardrobe_details = _format_wardrobe_items(items)
    system_prompt = (
        "You are FitFindr, a friendly secondhand fashion stylist. "
        "Suggest outfits using only items from the user's wardrobe when possible. "
        "Reference wardrobe pieces by their exact name. "
        "Write 2–4 sentences and include one practical styling tip."
    )
    user_prompt = (
        "The user is considering buying this thrifted item:\n"
        f"{item_details}\n\n"
        "Here is their existing wardrobe:\n"
        f"{wardrobe_details}\n\n"
        "Suggest one complete outfit that pairs the new item with pieces from their wardrobe. "
        "You must reference specific wardrobe items by their exact name. "
        "Include at least one bottom and one shoe when styling a top. "
        "Only use items listed above — do not invent wardrobe pieces. "
        "If the wardrobe cannot form a complete outfit, explain what is missing "
        "(for example, bottoms or shoes) and what the user should add."
    )
    return _call_groq_llm(system_prompt, user_prompt) or (
        "I couldn't build a full outfit from your wardrobe — you may be missing "
        "bottoms or shoes. Add your usual jeans and sneakers and try again."
    )


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    if not outfit or not outfit.strip():
        return (
            "Found your item and here's how to style it, but I couldn't generate "
            "a fit card caption because the outfit suggestion was incomplete. "
            "Try again once your wardrobe has bottoms and shoes listed."
        )

    title = new_item.get("title")
    price = new_item.get("price")
    platform = new_item.get("platform")
    if title is None or price is None or platform is None:
        return (
            "Your outfit suggestion is ready, but I couldn't build a full fit card. "
            "The listing is missing price or platform info."
        )

    style_tags = ", ".join(new_item.get("style_tags", []))
    item_details = (
        f"Title: {title}\n"
        f"Price: ${price:.2f}\n"
        f"Platform: {platform}\n"
        f"Style tags: {style_tags}"
    )

    system_prompt = (
        "You are FitFindr, writing casual social media captions for thrift outfit posts. "
        "Write 1–2 sentences in first person, like a real OOTD post on Instagram or TikTok. "
        "Mention the item casually (not the full listing title), include the price and "
        "platform once each, and capture the outfit vibe. Emoji are optional. "
        "Vary your wording — do not reuse the same opening phrase."
    )
    user_prompt = (
        f"Thrifted item:\n{item_details}\n\n"
        f"Outfit suggestion:\n{outfit.strip()}\n\n"
        "Write a fit card caption the user can copy and post."
    )

    try:
        caption = _call_groq_llm(
            system_prompt, user_prompt, temperature=FIT_CARD_TEMPERATURE
        )
    except Exception:
        caption = ""

    if caption.strip():
        return caption

    return (
        "Your outfit suggestion is ready, but I couldn't build a full fit card. "
        "The caption generator didn't return a response — try again."
    )
