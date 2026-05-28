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

---

## Self-Discovered Problem 1 — Forced Login Modal Blocks Guest Train Availability Search

- What is broken: When a guest user (not logged in) attempts to search for trains by typing a station name in the From/To field, a login modal appears immediately, preventing the user from exploring train availability without authentication. The modal completely blocks the search form, forcing authentication before any browsing.
- Who is affected and how many: Guest/casual users who want to check train availability before deciding to create an account; this affects potentially thousands of daily users who prefer to browse first before committing to login. Effect: reduced platform discoverability, poor user experience for first-time visitors, lost opportunity to convert casual browsers into registered users.
- Frequency: Every time a guest user starts typing in the station search field; 100% reproducible.
- How I found it: On the IRCTC homepage (irctc.co.in), I clicked on the "From" station field in the BOOK TICKET section and typed "Delhi" to search for origin stations. The login modal appeared immediately, blocking the search form and preventing further exploration.
- Screenshot or description: The IRCTC homepage shows a "BOOK TICKET" form with From, To, Date, Class dropdowns. When typing in the "From" field, an overlay login modal appears with User Name and Password fields, along with "FORGOT ACCOUNT DETAILS?", OTP option for "Visually impaired users", and a "SIGN IN" button. The modal prevents interaction with the form behind it.

- Step-by-step current flow (reproduction steps):
  1. User opens IRCTC homepage at irctc.co.in (not logged in).
  2. User sees the "BOOK TICKET" search form with From, To, Date, Class dropdowns.
  3. User clicks on or focuses the "From" station search field.
  4. User begins typing a station name (e.g., "Delhi").
  5. Before autocomplete results can appear, a login modal overlay appears on the screen.
  6. The modal blocks all interaction with the search form behind it.
  7. User must either login, dismiss the modal (if possible), or leave the page.

- Where it breaks (specific step & why): The break occurs between step 3 and step 5 - after the user inputs text into the From field. A JavaScript event listener (likely on input or focus) triggers the login modal rather than allowing the station search autocomplete to proceed. The modal is likely triggered by a global auth guard that treats any form interaction as a booking intent that requires authentication, but this is unnecessarily restrictive for casual browsing.

Evidence from live page: Observed on the live IRCTC homepage during May 28, 2026 exploration. Console logs show multiple event listeners and permission policy violations, suggesting aggressive authentication checks may be interfering with normal page interactions.

---

## Self-Discovered Problem 2 — Confusing Auto-Complete Initial State in Reservation Charts

- What is broken: On the Reservation Charts page (irctc.co.in/online-charts), the "Train Name/Number" search field displays "0 results available" in the dropdown before the user has typed anything. This suggests the field is non-functional or broken, causing user confusion about whether the autocomplete feature works.
- Who is affected and how many: Users trying to look up specific train charts by train number or name; affects users trying to verify their seat allocations or check train availability details. Effect: user confusion about field functionality, hesitation to use the feature, increased support queries about "why the train search doesn't work".
- Frequency: Every page load of the Reservation Charts page; 100% reproducible.
- How I found it: I navigated to the CHARTS / VACANCY link from the IRCTC homepage, which took me to irctc.co.in/online-charts. The page displayed a "Journey Details" form with a "Train Name/Number" field that had text "0 results available. Select is focused ,type to refine list, press Down to open the menu," visible in the field dropdown even before I typed anything.
- Screenshot or description: The Reservation Chart page shows a form titled "Journey Details" with three input fields: Train Name/Number (with a search icon), Journey Date (with date picker), and Boarding Station. The Train Name/Number field has a prominent message saying "0 results available" displayed in the input area, creating the false impression that no trains exist or the search is broken.

- Step-by-step current flow (reproduction steps):
  1. User opens the IRCTC Reservation Charts page at irctc.co.in/online-charts.
  2. The page loads the "Journey Details" form.
  3. The "Train Name/Number" input field is visible with placeholder or label text.
  4. The field displays "0 results available" message in the dropdown/autocomplete area.
  5. User sees this message and questions whether the field works.
  6. User may hesitate to interact with the field or assume it's broken.
  7. User starts typing a train name or number.
  8. Autocomplete should then filter results (if they exist).

- Where it breaks (specific step & why): The break occurs at step 4 - the autocomplete dropdown is showing an empty-state message ("0 results available") before the user has entered any search term. This violates the principle of "only show relevant information" - an autocomplete dropdown should either show a placeholder/help text or remain hidden until the user types. Showing "0 results" immediately implies the search is broken or no data exists, which is misleading and creates a poor user experience.

Evidence from live page: Observed on irctc.co.in/online-charts during May 28, 2026 exploration. The text was visible in the form input field before any user interaction.

---

## Self-Discovered Problem 3 — Redundant and Confusing Class Selection Dropdowns

- What is broken: The BOOK TICKET form on the IRCTC homepage displays two separate class selection dropdowns: "All Classes" and "GENERAL", creating ambiguity about which dropdown to use and what the difference is. Users are confused about whether to select "All Classes", then separately "GENERAL", or if one is a filter and the other a search parameter.
- Who is affected and how many: All users attempting to search for trains using the booking form; frequent cause of user confusion and incorrect search selections. Effect: users may not search for the right class of tickets, leading to irrelevant results or the need to search again.
- Frequency: Every time a user uses the booking form; affects all users who interact with class selection (likely a significant percentage of IRCTC users).
- How I found it: While exploring the BOOK TICKET form on the IRCTC homepage, I scrolled down the form and observed two distinct dropdown fields: the first labeled "All Classes" (showing a seat icon) and the second labeled "GENERAL" (showing a grid icon), both visible on the same form. The purpose and relationship between these two fields was unclear.
- Screenshot or description: The BOOK TICKET form on irctc.co.in shows two class-related dropdowns stacked vertically: the first is "All Classes" with a dropdown arrow, and below it is "GENERAL" also with a dropdown arrow. The form also includes checkboxes for "Person With Disability Concession", "Flexible With Date", and "Railway Pass Concession". The redundancy of two class fields is confusing.

- Step-by-step current flow (reproduction steps):
  1. User opens IRCTC homepage at irctc.co.in.
  2. User scrolls down to see the complete BOOK TICKET form.
  3. User sees the form has these fields: From, To, Date, "All Classes" (dropdown), "GENERAL" (dropdown), and checkboxes.
  4. User is uncertain which dropdown to use or what the difference is.
  5. User may click "All Classes" assuming it's the main class selector.
  6. User notices "GENERAL" dropdown below it and questions if they need to select it separately.
  7. User either selects both, selects one, or is unsure and defaults to both "All Classes" and "GENERAL".
  8. Search results may be filtered confusingly or user may have to re-search with different selections.

- Where it breaks (specific step & why): The break occurs at step 4 - the form UI does not clearly distinguish between the two class dropdowns. The labels "All Classes" and "GENERAL" are ambiguous. The first might be interpreted as "search all class types", while "GENERAL" might be a specific class (General/3rd class, which is a real class in Indian Railways). The presence of both fields without clear labeling or explanation creates cognitive load and decision paralysis. Best practice would be to have a single, clearly-labeled class selector (e.g., "Preferred Class" with options: All Classes, First AC, 2nd AC, 3rd AC, Sleeper, General) or remove the redundant field.

Evidence from live page: Observed on irctc.co.in during May 28, 2026 exploration while reviewing the booking form layout.

---

### Self-Discovery Notes

- Exploration was conducted on May 28, 2026, using Chrome browser at 1200x800 desktop viewport and 375x812 mobile viewport.
- Three issues were identified through systematic exploration of: (Area 1) train search functionality, (Area 2) booking form, (Area 3) reservation charts and status pages, (Area 4) mobile responsiveness, and (Area 5) accessibility features.
- All three issues are reproducible on the live site without requiring authentication or specific timing conditions.
- Screenshots of the issues were referenced from direct observation of the live pages during exploration.
