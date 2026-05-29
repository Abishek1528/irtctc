# Feature Specifications — IRCTC Sprint (Part B)

Specifications continue from [Part A problems](../part-a/PROBLEMS.md). Each spec addresses one documented pain point.

---

## Feature Spec 1: Tatkal Booking Crashes at 10:00 AM

### Problem Statement

At Tatkal release time (10:00 AM), thousands of users hit the booking flow simultaneously. The availability confirmation step often times out or returns ambiguous states with no queue position, no progress indicator, and no actionable error. Users lose high-demand tickets, see only “quota exhausted” or a silent failure, and must retry blindly. Everyone attempting Tatkal at release time is affected; the impact is daily and predictable.

### Current State (from Part A)

Users open IRCTC before 10:00, search trains, pre-fill passenger and payment details, and trigger “Book” at exactly 10:00:00. At step 6—the booking/availability confirmation API—the call times out or returns an opaque state. The UI shows a spinner without queue position or progress (Part A steps 5–7). After several seconds the booking fails silently or shows “Quota not available” with no diagnostic. Console evidence from Part A includes CORS failures, 403 responses, and missing queue UI during peak load.

### Proposed Solution

When a user starts a Tatkal booking near release time, they see a clear “joining queue” screen with their position, estimated wait, and live status updates. If the server is busy, the app holds their place in line instead of failing silently. They always get a plain-language outcome: success, quota full, session expired, or try again—with a suggested next action. They never stare at a blank spinner wondering whether anything is happening.

### Proposed User Flow — Step by Step

1. User logs in and completes train search and passenger details before 10:00 AM (unchanged from Part A steps 1–4).
2. User taps **Book Tatkal**; the app detects Tatkal window and shows a countdown to 10:00:00 with a note that a queue may form at release.
3. At 10:00:00 the app submits a **queue enrollment** request instead of a raw availability call; the UI shows “You are in line — position #847 of ~12,000” with a progress bar.
4. The UI polls or receives push updates: position moves, “Checking availability…”, or “Almost there…”.
5. When the user reaches the front, the app runs the seat-hold/booking step automatically; the user sees “Confirming your berth…”
6. Outcome screen shows one of: **Booked** (PNR and payment), **Quota full** (with option to try alternate train/class), **Session expired** (re-login link), or **Temporary error** (retry with preserved form data).
7. User can leave the page and return via **My Queue** in the account menu to see live status without losing position (within TTL).

*Compared to Part A:* Steps 5–7 replace the silent timeout/spinner with explicit queue enrollment, position, and categorized outcomes.

### Technical Implementation Plan

**System components affected:**
- Booking microservice (availability/hold APIs)
- New queue orchestration service (or integration with existing peak-load middleware)
- Web and mobile booking UI
- Session and rate-limiting layer
- Notification service (optional SMS/push for queue turn)

**New data requirements:**
- `tatkal_queue_entries`: user_id, session_id, train_id, class, quota_type, position, status (waiting | processing | completed | failed), enrolled_at, expires_at
- `tatkal_queue_metrics`: window_id, total_enrolled, peak_concurrency, avg_wait_seconds
- Audit log for booking attempt outcomes at release window

**API changes:**
- `POST /api/v1/tatkal/queue/enroll` — enroll before or at release; returns queue_token and initial position
- `GET /api/v1/tatkal/queue/{queue_token}/status` — position, ETA, state
- `POST /api/v1/tatkal/queue/{queue_token}/process` — internal/worker: run hold when dequeued
- Modify existing availability/hold endpoints to accept `queue_token` and reject duplicate direct calls during peak window

**Frontend changes:**
- `TatkalQueueScreen` component: countdown, position, progress, cancel
- WebSocket or short-polling hook for queue status
- Replace generic spinner on booking confirmation with state machine UI (queued → processing → result)
- “My Queue” entry in user menu when active enrollment exists

**Third-party services (if any):**
- Message queue (e.g., Redis Streams, RabbitMQ, or cloud equivalent) for fair FIFO ordering
- Optional push notification provider for “your turn” alerts
- CDN/WAF tuning for 10:00 AM traffic spikes (infrastructure, not user-facing)

### Success Metrics

- Tatkal booking attempts with a visible queue/status UI: from ~0% (Part A) to **≥95%** of enrollments during release window
- Silent failures (timeout with no message): reduce by **≥80%** within 30 days of launch
- User-reported “unclear outcome” support tickets for Tatkal window: reduce by **≥50%** quarter-over-quarter

### Edge Cases and Constraints

- Queue token must bind to session, train, class, and passenger count to prevent abuse; one active Tatkal queue per user per window
- Railway APIs may still return quota exhausted—surface honestly, not as a system error
- Payment gateway timeouts during peak: hold queue slot briefly, show “payment pending” with retry window
- Clock skew: server authoritative time for 10:00 release; client countdown is approximate
- Graceful degradation: if queue service is down, fall back to direct booking with a banner “High traffic — you may not see queue position” and standard error messages (no silent failure)

---

## Feature Spec 2: Search Filters Do Not Work Reliably

### Problem Statement

Train search filters (class, departure time, availability) often do not change the result list, or they appear selected after navigation while results are unfiltered. Casual and power users waste time re-searching and lose trust in the UI. The issue is intermittent but reproducible during normal use (Part A Problem 2).

### Current State (from Part A)

User searches From/To/date, opens “Refine Results,” selects Sleeper or Morning departure (steps 1–3). The checkbox shows selected but the list sometimes unchanged (step 4). After viewing train details and going back, filters reset or show selected while results are wrong (steps 5–6). Re-applying filters gives inconsistent results (step 7). Break is between client filter state and server-side or unified result refresh; per-train “Refresh” controls may race and overwrite filter state.

### Proposed Solution

Filters always change what the user sees: checking “Sleeper” shows only sleeper trains, and that stays true when they go back from train details. A single “Applied filters” chip row shows what is active; clearing one chip updates the list immediately. The user never wonders whether a checked box actually did anything.

### Proposed User Flow — Step by Step

1. User enters From, To, date and taps **Search** (unchanged).
2. Results load; user opens **Refine Results** and selects **Sleeper (SL)** and **Morning (06:00–12:00)**.
3. List updates within one second; header shows “12 trains (filtered from 48)” and chips: `Sleeper ×` `Morning ×` `Clear all`.
4. User opens a train’s details, then taps **Back**.
5. Same filtered list and chip state appear; URL or session stores `?class=SL&departure=morning`.
6. User clears **Morning** chip; list widens; chip row updates.
7. User taps **Modify Search**; filter panel reopens with last selections pre-checked.

*Compared to Part A:* Steps 3–6 become deterministic—filter application triggers one refresh path; back navigation restores URL/session state instead of UI/result mismatch.

### Technical Implementation Plan

**System components affected:**
- Train search API and result aggregation layer
- Search results page (web + mobile)
- Browser history / deep-link routing

**New data requirements:**
- Persist filter state in URL query params and optional short-lived `search_context` server cache keyed by `search_id`
- Server-side filter schema: `classes[]`, `departure_buckets[]`, `availability_only` boolean

**API changes:**
- `GET /api/v1/trains/search` — accept query params `class`, `departure_from`, `departure_to`, `available_only`; return `total_unfiltered` and `total_filtered`
- Deprecate client-only filtering for fields available server-side
- `GET /api/v1/trains/search/{search_id}/filters` — optional restore of last context for back navigation

**Frontend changes:**
- Central `useSearchFilters` hook: single source of truth synced to URL
- Debounced refetch on filter change (cancel in-flight requests)
- Disable or sequence per-train **Refresh** so it does not reset global filter state
- `FilterChips` bar and empty state (“No trains match — clear filters”)

**Third-party services (if any):**
- None required; optional analytics (e.g., filter usage events)

### Success Metrics

- Filter apply → visible list change success rate: from intermittent (~60% per reports) to **≥98%** in synthetic and production sampling
- Back-navigation filter/result mismatch rate: reduce to **<2%** of sessions
- Repeat searches caused by “filters didn’t work”: reduce support/social complaints by **≥40%** in 60 days

### Edge Cases and Constraints

- Zero results after filter: show helpful message, not empty broken UI
- Very slow networks: show loading skeleton on list, not stale unfiltered data labeled as filtered
- IRCTC: class codes must match Railway master (SL, 3A, etc.); do not invent client-only class mappings
- Graceful degradation: if server filter params fail, show error banner and last known good results; do not show checked filters with unfiltered data

---

## Feature Spec 3: Seat Selection Resets

### Problem Statement

Users who pick a specific berth on the seat map often find it unassigned or changed on the passenger-details or payment page, especially on mobile. They must re-select or accept an unwanted berth, increasing abandonment and complaints (Part A Problem 3).

### Current State (from Part A)

User selects a train with seat map, picks class, taps a berth (step 3), proceeds to passenger details (step 4). On load, berth shows unassigned or different (step 5). Returning to the map may show selection cleared (step 6). Break is on transition steps 4–5—likely missing server-side hold, client state lost on navigation, or async availability refresh overwriting selection; mobile touch and session timeouts correlate with higher reset rate.

### Proposed Solution

When the user taps a berth, it stays highlighted and a short “Held for 10 minutes” message appears. On the next screen they see the same berth number and type (e.g., “B2 — Lower”). If the hold expires or someone else takes the seat, they get a clear warning before payment, not a surprise at the end.

### Proposed User Flow — Step by Step

1. User selects train and class with seat map enabled (unchanged steps 1–2).
2. User taps berth **B2 Lower**; map shows selected state and banner: “Berth B2 held until 10:42 AM.”
3. App calls **hold berth** API; on success, stores `hold_id` in session.
4. User taps **Continue**; passenger-details page shows read-only **Selected berth: B2 (Lower)** with **Change seat** link.
5. If user taps **Change seat**, return to map with prior berth still held until TTL unless released.
6. User fills passenger details and proceeds to payment; payment summary repeats berth line.
7. On successful payment, hold converts to confirmed allocation; on abandon, hold auto-releases after TTL.

*Compared to Part A:* Steps 4–5 gain server-backed hold and visible confirmation on every subsequent screen.

### Technical Implementation Plan

**System components affected:**
- Seat map service and inventory/coach layout APIs
- Booking session service
- Passenger details and payment pages (web + mobile)

**New data requirements:**
- `berth_holds`: hold_id, user_id, session_id, train_id, coach, berth_no, berth_type, status (active | converted | expired), held_until, created_at
- Link `hold_id` to booking draft record

**API changes:**
- `POST /api/v1/booking/berth/hold` — create hold; returns hold_id, held_until
- `GET /api/v1/booking/berth/hold/{hold_id}` — validate still active
- `DELETE /api/v1/booking/berth/hold/{hold_id}` — release on change/cancel
- `POST /api/v1/booking/berth/hold/{hold_id}/confirm` — on payment success
- Availability refresh endpoints must respect active holds (exclude held berths for others)

**Frontend changes:**
- Persist `hold_id` in sessionStorage/local booking context across routes
- Seat map: optimistic UI with rollback on hold failure
- Passenger and payment components: display berth from `hold_id` fetch, not stale client state
- Mobile: reduce navigation remounts; avoid clearing hold on soft back if within TTL

**Third-party services (if any):**
- None; relies on Railway inventory APIs behind IRCTC services

### Success Metrics

- Berth shown on passenger-details matching seat-map selection: from intermittent failure to **≥99%** when hold succeeds
- Mobile seat-reset reports: reduce by **≥70%** within 90 days
- Booking abandonment after seat selection: reduce by **≥15%** for seat-map-enabled trains

### Edge Cases and Constraints

- Hold TTL (e.g., 10 min) must align with IRCTC session and payment timeouts
- Twin side-by-side berths and gender quotas: hold API must validate Railway rules before UI confirms
- Concurrent selection: second user gets “Berth just taken — pick another” on map, not on payment page
- Graceful degradation: if hold API fails, block **Continue** with message “Unable to reserve seat — try again” rather than proceeding with unstored selection

---

## Feature Spec 4: Forced Login Modal Blocks Guest Train Availability Search

### Problem Statement

Guest users who type in the From station field on the homepage immediately see a login modal that blocks the entire search form. Casual visitors cannot browse availability before creating an account, hurting discoverability and conversion (Part A Self-Discovered Problem 1). Affects every guest interaction with station autocomplete—100% reproducible.

### Current State (from Part A)

Guest opens irctc.co.in, focuses **From**, types “Delhi” (steps 1–4). Before autocomplete appears, a login overlay blocks the form (steps 5–6). User must sign in, dismiss if possible, or leave (step 7). Break is between steps 3–5: an auth guard on input/focus treats station search as booking intent requiring login.

### Proposed Solution

Guests can search stations, dates, and classes and view train lists and fares without logging in. Login is required only when they start booking (passenger details, payment, or PNR). A subtle banner explains: “Login to book tickets — browsing is free.”

### Proposed User Flow — Step by Step

1. Guest opens homepage **BOOK TICKET** form (not logged in).
2. Guest types in **From**; station autocomplete works without modal.
3. Guest completes **To**, **Date**, **Class**, taps **Search**.
4. Results page shows trains, availability summary, and fares where policy allows.
5. Guest taps **Book** on a train; app shows login/register prompt with return URL to resume booking.
6. After login, user returns to same search context and continues booking.
7. Optional: guest can save search to clipboard or email reminder after login CTA (no account required).

*Compared to Part A:* Steps 4–5 no longer trigger login on typing; login moves to explicit booking intent.

### Technical Implementation Plan

**System components affected:**
- Homepage booking widget and global auth middleware
- Train search and availability read APIs
- Identity/login service

**New data requirements:**
- `guest_search_sessions`: anonymous token, search params, created_at, TTL (for resume-after-login)
- Audit: distinguish `browse` vs `book` API access in logs

**API changes:**
- `GET /api/v1/stations/autocomplete` — allow unauthenticated
- `GET /api/v1/trains/search` — allow unauthenticated for read-only results (per IRCTC policy)
- Guard `POST` booking, hold, and payment endpoints with auth; remove auth trigger from station autocomplete routes
- `POST /api/v1/guest/search-session` — store context; merge to user session on login

**Frontend changes:**
- Remove or narrow login modal trigger on `From`/`To` input events
- `LoginRequiredDialog` only on **Book** / **Waitlist** / **Favorite route**
- Banner component on search results for guests
- Post-login redirect restores `guest_search_session`

**Third-party services (if any):**
- None

### Success Metrics

- Guest users completing station autocomplete without modal: from **0%** to **100%**
- Search-to-login conversion rate: measure increase in registrations from browse-first funnel
- Bounce rate on homepage for logged-out users: reduce by **≥20%** in 90 days

### Edge Cases and Constraints

- IRCTC policy may restrict some fare types or quotas to logged-in users only—show “Login to view” for restricted fields, not block entire search
- Rate-limit anonymous search to prevent scraping
- PNR and personal data never exposed without auth
- Graceful degradation: if guest search API disabled by policy, show message “Sign in to search trains” instead of broken modal on first keystroke

---

## Feature Spec 5: Confusing Auto-Complete Initial State in Reservation Charts

### Problem Statement

On the Reservation Charts page, the Train Name/Number field shows “0 results available” before the user types, implying the feature is broken. Users hesitate or abandon chart lookups (Part A Self-Discovered Problem 2). Reproducible on every page load.

### Current State (from Part A)

User opens irctc.co.in/online-charts (step 1). **Journey Details** form loads (step 2). Train field shows “0 results available. Select is focused…” in the dropdown area before input (steps 3–4). User assumes broken search (steps 5–6). Typing should filter results (steps 7–8) but initial empty-state copy violates UX norms.

### Proposed Solution

The train field looks like a normal search box: placeholder “Enter train number or name,” closed dropdown until the user types at least two characters. If nothing matches after typing, a helpful “No trains found — check number” message appears—not “0 results” on load.

### Proposed User Flow — Step by Step

1. User opens Reservation Charts page.
2. **Train Name/Number** shows placeholder only; dropdown closed.
3. User types “12” or train name fragment; after debounce, dropdown opens with matches.
4. User selects a train; field shows selected train label.
5. User enters **Journey Date** and **Boarding Station**, submits.
6. Chart loads for selected journey.
7. If user clears train field, return to placeholder state without “0 results” message.

*Compared to Part A:* Step 4 on load is eliminated; empty-state copy only after meaningful search input.

### Technical Implementation Plan

**System components affected:**
- Online charts frontend (irctc.co.in/online-charts)
- Train lookup/autocomplete API used by charts module

**New data requirements:**
- None beyond existing train master list; optional client cache of recent trains per user (authenticated)

**API changes:**
- `GET /api/v1/trains/autocomplete?q=` — require `min_length=2`; return `[]` without error for short queries
- No change to chart vacancy API

**Frontend changes:**
- Replace combobox `emptyMessage` on mount: use `openOnFocus: false`, `minChars: 2`
- Initial render: hide listbox; `aria-expanded=false` until query length met
- Accessible labels: `aria-describedby` helper text “Type at least 2 characters”
- After failed search: “No trains found” instead of “0 results available”

**Third-party services (if any):**
- None

### Success Metrics

- Page loads showing “0 results” before input: from **100%** to **0%**
- Chart form completion rate (train selected + submit): increase by **≥25%** in 60 days
- Support queries mentioning “train search doesn’t work” on charts page: reduce by **≥50%**

### Edge Cases and Constraints

- Large train catalog: server-side pagination/typeahead required; do not load full list on focus
- Screen readers: avoid announcing empty result count on page load
- Slow API: show “Searching…” not “0 results” during load
- Graceful degradation: if autocomplete fails, allow manual train number entry with validation on submit

---

## Feature Spec 6: Redundant and Confusing Class Selection Dropdowns

### Problem Statement

The homepage **BOOK TICKET** form shows two class dropdowns—“All Classes” and “GENERAL”—without explaining their relationship. Users suffer decision paralysis and may search with wrong class filters, yielding irrelevant results (Part A Self-Discovered Problem 3). Affects virtually every search using the homepage form.

### Current State (from Part A)

User scrolls the booking form and sees **All Classes** and **GENERAL** stacked (steps 2–3). Unclear which to use (step 4). User may set both, one, or neither (steps 5–7). Results may be wrong or require re-search (step 8). Break at step 4: ambiguous labels and duplicate controls without a single mental model.

### Proposed Solution

One clearly labeled control: **Travel class** with options such as All Classes, First AC, Second AC, Third AC, Sleeper, and General. Helper text explains: “Choose a class to narrow results, or All Classes to see every option.” The redundant second dropdown is removed.

### Proposed User Flow — Step by Step

1. User opens homepage **BOOK TICKET** form.
2. User sees single **Travel class** dropdown defaulting to **All Classes**.
3. Optional helper: “Showing all classes — select one to filter.”
4. User picks **Sleeper**; only sleeper-related options apply to search.
5. User completes From, To, Date, taps **Search**.
6. Results and chips reflect chosen class; user can change class from results page without returning to duplicate controls.
7. User with disability or pass concessions uses separate labeled checkboxes (unchanged), not a second class dropdown.

*Compared to Part A:* Steps 3–7 replace dual dropdowns with one control and consistent labeling.

### Technical Implementation Plan

**System components affected:**
- Homepage booking form component
- Train search API (single `class` or `classes[]` parameter)
- Design system / form field registry

**New data requirements:**
- Map UI labels to canonical Railway class codes in config table (admin-maintained)
- Migration note: log usage of legacy “GENERAL” secondary field for deprecation analytics

**API changes:**
- `GET /api/v1/trains/search` — accept single `preferred_class` enum; ignore deprecated duplicate param after sunset period
- Document enum: `ALL`, `1A`, `2A`, `3A`, `SL`, `GN`, etc.

**Frontend changes:**
- Remove second dropdown; add `TravelClassSelect` with grouped options and icons
- Inline validation if incompatible with other form options (e.g., pass concession rules)
- Align with Feature Spec 2 filter chips when user changes class post-search

**Third-party services (if any):**
- None

### Success Metrics

- Homepage searches using ambiguous dual-dropdown state: reduce to **0%** after UI deploy
- Search result relevance complaints tied to class confusion: reduce by **≥30%** in 90 days
- Time-to-first successful search (form fill to results): reduce median by **≥10%**

### Edge Cases and Constraints

- “General” is both a colloquialism and a real quota/class—label clearly as **General (GN)** in UI
- Regional language support: translate labels, keep API codes stable
- Backward compatibility: accept old query params during transition, map to single field
- Graceful degradation: if new component fails, show single native `<select>` with same options—not two dropdowns

---

*End of Part B feature specifications. See [AI-FEATURE.md](./AI-FEATURE.md) and [MATRIX.md](./MATRIX.md) for AI proposal and prioritization.*
