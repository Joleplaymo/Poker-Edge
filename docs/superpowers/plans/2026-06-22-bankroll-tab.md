# Bankroll Tracking Tab Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a "Bankroll" tab to Poker Edge with KPI dashboard, manual cash sessions + deposit/withdrawal transactions, a bankroll-over-time chart, and period filtering.

**Architecture:** All changes are inside the single file `index.html`. A new bottom-nav tab (`view-bankroll`) follows the existing view/`switchView()` pattern. Two new `state` arrays (`bankrollTx`, `bankrollSessions`) persist via the existing `localStorage` + `Object.assign` flow. Rendering is hand-rolled DOM/HTML; the chart is an inline SVG modeled on the existing `renderStackChart()`. Forms reuse the existing `openModal(html)` / `closeModal()` modal.

**Tech Stack:** Vanilla HTML/CSS/JS, single file. No build, no test framework, no charting lib. Verification is manual in a browser.

## Global Constraints

- Single file only: `c:\Users\lemoa\Desktop\Projets\Poker-Edge\index.html`. No new files, no dependencies.
- Currency: EUR only. Format money as `xx.xx€` (or `xx.xx€/h` for hourly). Use `var(--green)` for ≥0, `var(--red)` for <0. Match existing `.profit`/`.loss` convention.
- Reuse existing classes/tokens: `.card`, `.btn`, `.btn.secondary`, `.btn.compact`, `.btn.small`, `.stat-grid`, `.stat` (`.v` value + `.l` label), `.row`, `--bg-*`, `--gold`, `--green`, `--red`, `--txt`, `--txt-mute`. No new CSS unless a step says so.
- Never produce `NaN`, `Infinity`, or `undefined` in the UI — guard every division (return 0 when denominator is 0).
- No automated tests exist. Each task's verification is: open `index.html` in a browser (or reload), perform the listed actions, confirm the listed outcome. Use the browser devtools console where noted.
- Tournament profit source (do not change): `state.tournaments.filter(t=>t.result)`, profit `= (parseFloat(t.result.payout)||0) - (parseFloat(t.buyin)||0)`, result date `= t.result.end` (ms timestamp).
- Commit after each task with the exact message given.

---

## File Structure

Single file `index.html`. Insertion points (line numbers approximate — match on the quoted anchor text, not the number):

- **HTML view section** — after `</section>` of `view-res` (line ~834), before `</main>` (line ~836).
- **HTML nav button** — inside `<nav class="bottom">` (lines ~839-845), after the `res` button.
- **`state` literal** — lines ~1109-1119.
- **`confirmReset()` reset literal** — line ~4002.
- **`switchView()`** — lines ~1410-1422.
- **New JS (helpers + render + forms + chart)** — appended as one `<script>`-internal block immediately after `switchView()` closes (after line ~1422), inside the existing `<script>`.

All new JS identifiers are namespaced `br*` (bankroll) to avoid collisions.

---

### Task 1: Scaffold the tab (state, nav, view shell, render stub)

**Files:**
- Modify: `index.html` state literal (~1109), reset literal (~4002), nav (~845), view insert (~834), switchView (~1421), new JS block (~1423).

**Interfaces:**
- Produces: `state.bankrollTx` (array), `state.bankrollSessions` (array); DOM container IDs `brPeriodChips`, `brKpiGrid`, `brChart`, `brSummary`, `brRecent`; function `renderBankroll()` (stub for now).

- [ ] **Step 1: Add the two state arrays**

In the `state` literal (lines ~1109-1119), change the `tournaments`/`liveId` area so the object includes the new keys. Replace:

```js
  tournaments: [],
  liveId: null,
```

with:

```js
  tournaments: [],
  liveId: null,
  bankrollTx: [],        // [{id,type:"deposit"|"withdraw",amount,date,room,note}]
  bankrollSessions: [],  // [{id,date,durationH,result,room,note}]
```

- [ ] **Step 2: Add the arrays to the reset literal**

In `confirmReset()` (line ~4002), replace:

```js
  state = {tasks:{},drillScore:0,drillTotal:0,drillSession:{score:0, total:0},tournaments:[],liveId:null};
```

with:

```js
  state = {tasks:{},drillScore:0,drillTotal:0,drillSession:{score:0, total:0},tournaments:[],liveId:null,bankrollTx:[],bankrollSessions:[]};
```

- [ ] **Step 3: Add the nav button**

In `<nav class="bottom">`, after the `res` button line (~844), add:

```html
  <button data-view="bankroll" onclick="switchView('bankroll')"><span class="ico">€</span>Bankroll</button>
```

- [ ] **Step 4: Add the view section shell**

After the `view-res` section's closing `</section>` (~834) and before `</main>` (~836), insert:

```html
<!-- ============== BANKROLL ============== -->
<section class="view" id="view-bankroll">
  <h2 style="margin:0 0 4px;font-size:24px">Gestion de bankroll</h2>
  <p style="color:var(--txt-mute);font-size:13px;margin:0 0 14px">Suivi de gains, sessions &amp; transactions</p>

  <div id="brPeriodChips" class="br-chips"></div>

  <div class="row" style="margin:12px 0">
    <button class="btn compact" onclick="brOpenSessionForm()">+ Nouvelle session</button>
    <button class="btn secondary compact" onclick="brOpenTxForm()">+ Nouvelle transaction</button>
  </div>

  <div id="brKpiGrid" class="stat-grid"></div>
  <div id="brChart"></div>
  <div id="brSummary" class="stat-grid" style="margin-top:14px"></div>
  <div id="brRecent"></div>
</section>
```

- [ ] **Step 5: Add minimal CSS for the period chips**

In the `<style>` block, immediately before the closing `</style>`, add:

```css
.br-chips{display:flex;gap:6px;flex-wrap:wrap}
.br-chips button{flex:0 0 auto;padding:6px 12px;border-radius:999px;border:1px solid var(--line-2);background:var(--bg-2);color:var(--txt-dim);font-size:12px;cursor:pointer}
.br-chips button.active{background:var(--gold);color:var(--on-gold);border-color:var(--gold)}
.br-row{display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:1px solid var(--line)}
.br-row .br-meta{font-size:12px;color:var(--txt-mute)}
.br-row .br-amt{font-weight:700}
.br-del{background:none;border:none;color:var(--txt-mute);cursor:pointer;font-size:16px;padding:0 4px}
```

- [ ] **Step 6: Hook switchView**

In `switchView()` (line ~1421), after the `if(name==="drills") resetDrillArea();` line, add:

```js
  if(name==="bankroll") renderBankroll();
```

- [ ] **Step 7: Add the render stub + period state**

Immediately after the closing `}` of `switchView()` (line ~1422), insert:

```js
/* =========================================================
   BANKROLL
   ========================================================= */
let brPeriod = "all"; // "all" | "year" | "month" | "week"

function renderBankroll(){
  document.getElementById("brKpiGrid").innerHTML =
    '<div class="stat"><div class="v">—</div><div class="l">Bankroll</div></div>';
  document.getElementById("brChart").innerHTML = "";
  document.getElementById("brSummary").innerHTML = "";
  document.getElementById("brRecent").innerHTML = "";
  document.getElementById("brPeriodChips").innerHTML = "";
}
```

- [ ] **Step 8: Verify**

Open `index.html` in a browser. Tap the **Bankroll** tab in the bottom nav. Expected: the view switches, shows the "Gestion de bankroll" header, the two action buttons, and a single placeholder KPI card reading "—". In devtools console run `state.bankrollTx` and `state.bankrollSessions` — both must be `[]` (not `undefined`). Reload — they persist as `[]`.

- [ ] **Step 9: Commit**

```bash
git add index.html
git commit -m "feat(bankroll): scaffold bankroll tab, state, nav"
```

---

### Task 2: Period chips + KPI computation + KPI grid

**Files:**
- Modify: `index.html` new JS block.

**Interfaces:**
- Consumes: `state.bankrollTx`, `state.bankrollSessions`, `state.tournaments`, `brPeriod`, `renderBankroll()`.
- Produces: `brInPeriod(dateMs, period)` → bool; `brStartOf(period)` → ms; `brCompute(period)` → `{bankroll, profit, roi, hourly, abi, sessions, tournois, sessionsArr, txArr, tournArr}`; `brFmt(n)` → string `"x.xx€"`; `brSetPeriod(p)`; `renderBrChips()`; `renderBrKpis()`.

- [ ] **Step 1: Add period + format + compute helpers**

Inside the BANKROLL block, after the `brPeriod` declaration (before `renderBankroll`), insert:

```js
function brFmt(n){ return (n>=0?"":"-") + Math.abs(n).toFixed(2) + "€"; }
function brToMs(dateStr){ const d = new Date(dateStr + "T00:00:00"); return d.getTime(); }

function brStartOf(period){
  const now = new Date();
  if(period==="week"){ const d=new Date(now); const day=(d.getDay()+6)%7; d.setHours(0,0,0,0); d.setDate(d.getDate()-day); return d.getTime(); }
  if(period==="month"){ return new Date(now.getFullYear(), now.getMonth(), 1).getTime(); }
  if(period==="year"){ return new Date(now.getFullYear(), 0, 1).getTime(); }
  return 0; // "all"
}
function brInPeriod(dateMs, period){ return dateMs >= brStartOf(period); }

function brTournProfit(t){ return (parseFloat(t.result.payout)||0) - (parseFloat(t.buyin)||0); }

function brCompute(period){
  const txArr = state.bankrollTx.filter(x=>brInPeriod(brToMs(x.date), period));
  const sessionsArr = state.bankrollSessions.filter(s=>brInPeriod(brToMs(s.date), period));
  const tournArr = state.tournaments.filter(t=>t.result && brInPeriod(t.result.end||0, period));

  // bankroll is ALWAYS all-time (real current balance)
  const allTx = state.bankrollTx.reduce((s,x)=> s + (x.type==="deposit" ? +x.amount : -(+x.amount)), 0);
  const allSess = state.bankrollSessions.reduce((s,x)=> s + (+x.result||0), 0);
  const allTourn = state.tournaments.filter(t=>t.result).reduce((s,t)=> s + brTournProfit(t), 0);
  const bankroll = allTx + allSess + allTourn;

  const sessProfit = sessionsArr.reduce((s,x)=> s + (+x.result||0), 0);
  const tournProfit = tournArr.reduce((s,t)=> s + brTournProfit(t), 0);
  const profit = sessProfit + tournProfit;

  const buyins = tournArr.reduce((s,t)=> s + (parseFloat(t.buyin)||0), 0);
  const roi = buyins>0 ? (tournProfit/buyins*100) : 0;

  const hours = sessionsArr.reduce((s,x)=> s + (+x.durationH||0), 0);
  const hourly = hours>0 ? (sessProfit/hours) : 0;

  const abi = tournArr.length>0 ? (buyins/tournArr.length) : 0;

  return { bankroll, profit, roi, hourly, abi, sessions: sessionsArr.length, tournois: tournArr.length, sessionsArr, txArr, tournArr };
}
```

- [ ] **Step 2: Add chips + KPI renderers**

After `brCompute`, insert:

```js
function brSetPeriod(p){ brPeriod = p; renderBankroll(); }

function renderBrChips(){
  const opts = [["all","Tout"],["year","Année"],["month","Mois"],["week","Semaine"]];
  document.getElementById("brPeriodChips").innerHTML = opts.map(([k,label])=>
    `<button class="${brPeriod===k?"active":""}" onclick="brSetPeriod('${k}')">${label}</button>`
  ).join("");
}

function brColor(n){ return n>=0 ? "var(--green)" : "var(--red)"; }

function renderBrKpis(){
  const c = brCompute(brPeriod);
  const cards = [
    {v: brFmt(c.bankroll), l:"Bankroll actuelle", color: brColor(c.bankroll)},
    {v: brFmt(c.profit),   l:"Profit (période)",  color: brColor(c.profit)},
    {v: c.roi.toFixed(1)+"%", l:"ROI", color: brColor(c.roi)},
    {v: brFmt(c.hourly)+"/h", l:"Taux horaire", color: brColor(c.hourly)},
    {v: c.abi.toFixed(2)+"€", l:"ABI", color:"var(--txt)"},
    {v: String(c.sessions), l:"Sessions", color:"var(--txt)"},
    {v: String(c.tournois), l:"Tournois", color:"var(--txt)"},
  ];
  document.getElementById("brKpiGrid").innerHTML = cards.map(k=>
    `<div class="stat"><div class="v" style="color:${k.color}">${k.v}</div><div class="l">${k.l}</div></div>`
  ).join("");
}
```

- [ ] **Step 3: Replace the render stub**

Replace the entire `renderBankroll()` stub from Task 1 with:

```js
function renderBankroll(){
  renderBrChips();
  renderBrKpis();
  document.getElementById("brChart").innerHTML = "";    // Task 5
  document.getElementById("brSummary").innerHTML = "";  // Task 5
  document.getElementById("brRecent").innerHTML = "";   // Task 3
}
```

- [ ] **Step 4: Verify**

Reload, open Bankroll tab. Expected: 4 period chips (Tout active by default), 7 KPI cards. With no manual data but if `state.tournaments` has finished tournaments, Profit/ROI/ABI/Tournois reflect them; otherwise all show zeros (`0.00€`, `0.0%`, `0.00€/h`, `0`). Click each chip — active style moves, KPIs recompute (no `NaN`). In console: `brCompute("all")` returns an object with numeric fields, none `NaN`.

- [ ] **Step 5: Commit**

```bash
git add index.html
git commit -m "feat(bankroll): period filter and KPI computation"
```

---

### Task 3: Transaction form + recent entries list + delete

**Files:**
- Modify: `index.html` new JS block.

**Interfaces:**
- Consumes: `openModal`, `closeModal`, `saveState`, `toast`, `renderBankroll`, `state.bankrollTx`, `brFmt`, `brColor`.
- Produces: `brOpenTxForm()`, `brSaveTx()`, `brTodayStr()`, `brId()`, `brDeleteTx(id)`, `renderBrRecent()` (handles tx now, sessions in Task 4).

- [ ] **Step 1: Add id + today helpers**

After `renderBrKpis` (before any form code), insert:

```js
function brId(){ return "br_" + Date.now() + "_" + Math.floor(Math.random()*1e6); }
function brTodayStr(){ const d=new Date(); return d.getFullYear()+"-"+String(d.getMonth()+1).padStart(2,"0")+"-"+String(d.getDate()).padStart(2,"0"); }
```

- [ ] **Step 2: Add the transaction form + save**

Insert:

```js
function brOpenTxForm(){
  openModal(`
    <h3 style="margin:0 0 12px">Nouvelle transaction</h3>
    <label class="fld"><span>Type</span>
      <select id="brTxType">
        <option value="deposit">Dépôt</option>
        <option value="withdraw">Retrait</option>
      </select>
    </label>
    <label class="fld"><span>Montant (€)</span><input id="brTxAmount" type="number" min="0" step="0.01" placeholder="0.00"></label>
    <label class="fld"><span>Date</span><input id="brTxDate" type="date" value="${brTodayStr()}"></label>
    <label class="fld"><span>Room</span><input id="brTxRoom" type="text" placeholder="Optionnel"></label>
    <label class="fld"><span>Note</span><input id="brTxNote" type="text" placeholder="Optionnel"></label>
    <div class="row" style="margin-top:14px">
      <button class="btn compact" onclick="brSaveTx()">Enregistrer</button>
      <button class="btn secondary compact" onclick="closeModal()">Annuler</button>
    </div>
  `);
}

function brSaveTx(){
  const amount = parseFloat(document.getElementById("brTxAmount").value);
  if(!(amount>0)){ toast("Montant invalide"); return; }
  const date = document.getElementById("brTxDate").value || brTodayStr();
  state.bankrollTx.push({
    id: brId(),
    type: document.getElementById("brTxType").value,
    amount: amount,
    date: date,
    room: document.getElementById("brTxRoom").value.trim(),
    note: document.getElementById("brTxNote").value.trim(),
  });
  saveState();
  closeModal();
  renderBankroll();
  toast("Transaction ajoutée ✓");
}

function brDeleteTx(id){
  state.bankrollTx = state.bankrollTx.filter(x=>x.id!==id);
  saveState();
  renderBankroll();
}
```

- [ ] **Step 3: Add the recent entries renderer (tx only for now)**

Insert:

```js
function renderBrRecent(){
  const rows = state.bankrollTx.map(x=>({
    id: x.id, kind: "tx", date: x.date,
    label: (x.type==="deposit"?"Dépôt":"Retrait") + (x.room?" · "+x.room:""),
    note: x.note,
    amount: (x.type==="deposit"? +x.amount : -(+x.amount)),
    del: "brDeleteTx",
  }));
  rows.sort((a,b)=> (b.date||"").localeCompare(a.date||""));
  if(!rows.length){
    document.getElementById("brRecent").innerHTML =
      `<div class="card" style="margin-top:14px"><p style="color:var(--txt-mute);font-size:13px;margin:0">Aucune entrée. Ajoute une session ou une transaction.</p></div>`;
    return;
  }
  document.getElementById("brRecent").innerHTML =
    `<div class="section-title">Entrées récentes</div><div class="card">` +
    rows.map(r=>`
      <div class="br-row">
        <div>
          <div>${r.label}</div>
          <div class="br-meta">${r.date}${r.note?" · "+r.note:""}</div>
        </div>
        <div style="display:flex;align-items:center;gap:8px">
          <span class="br-amt" style="color:${brColor(r.amount)}">${brFmt(r.amount)}</span>
          <button class="br-del" onclick="${r.del}('${r.id}')" title="Supprimer">✕</button>
        </div>
      </div>`).join("") +
    `</div>`;
}
```

- [ ] **Step 4: Wire the recent renderer into renderBankroll**

In `renderBankroll()`, replace the line:

```js
  document.getElementById("brRecent").innerHTML = "";   // Task 3
```

with:

```js
  renderBrRecent();
```

- [ ] **Step 5: Add `.fld` form-field CSS**

In the `<style>` block, before `</style>`, add (only if `.fld` is not already defined — search first; if present, skip this step):

```css
.fld{display:block;margin:0 0 10px}
.fld span{display:block;font-size:12px;color:var(--txt-dim);margin:0 0 4px}
.fld input,.fld select{width:100%;padding:8px 10px;border-radius:8px;border:1px solid var(--line-2);background:var(--bg-2);color:var(--txt);font-size:14px}
```

- [ ] **Step 6: Verify**

Reload, Bankroll tab. Click **+ Nouvelle transaction**. Modal opens with Type/Montant/Date/Room/Note. Submit empty amount → toast "Montant invalide", modal stays. Enter Dépôt 100 → modal closes, Bankroll actuelle increases by 100.00€, a row appears under "Entrées récentes" showing "+100.00€" in green. Add a Retrait 30 → Bankroll drops to 70.00€, row shows "-30.00€" in red. Click ✕ on the deposit → it disappears, Bankroll becomes -30.00€ (or recomputed). Reload — remaining entries persist.

- [ ] **Step 7: Commit**

```bash
git add index.html
git commit -m "feat(bankroll): transaction form, recent list, delete"
```

---

### Task 4: Session form

**Files:**
- Modify: `index.html` new JS block.

**Interfaces:**
- Consumes: `openModal`, `closeModal`, `saveState`, `toast`, `renderBankroll`, `state.bankrollSessions`, `brTodayStr`, `brId`, `brFmt`, `brColor`, `renderBrRecent`.
- Produces: `brOpenSessionForm()`, `brSaveSession()`, `brDeleteSession(id)`.

- [ ] **Step 1: Add the session form + save + delete**

After `brDeleteTx` (or anywhere in the BANKROLL block), insert:

```js
function brOpenSessionForm(){
  openModal(`
    <h3 style="margin:0 0 12px">Nouvelle session</h3>
    <label class="fld"><span>Date</span><input id="brSeDate" type="date" value="${brTodayStr()}"></label>
    <label class="fld"><span>Durée (h)</span><input id="brSeDur" type="number" min="0" step="0.25" placeholder="0"></label>
    <label class="fld"><span>Résultat (€, peut être négatif)</span><input id="brSeResult" type="number" step="0.01" placeholder="0.00"></label>
    <label class="fld"><span>Room</span><input id="brSeRoom" type="text" placeholder="Optionnel"></label>
    <label class="fld"><span>Note</span><input id="brSeNote" type="text" placeholder="Optionnel"></label>
    <div class="row" style="margin-top:14px">
      <button class="btn compact" onclick="brSaveSession()">Enregistrer</button>
      <button class="btn secondary compact" onclick="closeModal()">Annuler</button>
    </div>
  `);
}

function brSaveSession(){
  const dur = parseFloat(document.getElementById("brSeDur").value);
  const resultRaw = document.getElementById("brSeResult").value;
  if(!(dur>=0) || resultRaw===""){ toast("Durée et résultat requis"); return; }
  state.bankrollSessions.push({
    id: brId(),
    date: document.getElementById("brSeDate").value || brTodayStr(),
    durationH: dur,
    result: parseFloat(resultRaw)||0,
    room: document.getElementById("brSeRoom").value.trim(),
    note: document.getElementById("brSeNote").value.trim(),
  });
  saveState();
  closeModal();
  renderBankroll();
  toast("Session ajoutée ✓");
}

function brDeleteSession(id){
  state.bankrollSessions = state.bankrollSessions.filter(x=>x.id!==id);
  saveState();
  renderBankroll();
}
```

- [ ] **Step 2: Extend `renderBrRecent` to include sessions**

In `renderBrRecent()`, after the `const rows = state.bankrollTx.map(...)` block and before `rows.sort(...)`, insert:

```js
  state.bankrollSessions.forEach(s=>{
    rows.push({
      id: s.id, kind: "session", date: s.date,
      label: "Session" + (s.durationH? " · "+s.durationH+"h":"") + (s.room?" · "+s.room:""),
      note: s.note,
      amount: (+s.result||0),
      del: "brDeleteSession",
    });
  });
```

- [ ] **Step 3: Verify**

Reload, Bankroll tab. Click **+ Nouvelle session**. Submit with empty duration/result → toast "Durée et résultat requis". Enter Durée 2, Résultat 50 → row "Session · 2h" shows "+50.00€" green; Sessions KPI = 1; Taux horaire = 25.00€/h; Profit +50; Bankroll +50. Add a losing session Durée 1 Résultat -20 → Sessions 2, Taux horaire = (50-20)/3 = 10.00€/h, row red "-20.00€". Delete a session via ✕ → recomputes. Switch to "Semaine" chip → sessions dated this week count, older excluded. Reload — persists.

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "feat(bankroll): cash session form and entries"
```

---

### Task 5: Bankroll chart + weekly/monthly/yearly summary cards

**Files:**
- Modify: `index.html` new JS block.

**Interfaces:**
- Consumes: `state.bankrollTx`, `state.bankrollSessions`, `state.tournaments`, `brTournProfit`, `brToMs`, `brFmt`, `brStartOf`, `renderBankroll`.
- Produces: `brEvents()` → sorted `[{ms, delta}]`; `renderBrChart()`; `brPeriodProfit(period)` → number; `renderBrSummary()`.

- [ ] **Step 1: Add the event series builder**

Insert in the BANKROLL block:

```js
// All bankroll-affecting events as {ms, delta}, sorted ascending by time.
function brEvents(){
  const ev = [];
  state.bankrollTx.forEach(x=> ev.push({ms: brToMs(x.date), delta: x.type==="deposit"? +x.amount : -(+x.amount)}));
  state.bankrollSessions.forEach(s=> ev.push({ms: brToMs(s.date), delta: +s.result||0}));
  state.tournaments.filter(t=>t.result).forEach(t=> ev.push({ms: t.result.end||0, delta: brTournProfit(t)}));
  ev.sort((a,b)=> a.ms - b.ms);
  return ev;
}
```

- [ ] **Step 2: Add the chart renderer (SVG, modeled on renderStackChart)**

Insert:

```js
function renderBrChart(){
  const ev = brEvents();
  const host = document.getElementById("brChart");
  if(ev.length < 2){
    host.innerHTML = `<div class="card" style="margin-top:14px"><div class="stats-head"><h3>Évolution bankroll</h3></div>
      <p style="font-size:13px;color:var(--txt-mute);margin:4px 0 0">Pas assez de données. Ajoute des entrées pour voir la courbe.</p></div>`;
    return;
  }
  // cumulative points
  let cum = 0;
  const pts = ev.map(e=>{ cum += e.delta; return {x: e.ms, y: cum}; });
  const xs = pts.map(p=>p.x), ys = pts.map(p=>p.y);
  const xMin = Math.min(...xs), xMax = Math.max(...xs);
  const yMin = Math.min(...ys, 0), yMax = Math.max(...ys, 0);
  const xR = Math.max(1, xMax - xMin);
  const yR = Math.max(1, yMax - yMin);
  const W=600, H=180, padL=52, padR=12, padT=14, padB=26;
  const innerW = W - padL - padR, innerH = H - padT - padB;
  const sx = x => padL + ((x - xMin)/xR) * innerW;
  const sy = y => padT + (1 - (y - yMin)/yR) * innerH;
  const path = pts.map((p,i)=> (i===0?"M":"L")+sx(p.x).toFixed(1)+","+sy(p.y).toFixed(1)).join(" ");
  const area = path + ` L ${sx(xs[xs.length-1]).toFixed(1)},${(H-padB).toFixed(1)} L ${sx(xs[0]).toFixed(1)},${(H-padB).toFixed(1)} Z`;
  const yTicks = [yMin, (yMin+yMax)/2, yMax];
  const yTicksHtml = yTicks.map(v=>`
    <line x1="${padL}" y1="${sy(v)}" x2="${W-padR}" y2="${sy(v)}" stroke="rgba(255,255,255,0.06)" stroke-dasharray="3,3"/>
    <text x="${padL-6}" y="${sy(v)+3}" text-anchor="end" fill="var(--txt-mute)" font-size="9">${v.toFixed(0)}€</text>`).join("");
  const fmtDate = ms => { const d=new Date(ms); return String(d.getDate()).padStart(2,"0")+"/"+String(d.getMonth()+1).padStart(2,"0"); };
  const xTicks = [xs[0], xs[Math.floor(xs.length/2)], xs[xs.length-1]];
  const xTicksHtml = xTicks.map(x=>`<text x="${sx(x)}" y="${H-padB+14}" text-anchor="middle" fill="var(--txt-mute)" font-size="9">${fmtDate(x)}</text>`).join("");
  const trend = pts[pts.length-1].y - pts[0].y;
  const trendColor = trend>=0 ? "#3aa757" : "#c0392b";
  host.innerHTML = `<div class="card" style="margin-top:14px"><div class="stats-head"><h3>Évolution bankroll</h3></div>
    <svg viewBox="0 0 ${W} ${H}" style="width:100%;height:auto;display:block">
      ${yTicksHtml}
      <path d="${area}" fill="${trendColor}" opacity="0.12"/>
      <path d="${path}" fill="none" stroke="${trendColor}" stroke-width="2"/>
      ${xTicksHtml}
    </svg></div>`;
}
```

- [ ] **Step 3: Add the summary cards**

Insert:

```js
function brPeriodProfit(period){
  const start = brStartOf(period);
  const sess = state.bankrollSessions.filter(s=>brToMs(s.date)>=start).reduce((a,s)=>a+(+s.result||0),0);
  const tourn = state.tournaments.filter(t=>t.result && (t.result.end||0)>=start).reduce((a,t)=>a+brTournProfit(t),0);
  return sess + tourn;
}

function renderBrSummary(){
  const cards = [
    {p:"week",  l:"Cette semaine"},
    {p:"month", l:"Ce mois"},
    {p:"year",  l:"Cette année"},
  ].map(c=>{ const v = brPeriodProfit(c.p); return `<div class="stat"><div class="v" style="color:${v>=0?"var(--green)":"var(--red)"}">${brFmt(v)}</div><div class="l">${c.l}</div></div>`; });
  document.getElementById("brSummary").innerHTML = cards.join("");
}
```

- [ ] **Step 4: Wire chart + summary into renderBankroll**

In `renderBankroll()`, replace these two lines:

```js
  document.getElementById("brChart").innerHTML = "";    // Task 5
  document.getElementById("brSummary").innerHTML = "";  // Task 5
```

with:

```js
  renderBrChart();
  renderBrSummary();
```

- [ ] **Step 5: Verify**

Reload, Bankroll tab. With <2 total entries: chart card shows "Pas assez de données". Add 2+ entries on different dates → an SVG line chart renders (green if cumulative trend up, red if down), with €-axis labels and date ticks. Summary cards (Cette semaine / Ce mois / Cette année) show period profit, colored by sign. Add an entry dated today → "Cette semaine" updates. Confirm no `NaN` in axis labels and the SVG scales to the card width. Reload — chart and summary rebuild from persisted data.

- [ ] **Step 6: Commit**

```bash
git add index.html
git commit -m "feat(bankroll): bankroll-over-time chart and summary cards"
```

---

## Self-Review Notes

**Spec coverage:**
- Nav tab + view + switchView hook → Task 1. ✓
- `bankrollTx` / `bankrollSessions` state + migration + reset → Task 1. ✓
- KPIs (bankroll all-time, profit, ROI, taux horaire, ABI, sessions, tournois) → Task 2 (`brCompute`). ✓
- Period filter Tout/Année/Mois/Semaine → Task 2. ✓
- Transaction form + save/delete + recent list → Task 3. ✓
- Session form + save/delete → Task 4. ✓
- Chart (SVG, renderStackChart model) → Task 5. ✓
- Week/month/year summary cards → Task 5. ✓
- EUR only, green/red convention, no NaN guards → Global Constraints + every divisor guarded. ✓
- Persistence via existing localStorage/Object.assign + export/import for free → Task 1. ✓
- Out of scope (USD, rooms, rakeback, tickets, sub-tabs, custom range) → not implemented. ✓

**Type consistency:** `brCompute` returns `{bankroll, profit, roi, hourly, abi, sessions, tournois, sessionsArr, txArr, tournArr}` — consumed only by `renderBrKpis`. `brEvents` returns `[{ms, delta}]` — consumed by `renderBrChart`. Delete fns `brDeleteTx`/`brDeleteSession` referenced via `r.del` string in `renderBrRecent` and exist in Tasks 3/4. `brTournProfit`, `brToMs`, `brStartOf`, `brFmt`, `brColor`, `brTodayStr`, `brId` defined once, reused. Container IDs (`brPeriodChips`, `brKpiGrid`, `brChart`, `brSummary`, `brRecent`) match between Task 1 HTML and all renderers.

**Placeholder scan:** No TBD/TODO; all steps carry complete code.
