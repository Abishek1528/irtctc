# AI Feature Specification: Tatkal Queue Intelligence (Wait-Time & Outcome Predictor)

## Problem It Solves

This feature directly addresses **Problem 1 — Tatkal Booking Crashes at 10:00 AM** ([part-a/PROBLEMS.md](../part-a/PROBLEMS.md), lines 7–25).

At 10:00 AM, users hit the booking/availability step with no queue position, no progress meaning, and no actionable guidance (Part A step 6). They stare at a spinner, then see “quota exhausted” or silence. The pain is not only server overload—it is **uncertainty**: users cannot decide whether to wait, switch trains, or give up.

The Tatkal virtual queue UI (Feature Spec 1) fixes visibility with position counters and progress bars. **Tatkal Queue Intelligence** adds an AI layer on top of that queue: a predicted wait time, a booking-success likelihood, and a single recommended next action—so users act on evidence instead of guessing during the highest-stress minute of the IRCTC experience.

Secondary benefit: reduces perceived “broken” state when the queue moves slowly but is still working (fewer abandonments that worsen load).

---

## Proposed Feature — User Perspective

After the user joins the Tatkal queue at 10:00 AM, the queue screen (same flow as Feature Spec 1) shows a new card below the position counter:

**“Smart estimate”** — e.g. *“About 2–3 minutes until your turn · 68% chance this train still has Tatkal berths”* and one line: *“Recommendation: Stay in queue”* or *“Consider train 12952 — similar route, shorter wait.”*

The user sees this:

- **When enrolling** — initial estimate within 2 seconds of queue token issuance (may say “Calculating…” briefly).
- **Every 15 seconds** while waiting — estimates refresh as position and live quota signals change.
- **When reaching the front** — estimate switches to *“Confirming berth…”* and success probability is hidden (deterministic booking step takes over).

The user can:

- **Trust the wait estimate** to decide whether to keep the app open.
- **Tap “Why this estimate?”** to see plain factors (position, train demand tier, today’s release speed)—not model internals.
- **Tap an alternate-train suggestion** (only shown when model confidence ≥ 0.75 and a materially better option exists) to open pre-filled search for that train—without losing their current queue place until they explicitly switch.

They never see raw model scores—only rounded time ranges, percentage bands, and one clear recommendation.

---

## Model or API Choice

**Primary model: XGBoost regressor + XGBoost classifier** (Python `xgboost` 2.x, served via an internal prediction microservice).

| Task | Model | Output |
|------|--------|--------|
| Wait time until dequeue | `XGBRegressor` (`objective=reg:squarederror`) | Seconds (converted to “~2–3 min” range in UI) |
| Tatkal berth still available when user reaches front | `XGBClassifier` (`objective=binary:logistic`) | Probability 0–1 |

**Why XGBoost and not alternatives**

| Alternative | Why not primary |
|-------------|------------------|
| OpenAI GPT-4 / Gemini | High latency (800ms–3s), cost per poll every 15s × millions of users, non-deterministic text, harder to audit for a government-adjacent system; poor fit for numeric queue ETA |
| Generic “use ML” | No reproducible training pipeline or confidence scores |
| LSTM / deep learning | Needs very long series per route; IRCTC queue feature is new—tabular features (position, concurrency, train tier) work well with limited history |
| Rule-only ETA (`position × avg_sec`) | Ignores train-specific demand, day-of-week, AC vs SL, and live dequeue velocity; fails on spike days |

**Optional enrichment (not on critical path):** one-sentence explanation strings can be templated from feature contributions (SHAP values computed offline in batch). No LLM is required for v1.

**Serving:** REST `POST /api/v1/tatkal/predict` behind the queue service; model artifacts versioned in object storage (`tatkal-eta-v{semver}.json` + `.ubj`).

---

## Training or Input Data

### What the model needs (feature vector at prediction time)

| Feature | Source | Available today? |
|---------|--------|------------------|
| `queue_position` | Tatkal queue service (`tatkal_queue_entries.position`) | **New** — requires Feature Spec 1 queue deployment |
| `queue_depth_total` | Queue metrics (`tatkal_queue_metrics.total_enrolled`) | **New** |
| `seconds_since_window_open` | Server clock vs 10:00:00 release | Yes |
| `dequeue_rate_30s` | Rolling count of `status=processing` transitions / 30s | **New** — derived from queue logs |
| `train_demand_tier` | Static lookup: train_number → tier (A/B/C) from historical Tatkal sell-out minutes | **Partial** — build from 90-day booking outcome warehouse |
| `class_code` | User session (SL, 3A, etc.) | Yes |
| `route_pair_hash` | From/to station IDs | Yes |
| `day_of_week`, `is_holiday` | Calendar service | Yes |
| `historical_avg_wait_p50_p90` | Aggregated past windows per route+class | **Needs ETL** — 90 days minimum |
| `live_quota_signals` | Railway availability API sample (Tatkal remaining flag, rate-limited) | Yes (with latency caveats) |
| `user_retry_count_today` | Booking audit log | Yes |

### Training labels (historical)

| Label | Definition | Source |
|-------|------------|--------|
| `actual_wait_seconds` | `processing_started_at - enrolled_at` | Queue audit tables (post-launch) + **bootstrap** from synthetic replay of web server access logs during 10:00–10:05 windows (proxy: time from HTTP 202 queue response to 200 hold response) |
| `booking_success` | 1 if PNR issued within session, else 0 | IRCTC booking DB / PNR table |

### Data collection plan

1. **Phase 0 (weeks 1–2):** Backfill `historical_avg_wait_p50_p90` and `train_demand_tier` from anonymized Tatkal attempt logs (existing IRCTC ops data—assumed available to platform team; if not, start with route-level defaults).
2. **Phase 1 (weeks 3–6):** Run queue service in **shadow mode** (log features + outcomes, do not show AI card) to accumulate ≥10,000 labeled windows across top 200 trains.
3. **Phase 2:** Train v1 XGBoost; validate MAE &lt; 45s on wait time and AUC &gt; 0.72 on success classifier on hold-out last 14 days.
4. **Ongoing:** Nightly retrain on rolling 90-day window; champion/challenger in staging.

**Not used:** user name, Aadhaar, payment details, or free-text—only operational and booking-metadata features.

---

## How Output Is Shown to the User

Integrated into the **Tatkal Queue screen** wireframe ([assets/wireframes/tatkal-queue-screen.png](../assets/wireframes/tatkal-queue-screen.png)) — mobile-first, below existing components.

### ASCII layout (proposed card placement)

```
┌─────────────────────────────────────┐
│  Tatkal Queue                       │
├─────────────────────────────────────┤
│  Queue position: #847 / ~12,000     │  ← existing (Spec 1)
│  [████████░░░░] progress            │
│  Countdown to 10:00 AM              │
├─────────────────────────────────────┤
│  ✦ Smart estimate          [?]      │  ← NEW AI card
│  About 2–3 min until your turn      │
│  ~68% chance berths still available │
│  → Stay in queue                    │  ← recommendation line
├─────────────────────────────────────┤
│  [ Cancel queue ]    [ My Queue ]   │
└─────────────────────────────────────┘
```

### UI component spec

| Element | Label / copy | Behavior |
|---------|----------------|----------|
| Card container | `SmartEstimateCard` | Subtle blue border; spark icon ✦ denotes AI-assisted |
| Wait line | `About {low}–{high} min until your turn` | Rounded from regressor seconds ÷ 60; band = ±1 bucket |
| Success line | `~{pct}% chance berths still available` | Classifier probability × 100, rounded to nearest 5% |
| Recommendation | `→ {action}` | Enum: `Stay in queue` \| `Consider train {no}` \| `High demand — prepare payment` |
| Help icon `[?]` | “Why this estimate?” | Bottom sheet: 3 bullet factors (position, train demand, current speed)—no SHAP jargon |
| Alternate train link | Only if recommendation = Consider train X | Tap → new tab/search; queue preserved until user confirms switch |
| Loading | `Calculating estimate…` | Skeleton in card for &lt; 2s on first paint |
| Updating | Pulsing dot on card | Every 15s refresh without layout shift |

**Wireframe reference:** Extend the “AFTER (Proposed)” phone mock in `tatkal-queue-screen.png` with the `Smart estimate` block between the progress bar and **Cancel queue** button.

**States tied to wireframe legend**

- **Loading:** skeleton inside Smart estimate card (not whole-screen spinner).
- **High confidence:** full card as above.
- **Low confidence / fallback:** see next section—card collapses to rule-based copy.
- **Error:** card hidden; queue position UI unchanged (Spec 1 graceful degradation).

---

## Confidence Threshold and Fallback

Predictions are shown only when the **combined gate** passes:

```
show_ai_card = (
  regressor_confidence >= 0.70
  AND classifier_confidence >= 0.65
  AND model_version != "fallback"
  AND predict_api_latency_ms < 500
)
```

**Confidence definition (XGBoost):**

- Regressor: `1 - min(1, prediction_interval_width / 120)` where interval width comes from quantile models `XGBRegressor` at α=0.1 and α=0.9 trained alongside point estimate.
- Classifier: `max(probability, 1 - probability)` — distance from 0.5.

### When AI output is hidden or downgraded

| Condition | User sees |
|-----------|-----------|
| `show_ai_card == false` (low confidence) | **Rule-based fallback:** `Estimated wait: position × 4 sec (typical)` — gray card, no ✦ icon, label *“Standard estimate”* |
| Predict API timeout or 5xx | No Smart estimate card; only Spec 1 queue position + progress bar |
| Model version stale (&gt; 48h failed retrain) | Banner: *“Estimates temporarily unavailable”* — queue still works |
| `live_quota_signals` stale (&gt; 60s) | Success probability line hidden; wait estimate only with disclaimer *“Berth availability unknown”* |
| User at position ≤ 10 | Wait line only; success probability hidden (too late to act) |

**User actions on wrong predictions**

- **“Was this helpful?”** thumbs on card → logs for retraining.
- Estimates are **advisory** — footer microcopy: *“Estimates are not guaranteed. Booking subject to Railway availability.”*

---

## Success Metrics

| Metric | Baseline (Problem 1) | Target (90 days post-launch) |
|--------|----------------------|------------------------------|
| Tatkal queue sessions with any wait guidance beyond spinner | ~0% | **≥90%** (AI + rule fallback) |
| Wait-time MAE (held-out windows) | N/A | **&lt; 45 seconds** at p50 |
| User abandonment during queue (exit before dequeue) | High (qualitative) | **↓ 25%** vs pre-queue baseline |
| “Unclear wait / silent failure” support tags | High | **↓ 40%** |
| Smart estimate thumbs-up rate | N/A | **≥ 70%** |
| Incorrect alternate-train suggestion rate (user taps then returns) | N/A | **&lt; 5%** |

**Guardrail metrics:** PNR issuance rate must not decrease; payment timeout rate must not increase (detect if bad “leave queue” advice).

---

## Limitations and Risks

### Limitations

- **Cold start:** New trains/routes lack `train_demand_tier` — fallback rules only until 30+ windows observed.
- **Railway API lag:** Quota signals may trail reality by 30–60s; success probability can be wrong on instant sell-out.
- **Non-stationary peaks:** Festivals, strikes, or DDoS-like spikes are underrepresented in 90-day training data.
- **English/Hindi copy only in v1** — regional language requires separate UX pass, not model change.

### Risks and mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| User leaves queue based on optimistic ETA, loses place | Lost booking | Never auto-cancel queue from AI; alternate train requires explicit confirm |
| Model bias toward popular routes (more training data) | Unfair estimates on rural lines | Per-route calibration layer; widen intervals for low-data routes → triggers fallback sooner |
| Over-trust in success % | Payment prep failure, anger | Cap displayed probability wording; show ranges; mandatory disclaimer |
| Model wrong on sell-out day | Reputation harm | Conservative classifier threshold; hide success % when quota API uncertain |
| PII leakage in logs | Compliance | Feature store excludes identity fields; aggregate training tables only |
| Adversarial scraping of predict API | Load + gaming | Rate limit per `queue_token`; auth required |

### When the model is wrong

Users may wait too long or switch trains unnecessarily. Mitigation: post-session survey, thumbs feedback, weekly error analysis on top decile |predicted_wait − actual_wait|, and automatic rollback to **rule-only fallback** if MAE &gt; 90s for 24h rolling window.

---

*This AI feature extends [Feature Spec 1](./SPECS.md) (Tatkal queue) and is displayed on [tatkal-queue-screen.png](../assets/wireframes/tatkal-queue-screen.png). It does not replace Railway authority on availability— it reduces uncertainty during Problem 1’s failure window.*
