# Bankroll Manual Adjustment — Design

**Date:** 2026-06-23
**File touched:** `index.html` (single-file HTML app "Poker Edge — Plan & Tracker")

## Goal

Let the user set the displayed "Bankroll actuelle" to an arbitrary value without creating a
deposit/withdrawal transaction — a reconciliation/correction tool. The manual value is stored as
an offset, so future sessions and transactions continue to move the bankroll on top of it.

## Background

Today `brCompute()` returns `bankroll = Σ tx + Σ sessions + Σ tournament profit` (all-time, never
period-filtered). There is no way to nudge that figure directly.

## Architecture

One new state field plus three small touch points. No new subsystem.

1. **State** — add `bankrollAdjust: 0` (a number) to the `state` literal and to the `confirmReset()`
   reset literal. `loadState()`'s `Object.assign` migrates old saves (defaults to `0`).
2. **Computation** — `brCompute()` adds `(state.bankrollAdjust||0)` to the all-time `bankroll` sum.
   No other KPI changes (profit/ROI/hourly/ABI stay as-is; the adjustment is not "profit").
3. **Trigger** — the "Bankroll actuelle" KPI card becomes clickable (cursor pointer + a small ✎
   affordance) and calls `brOpenAdjustForm()`.
4. **Form** — `brOpenAdjustForm()` opens the existing modal with a single numeric input pre-filled
   with the current displayed bankroll (`brCompute("all").bankroll`). `brSaveAdjust()` computes the
   new offset and stores it.
5. **Transparency / undo** — when `bankrollAdjust !== 0`, `renderBrRecent()` shows an extra
   "Ajustement manuel" row (signed, colored) with a ✕ that calls `brResetAdjust()` (sets
   `bankrollAdjust = 0`).

## Data flow

- **Set:** `newOffset = enteredValue − (currentBankroll − currentAdjust)`, i.e. entered value minus
  the computed bankroll excluding the existing offset. Store `state.bankrollAdjust = newOffset`,
  `saveState()`, `renderBankroll()`. Displayed bankroll then equals `enteredValue` exactly.
  Concretely: `base = brCompute("all").bankroll - (state.bankrollAdjust||0); state.bankrollAdjust = enteredValue - base;`
- **Future activity:** adding a session/transaction increases the computed sum; the offset is
  unchanged, so bankroll = newSum + offset — activity stacks on top of the manual value. ✓
- **Reset:** `state.bankrollAdjust = 0` → bankroll reverts to pure computed sum.

## UI details

- KPI card: only the first card ("Bankroll actuelle") gets `onclick="brOpenAdjustForm()"`,
  `style="cursor:pointer"`, and a small "✎" appended to its label (e.g. `Bankroll actuelle ✎`).
  Other cards stay non-interactive.
- Form modal:
  - Title "Modifier la bankroll".
  - One field: "Bankroll (€)" — `type="number"`, `step="0.01"`, value pre-filled with current
    bankroll (2 decimals). May be negative.
  - Helper line (small, muted): "Crée un ajustement manuel, sans transaction. L'activité future s'ajoute par-dessus."
  - Buttons: Enregistrer (`brSaveAdjust()`) / Annuler (`closeModal()`).
- Recent-list adjustment row (only when offset ≠ 0): label "Ajustement manuel", no date (renders
  with the existing `.br-row` markup; date field empty), amount = `brFmt(state.bankrollAdjust)`
  colored by sign, ✕ → `brResetAdjust()`. It sorts to the top since its date is empty
  (`localeCompare` puts "" last in a descending sort → appears at the bottom; acceptable, OR give it
  a synthetic always-top treatment). Decision: render the adjustment row FIRST, before the sorted
  tx/session rows, by prepending its HTML — it is a current-state marker, not a dated event.

## Validation & edge cases

- Empty input → reject (`toast("Valeur invalide")`, keep modal open).
- Non-numeric → `parseFloat` guard; reject if `NaN`.
- Value `0` is valid (user may intentionally set bankroll to 0).
- Setting the entered value equal to the current bankroll → offset adjusts so display is unchanged
  (no error).
- No NaN/Infinity in UI — offset is a plain number; all sums stay finite.

## Persistence

`localStorage` key `pokerEdge_v1`; whole `state` serialized (export/import include the new field
for free). Reset literal updated to include `bankrollAdjust: 0`.

## Testing (manual, browser)

1. Bankroll shows computed sum. Tap the "Bankroll actuelle" card → modal opens pre-filled with that
   sum.
2. Enter a different value (e.g. 500) → save → Bankroll actuelle shows exactly 500.00€; an
   "Ajustement manuel" row appears with the offset amount, colored.
3. Add a session +50 → Bankroll becomes 550.00€ (activity stacks on the manual value).
4. Tap the card again → pre-filled with 550.00€; the offset, not the entered value, is what persists.
5. ✕ on the adjustment row → bankroll reverts to pure computed sum; row disappears.
6. Enter empty/invalid → "Valeur invalide", no change.
7. Reload → offset persists. Export/import round-trips it. Reset ("Tout effacer") clears it to 0.

## Out of scope

History of adjustments (only one current offset), a date/note on the adjustment, period-scoping the
adjustment (it is always all-time, like bankroll itself).
