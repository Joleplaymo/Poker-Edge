# Bankroll Tracking Tab — Design

**Date:** 2026-06-22
**File touched:** `index.html` (single-file HTML app "Poker Edge — Plan & Tracker")
**Reference UI:** `poklab.jpeg` (poklab "Gestion de bankroll")

## Goal

Add a new "Bankroll" tab to Poker Edge: a KPI dashboard fed by manual cash sessions and
deposit/withdrawal transactions, combined with the existing tournament results, with a
bankroll-over-time chart and period filtering.

Scope chosen: **KPI dashboard + manual transactions + cash sessions**. A full poklab clone
(rooms management, rakeback, tickets, EUR/USD toggle, Global/Historique/Session sub-tabs) is
explicitly out of scope.

## Architecture

Single-file app. All work lives in `index.html`. Three coordinated insertion points, matching
the existing tab pattern:

1. **View section** — new `<section class="view" id="view-bankroll">` after `view-res` (~line 834).
2. **Nav button** — new `<button data-view="bankroll" onclick="switchView('bankroll')">` in
   `<nav class="bottom">` (~line 845). This makes 6 nav buttons; on narrow screens the bar
   compresses slightly (`nav.bottom button{flex:1}`). Accepted.
3. **Render hook** — add `if(name==="bankroll") renderBankroll();` in `switchView()` (~line 1421).

Rendering is hand-rolled DOM/HTML (no charting library), consistent with the rest of the
codebase. The bankroll-over-time chart follows the existing `renderStackChart()` pattern
(~line 1315): an inline SVG / CSS construction, no new dependency.

## Data model

Two new arrays on the global `state` object (defined ~line 1109). Both must also be added to
the reset literal (~line 4002). `loadState()` uses `Object.assign(state, parsed)`, so existing
saved data migrates automatically (the new keys default to `[]`).

```js
// transactions: money in/out of the bankroll, unrelated to play results
bankrollTx: []      // [{ id, type, amount, date, room, note }]
//   id:     string, unique (timestamp-based)
//   type:   "deposit" | "withdraw"
//   amount: number, positive € value
//   date:   "YYYY-MM-DD"
//   room:   string (free text, optional)
//   note:   string (optional)

// cash-game sessions: time played + net result
bankrollSessions: []  // [{ id, date, durationH, result, room, note }]
//   id:        string, unique
//   date:      "YYYY-MM-DD"
//   durationH: number, hours played (e.g. 2.5)
//   result:    number, net € (may be negative)
//   room:      string (optional)
//   note:      string (optional)
```

Tournament profit continues to come from the existing source:
`state.tournaments.filter(t => t.result)`, profit per tournament =
`(parseFloat(t.result.payout)||0) - (parseFloat(t.buyin)||0)`.

Currency: **EUR only** (matches the rest of the app). No USD toggle.

## KPI computation

A `period` UI state selects one of: `all` | `year` | `month` | `week`. Helper
`inPeriod(dateStr, period)` returns whether a date falls in the selected window (relative to
today, `2026-06-22` at build time but computed live via the app's date logic).

Period-filtered inputs:
- `sessions` = `bankrollSessions` whose `date` is in period
- `tournois` = tournaments with a result whose result date is in period
- `tx` = `bankrollTx` whose `date` is in period

| KPI | Formula |
|---|---|
| **Bankroll actuelle** | Σ deposits − Σ withdrawals + Σ session.result + Σ tournament profit. **Always all-time** (not period-filtered) — it is the current real balance. |
| **Profit (période)** | Σ session.result (period) + Σ tournament profit (period) |
| **ROI** | profit(period) / Σ tournament buy-ins (period). Shown `0.0%` when denominator is 0. |
| **Taux horaire** | Σ session.result (period) / Σ session.durationH (period). Sessions only (tournaments have no recorded duration). `0.00€/h` when no hours. |
| **ABI** | average tournament buy-in (period). `0.0€` when none. |
| **Sessions** | count of sessions (period) |
| **Tournois** | count of tournaments with result (period) |

Summary cards (always shown, independent of the period chip): **Cette semaine / Ce mois /
Cette année** — each shows profit (sessions + tournament profit) for that fixed window.

## UI layout

Reuses existing theme tokens (`--bg-*`, `--gold`, `--green`, `--red`, `--txt*`) and classes
(`.card`, `.btn`, `.stat`). Green for positive money, red for negative, following the existing
`.profit`/`.loss` convention.

Top → bottom inside `view-bankroll`:

1. **Header** — title "Gestion de bankroll".
2. **Period chips** — Tout / Année / Mois / Semaine. Active chip highlighted (`--gold`).
   Clicking re-renders.
3. **Action buttons** — `+ Nouvelle session`, `+ Nouvelle transaction`. Each opens a modal form.
4. **KPI grid** — cards for the 7 KPIs above.
5. **Bankroll chart** — cumulative bankroll over time (all entries sorted by date), hand-built
   SVG line/area, modeled on `renderStackChart()`. Empty-state message when no data.
6. **Summary cards** — Cette semaine / Ce mois / Cette année.
7. **Recent entries list** — merged sessions + transactions, newest first, each row showing
   date, type/label, amount (colored), room/note, and a delete (✕) control. Deleting removes
   from the relevant array, saves, and re-renders.

## Forms (modals)

A lightweight modal overlay (consistent with the app's existing styling) for each action.

**Nouvelle transaction:**
- Type (deposit/withdraw) — toggle or select
- Montant (€) — number, required, > 0
- Date — date input, defaults to today
- Room — text, optional
- Note — text, optional
- Enregistrer / Annuler

**Nouvelle session:**
- Date — defaults to today
- Durée (h) — number, required, ≥ 0
- Résultat (€) — number, required, may be negative
- Room — text, optional
- Note — text, optional
- Enregistrer / Annuler

On save: build the object with a unique `id`, push to the right array, `saveState()`, close
modal, `renderBankroll()`.

## Validation & edge cases

- Empty amounts / durations: reject save, keep modal open (basic guard).
- No data at all: KPIs show zeros (`0.00€`, `0.0%`), chart shows empty-state text.
- Division by zero (ROI, taux horaire, ABI): show `0` variants, never `NaN`/`Infinity`.
- Delete is immediate (no confirm) — entries are cheap to re-add; matches app's lightweight feel.

## Persistence

`localStorage` key `pokerEdge_v1` (whole `state` serialized). Export/Import JSON already
serialize the entire `state`, so the new arrays are included for free. Reset literal updated to
include `bankrollTx: []` and `bankrollSessions: []`.

## Testing

Manual verification in browser (single-file app, no test harness):
1. Add a transaction (deposit) → bankroll increases by amount; appears in recent list.
2. Add a withdrawal → bankroll decreases.
3. Add a winning session → profit + bankroll increase; taux horaire and sessions count update.
4. Add a losing session → values go red/negative correctly.
5. Switch period chips → period-scoped KPIs (profit, ROI, taux horaire, ABI, counts) recompute;
   bankroll actuelle stays all-time.
6. Existing tournament with a result → its profit is reflected in profit/bankroll.
7. Delete an entry → removed, totals recompute.
8. Reload page → data persists.
9. Export then reset then import → bankroll data round-trips.

## Out of scope (explicit)

EUR/USD toggle, room management + ordering, rakeback, tickets, Global/Historique/Session
sub-tabs, custom date range ("Personnalisé").
