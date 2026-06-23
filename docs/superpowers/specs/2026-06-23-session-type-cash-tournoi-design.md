# Typed Sessions (Cash / Tournoi) + Type Filter — Design

**Date:** 2026-06-23
**File touched:** `index.html` (single-file HTML app "Poker Edge — Plan & Tracker")

## Goal

Differentiate bankroll sessions by type — **cash** (with a number of tables) vs **tournoi**
(with a number of tournaments) — and add a Type filter (Tout / Cash / Tournoi) so the user can
read KPIs scoped to all play, cash only, or tournament only.

## Major behavior change

The bankroll KPIs become **sessions-only**: they derive from `state.bankrollSessions` +
`state.bankrollTx` + `state.bankrollAdjust`, and **no longer use `state.tournaments`** (the
Tracker). Consequences:
- Bankroll, profit, chart, and summary no longer include Tracker tournament profit.
- **ROI and ABI cards are removed** (sessions carry no buy-in).
This is the user's explicit choice ("Bankroll = sessions seules").

## Data model

Add two fields to each `bankrollSessions` entry:
- `type`: `"cash" | "tournoi"` — default `"cash"`.
- `count`: number — number of tables (cash) or number of tournaments (tournoi); default `0`.

Migration: existing sessions lack these. Read them defensively: `s.type||"cash"`, `+s.count||0`.
No data rewrite needed (`loadState` keeps old entries; defaults applied at read time).

`state` literal and `confirmReset` reset literal are unchanged for sessions (array already
exists); no new top-level state key for the data, but a new UI state var `brType` (see below).

## UI state

- Existing: `let brPeriod = "all";`
- New: `let brType = "all";  // "all" | "cash" | "tournoi"`
  `brSetType(t)` sets it and calls `renderBankroll()`.

## Session form (`brOpenSessionForm` / `brSaveSession`)

Add at the top of the form:
- **Type** select: options `Cash` (value `cash`, default) / `Tournoi` (value `tournoi`),
  `id="brSeType"`, `onchange="brSessionTypeChange()"`.
- **Count** field: `id="brSeCount"`, `type="number"`, `min="0"`, `step="1"`. Its label lives in a
  `<span id="brSeCountLabel">` updated by `brSessionTypeChange()`:
  - cash → "Nombre de tables"
  - tournoi → "Nombre de tournois"
  Initial label matches the default type (cash → "Nombre de tables").

`brSessionTypeChange()`: reads `brSeType` value, sets `brSeCountLabel` text accordingly.

`brSaveSession()` additions: read `type = document.getElementById("brSeType").value`,
`count = parseInt(document.getElementById("brSeCount").value,10)||0`; store both in the pushed
object alongside existing fields. Existing validation (duration ≥0, result non-empty) unchanged;
count is optional (defaults 0).

## Filters (two chip rows)

`renderBrChips()` renders the existing period row, then a second row for type. Markup: keep the
existing `#brPeriodChips` for period; add a second container. Simplest: render BOTH rows into
`#brPeriodChips` as two `.br-chips` divs (period chips, then type chips) so no HTML change is
needed beyond the existing container.

Type chips: `[["all","Tout"],["cash","Cash"],["tournoi","Tournoi"]]`, active = `brType`,
`onclick="brSetType('...')"`. Reuse the `.br-chips` styling.

## Computation (`brCompute(period, type)`)

Signature gains a `type` argument (default `"all"`). Session filtering:
`sessionsArr = state.bankrollSessions.filter(s => brInPeriod(brToMs(s.date), period) && (type==="all" || (s.type||"cash")===type))`.

- **bankroll** (all-time, ALL types — real money): `Σtx + Σ(all sessions).result + (bankrollAdjust||0)`.
  Tracker tournaments removed. Not affected by period or type.
- **profit** (period+type): `Σ sessionsArr.result`.
- **hourly**: `hours>0 ? sessProfit/hours : 0` over `sessionsArr`.
- **sessions**: `sessionsArr.length`.
- **tournoiCount**: `Σ count` over period-filtered sessions where `type==="tournoi"`
  (independent of the active type filter so the "Tournois" card is meaningful; but to respect the
  filter, compute over `sessionsArr` when type≠all, else over all tournoi sessions in period).
  Decision: compute over period-filtered sessions of type tournoi, regardless of `brType`, so the
  card always reflects tournament volume in the period.
- **tablesCount**: `Σ count` over period-filtered sessions where `type==="cash"`, same rule.

Return object: `{ bankroll, profit, hourly, sessions, tournoiCount, tablesCount, sessionsArr, txArr }`.
Remove `roi`, `abi`, `tournois` (Tracker), `tournArr` from consumers.

## KPI cards (`renderBrKpis`)

Compute `const c = brCompute(brPeriod, brType);`. Cards:
1. **Bankroll actuelle ✎** — `brFmt(c.bankroll)`, clickable (`brOpenAdjustForm`), colored by sign.
2. **Profit (période)** — `brFmt(c.profit)`, colored.
3. **Taux horaire** — `brFmt(c.hourly)+"/h"`, colored.
4. **Sessions** — `String(c.sessions)`, neutral.
5. **Tournois** — `String(c.tournoiCount)`, neutral. Shown when `brType !== "cash"`.
6. **Tables** — `String(c.tablesCount)`, neutral. Shown when `brType !== "tournoi"`.

(ROI and ABI cards removed.)

## Recent list (`renderBrRecent`)

Session row label becomes:
`"Session " + (s.type==="tournoi"?"tournoi":"cash") + (count? " · "+count+(tournoi?" tournois":" tables") : "") + (durationH? " · "+durationH+"h" : "") + (room? " · "+room : "")`.
Transactions and the manual-adjustment row are unchanged.

## Chart & summary

- `brEvents()`: drop the `state.tournaments` line; build from tx + sessions only. (Chart is the
  total bankroll curve, all types.)
- `brPeriodProfit(period)`: drop the Tracker tournament term; return `Σ sessions.result` in period.
  Make it respect the type filter too: add a `type` param defaulting to `brType`, filter sessions
  by type like `brCompute`. Summary cards call `brPeriodProfit(p)` using the active `brType`.

## Validation & edge cases

- `count` empty → 0 (optional field). Negative not allowed (`min=0`; `parseInt||0`).
- Old sessions (no type) → counted as cash; their `count` 0, so Tables card unaffected by them
  beyond count 0.
- No NaN: all sums guarded; `hourly` guarded by `hours>0`.
- Type filter `cash` hides the Tournois card; `tournoi` hides the Tables card; `all` shows both.

## Persistence

`localStorage` `pokerEdge_v1`; sessions array already serialized — new fields ride along.
Export/import unaffected. Reset literal already seeds `bankrollSessions: []`.

## Testing (manual, browser)

1. New session form shows Type select (Cash default) + a count field labelled "Nombre de tables".
   Switch type to Tournoi → label becomes "Nombre de tournois".
2. Add a cash session (2 tables, 3h, +60) → recent row "Session cash · 2 tables · 3h", Tables card
   shows 2, Sessions 1, profit +60, hourly 20.00€/h.
3. Add a tournoi session (5 tournois, 4h, −40) → row "Session tournoi · 5 tournois · 4h", Tournois
   card 5.
4. Type filter Cash → only cash sessions feed profit/hourly/sessions; Tournois card hidden, Tables
   shown. Tournoi → mirror. Tout → both cards, all sessions.
5. Period filter still composes with type filter.
6. Bankroll actuelle = tx + all sessions + adjust (independent of filters); Tracker tournaments do
   NOT contribute.
7. Chart and summary reflect sessions+tx only.
8. Reload / export-import round-trips type+count.

## Out of scope

Per-table or per-tournament buy-in, ROI/ABI reconstruction from sessions, back-filling type on old
sessions, separate cash/tournoi bankrolls.
