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

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): ...
- `size` (str): ...
- `max_price` (float): ...

**What it returns:**
<!-- Describe the return value — what fields does a result contain? -->

**What happens if it fails or returns nothing:**
<!-- What should the agent do if no listings match? -->

---

### Tool 2: suggest_outfit

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): ...
- `wardrobe` (dict): ...

**What it returns:**
<!-- Describe the return value -->

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the wardrobe is empty or no outfit can be suggested? -->

---

### Tool 3: create_fit_card

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (...): ...

**What it returns:**
<!-- Describe the return value -->

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the outfit data is incomplete? -->

---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?**
<!-- Describe the logic your planning loop uses. What does it look at? What conditions change its behavior? How does it know when it's done? -->

---

## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | |
| suggest_outfit | Wardrobe is empty | |
| create_fit_card | Outfit input is missing or incomplete | |

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

**Milestone 4 — Planning loop and state management:**

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**What FitFindr does:** FitFindr is a secondhand shopping agent that takes a natural-language style request, searches mock listings (filtering on fields like `title`, `description`, `style_tags`, `size`, `price`, and `category`), picks the best match, then suggests how to style it with the user's existing wardrobe. Each successful search triggers `suggest_outfit`, which is then passed to `create_fit_card` for a shareable caption. If `search_listings` returns no matches, the agent tells the user what to adjust (budget, size, keywords) and stops — it never calls downstream tools with empty input.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1 — Search:** The agent parses the query and calls `search_listings("vintage graphic tee", max_price=30.0)`. The tool loads listings via `load_listings()` and filters against `title`, `description`, `style_tags`, `category`, `price`, and other fields. It returns 3 matching tops sorted by relevance — e.g. "Vintage Band Tee — Faded Grey" ($19, Depop), "Graphic Tee — 2003 Tour Bootleg Style" ($24, Depop), and "Y2K Baby Tee — Butterfly Print" ($18, Depop). The agent selects the top result: **Vintage Band Tee — Faded Grey — $19, Depop, fair condition** (`lst_033`).

**Step 2 — Suggest outfit:** Using the selected listing and the user's wardrobe (loaded with `get_example_wardrobe()` for testing — 10 items including baggy jeans and chunky sneakers), the agent calls `suggest_outfit(new_item=<band tee>, wardrobe=<user's wardrobe>)`. The tool matches the new tee against wardrobe items by `category`, `colors`, and `style_tags`. It returns: *"Pair this with your baggy straight-leg jeans and chunky white sneakers for an easy streetwear look. Roll the sleeves once and half-tuck the front for shape — the faded grey plays well against dark-wash denim."*

**Step 3 — Fit card:** The agent calls `create_fit_card(outfit=<suggestion from step 2>, new_item=<band tee>)`. The tool turns the outfit suggestion into a short social-style caption. It returns: *"thrifted this faded band tee off depop for $19 and honestly it was made for my baggy jeans 🖤 full look in my stories"*

**Error path:** If `search_listings` returns an empty list (e.g. `search_listings("designer silk blouse", max_price=10.0)`), the agent responds with something like *"Nothing matched that search — try raising your budget, loosening the size filter, or broadening the style keywords"* and does **not** call `suggest_outfit` or `create_fit_card`.

**Final output to user:** A single response combining all three steps: the top listing details (title, price, platform, condition), the styling suggestion referencing specific wardrobe pieces, and the ready-to-post fit card caption.
