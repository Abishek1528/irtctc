# Impact vs Effort Matrix

Prioritization for all six solutions documented in [part-a/PROBLEMS.md](../part-a/PROBLEMS.md) and specified in [part-b/SPECS.md](./SPECS.md). The AI feature ([AI-FEATURE.md](./AI-FEATURE.md)) extends Problem 1 and is sequenced after the Tatkal queue foundation.

## The Matrix

|                   | Low Effort         | High Effort        |
|-------------------|--------------------|--------------------|
| **High Impact**   | Forced Login Modal Blocks Guest Search; Redundant Class Selection Dropdowns; Search Filters Do Not Work Reliably | Tatkal Booking Crashes at 10:00 AM; Seat Selection Resets |
| **Low Impact**    | Confusing Auto-Complete Initial State in Reservation Charts | — |

## How I Scored Each Dimension

### Impact Scoring (1–5)

I scored Impact based on:
- Number of users affected (from Part A frequency analysis)
- Whether the problem is in the core booking flow
- Severity of consequence for the user

| Problem | Impact score | Rationale summary |
|---------|:------------:|-------------------|
| Tatkal Booking Crashes at 10:00 AM | **5** | Daily peak; thousands concurrent; core booking; lost tickets |
| Search Filters Do Not Work Reliably | **4** | All search users; core discovery path; erodes trust, forces re-search |
| Seat Selection Resets | **4** | Booking flow; intermittent but high severity when seat map used; mobile-heavy |
| Forced Login Modal Blocks Guest Search | **4** | 100% of guest station typing; top-of-funnel; blocks browse-before-register |
| Confusing Charts Autocomplete Initial State | **2** | Charts page only; confusion, not hard block; every load but narrower audience |
| Redundant Class Selection Dropdowns | **3** | Every homepage search; wrong-class results; below Tatkal severity |

### Effort Scoring (1–5)

I scored Effort based on:
- Number of system components touched
- Whether new infrastructure is required
- Risk of breaking existing flows
- Railway API dependencies

| Problem | Effort score | Rationale summary |
|---------|:------------:|-------------------|
| Tatkal Booking Crashes at 10:00 AM | **5** | New queue service, message broker, booking API changes, peak-load ops |
| Search Filters Do Not Work Reliably | **2** | Search API params, URL state, frontend hook; no new infra |
| Seat Selection Resets | **4** | Berth hold APIs, inventory sync, session across routes; Railway hold rules |
| Forced Login Modal Blocks Guest Search | **2** | Auth middleware + read API policy; frontend trigger removal |
| Confusing Charts Autocomplete Initial State | **1** | Single-page combobox + autocomplete `min_length`; isolated module |
| Redundant Class Selection Dropdowns | **1** | Homepage form + single API param; UI consolidation only |

**Quadrant rule:** Impact ≥ 4 and Effort ≤ 2 → High Impact / Low Effort. Impact ≥ 4 and Effort ≥ 4 → High Impact / High Effort. Impact ≤ 2 → Low Impact. Effort ≥ 4 with Impact &lt; 4 would land Low Impact / High Effort (none of our six qualify).

---

## Placement Justifications

### Tatkal Booking Crashes at 10:00 AM — High Impact / High Effort

Part A reports daily 10:00 AM Tatkal windows affecting thousands of concurrent users in the core booking path, with lost tickets and silent failures as the consequence (Impact **5**). The spec requires a new queue orchestration service, message queue, booking microservice changes, and peak-traffic operations—plus Railway availability coupling at release time (Effort **5**). This belongs in the strategic quadrant: prioritize after quick wins, but do not defer indefinitely—it is the highest-impact problem in the set.

### Search Filters Do Not Work Reliably — High Impact / Low Effort

Part A states all train-search users hit intermittent filter/result mismatches in the main discovery flow, undermining trust and forcing repeat searches (Impact **4**). The fix is largely server-side filter parameters, a unified `useSearchFilters` hook, URL persistence, and sequencing per-train refresh—no new infrastructure (Effort **2**). Ship early in the sprint: high user-visible value relative to engineering cost.

### Seat Selection Resets — High Impact / High Effort

Part A shows berth selection dropping between seat map and passenger/payment steps, especially on mobile, directly threatening booking completion for seat-map-enabled trains (Impact **4**). The spec needs `berth_holds` storage, hold/confirm/release APIs, inventory respect for holds, and cross-page session persistence with Railway validation rules (Effort **4**). Plan as a mid-to-late sprint item after auth and search UX fixes, paired with Tatkal only where booking stability is already improved.

### Forced Login Modal Blocks Guest Train Availability Search — High Impact / Low Effort

Part A documents 100% reproduction for guests typing in the From field, blocking the entire homepage search form and browse-first conversion (Impact **4**). Effort is low: narrow auth guards on booking `POST`s, allow read-only autocomplete/search, remove modal-on-input, and add post-login session merge (Effort **2**). This is a top sprint pick—maximum funnel relief with minimal platform risk.

### Confusing Auto-Complete Initial State in Reservation Charts — Low Impact / Low Effort

Part A confirms every charts page load shows misleading “0 results available” copy, causing hesitation on a secondary journey (chart lookup, not ticket purchase) (Impact **2**). Effort is minimal: `openOnFocus: false`, `minChars: 2`, copy changes on one module—no Railway or booking changes (Effort **1**). Ideal filler early in the sprint when a team member has spare frontend capacity.

### Redundant and Confusing Class Selection Dropdowns — High Impact / Low Effort

Part A notes virtually every homepage booker sees two ambiguous class controls, leading to wrong-class searches and cognitive load (Impact **3**, rounded into High Impact band with other funnel fixes because frequency is universal). Effort is a single `TravelClassSelect`, remove duplicate field, map one `preferred_class` API param (Effort **1**). Pair with guest search and filters in the first sprint wave—cleans the entry form before deeper booking work.

---

## Recommended Sprint Order

1. **Redundant Class Selection Dropdowns** — Lowest effort; fixes the homepage form before any search or guest flow work; zero backend risk.
2. **Forced Login Modal Blocks Guest Search** — Unblocks the full top-of-funnel immediately; high conversion impact with auth-policy changes only.
3. **Confusing Auto-Complete Initial State in Reservation Charts** — One-day frontend fix; clears a 100% reproducible UX bug while backend teams ramp on larger items.
4. **Search Filters Do Not Work Reliably** — Restores trust in the core search path before users enter seat selection or Tatkal; depends on stable class/search params from items 1–2.
5. **Seat Selection Resets** — Requires hold infrastructure and Railway coordination; best attempted once search and session patterns from items 1–4 are stable.
6. **Tatkal Booking Crashes at 10:00 AM** — Highest impact but needs queue service, load testing, and optional [AI wait-time layer](./AI-FEATURE.md); schedule last with dedicated infra and a timed release validation window.

**Note:** Tatkal Queue Intelligence (XGBoost ETA) should follow Problem 1’s queue MVP in a subsequent sprint—not block the core queue from shipping.
