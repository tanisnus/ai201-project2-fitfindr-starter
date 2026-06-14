# FitFindr — Starter Kit

This starter kit contains everything you need to begin Project 2.

FitFindr is a secondhand shopping agent that takes a natural-language style request, searches mock listings, suggests how to style the best match with the user's wardrobe, and generates a shareable fit-card caption.

## What's Included

```
ai201-project2-fitfindr-starter/
├── data/
│   ├── listings.json          # 40 mock secondhand listings
│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe
├── utils/
│   └── data_loader.py         # Helper functions for loading the data
├── planning.md                # Your planning template — fill this out first
└── requirements.txt           # Python dependencies
```

## Setup

```bash
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):
```
GROQ_API_KEY=your_key_here
```

Run the Gradio UI:

```bash
python app.py
```

Run tests:

```bash
python -m pytest
```

Run the agent CLI (happy path + no-results):

```bash
python agent.py
```

## The Mock Listings Dataset

`data/listings.json` contains 40 mock secondhand listings across categories (tops, bottoms, outerwear, shoes, accessories) and styles (vintage, y2k, grunge, cottagecore, streetwear, and more).

Each listing has: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

Load it with:
```python
from utils.data_loader import load_listings
listings = load_listings()
```

## The Wardrobe Schema

`data/wardrobe_schema.json` defines the format your agent uses to represent a user's existing wardrobe. It includes:

- `schema`: field definitions for a wardrobe item
- `example_wardrobe`: a sample wardrobe with 10 items you can use for testing
- `empty_wardrobe`: a starting template for a new user

Load an example wardrobe with:
```python
from utils.data_loader import get_example_wardrobe
wardrobe = get_example_wardrobe()
```

## Where to Start

1. **Read `planning.md` and fill it out before writing any code.**
2. Verify the data loads correctly by running `python utils/data_loader.py`.
3. Build and test each tool individually before connecting them through your planning loop.

Your implementation files go in this same directory. There's no required file structure for your agent code — organize it however makes sense for your design.

---

## Tool Inventory

### 1. `search_listings(description, size, max_price)`

**Purpose:** Search the mock secondhand dataset for items matching the user's keywords, with optional size and price filters.

**Inputs:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `description` | `str` | Keywords to match (e.g. `"vintage graphic tee"`) against title, description, and style_tags |
| `size` | `str \| None` | Optional size filter (e.g. `"M"`). Case-insensitive; `"M"` matches `"S/M"`. `None` skips filtering. |
| `max_price` | `float \| None` | Optional maximum price in dollars (inclusive). `None` skips filtering. |

**Output:** `list[dict]` — matching listings sorted by relevance (highest keyword score first), then lowest price as tiebreaker. Returns `[]` if nothing matches. Each listing dict contains:

- `id` (str), `title` (str), `description` (str)
- `category` (str): tops, bottoms, outerwear, shoes, accessories
- `style_tags` (list[str]), `size` (str), `condition` (str)
- `price` (float), `colors` (list[str])
- `brand` (str | None), `platform` (str): depop, thredUp, poshmark

**Called in:** `agent.py` → `run_agent()` step 3, after query parsing.

---

### 2. `suggest_outfit(new_item, wardrobe)`

**Purpose:** Given a thrifted listing and the user's wardrobe, suggest how to style the new piece — using specific wardrobe items when available, or general advice when the wardrobe is empty.

**Inputs:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `new_item` | `dict` | The selected listing from `search_listings` (typically `results[0]`). Uses `title`, `category`, `style_tags`, `colors`, `description`. |
| `wardrobe` | `dict` | User's wardrobe with an `items` key containing wardrobe item dicts (`id`, `name`, `category`, `colors`, `style_tags`, `notes`). |

**Output:** `str` — a 2–4 sentence outfit suggestion. Always returns a non-empty string (never raises). With a populated wardrobe, references items by exact `name`. With an empty wardrobe, returns general styling advice.

**Called in:** `agent.py` → `run_agent()` step 5, only after `selected_item` is set.

---

### 3. `create_fit_card(outfit, new_item)`

**Purpose:** Turn the outfit suggestion and listing into a short, social-media-style caption the user can copy and post.

**Inputs:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `outfit` | `str` | The styling suggestion string from `suggest_outfit()` |
| `new_item` | `dict` | The same listing dict passed to `suggest_outfit`. Uses `title`, `price`, `platform`, `style_tags`. |

**Output:** `str` — a 1–2 sentence first-person caption mentioning the item, price, and platform. If `outfit` is empty or listing fields are missing, returns a descriptive error message string instead of raising an exception.

**Called in:** `agent.py` → `run_agent()` step 6, only when the wardrobe has items and `outfit_suggestion` is set.

---

## Planning Loop

`run_agent(query, wardrobe)` in `agent.py` runs a fixed 3-step pipeline with **early exits** — it does not call all three tools unconditionally.

### Conditional logic

**0. Initialize session** — create a fresh `session` dict for this interaction.

**1. Parse query** — `_parse_query()` extracts `description`, `size`, and `max_price` using regex. Stored in `session["parsed"]`.
- If description is empty → set `session["error"]`, return immediately.

**2. Call `search_listings`** with parsed parameters. Store results in `session["search_results"]`.
- **If `results == []`:** set `session["error"]` to a helpful message, **return** — do not call `suggest_outfit` or `create_fit_card`.
- **If results exist:** set `session["selected_item"] = results[0]`, proceed.

**3. Call `suggest_outfit`** with `selected_item` and `wardrobe`. Store in `session["outfit_suggestion"]`.
- **If `wardrobe["items"]` is empty:** return session with outfit advice but `fit_card = None` — skip `create_fit_card`.
- **If outfit is a valid string and wardrobe has items:** proceed.

**4. Call `create_fit_card`** with `outfit_suggestion` and `selected_item`.
- **If return value is an error string** (contains "couldn't generate" or "couldn't build"): set `session["error"]`, return with listing + outfit but no fit card.
- **If return value is a caption:** set `session["fit_card"]`, return full session.

### Three distinct paths

| Input scenario | Tools called | Session at end |
|----------------|-------------|----------------|
| Happy path (`vintage graphic tee under $30`, example wardrobe) | search → outfit → fit card | `selected_item`, `outfit_suggestion`, `fit_card` all set |
| No results (`designer ballgown size XXS under $5`) | search only | `error` set; rest `None` |
| Empty wardrobe (`vintage graphic tee under $30`, empty wardrobe) | search → outfit | `selected_item`, `outfit_suggestion` set; `fit_card` is `None` |

---

## State Management

All data flows through a single `session` dict for the duration of one user query. Each tool reads from keys set by earlier steps and writes its output back before the next step runs.

| Session key | Set by | Used by |
|-------------|--------|---------|
| `query` | User input | Query parser |
| `parsed` | `_parse_query()` | `search_listings` |
| `wardrobe` | Loaded at init | `suggest_outfit` |
| `search_results` | `search_listings` | Planning loop (to pick `selected_item`) |
| `selected_item` | Planning loop (`results[0]`) | `suggest_outfit`, `create_fit_card` |
| `outfit_suggestion` | `suggest_outfit` | `create_fit_card`, UI |
| `fit_card` | `create_fit_card` | UI |
| `error` | Planning loop (on failure) | UI |

**Data flow between tools (no re-entry, no hardcoded values):**

```
search_listings → session["search_results"]
                → session["selected_item"] = results[0]
                → suggest_outfit(new_item=session["selected_item"], ...)
                → session["outfit_suggestion"]
                → create_fit_card(outfit=session["outfit_suggestion"], new_item=session["selected_item"])
                → session["fit_card"]
```

`handle_query()` in `app.py` reads the completed session and maps it to three UI panels — it does not re-call any tools.

---

## Error Handling

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| `search_listings` | No results match | Set `session["error"]`. Return immediately. Do not call downstream tools. |
| `suggest_outfit` | Empty wardrobe | Return general styling advice in `outfit_suggestion`. Skip `create_fit_card`. |
| `suggest_outfit` | Wardrobe has items but LLM can't build outfit | Return fallback message in `outfit_suggestion`. |
| `create_fit_card` | Empty or incomplete `outfit` | Return error string. Agent sets `session["error"]`. Listing + outfit still shown; no fit card. |
| `create_fit_card` | Missing `title`, `price`, or `platform` on listing | Return error string about incomplete listing data. |

### Concrete examples from testing

**No-results (search_listings):**

```bash
python -c "from tools import search_listings; print(search_listings('designer ballgown', size='XXS', max_price=5))"
# Output: []
```

```bash
python agent.py
# No-results path prints:
# Error message: Nothing matched that search — try raising your budget,
# loosening the size filter, or broadening your style keywords.
```

Verified by `test_no_results_skips_downstream_tools`: `selected_item`, `outfit_suggestion`, and `fit_card` are all `None`.

**Empty wardrobe (suggest_outfit):**

```bash
python -c "
from tools import search_listings, suggest_outfit
from utils.data_loader import get_empty_wardrobe
results = search_listings('vintage graphic tee', size=None, max_price=50)
print(suggest_outfit(results[0], get_empty_wardrobe()))
"
```

Returns a non-empty string with general styling advice — no exception, no empty string. Agent skips `create_fit_card`; `fit_card` stays `None`.

**Incomplete outfit (create_fit_card):**

```bash
python -c "
from tools import search_listings, create_fit_card
results = search_listings('vintage graphic tee', size=None, max_price=50)
print(create_fit_card('', results[0]))
"
# Output: Found your item and here's how to style it, but I couldn't generate
# a fit card caption because the outfit suggestion was incomplete...
```

Verified by `test_create_fit_card_empty_outfit` — returns error string, never raises.

---

## Spec Reflection

### How planning.md helped

The Error Handling table in `planning.md` drove the early-exit design in `run_agent()`. Writing specific agent responses for each failure mode before coding made it clear that `suggest_outfit` and `create_fit_card` must not run when `search_listings` returns `[]`. The Architecture diagram and State Management table directly mapped to the `session` dict keys and the data flow between tools.

### One divergence and why

**Spec:** `suggest_outfit` would match wardrobe items by category, style_tags, and colors using rule-based logic.

**Implementation:** `suggest_outfit` and `create_fit_card` use the Groq LLM (`llama-3.3-70b-versatile`) with structured prompts instead of pure rule matching. This produces more natural outfit suggestions and varied fit-card captions, but requires a `GROQ_API_KEY` and adds network dependency. Rule-based fallbacks are kept for empty wardrobe (when the LLM is unavailable) and missing listing fields.

**Spec:** Session uses `error_message` and a `done` flag.

**Implementation:** Uses `session["error"]` and early `return` statements instead of a `done` flag. Same behavior, simpler code.

---

## AI Usage Transparency

### Instance 1: Implementing the three tools (`tools.py`)

**Directed AI to:** Implement `search_listings`, `suggest_outfit`, and `create_fit_card` using the Tool 1–3 blocks from `planning.md` (inputs, return values, failure modes) and `utils/data_loader.py`.

**Reviewed and revised:**
- Confirmed `search_listings` calls `load_listings()` instead of re-implementing file I/O.
- Verified `create_fit_card` takes both `outfit` and `new_item` per the stub signature.
- Changed `suggest_outfit` to use Groq LLM prompts instead of the spec's rule-based wardrobe matching — kept rule-based fallbacks for empty wardrobe and LLM failures.
- Ran `pytest tests/test_tools.py` and fixed guards so tools return error strings instead of raising exceptions.

### Instance 2: Implementing the planning loop (`agent.py`)

**Directed AI to:** Implement `run_agent()` using the Planning Loop, State Management, and Architecture diagram sections from `planning.md`, matching the numbered TODO steps in `agent.py`.

**Reviewed and revised:**
- Verified early return when `search_listings` returns `[]` — downstream tools must not run.
- Confirmed `session["selected_item"]` is the exact dict passed to `suggest_outfit` and `create_fit_card`.
- Renamed `error_message` → `error` to match the starter session dict.
- Added empty-wardrobe branch to skip `create_fit_card`.
- Ran `pytest tests/test_agent.py` and `python agent.py` to confirm happy path and no-results path.

---

## Demo Queries

| Query | Wardrobe | Expected behavior |
|-------|----------|-------------------|
| `vintage graphic tee under $30` | Example wardrobe | Happy path — all 3 panels fill |
| `designer ballgown size XXS under $5` | Example wardrobe | Error in panel 1 only |
| `vintage graphic tee under $30` | Empty wardrobe | Listing + outfit; no fit card |
