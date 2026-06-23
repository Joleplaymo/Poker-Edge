# Bankroll Management Recommendation + Room Filter — Design

**Date:** 2026-06-23
**File touched:** `index.html` (single-file HTML app "Poker Edge — Plan & Tracker")

Two related additions to the Bankroll tab:
A. A bankroll-management recommendation section (max recommended buy-in from the current bankroll,
   with adjustable required-buy-in counts for cash and tournament).
B. A Room filter as a third KPI filter dimension (period × type × room).

## Feature A — Bankroll management recommendation

### Goal
Show the user the maximum buy-in they should play given their current bankroll, using the classic
"bankroll / required buy-ins" rule, with the required count adjustable per game type.

### State
- `brBuyinCash: 30` — required number of cash buy-ins (default 30).
- `brBuyinTournoi: 100` — required number of tournament buy-ins (default 100).
Both added to the `state` literal and the `confirmReset()` reset literal. `Object.assign` migration
applies defaults to old saves. Stored as numbers.

### Computation
Bankroll used = `brCompute("all").bankroll` (all-time real balance, unaffected by filters).
- `maxBuyinCash = nCash>0 ? bankroll / nCash : 0`
- `maxBuyinTournoi = nTournoi>0 ? bankroll / nTournoi : 0`
Guard division by zero (show `0.00€` if the count is 0 or empty).

### UI
A new container `<div id="brReco"></div>` added to `view-bankroll`, after `#brRecent`.
`renderBrReco()` renders a `.card` titled "Gestion de bankroll":
- Intro line (muted): "Buy-in max conseillé selon ta bankroll actuelle (<bankroll>€)."
- Two editable rows (inputs), each `type="number" min="1" step="1"`:
  - "Buy-ins requis (cash)" → `id="brNCash"`, value = `state.brBuyinCash`, `onchange="brSaveReco()"`.
  - "Buy-ins requis (tournoi)" → `id="brNTournoi"`, value = `state.brBuyinTournoi`,
    `onchange="brSaveReco()"`.
- Two result rows (read-only, emphasized): "Buy-in max cash: <maxBuyinCash>€" and
  "Buy-in max tournoi: <maxBuyinTournoi>€".

`brSaveReco()`: read both inputs (`parseInt(...,10)`), clamp to `>=1` (if `NaN`/`<1`, fall back to
the current stored value), store in `state`, `saveState()`, re-render (`renderBrReco()` is enough,
but calling `renderBankroll()` is simplest and idempotent).

`renderBrReco()` is called from `renderBankroll()`.

### Edge cases
- Empty/zero/negative count → treated as the previous valid value on save; display guards against
  division by zero (0 → `0.00€`).
- Negative bankroll → recommended buy-in shows the (negative) division result; acceptable, it simply
  signals "no bankroll to play". No special-casing.

## Feature B — Room filter (third KPI filter)

### Goal
Filter the bankroll KPIs by playing room (free-text field already on sessions), in addition to the
existing period and type filters.

### State (UI only)
- `let brRoom = "all";` and `brSetRoom(r){ brRoom = r; renderBankroll(); }`. Not persisted (a
  transient view filter, like `brPeriod`/`brType`).

### Distinct rooms
`brRooms()` returns the sorted list of distinct non-empty `room` values across
`state.bankrollSessions` (trimmed). Used to build the select options.

### UI
In `renderBrChips()`, after the type chip row, render a room `<select id="brRoomSel">`:
- First option `value="all"` → "Toutes les rooms".
- One option per distinct room (value = room text, label = room text), `selected` when
  `brRoom===room`.
- `onchange="brSetRoom(this.value)"`.
- If `brRoom` is set to a room that no longer exists (e.g. after deleting its last session), it
  falls back to "all" on next render (the select simply shows "Toutes" because no option matches;
  to be safe, `brCompute` treats an unmatched room as filtering to zero sessions — acceptable, and
  the user can reselect "Toutes"). Decision: keep simple; no auto-reset logic.

Styled inline (reuse `.fld`-like select styling or a plain select with small margin-top).

### Computation
`brCompute(period, type, room)` gains a `room` parameter (default `"all"`). Session filtering:
`periodSess = state.bankrollSessions.filter(s => brInPeriod(brToMs(s.date), period) && (room==="all" || (s.room||"")===room))`.
Then `sessionsArr = periodSess.filter(s => type==="all" || (s.type||"cash")===type)` as today.
`tournoiCount`/`tablesCount` derive from `periodSess` (so they respect period + room).
- `bankroll` stays all-time, all sessions + tx + adjust — NOT room/period/type filtered.
- `profit`, `hourly`, `sessions`, counts respect period + type + room.

`renderBrKpis()` calls `brCompute(brPeriod, brType, brRoom)`.

`brPeriodProfit(period, type, room)` gains a `room` param; summary cards pass `brType, brRoom`.

### Out of scope
- Room filter on the recent-entries list (stays unfiltered — user's choice).
- Room on Tracker tournaments (no such field).
- Recommendation based on variance/ROI; persisting filter selections.

## Persistence
`localStorage` `pokerEdge_v1`. New persisted keys: `brBuyinCash`, `brBuyinTournoi` (added to state +
reset literals). `brRoom` is transient (not persisted). Export/import include the two new numeric
keys for free.

## Testing (manual, browser)

Feature A:
1. Bankroll tab shows a "Gestion de bankroll" card with two count inputs (30 / 100 by default) and
   two computed max buy-ins.
2. With bankroll 3000€: cash max = 3000/30 = 100.00€, tournoi max = 3000/100 = 30.00€.
3. Change cash count to 20 → cash max updates to 150.00€ live; persists on reload.
4. Set a count to 0/empty → reverts to last valid value; no NaN/Infinity shown.

Feature B:
5. Add sessions with rooms "Winamax" and "PokerStars". The room select lists "Toutes",
   "PokerStars", "Winamax" (sorted).
6. Select "Winamax" → profit/hourly/sessions/Tournois/Tables reflect only Winamax sessions; combine
   with period and type filters.
7. Bankroll actuelle is unchanged by the room filter.
8. Recent-entries list is NOT filtered by room.
9. Reload → buy-in counts persist; room filter resets to "Toutes" (transient).
