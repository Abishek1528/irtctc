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
| Forced Login Modal Blocks Guest Search | **4** | 100% of guest station typing; top-of-funnel; blocks browse-before-register (unchanged after peer review) |
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
| Forced Login Modal Blocks Guest Search | **3** | Auth middleware + read API policy + WAF/CAPTCHA + compliance sign-off (peer review: not a one-line change) |
| Confusing Charts Autocomplete Initial State | **1** | Single-page combobox + autocomplete `min_length`; isolated module |
| Redundant Class Selection Dropdowns | **1** | Homepage form + single API param; UI consolidation only |

**Quadrant rule:** Impact ≥ 4 and Effort ≤ 3 → High Impact / Low Effort. Impact ≥ 4 and Effort ≥ 4 → High Impact / High Effort. Impact ≤ 2 → Low Impact. Effort ≥ 4 with Impact &lt; 4 would land Low Impact / High Effort (none of our six qualify).

*Peer review (Step 6): Effort threshold for “Low Effort” quadrant raised from ≤2 to ≤3 so security/compliance work on guest browse is reflected; Guest Login remains High Impact / Low Effort at score 3.*

---

## Placement Justifications

### Tatkal Booking Crashes at 10:00 AM — High Impact / High Effort

Part A reports daily 10:00 AM Tatkal windows affecting thousands of concurrent users in the core booking path, with lost tickets and silent failures as the consequence (Impact **5**). The spec requires a new queue orchestration service, message queue, booking microservice changes, and peak-traffic operations—plus Railway availability coupling at release time (Effort **5**). Peer review agreed placement is correct; sprint order last is due to **phased rollout** (shadow → position UI → full outcomes), not lower impact. Do not defer indefinitely—it is the highest-impact problem in the set.

### Search Filters Do Not Work Reliably — High Impact / Low Effort

Part A states all train-search users hit intermittent filter/result mismatches in the main discovery flow, undermining trust and forcing repeat searches (Impact **4**). The fix is largely server-side filter parameters, a unified `useSearchFilters` hook, URL persistence, and sequencing per-train refresh—no new infrastructure (Effort **2**). Ship early in the sprint: high user-visible value relative to engineering cost.

### Seat Selection Resets — High Impact / High Effort

Part A shows berth selection dropping between seat map and passenger/payment steps, especially on mobile, directly threatening booking completion for seat-map-enabled trains (Impact **4**). The spec needs `berth_holds` storage, hold/confirm/release APIs, inventory respect for holds, and cross-page session persistence with Railway validation rules (Effort **4**). Plan as a mid-to-late sprint item after auth and search UX fixes, paired with Tatkal only where booking stability is already improved.

### Forced Login Modal Blocks Guest Train Availability Search — High Impact / Low Effort

Part A documents 100% reproduction for guests typing in the From field, blocking the entire homepage search form and browse-first conversion (Impact **4**). Peer review noted WAF rate limits, CAPTCHA for scrape protection, compliance review on fare visibility, and post-login stale-context handling—raising Effort from **2** to **3** while staying in the Low Effort quadrant. Still a top sprint pick, but schedule **one security/compliance checkpoint** before enabling guest search in production.

### Confusing Auto-Complete Initial State in Reservation Charts — Low Impact / Low Effort

Part A confirms every charts page load shows misleading “0 results available” copy, causing hesitation on a secondary journey (chart lookup, not ticket purchase) (Impact **2**). Effort is minimal: `openOnFocus: false`, `minChars: 2`, copy changes on one module—no Railway or booking changes (Effort **1**). Ideal filler early in the sprint when a team member has spare frontend capacity.

### Redundant and Confusing Class Selection Dropdowns — High Impact / Low Effort

Part A notes virtually every homepage booker sees two ambiguous class controls, leading to wrong-class searches and cognitive load (Impact **3**, rounded into High Impact band with other funnel fixes because frequency is universal). Effort is a single `TravelClassSelect`, remove duplicate field, map one `preferred_class` API param (Effort **1**). Pair with guest search and filters in the first sprint wave—cleans the entry form before deeper booking work.

---

## Recommended Sprint Order

1. **Redundant Class Selection Dropdowns** — Lowest effort; fixes the homepage form before any search or guest flow work; zero backend risk.
2. **Forced Login Modal Blocks Guest Search** — Unblocks the full top-of-funnel; ship after WAF/CAPTCHA rules are staged (peer review); compliance sign-off on guest-visible fares in parallel with step 1.
3. **Confusing Auto-Complete Initial State in Reservation Charts** — One-day frontend fix; clears a 100% reproducible UX bug while backend teams ramp on larger items.
4. **Search Filters Do Not Work Reliably** — Restores trust in the core search path before users enter seat selection or Tatkal; depends on stable class/search params from items 1–2.
5. **Seat Selection Resets** — Requires hold infrastructure and Railway coordination; best attempted once search and session patterns from items 1–4 are stable.
6. **Tatkal Booking Crashes at 10:00 AM** — Highest impact; start **shadow mode** early in sprint calendar even if UI ships last; Phase 1 position-only UI before AI. Load-test at simulated 10:00 AM; optional [AI wait-time layer](./AI-FEATURE.md) in Phase 2 only.

**Note:** Tatkal Queue Intelligence (XGBoost ETA) should follow Problem 1’s queue MVP in a subsequent sprint—not block the core queue from shipping.

---

## Peer Review Changelog (Step 6)

- Guest login **Effort 2 → 3**; quadrant unchanged (High Impact / Low Effort)
- Tatkal sprint rationale clarified: phased delivery, not deprioritization
- Sprint order #2 and #6 footnotes updated per security and shadow-mode feedback
