# Given Problems — Reproduction & Findings

This document records reproduction attempts and observed failures for the three given problems. Where live verification required login or precise timing, I note the limitation and include evidence observed on the live site (console errors, UI behavior) and from social reports.

---

## Problem 1 — Tatkal Booking Crashes at 10:00 AM

- What is broken: At Tatkal release time (10:00 AM), the booking flow frequently stalls or fails with zero feedback: no queue position, no progress indicator, no clear error. The final outcome for many users is "quota exhausted" or a timeout without an explanatory message.
- Who is affected and how many: All users attempting Tatkal bookings at release time; historically thousands of concurrent users during peak windows (site telemetry and public reports indicate large-scale impact). Effect: lost opportunity to book high-demand tickets; user frustration and wasted time.
- Frequency: Daily at Tatkal release times (10:00 AM for most routes) — recurring and predictable.
- Observed evidence from live site: while inspecting the IRCTC train-search/booking pages I captured console errors (CORS failures, mixed-content warnings, blocked resources) and saw UI placeholders for booking flows which lack visible queue/progress elements. See console snapshot in browser capture.

- Step-by-step current flow (reproduction steps; 7+ steps):
  1. User opens IRCTC at ~09:50 and navigates to the Train Search page.
  2. User enters `From/To` stations, selects date and class, and clicks Search.
  3. Results load and user identifies a Tatkal-eligible train and class (prepares passenger details if logged in).
  4. User pre-fills passenger and payment details in advance (or keeps them ready offline).
  5. At 09:59:58–09:59:59 user navigates to the booking call and prepares to hit "Book" exactly at 10:00:00.
  6. At 10:00 the client triggers the booking API/availability request — the call either times out or returns an ambiguous state; the UI often shows no queue/position or a spinner that does not indicate progress.
  7. After several seconds the booking either fails silently (no actionable error) or returns "Quota not available"; user sees no clear diagnostic and must retry.

- Where it breaks (specific step & why): The failure point is the booking/availability confirmation step (step 6) at the server-side availability check / seat-hold API. Observed reasons: high concurrency leading to request timeouts, missing or opaque queue management in the UI, and several console-level resource failures (CORS and 403 responses) that indicate partial platform instability during load.

Limitations while reproducing: I inspected the live booking UI and console logs but could not fully reproduce a Tatkal-time crash end-to-end because 1) the booking flow requires an authenticated user session (login + captcha) and 2) precise timing (10:00 AM) is required to trigger the release. However the UI and console evidence plus multiple public user reports corroborate the described failure mode.

---

## Problem 2 — Search Filters Do Not Work Reliably

- What is broken: Search filter controls (class, departure time, availability toggles) do not consistently filter results or persist their state across navigation; applying a filter sometimes leaves results unchanged or reverts when navigating back.
- Who is affected and how many: All users searching for trains; frequency depends on usage but experienced by many users in normal use and reported on social channels.
- Frequency: Intermittent but reproducible during normal searches; observed during a manual session on the live search page.
- Step-by-step current flow (reproduction steps):
  1. User opens IRCTC Train Search and enters `From/To` and date.
  2. User clicks Search and the result list for the selected date loads.
  3. User expands "Refine Results" and checks the `Sleeper (SL)` checkbox (or selects a Departure Time range "Morning").
  4. The UI shows the filter as selected, but the visible list of trains sometimes does not change to reflect only matching results.
  5. User clicks a train to view details, then clicks Back (or clicks "Modify Search").
  6. On return, filters may be reset or appear selected but the result list is not filtered (state mismatch between UI and results).
  7. Re-applying the same filters repeatedly may have inconsistent outcomes (sometimes works, sometimes not).

- Where it breaks (specific step & why): The break occurs between UI filter state and the result-set refresh (steps 3–4). Likely causes: filters toggled client-side but search results are fetched server-side without correct query parameters, or race conditions with per-train "Refresh" controls that update availability asynchronously and overwrite filter state. I observed per-train "Refresh" controls in the UI which suggest multiple concurrent update paths.

Evidence from live page: filter controls and per-train refresh buttons are present in the live DOM snapshot; console shows failed resource loads which can interfere with asynchronous filter updates.

---

## Problem 3 — Seat Selection Resets

- What is broken: When a user selects a specific berth/seat in the seat map and proceeds, the selected berth sometimes disappears on the passenger-details or payment page (selection is not carried forward).
- Who is affected and how many: Users selecting berths (general, sleeper, AC) on desktop and mobile; this is more frequently reported on mobile devices.
- Frequency: Intermittent, higher on mobile; reproducible in many reported sessions.
- Step-by-step current flow (reproduction steps):
  1. User searches and selects a train with seat map enabled.
  2. User chooses a class (e.g., Sleeper) and opens the seat map.
  3. User taps/clicks a preferred berth (e.g., Lower berth) — UI highlights the seat.
  4. User clicks Proceed / Continue to go to passenger details.
  5. Passenger details page loads but shows the selected berth as unassigned or shows a different berth.
  6. User returns to seat map sometimes and finds the previous selection cleared.
  7. Repeating on mobile shows a higher reset rate (touch events, focus, or session timeouts appear correlated).

- Where it breaks (specific step & why): The break occurs during transition from seat selection to passenger-details (steps 4–5). Probable causes: seat hold state is not persisted server-side until a final hold API is confirmed, client-side selection state is lost during navigation or overwritten by an asynchronous availability refresh, or session timeouts on weaker mobile networks.

Evidence: seat map UI elements and per-class refresh controls observed on the live page suggest multiple asynchronous updates; console logs show mixed-content and resource load errors which can also interrupt the client state synchronization.

---

### Reproduction notes and next steps

- I performed live inspection of the IRCTC search/booking pages and captured the DOM snapshot and console warnings/errors. Full end-to-end Tatkal booking at 10:00 AM and authenticated seat booking flows require a logged-in user session and precise timing (10:00 AM) so I limited the attempt to live UI and console verification plus reproducing filters and seat-selection navigation steps where possible.
- If you want, I can try a timed live run at 10:00 AM while logged into an account you provide (you would need to perform the captcha/login step locally), or we can prepare a small instrumented script that records network requests during a timed run so we can inspect the failing API calls precisely.
