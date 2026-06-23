# Global Save / Load FAB — Design

**Date:** 2026-06-23
**File touched:** `index.html` (single-file HTML app "Poker Edge — Plan & Tracker")

## Goal

Add two globally-visible floating action buttons (FABs) — Save and Load — accessible from
every view, so the user can download a full backup or restore one without digging into the
Ressources tab. Reuses the existing `exportData()` / `importDataPrompt()` functions.

## Background (existing behavior)

- Data auto-saves to `localStorage` key `pokerEdge_v1` on every `saveState()`.
- `exportData()` (index.html ~4265) already downloads a full JSON of the entire `state`
  (bankroll included) as `poker-edge-export-YYYY-MM-DD.json`.
- `importDataPrompt()` (index.html ~4277) opens a file picker, parses JSON, confirms, replaces
  `state`, saves, and currently re-renders ONLY `renderTracker()` + `renderHome()`.
- These two actions are currently buried as buttons in the Ressources view (index.html ~831-832).

## Architecture

Pure HTML + CSS addition plus one small JS tweak. No new feature logic.

1. **FAB container** — a `<div class="fab-stack">` placed as a sibling of `<nav class="bottom">`
   (outside all `.view` sections), so it is fixed and visible on every view.
2. **Two round buttons** inside it:
   - Save: 💾, `onclick="exportData()"`, `title`/`aria-label` "Sauvegarder (télécharger backup)".
   - Load: 📂, `onclick="importDataPrompt()"`, `title`/`aria-label` "Recharger les données (importer)".
3. **JS tweak** — extend `importDataPrompt()` so that after a successful import it also refreshes
   the currently-active view (e.g. Bankroll), not just home/tracker, so restored data is visible
   immediately.

## Layout & styling

- Container fixed: `right:14px; bottom: calc(76px + env(safe-area-inset-bottom)); z-index:90;`
  `display:flex; flex-direction:column; gap:10px;`. This clears the bottom nav (`z-index:100`,
  height ~64px + safe area) and sits below modals (`.modal-bg` `z-index:200`). FABs do not
  overlap nav buttons (positioned above the bar, lower z than nav).
- Each button: 48×48px, `border-radius:50%`, `background:var(--gold)`, `color:var(--on-gold)`,
  `box-shadow:var(--shadow)`, `border:none`, `font-size:20px`, `cursor:pointer`,
  `:active{transform:scale(0.95)}` (matches existing nav button press feedback).
- Order top→bottom: Save (💾) then Load (📂).

## JS change detail

Replace the post-import re-render block in `importDataPrompt()`:

```js
state = imported;
saveState();
renderTracker();
renderHome();
toast("Import réussi ✓");
```

with a version that also refreshes the active view via the existing `switchView` render hooks.
Determine the active view from `document.querySelector(".view.active")` id (strip the `view-`
prefix) and call the matching render. Simplest robust approach: keep `renderHome()`/`renderTracker()`
and additionally re-run the active view's renderer through `switchView(activeName)` (which already
routes to the right render function and is idempotent). Implementation picks the active id and calls
`switchView(name)`; if none found, default to `home`.

## Error handling

Unchanged — `importDataPrompt()` already guards parse errors (`alert("Fichier invalide.")`) and
confirms before replacing. `exportData()` already toasts on success. No new error paths.

## Testing

Manual, in browser (single-file app, no test harness):
1. From any view (Home, Bankroll, Tracker…), the two FABs are visible bottom-right, above the nav.
2. Tap 💾 → a `poker-edge-export-*.json` file downloads, toast "Export téléchargé ✓".
3. Tap 📂 → file picker opens; choose a valid export → confirm dialog → data replaces, toast
   "Import réussi ✓", and the current view (incl. Bankroll) shows the restored data immediately.
4. Choose an invalid file → `alert("Fichier invalide.")`, no data change.
5. Open a modal (e.g. new transaction) → modal (z=200) covers the FABs.
6. FABs do not overlap or block the bottom-nav buttons on a narrow screen.

## Out of scope

Named/dated save slots, in-app restore list, auto-export, cloud sync. The existing Ressources
buttons stay as-is (no removal).
