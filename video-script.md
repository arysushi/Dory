# sync-cents — Video Script
**Estimated runtime:** 8–10 minutes  
**Format:** Product demo + technical walkthrough  
**Audience:** General viewers interested in fintech UX; developers reviewing the implementation

---

## SCENE 1 — Cold open
**[VISUAL]** Synchrony-style mobile UI. Yellow hero banner. sync-cents balance ticking up cent by cent.  
**[ON SCREEN]** Title: *sync-cents — A Synchrony Savings Extension*

**NARRATOR:**  
Most people know they should save money. Fewer people actually do it consistently. sync-cents is a feature built into the Synchrony mobile experience that solves that gap — not with big transfers you have to remember, but with small, automatic daily deposits driven by your real spending habits.

Today we'll walk through what sync-cents does for the user, and then go under the hood — the functions, APIs, and algorithms that make it work.

---

## SCENE 2 — What sync-cents is
**[VISUAL]** Diagram: Synchrony app shell with Accounts tab, sync-cents tab, Settings tab.  
**[ON SCREEN]** *Not a standalone app — an integrated extension*

**NARRATOR:**  
sync-cents is intentionally not a separate application. It's an extension embedded inside the Synchrony app shell. Users navigate to it from the same tab bar they use for accounts and settings. The UI follows Synchrony's white-and-gold design language — clean headers, mobile-first layout, and a familiar enrollment flow that mirrors first-time Synchrony setup.

At a high level, sync-cents does three things:

1. **Analyzes spending** — it reviews linked account activity and breaks it down by category.  
2. **Recommends a daily savings amount** — an algorithm suggests how many cents per day you can afford to save.  
3. **Auto-deposits into savings** — when your checking balance stays above a safety threshold you set, sync-cents quietly moves that daily amount into your savings account.

---

## SCENE 3 — User flow: enrollment
**[VISUAL]** Screen recording of `/synccents/onboarding`. Step dots at the bottom.  
**[ON SCREEN]** Step 1 → Step 2 → Step 3 → Step 4

**NARRATOR:**  
When a user opens sync-cents for the first time, they hit a four-step onboarding flow — all client-side steps, backed by a single API call at the end.

**Step 1 — Welcome.**  
Purely informational. Explains micro-savings: save a little every day, personalized to your spending, with no ongoing effort.

**Step 2 — Spending analysis.**  
Here the app calls `GET /api/onboarding`. On the backend, that triggers `SyncCents.get_onboarding_data()`. If the user has no expense history yet, the engine runs `seed_linked_account_data()` — which simulates linked Synchrony account transactions like groceries, subscriptions, and dining. Then `get_spending_habits()` aggregates those expenses by category and flags each as high, moderate, or low based on percentage of total spend.

**Step 3 — Daily contribution.**  
This is the core user decision: how many cents per day to save. The app displays a **suggested amount** computed by `suggest_daily_contribution()`. The user can accept the suggestion with one tap or enter their own value. A live projection shows the monthly and yearly impact.

**Step 4 — Safety balance.**  
Users set a **minimum checking balance threshold**. sync-cents will only deposit when the account stays above this floor — protecting bill money from automatic transfers. When they tap "Enroll," the frontend sends `POST /api/enroll` with their daily cents and threshold. The backend calls `SyncCents.enroll()`, sets `enrolled = true` in persistent storage, and redirects to the home page.

**[ON SCREEN]**  
```
POST /api/enroll
→ SyncCents.enroll(daily_contribution_cents, min_balance_threshold)
→ data/synccents.json updated
```

---

## SCENE 4 — User flow: home page
**[VISUAL]** Home page with balance hero, today's deposit card, 14-day feed.  
**[ON SCREEN]** `GET /api/home`

**NARRATOR:**  
After enrollment, the user lands on the sync-cents home page at `/synccents`. Every time this page loads, the frontend calls `GET /api/home`. That endpoint does something important before returning data: it automatically runs `sync_cents()`.

The home page shows:

- **sync-cents balance** — total savings accumulated.  
- **Today's deposit** — whether today's micro-transfer happened, is pending, or was skipped.  
- **Daily rate and monthly projection** — based on the enrolled contribution.  
- **A 14-day deposit feed** — each day marked as deposited or missed.  
- **A streak counter** — consecutive days with successful deposits.

All of this is assembled by `get_home_summary()`, which calls `get_daily_deposits()` to group `auto_deposits` records by calendar date and compute the streak from most recent backward.

---

## SCENE 5 — User flow: settings
**[VISUAL]** Navigate via gear icon to `/synccents/settings`.  
**[ON SCREEN]** Separate page — not inline on home

**NARRATOR:**  
Settings live on a dedicated page — not mixed into the home screen. Users reach it through the gear icon in the header or the tab bar.

`GET /api/settings` loads current values plus a fresh suggestion from the algorithm, so users can re-apply a recommended amount anytime. Saving calls `POST /api/settings`, which invokes `SyncCents.configure()` to update income, checking balance, daily contribution, and the safety threshold. Every change persists immediately to JSON.

---

## SCENE 6 — Architecture overview
**[VISUAL]** Layered architecture diagram animating in.  
**[ON SCREEN]** Browser → Flask → sync-cents engine → JSON file

**NARRATOR:**  
Let's talk about how this is built technically. sync-cents uses a classic three-tier structure:

**Presentation layer** — Jinja2 HTML templates (`base.html`, `onboarding.html`, `home.html`, `settings.html`), styled with `synchrony.css`, and driven by page-specific JavaScript files that call the REST API with `fetch`.

**Application layer** — a Flask server in `app.py`. It handles page routing with enrollment guards: if you're not enrolled, you can't reach home or settings. If you are enrolled, onboarding redirects you away. The same file exposes JSON endpoints under `/api/`.

**Business logic layer** — the `synccents` Python package. The centerpiece is the `SyncCents` class in `engine.py`. It owns all rules: expense tracking, spending analysis, savings recommendations, daily deposit logic, enrollment, and reset.

**Persistence layer** — `storage.py` reads and writes a single JSON file at `data/synccents.json`. No database — every state mutation calls `_persist()` which serializes the full state object to disk.

Supporting modules include `models.py` for typed dataclasses like `Expense`, `AutoDeposit`, and `SpendingInsight`, and `tips.py` for category-specific savings advice strings.

---

## SCENE 7 — Core functions deep dive
**[VISUAL]** Code editor highlighting `engine.py`. Function names appear as callouts.  
**[ON SCREEN]** Key functions list

**NARRATOR:**  
Here are the most important functions in the engine and what each one does.

---

### `seed_linked_account_data()`
**[ON SCREEN]** Simulates linked Synchrony transactions

**NARRATOR:**  
Runs once during onboarding if the expense array is empty. Populates sample transactions — food, utilities, entertainment, transport — spread across the last 28 days. In production this would be replaced by a real account aggregation feed; here it demonstrates the analysis pipeline without external integrations.

---

### `get_spending_habits(days=30)`
**[ON SCREEN]** Returns category totals, percentages, trends, advice

**NARRATOR:**  
Pulls expenses from the last 30 days, groups them by `ExpenseCategory`, and calculates each category's share of total spend. Categories above 25% are flagged `high`, 10–25% as `moderate`, below 10% as `low`. Each insight includes personalized advice from `tips.py` — for example, meal prepping for high food spend, or the 24-hour rule for shopping.

---

### `get_savings_recommendation(days=30)`
**[ON SCREEN]** 50/30/20 rule applied to income vs spending

**NARRATOR:**  
Implements a simplified 50/30/20 budgeting model. It scales recent spending to a monthly figure, targets 20% of income for savings, and adjusts downward if estimated needs exceed 50% of income. Returns a `SavingsRecommendation` dataclass with recommended monthly savings, current savings rate, gap to goal, and up to five personalized tips.

---

### `suggest_daily_contribution()`
**[ON SCREEN]** Algorithm flowchart

**NARRATOR:**  
This is the function behind the onboarding suggestion. It chains together the recommendation and habits analysis:

1. Start with recommended monthly savings divided by 30.  
2. If no recommendation exists, fall back to 5% of monthly income divided by 30.  
3. If discretionary categories — food, entertainment, shopping — exceed 45% of total spend, reduce the daily amount by 30%.  
4. Clamp the result between **25 cents and 100 cents** per day — keeping it in true micro-savings territory.

It returns suggested cents, monthly and yearly projections, top spending categories, and a plain-language explanation string for the UI.

---

### `enroll(daily_contribution_cents, min_balance_threshold)`
**[ON SCREEN]** Sets enrolled=true, records enrolled_at timestamp

**NARRATOR:**  
Persists the user's choices and flips the enrollment flag. After this, Flask route guards send them to the home page instead of onboarding.

---

### `sync_cents()` — the heart of the product
**[VISUAL]** Flowchart animation: balance check → threshold check → transfer  
**[ON SCREEN]** Pseudocode

**NARRATOR:**  
`sync_cents()` is the core deposit function. It runs automatically when the home page loads. The logic is strict:

```
1. Has a deposit already been recorded today? → skip
2. Is checking_balance > min_balance_threshold? → if not, skip
3. Would the deposit drop balance below threshold? → if yes, skip
4. Transfer daily_contribution_cents from checking to savings
5. Append an AutoDeposit record with timestamp and before/after balances
6. Persist to JSON
```

Only one deposit per calendar day. The amount is whatever the user enrolled with — stored as cents, converted to dollars at transfer time.

There's also a standalone `sync_cents()` function exported at module level for one-off checks without the full class instance — useful for testing or external integrations.

---

### `reset_enrollment()`
**[VISUAL]** Tap hidden "automatically" text on home page

**NARRATOR:**  
Sets `enrolled = false` without wiping savings history or deposit records. Triggered by a hidden UI affordance — tapping the word "automatically" on the home page — which calls `POST /api/reset-enrollment` and sends the user back to the welcome step. Useful for demos and QA.

---

## SCENE 8 — API reference (quick tour)
**[VISUAL]** API table on screen. Highlight each row as mentioned.

**NARRATOR:**  
The Flask API is small and REST-shaped:

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/onboarding` | Spending habits + daily suggestion |
| POST | `/api/enroll` | Complete enrollment |
| GET | `/api/home` | Auto-deposit + home dashboard data |
| GET | `/api/settings` | Load settings + fresh suggestion |
| POST | `/api/settings` | Update configuration |
| POST | `/api/reset-enrollment` | Return to onboarding |

Page routes handle HTML; API routes return JSON. The frontend never touches the JSON file directly — all state changes go through the engine.

---

## SCENE 9 — Data model
**[VISUAL]** JSON file structure highlighted in editor  
**[ON SCREEN]** `data/synccents.json` schema

**NARRATOR:**  
All state lives in one JSON document:

```json
{
  "enrolled": true,
  "monthly_income": 3500.0,
  "checking_balance": 1247.83,
  "savings_balance": 12.50,
  "min_balance_threshold": 500.0,
  "daily_contribution_cents": 50,
  "total_auto_saved": 12.50,
  "enrolled_at": "2026-06-30T10:00:00",
  "expenses": [ ... ],
  "auto_deposits": [ ... ]
}
```

Expenses track amount, category, description, and ISO date. Auto-deposits track amount, timestamp, and balance snapshots. The `SyncCents` class loads this on init and re-saves on every property change through `_persist()`.

---

## SCENE 10 — Running the project
**[VISUAL]** Terminal commands. Browser at localhost:5050.

**NARRATOR:**  
To run sync-cents locally:

```bash
cd dory
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python app.py
```

Open `http://localhost:5050`. First visit routes to onboarding. After enrollment, the root URL goes straight to home. Delete `data/synccents.json` — or use the hidden reset — to replay enrollment.

Dependencies are minimal: **Flask** for the web server, everything else is Python standard library plus the local `synccents` package.

---

## SCENE 11 — Design decisions (technical)
**[VISUAL]** Split screen: UX mockup | code architecture  
**[ON SCREEN]** Key decisions

**NARRATOR:**  
A few intentional technical choices worth calling out:

**Enrollment guards in Flask, not JavaScript.**  
The server decides whether you see onboarding or home. That prevents URL tampering from skipping setup.

**Auto-deposit on page load, not a cron job.**  
In this prototype, `GET /api/home` triggers `sync_cents()`. A production version would use a scheduled job or banking API webhook — but the deposit logic itself wouldn't change.

**Micro-savings clamp at 100 cents.**  
The suggestion algorithm caps at one dollar per day to keep the product aligned with "a few cents" positioning, even if the 50/30/20 math suggests more.

**Single JSON file over a database.**  
Appropriate for a demo and easy to inspect. Swapping in SQLite or a real banking ledger would mean replacing `storage.py` only — the engine interface stays the same.

**Thin client, fat server.**  
All business rules live in Python. The JavaScript files only fetch, render, and collect form input. That separation makes the engine testable without a browser.

---

## SCENE 12 — Closing
**[VISUAL]** Home page with streak growing. Synchrony logo fade.  
**[ON SCREEN]** *sync-cents — save without thinking*

**NARRATOR:**  
sync-cents turns saving from a willpower problem into a background process. Users enroll once, set a daily amount informed by their real spending, and watch cents accumulate into meaningful savings over weeks and months.

Technically, it's a Flask extension with a focused Python engine, a REST API, JSON persistence, and a mobile-first UI styled as part of Synchrony — with clear separation between onboarding, daily dashboard, and settings.

The code is in the `dory` repository: `app.py` for routes, `synccents/engine.py` for logic, and `templates/` plus `static/` for the front end.

Thanks for watching.

**[ON SCREEN]**  
GitHub / repo link  
`app.py` · `synccents/engine.py` · `localhost:5050`

**[END]**

---

## PRODUCTION NOTES

| Item | Suggestion |
|------|------------|
| **B-roll** | Screen recordings of each onboarding step, home feed updating, settings save |
| **Code shots** | `sync_cents()`, `suggest_daily_contribution()`, `app.py` routes |
| **Graphics** | Architecture diagram, API table, deposit flowchart (from prior docs) |
| **Pacing** | Scenes 1–5 user-facing (~4 min), Scenes 6–11 technical (~4 min), Scene 12 close (~30 sec) |
| **Optional cut** | Scene 10 (running locally) can be appendix for developer audience only |
