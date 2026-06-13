# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->

Seaches the mock secondhand listing dataset for items that match the user's query. It loads all listings via load_listings(), then filters and ranks them by relevance using keywords in title, description, and style_tags, along with optional filters like size, price, and category

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->

- `description` (str): The user's search query in natural language (e.g. "vintage graphic tee") It will be used to match against title, description, and style_tags
- `size` (str): Size filter (e.g. "M", "L"). This will match against the listing's size field. If omitted, size is not filtered.
- `max_price` (float): Maximum price in dollars (e.g. 30.0). It only returns listing where price is less than or equal to max_price. If omitted, no price cap is applied

**What it returns:**
<!-- Describe the return value — what fields does a result contain? -->

A list of matching listing dicts, sorted by relevance (best match first).
Eact listing contains:
- id (str) - unique identifier, e.g. "lst_033"
- title (str) - item name
- description (str) - full item description
- category (str) - one of: tops, bottoms, outerwear, shoes, accessories
- style_tags (list[str]) - style descriptors, e.g. ["vintage", "graphic tee"]
- size (str) - e.g. "M", "L", "S/M"
- condition (str) - "execellent, good, or fair
- price (float) - price in dollars
- colors (list[str]) - e.g. ["grey", "charocal"]
- brand (str or None) - brand name if known
- platform (str) - depop, thredUp, poshmark
Returns an empty list if nothing mathces

**What happens if it fails or returns nothing:**
<!-- What should the agent do if no listings match? -->

The agent tells the user no listing matched and suggests changes such as raising the budget, try a different size, or use broader keywords. It stops there and does not call suggest_outfit or create_fit_card with empty input

---

### Tool 2: suggest_outfit

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->

Takes a newly found listing and the user's existing wardrobe, then suggests how to style the new piece with items they already own. It picks complementary wardrobe pieces by matching category (e.g. bottoms + shoes for a top), overlapping style_tags, and compatible colors, then returns a short styling paragraph that names specific wardrobe items and includes one practical styling tip.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->

- `new_item` (dict): The selected listing from search_listings (typically results[0]). Uses these fields:
     - id (str) — e.g. "lst_033"
     - title (str) — e.g. "Vintage Band Tee — Faded Grey"
     - category (str) — e.g. "tops"
     - style_tags (list[str]) — e.g. ["vintage", "grunge", "graphic tee"]
     - colors (list[str]) — e.g. ["grey", "charcoal"]
     - description (str) — used for extra style context  
- `wardrobe` (dict): The user's closet in wardrobe schema format in a dict with an items key containing a list of wardrobe item dicts. Load via get_example_wardrobe() for testing or get_empty_wardrobe() for the empty case. Each wardrobe item has:
     - id (str) — e.g. "w_001"
     - name (str) — e.g. "Baggy straight-leg jeans, dark wash"
     - category (str) — one of: tops, bottoms, outerwear, shoes, accessories
     - colors (list[str])
     - style_tags (list[str])
     - notes (str or None, optional) — fit/styling notes

**What it returns:**
<!-- Describe the return value -->

A string containing the outfit suggestion of 2 to 4 sentences naming specific wardrobe pieces and one styling tip. Example: "Pair this with your baggy straight-leg jeans and chunky white sneakers for an easy streetwear look. Roll the sleeves once and half-tuck the front for shape — the faded grey plays well against dark-wash denim."

The suggestion should always:

- Reference wardrobe items by their name field (not made-up pieces)
- Include at least one bottom and one shoe when styling a top
- Optionally suggest outerwear or accessories if they complement the look
- Returns None if the wardrobe is empty or no compatible outfit can be built from the available items.



**What happens if it fails or returns nothing:**
<!-- What should the agent do if the wardrobe is empty or no outfit can be suggested? -->

Empty wardrobe (wardrobe["items"] is []): The agent skips wardrobe-specific pairing and gives generic styling advice based only on the new item's style_tags and category. Example:

"I found a great piece, but your wardrobe is empty — add what you already own so I can style around it. For now: pair a vintage graphic tee with relaxed denim and chunky sneakers for a classic grunge look."

It does not call create_fit_card with a wardrobe-specific outfit if no real wardrobe items were used.

Wardrobe has items but nothing compatible (e.g. only accessories, no bottoms or shoes): The agent tells the user what's missing and suggests what to add. Example:

"I couldn't build a full outfit from your wardrobe — you have tops but no bottoms or shoes listed. Add your usual jeans and sneakers and try again."



---

### Tool 3: create_fit_card

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->

Turns the outfit suggestion and the new listing into a short, social-media-style caption the user can copy and post. It pulls key details from the listing (title, price, platform) and the styling suggestion from suggest_outfit, then writes a casual first-person caption in a thrift/fashion-post tone.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->

- `outfit` (str): The styling suggestion string returned by suggest_outfit. Must be a non-empty string that describes how to wear the new item. Example: "Pair this with your baggy straight-leg jeans and chunky white sneakers for an easy streetwear look. Roll the sleeves once and half-tuck the front for shape."

- `new_item` (dict): The same listing dict passed to suggest_outfit. Uses these fields to build the caption:

     - title (str) — e.g. "Vintage Band Tee — Faded Grey"
     - price (float) — e.g. 19.00
     - platform (str) — e.g. "depop"
     - style_tags (list[str]) — used for tone/vibe (e.g. "vintage", "grunge")

**What it returns:**
<!-- Describe the return value -->

A single string with a ready-to-post fit card caption, 1–2 sentences, and casual first-person voice.

Example:
     "thrifted this faded band tee off depop for $19 and honestly it was made for my baggy jeans 🖤 full look in my stories"

The caption should:

     - Mention the item in casual language (not the full listing title)
     - Include the price and platform
     - Reference the vibe or key wardrobe piece from the outfit suggestion
     - Feel like a real social post (emoji optional, informal tone)
     - Returns None if outfit is empty, None, or missing required new_item fields (title, price, platform).

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the outfit data is incomplete? -->

Outfit input is missing or incomplete (outfit is None, empty string, or generic advice with no wardrobe pairing): The agent skips the fit card and returns only the listing details and styling suggestion. Example:

"Found your tee and here's how to style it, but I couldn't generate a fit card caption because the outfit suggestion was incomplete. Try again once your wardrobe has bottoms and shoes listed."

It does not invent a caption from incomplete data.

new_item is missing required fields: The agent returns a simplified caption using whatever fields are available, or tells the user the listing data was incomplete. 

Example:

     "Your outfit suggestion is ready, but I couldn't build a full fit card. The listing is missing price or platform info."


---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?**
<!-- Describe the logic your planning loop uses. What does it look at? What conditions change its behavior? How does it know when it's done? -->

FitFindr runs a fixed 3-step pipeline with early exits on failure. The loop always starts with search; later tools only run if the previous step produced valid output.

**0. Initialize session.** On each user query, create a session dict with: `user_query`, `description`, `size`, `max_price`, `wardrobe`, `search_results`, `selected_item`, `outfit_suggestion`, `fit_card`, `error_message`, and `done` (all initially `None`/`False` except `user_query`). Load `wardrobe` from the user's saved closet, or `get_example_wardrobe()` during testing.

**1. Parse the user query.** Extract `description` (item/style keywords), `max_price` (if a budget is mentioned, e.g. "under $30" → `30.0`), and `size` (if mentioned, e.g. "size M" → `"M"`). Store in session. If `description` cannot be extracted, set `session["error_message"]` and return early.

**2. Call `search_listings`.**
```python
results = search_listings(description=session["description"], size=session["size"], max_price=session["max_price"])
session["search_results"] = results
```

- **If `results == []`:** Set `session["error_message"]` to *"Nothing matched that search — try raising your budget, loosening the size filter, or broadening your style keywords."*, set `session["done"] = True`, and **return** — do not call `suggest_outfit` or `create_fit_card`.
- **If `results` is non-empty:** Set `session["selected_item"] = results[0]` and proceed to step 3.

**3. Call `suggest_outfit`.** Only runs when `session["selected_item"]` is set.
```python
outfit = suggest_outfit(new_item=session["selected_item"], wardrobe=session["wardrobe"])
session["outfit_suggestion"] = outfit
```

- **If `session["wardrobe"]["items"] == []`:** Set `session["outfit_suggestion"]` to generic styling advice (*"I found a great piece, but your wardrobe is empty — add what you already own so I can style around it. For now: pair a vintage graphic tee with relaxed denim and chunky sneakers for a classic grunge look."*), leave `session["fit_card"] = None`, set `session["done"] = True`, and **return** — skip `create_fit_card`.
- **If `outfit is None`:** Set `session["error_message"]` to *"I couldn't build a full outfit from your wardrobe — you may be missing bottoms or shoes. Add your usual jeans and sneakers and try again."*, set `session["done"] = True`, and **return** — skip `create_fit_card`.
- **If `outfit` is a non-empty string:** Proceed to step 4.

**4. Call `create_fit_card`.** Only runs when `session["outfit_suggestion"]` is a valid wardrobe-specific string.
```python
fit_card = create_fit_card(outfit=session["outfit_suggestion"], new_item=session["selected_item"])
session["fit_card"] = fit_card
```

- **If `fit_card is None`:** Set `session["error_message"]` to *"Found your item and here's how to style it — but I couldn't generate a fit card caption. The outfit suggestion or listing data may be incomplete."* Still return listing + `outfit_suggestion`; `fit_card` stays `None`.
- **If `fit_card` is a non-empty string:** Set `session["done"] = True` and return session.

**5. Done condition.** The loop is done when: (a) `error_message` is set (early exit), (b) `fit_card` is set (full happy path), or (c) `outfit_suggestion` is set but `fit_card` is `None` (partial success). The agent never calls a tool whose required input is missing: no `selected_item` → no `suggest_outfit`; no valid `outfit_suggestion` → no `create_fit_card`.

**6. Build final response.** Assemble output from session: search failure → error only; empty wardrobe → listing + generic advice; outfit failure → listing + wardrobe gap message; full success → listing + styling + fit card caption; partial → listing + styling, note fit card failed.

---

## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->

All data flows through a single `session` dict that persists for the duration of one user query. Each tool reads from session keys set by earlier steps and writes its output back to session before the next step runs.

| Session key | Set by | Used by |
|-------------|--------|---------|
| `user_query` | User input | Query parser (step 1) |
| `description`, `size`, `max_price` | Query parser | `search_listings` |
| `wardrobe` | Loaded at init (`get_example_wardrobe()` or user's closet) | `suggest_outfit` |
| `search_results` | `search_listings` | Planning loop (to pick `selected_item`) |
| `selected_item` | Planning loop (`results[0]`) | `suggest_outfit`, `create_fit_card` |
| `outfit_suggestion` | `suggest_outfit` | `create_fit_card`, final response |
| `fit_card` | `create_fit_card` | Final response |
| `error_message` | Planning loop (on any failure branch) | Final response |
| `done` | Planning loop (when flow terminates) | Loop exit check |

**Passing data between tools:**
- `search_listings` → `selected_item` → passed as `new_item` to both `suggest_outfit` and `create_fit_card`
- `suggest_outfit` → `outfit_suggestion` → passed as `outfit` to `create_fit_card`
- `wardrobe` is loaded once at session init and never modified during the loop

The final response builder reads `selected_item`, `outfit_suggestion`, `fit_card`, and `error_message` from session — it does not re-call any tools.

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | Set `session["error_message"]` to *"Nothing matched that search — try raising your budget, loosening the size filter, or broadening your style keywords."* Set `done = True` and return immediately. Do not call `suggest_outfit` or `create_fit_card`. |
| suggest_outfit | Wardrobe is empty | Set `session["outfit_suggestion"]` to generic styling advice without wardrobe item names. Skip `create_fit_card`. Return listing details + generic advice. |
| suggest_outfit | Wardrobe has items but nothing compatible | Set `session["error_message"]` to *"I couldn't build a full outfit from your wardrobe — you may be missing bottoms or shoes. Add your usual jeans and sneakers and try again."* Return listing details + error. Skip `create_fit_card`. |
| create_fit_card | Outfit input is missing or incomplete | Set `session["error_message"]` to *"Found your item and here's how to style it — but I couldn't generate a fit card caption. The outfit suggestion or listing data may be incomplete."* Return listing + outfit suggestion without a fit card. Do not invent a caption. |

---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     ASCII art, a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html), or an embedded
     sketch are all fine. You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->

```
User query
    │
    ▼
Planning Loop ─────────────────────────────────────────────────────────────┐
    │                                                                        │
    │   Parse query → session: description, size, max_price                  │
    │                                                                        │
    ├─► search_listings(description, size, max_price)                        │
    │       │                                                                │
    │       │ results = []                                                   │
    │       ├──► [ERROR] "Nothing matched that search..."                    │
    │       │         session.error_message set → RETURN ────────────────────┤
    │       │                                                                │
    │       │ results = [item, ...]                                          │
    │       ▼                                                                │
    │   Session: selected_item = results[0]                                  │
    │       │                                                                │
    ├─► suggest_outfit(selected_item, wardrobe)                              │
    │       │                                                                │
    │       │ wardrobe.items = []                                            │
    │       ├──► generic outfit_suggestion → skip fit card → RETURN ─────────┤
    │       │                                                                │
    │       │ outfit = None                                                  │
    │       ├──► [ERROR] "Couldn't build outfit from wardrobe..." → RETURN ──┤
    │       │                                                                │
    │       │ outfit = "..."                                                 │
    │       ▼                                                                │
    │   Session: outfit_suggestion = "..."                                   │
    │       │                                                                │
    └─► create_fit_card(outfit_suggestion, selected_item)                    │
            │                                                                │
            │ fit_card = None                                                │
            ├──► partial response (listing + outfit, no caption) → RETURN ───┤
            │                                                                │
            │ fit_card = "..."                                               │
            ▼                                                                │
        Session: fit_card = "..."                                            │
            │                                                                │
            ▼                                                                │
        Return session (listing + outfit + fit card)                         │
                                                                             │
        error path returns here ◄────────────────────────────────────────────┘
            ↕
      State / Session
  (user_query, description, size, max_price, wardrobe,
   search_results, selected_item, outfit_suggestion,
   fit_card, error_message, done)
```

---

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

**Milestone 3 — Individual tool implementations:**

For `search_listings`, I'll use Claude in Cursor. I'll give it the Tool 1 block from `planning.md` (inputs, return value, failure mode) and `utils/data_loader.py`, and ask it to implement the function using `load_listings()` from the data loader. I expect a function that filters by `description`, `size`, and `max_price`, ranks results by keyword relevance, and returns a list of listing dicts (or `[]`). Before running it, I'll check that the generated code imports from `data_loader`, uses all three parameters, and handles the empty-results case. Then I'll test it with 3 queries: the vintage graphic tee example from Complete Interaction, a no-match query with `max_price=5.0`, and a query with a size filter.

For `suggest_outfit`, I'll use Claude in Cursor. I'll give it the Tool 2 block from `planning.md` (inputs, return value, failure mode), `data/wardrobe_schema.json`, and the `get_example_wardrobe()` / `get_empty_wardrobe()` helpers from the data loader. I expect a function that takes `new_item` and `wardrobe`, matches complementary pieces by `category`, `style_tags`, and `colors`, and returns a styling string naming real wardrobe items (or `None`). Before running it, I'll check that output references actual `name` values from the wardrobe, includes at least one bottom and one shoe when styling a top, and returns `None` for an empty wardrobe. Then I'll test with `get_example_wardrobe()` on the band tee listing and `get_empty_wardrobe()` for the failure case.

For `create_fit_card`, I'll use Claude in Cursor. I'll give it the Tool 3 block from `planning.md` (inputs, return value, failure mode) and the example fit card caption from the Complete Interaction section. I expect a function that takes `outfit` (str) and `new_item` (dict) and returns a casual first-person caption including `price` and `platform` (or `None` if input is incomplete). Before running it, I'll check that it does not invent a caption when `outfit` is `None` or empty, and that the output matches the tone of the walkthrough example. Then I'll test with the band tee listing and outfit suggestion from Complete Interaction.

**Milestone 4 — Planning loop and state management:**

I'll use Claude in Cursor. I'll give it the Planning Loop section, State Management section, Architecture diagram, and Error Handling table from `planning.md`, plus the three implemented tool functions. I expect a `run_agent(user_query, wardrobe)` function that initializes session state, parses the query, calls tools in order, branches on empty search results / empty wardrobe / `None` returns, and assembles a final response string. Before running it, I'll check that empty `search_listings` results stop the pipeline early (no `suggest_outfit` or `create_fit_card` called), session keys match the State Management table, and error messages match the Error Handling table. Then I'll test the example query from Complete Interaction for the full happy path, and `get_empty_wardrobe()` for the empty-wardrobe branch.

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**What FitFindr does:** FitFindr is a secondhand shopping agent that takes a natural-language style request, searches mock listings (filtering on fields like `title`, `description`, `style_tags`, `size`, `price`, and `category`), picks the best match, then suggests how to style it with the user's existing wardrobe. Each successful search triggers `suggest_outfit`, which is then passed to `create_fit_card` for a shareable caption. If `search_listings` returns no matches, the agent tells the user what to adjust (budget, size, keywords) and stops — it never calls downstream tools with empty input.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1 — Search:**
<!-- What does the agent do first? Which tool is called? With what input? -->

The agent parses the query and calls `search_listings("vintage graphic tee", max_price=30.0)`. The tool loads listings via `load_listings()` and filters against `title`, `description`, `style_tags`, `category`, `price`, and other fields. It returns 3 matching tops sorted by relevance — e.g. "Vintage Band Tee — Faded Grey" ($19, Depop), "Graphic Tee — 2003 Tour Bootleg Style" ($24, Depop), and "Y2K Baby Tee — Butterfly Print" ($18, Depop). The agent selects the top result: **Vintage Band Tee — Faded Grey — $19, Depop, fair condition** (`lst_033`).

**Step 2 — Suggest outfit:**
<!-- What happens next? What was returned from step 1? What tool is called now? -->

Using the selected listing and the user's wardrobe (loaded with `get_example_wardrobe()` for testing — 10 items including baggy jeans and chunky sneakers), the agent calls `suggest_outfit(new_item=<band tee>, wardrobe=<user's wardrobe>)`. The tool matches the new tee against wardrobe items by `category`, `colors`, and `style_tags`. It returns: *"Pair this with your baggy straight-leg jeans and chunky white sneakers for an easy streetwear look. Roll the sleeves once and half-tuck the front for shape — the faded grey plays well against dark-wash denim."*

**Step 3 — Fit card:**
<!-- Continue until the full interaction is complete -->

The agent calls `create_fit_card(outfit=<suggestion from step 2>, new_item=<band tee>)`. The tool turns the outfit suggestion into a short social-style caption. It returns: *"thrifted this faded band tee off depop for $19 and honestly it was made for my baggy jeans 🖤 full look in my stories"*

**Error path:** If `search_listings` returns an empty list (e.g. `search_listings("designer silk blouse", max_price=10.0)`), the agent responds with something like *"Nothing matched that search — try raising your budget, loosening the size filter, or broadening the style keywords"* and does **not** call `suggest_outfit` or `create_fit_card`.

**Final output to user:**
<!-- What does the user actually see at the end? -->

A single response combining all three steps: the top listing details (title, price, platform, condition), the styling suggestion referencing specific wardrobe pieces, and the ready-to-post fit card caption.
