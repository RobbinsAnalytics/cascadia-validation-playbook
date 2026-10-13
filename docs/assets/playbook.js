/* Interactions for the validation playbook. Ported from the accepted v5
   package's scenario-interactions.js with its semantics intact:
   - the displayed SQL is the executed SQL (DispatchExample.buggy / .fixed); the
     defective query carries two rule mismatches (the boundary operator and no
     dedup clause) and the correction changes exactly those two things (D14);
   - the expected IDs come from the embedded scenario JSON, never the query;
   - the defective line is not highlighted until a run, the correction button
     is disabled until a run, and every run stays in the visible history;
   - each experiment resets independently.
   One behaviour differs from the package: sql.js loads on the first click of
   the run button, never on page load (see runOpening). */
(() => {
  'use strict';
  const {scenario, pairs} = JSON.parse(document.getElementById('scenario-data').textContent);
  const $ = id => document.getElementById(id);
  const checked = id => $(id).checked;
  const on = (id, event, fn) => $(id).addEventListener(event, fn);
  const ids = rows => rows.map(r => r.id);
  const escapeCode = s => s.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
  const chips = values => values.map(id => `<span class="order-chip ${scenario.expectedIds.includes(id) ? '' : 'unexpected'}">${id}${scenario.expectedIds.includes(id) ? '' : ' ×'}</span>`).join('') || '<span>No orders</span>';

  /* ---------- Experiment 0: the code check ---------- */
  // openingStage: 0 = defective query, 1 = boundary corrected, 2 = GROUP BY added. Each
  // correction is one click and one rerun, so the history shows what each fix changed.
  let openingStage = 0, openingRuns = [], sqlEngine = null, sqlLoading = null, engineFailed = false;
  const QUERIES = () => [globalThis.DispatchExample.buggy, globalThis.DispatchExample.partial, globalThis.DispatchExample.fixed];
  const runButton = $('run-opening');
  const engineSrc = runButton.dataset.engine;

  function loadEngine() {
    if (sqlEngine) return Promise.resolve(sqlEngine);
    if (sqlLoading) return sqlLoading;
    sqlLoading = new Promise((resolve, reject) => {
      if (globalThis.initSqlJs) { resolve(); return; }
      const s = document.createElement('script');
      s.src = engineSrc;
      s.onload = () => resolve();
      s.onerror = () => reject(new Error('the local SQL engine did not load'));
      document.head.appendChild(s);
    }).then(() => globalThis.initSqlJs()).then(engine => { sqlEngine = engine; return engine; });
    return sqlLoading;
  }

  function renderOpening(loading) {
    const query = QUERIES()[openingStage];
    // After a run, the boundary line is marked in every state; the GROUP BY line exists only once it
    // has been added. Before that, the missing clause has no line to mark.
    $('opening-code').innerHTML = query.split('\n').map(line => `<span class="code-line ${openingRuns.length && (line.includes('age_hours') || line.startsWith('GROUP BY')) ? 'code-change' : ''}">${escapeCode(line) || ' '}</span>`).join('');
    $('code-state').textContent = ['IMPLEMENTATION / SQL', 'BOUNDARY CORRECTED / SQL', 'CORRECTED IMPLEMENTATION / SQL'][openingStage];
    document.querySelector('.code-pane').classList.toggle('corrected', openingStage > 0);
    $('fix-opening').disabled = !openingRuns.length || openingStage === 2 || !!loading || engineFailed;
    $('fix-opening').textContent = ['Correct the boundary and rerun', 'Add the GROUP BY and rerun', 'Corrections applied'][openingStage];
    runButton.disabled = !!loading || engineFailed;
    runButton.setAttribute('aria-busy', loading ? 'true' : 'false');
    runButton.textContent = loading ? 'Loading the SQL engine…' : openingRuns.length ? 'Run the check again' : 'Run the known-answer check';
    const result = $('opening-result');
    if (!openingRuns.length) {
      result.className = 'opening-result';
      result.innerHTML = loading
        ? '<b>Loading</b><p>The SQLite engine is loading from this page’s own assets. The expected IDs are fixed before this implementation is checked.</p>'
        : '<b>Not run yet</b><p>The expected IDs are fixed before this implementation is checked.</p>';
      $('opening-lesson').textContent = 'The check compares order IDs and multiplicity, not just the total. Reading and testing supply different evidence.';
      return;
    }
    const latest = openingRuns.at(-1);
    const verdict = latest.pass ? '✓ PASS · selected cases match' : latest.stage === 0 ? '× FAIL · same count, wrong orders' : '× FAIL · A105 repeated';
    const explain = latest.pass
      ? '48 ≥ 48 is true, and GROUP BY collapses the repeated row. A102 and A105 appear once each.'
      : latest.stage === 0
        ? '48 &gt; 48 is false, so A102 is excluded, and nothing collapses the repeated A105. Two rows match the expected count and not the expected IDs.'
        : 'A102 now appears, but nothing collapses the repeated A105. Three rows against the expected two.';
    const label = r => r.pass ? 'PASS, boundary and dedup corrected' : r.stage === 0 ? 'FAIL, A102 missing, A105 repeated' : 'FAIL, A105 repeated';
    result.className = 'opening-result ' + (latest.pass ? 'success' : 'warning');
    result.innerHTML = `<span class="mini-label">ACTUAL OUTPUT</span><strong>${latest.actual.join(' · ') || 'No orders'}</strong><b>${verdict}</b><p>${explain}</p><ol class="opening-history" aria-label="Runs in this experiment">${openingRuns.map((r, i) => `<li>Run ${i + 1}: ${label(r)}</li>`).join('')}</ol>`;
    $('opening-lesson').textContent = latest.pass
      ? 'The same expected answer rejects both defects and accepts the corrections. That is evidence for these cases, not a guarantee about all code.'
      : latest.stage === 0
        ? 'Line 7 is easy to inspect here, and the missing GROUP BY has no line to inspect at all. Now imagine 400 lines across six files, written overnight by an agent, and a review on Friday afternoon. The same known-answer check still catches both errors.'
        : 'One correction fixed the boundary and exposed the second defect: the count moved from two to three. A check that compares IDs and multiplicity says what remains.';
  }

  function executeOpening(engine) {
    const stage = openingStage, query = QUERIES()[stage];
    const db = new engine.Database();
    let actual;
    try {
      db.run('CREATE TABLE dispatch_orders (order_id TEXT, age_hours INTEGER, paid INTEGER, shipped INTEGER, canceled INTEGER)');
      for (const row of scenario.rows) db.run('INSERT INTO dispatch_orders VALUES (?, ?, ?, ?, ?)', [row.id, row.age, Number(row.paid), Number(row.shipped), Number(row.canceled)]);
      actual = db.exec(query)[0]?.values.map(row => row[0]) || [];
    } finally { db.close(); }
    const expected = [...scenario.expectedIds].sort();
    const pass = actual.length === expected.length && actual.every((id, i) => id === expected[i]);
    openingRuns.push({actual, pass, stage});
    renderOpening();
  }

  function runOpening() {
    if (sqlEngine) { executeOpening(sqlEngine); return; }
    renderOpening(true);
    loadEngine().then(executeOpening).catch(() => {
      engineFailed = true;
      renderOpening();
      $('opening-result').className = 'opening-result warning';
      $('opening-result').innerHTML = '<b>SQL engine unavailable</b><p>Reload the page with its local SQL asset to run this example.</p>';
    });
  }

  on('run-opening', 'click', runOpening);
  on('fix-opening', 'click', () => { if (openingStage < 2) { openingStage += 1; runOpening(); } });
  on('reset-opening', 'click', () => { openingStage = 0; openingRuns = []; renderOpening(); });

  /* ---------- Experiment 1: the queue ---------- */
  const compute = ({boundary = true, canceled = true, unique = true} = {}) => {
    const seen = new Set();
    return scenario.rows.map(r => {
      let reason = 'Include', included = true;
      if (!r.paid) { reason = 'Unpaid'; included = false; }
      else if (r.shipped) { reason = 'Shipped'; included = false; }
      else if (canceled && r.canceled) { reason = 'Canceled'; included = false; }
      else if (r.age < scenario.minimumAgeHours) { reason = 'Too early'; included = false; }
      else if (!boundary && r.age === scenario.minimumAgeHours) { reason = 'Boundary missed'; included = false; }
      else if (unique && seen.has(r.id)) { reason = 'Repeated copy'; included = false; }
      if (included) seen.add(r.id);
      return {...r, included, reason};
    });
  };
  const controlNames = {'include-boundary': '48-hour boundary', 'exclude-canceled': 'cancellation exclusion', 'unique-orders': 'duplicate collapse'};
  function queue() {
    const evaluated = compute({boundary: checked('include-boundary'), canceled: checked('exclude-canceled'), unique: checked('unique-orders')});
    const values = ids(evaluated.filter(r => r.included));
    const missing = scenario.expectedIds.filter(id => !values.includes(id));
    const unexpected = [...new Set(values.filter(id => !scenario.expectedIds.includes(id)))];
    const duplicates = values.length - new Set(values).size;
    const failures = [...missing.map(id => `${id} is missing`), ...unexpected.map(id => `${id} is canceled but included`), ...(duplicates ? [`${duplicates} repeated entry for A105`] : [])];
    $('queue-result').innerHTML = `<span class="mini-label">BUILD OUTPUT</span><strong>${values.length} ${values.length === 1 ? 'entry' : 'entries'}</strong><span>${values.join(' · ') || 'None'}</span>`;
    $('queue-result').classList.toggle('has-error', failures.length > 0);
    $('order-chart').innerHTML = `<div class="order-chart-head"><span>Input row</span><span>Age in hours · fixed 0–80 scale</span><span>Queue decision</span></div>${evaluated.map((r, i) => {
      const issue = (r.included && r.canceled) || r.reason === 'Boundary missed' || (r.included && i === 5);
      return `<div class="order-row ${r.included ? 'included' : ''} ${issue ? 'issue' : ''}"><div><b>${r.id}</b><small>${r.canceled ? 'Canceled' : r.shipped ? 'Shipped' : i === 5 ? 'Repeated copy of A105' : 'Paid, unshipped'}</small></div><div class="age-cell"><div class="age-track" aria-hidden="true"><span style="width:${r.age / 80 * 100}%"></span><i></i></div><b>${r.age} h</b></div><span class="row-decision">${r.included ? '✓ Include' : '− ' + r.reason}${issue && r.included ? ' (wrong)' : ''}</span></div>`;
    }).join('')}`;
    $('queue-finding').className = 'finding ' + (failures.length ? 'warning' : 'success');
    $('queue-finding').innerHTML = `<b>${failures.length ? 'Mismatch with the specified answer' : 'The selected cases match the specified answer'}</b><p>${failures.length ? failures.join('; ') + '.' : 'A102 meets the inclusive boundary. A105 appears once. The canceled and shipped orders stay out.'}</p>`;
    const removed = Object.keys(controlNames).filter(id => !checked(id)).map(id => controlNames[id]);
    $('queue-state').textContent = removed.length ? 'controls removed: ' + removed.join(', ') : 'all three controls on';
  }
  ['include-boundary', 'exclude-canceled', 'unique-orders'].forEach(id => on(id, 'change', queue));
  on('remove-controls', 'click', () => { ['include-boundary', 'exclude-canceled', 'unique-orders'].forEach(id => $(id).checked = false); queue(); });
  on('same-count', 'click', () => { $('include-boundary').checked = false; $('exclude-canceled').checked = true; $('unique-orders').checked = false; queue(); });
  on('reset-queue', 'click', () => { ['include-boundary', 'exclude-canceled', 'unique-orders'].forEach(id => $(id).checked = true); queue(); });

  /* ---------- Experiment 2: the agent boundary ---------- */
  function checker() {
    const defect = checked('checker-defect'), separate = checked('separate-checker');
    const build = ids(compute({canceled: !defect}).filter(r => r.included));
    // Teaching stand-in for another implementation: raw cases only, no compute() or build output.
    const answer = separate ? [...new Set(scenario.rows.filter(row => row.paid && !row.shipped && !row.canceled && row.age >= 48).map(row => row.id))].sort() : [...build];
    $('build-method').textContent = defect ? 'Receives rules and raw cases. Omits the cancellation rule in its implementation.' : 'Receives rules and raw cases. Applies the cancellation rule.';
    $('checking-agent').textContent = separate ? 'Second agent implements the check' : 'Original agent checks itself';
    document.querySelector('.branch-source').innerHTML = separate ? 'SEPARATE STARTING POINTS <span>Rules + raw cases → each agent</span>' : 'SHARED IMPLEMENTATION <span>Original agent → its existing filtered list</span>';
    $('check-method').textContent = separate ? 'Receives only rules and raw cases. No first implementation or output. Rebuilds the filter for this illustration.' : 'Receives its existing implementation and output. Reuses the faulty filter in this illustration.';
    $('build-orders').innerHTML = chips(build); $('check-orders').innerHTML = chips(answer);
    const match = build.length === answer.length && build.every(id => answer.includes(id));
    const title = !match ? 'Mismatch exposes the canceled order' : defect ? 'Agreement hides the shared mistake' : separate ? 'The specified cases agree' : 'Agreement, but no separate filter evidence';
    const message = !match ? 'Build: 3 orders. Checker: 2. A103 is the difference.' : defect ? 'Both paths report 3. Both include A103. Matching answers have not checked the canceled-order exclusion.' : separate ? 'Both paths report A102 and A105. That supports these cases, within the checker’s stated scope.' : 'Both paths report 2 because they use the same filtered list. The cancellation filter has not been checked separately.';
    $('checker-result').className = 'finding ' + (!match || defect || !separate ? 'warning' : 'success');
    $('checker-result').innerHTML = `<b>${title}</b><p>${message}</p>`;
    document.querySelector('.check-branch').classList.toggle('shared', !separate);
  }
  ['checker-defect', 'separate-checker'].forEach(id => on(id, 'change', checker));
  on('reset-checker', 'click', () => { $('checker-defect').checked = true; $('separate-checker').checked = false; checker(); });

  /* ---------- Experiment 3: the release gate ---------- */
  function release() {
    const defect = checked('release-defect'), gate = checked('enforce-gate'), age = Number($('source-age').value), stale = age > scenario.maximumSourceAgeHours;
    const blocked = gate && (defect || stale);
    $('age-value').textContent = age + ' ' + (age === 1 ? 'hour' : 'hours');
    $('source-age').setAttribute('aria-valuetext', `${age} ${age === 1 ? 'hour' : 'hours'} old; ${stale ? 'fails' : 'meets'} the two-hour freshness requirement`);
    $('rule-check').className = 'check-tile ' + (defect ? 'bad' : 'good');
    $('rule-check').innerHTML = `<span>KNOWN ANSWER</span><b>${defect ? '× FAIL · 3 ≠ 2' : '✓ PASS · 2 = 2'}</b><small>${defect ? 'Canceled A103 is included.' : 'A102 and A105, once each.'}</small>`;
    $('fresh-check').className = 'check-tile ' + (stale ? 'bad' : 'good');
    $('fresh-check').innerHTML = `<span>SOURCE FRESHNESS</span><b>${stale ? '× FAIL' : '✓ PASS'} · ${age} ${stale ? '&gt;' : '≤'} 2 h</b><small>${stale ? 'Older than the permitted limit.' : 'Within the permitted limit.'}</small>`;
    $('gate-state').className = 'gate-state ' + (gate ? '' : 'bypassed');
    $('gate-state').innerHTML = `<span class="gate-icon" aria-hidden="true">${gate ? '▥' : '⇢'}</span><b>${gate ? 'Gate enforced' : 'Gate bypassed'}</b><span>${blocked ? 'STOP →' : gate ? 'PASS →' : 'CONTINUE →'}</span>`;
    $('dashboard-state').className = 'dashboard-state ' + (blocked ? 'blocked' : defect || stale ? 'unsafe' : 'ready');
    $('dashboard-state').innerHTML = `<span class="mini-label">CURRENT RELEASE</span><strong>${blocked ? 'Withheld' : 'Published'}</strong><span>${blocked ? 'No current queue is released.' : `${defect ? '3' : '2'} orders shown to staff.`}</span><small>${blocked ? 'Investigate, fix and rerun.' : stale ? `${age}-hour-old input appears as current.` : defect ? 'The canceled order reaches the list.' : 'Ready for the accepted staff-review use.'}</small>`;
    const issues = [...(defect ? ['the queue is wrong'] : []), ...(stale ? ['the source is stale'] : [])];
    $('release-result').className = 'finding ' + (blocked ? 'neutral' : issues.length ? 'warning' : gate ? 'success' : 'warning');
    $('release-result').innerHTML = `<b>${blocked ? 'The failure is contained' : issues.length ? 'The check detects a problem, but release continues' : gate ? 'Both conditions pass; release proceeds' : 'A clean run does not prove the gate is enforced'}</b><p>${blocked ? `Release stops because ${issues.join(' and ')}. Detection and enforcement are both active.` : issues.length ? `The run publishes even though ${issues.join(' and ')}. A red report alone does not stop anything.` : gate ? 'The gate permits this run. Owner acceptance still applies to its intended use.' : 'The current output happens to meet the requirements. Inject a defect or age the source to expose the missing protection.'}</p>`;
  }
  ['release-defect', 'enforce-gate'].forEach(id => on(id, 'change', release)); on('source-age', 'input', release);
  on('reset-release', 'click', () => { $('release-defect').checked = true; $('enforce-gate').checked = true; $('source-age').value = 1; release(); });

  /* ---------- The V ---------- */
  let selectedPair = 'rule';
  function selectPair(key) {
    selectedPair = key; const p = pairs.find(p => p.key === key);
    document.querySelectorAll('[data-pair]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.pair === key)));
    $('v-detail').innerHTML = `<div><span class="mini-label">${p.level.toUpperCase()} / ${p.owner.toUpperCase()}</span><b>${p.promise}</b><span class="detail-arrow" aria-hidden="true">→</span><b>${p.check}</b></div><p><strong>Evidence:</strong> ${p.proof}</p><p><strong>Without this pairing:</strong> ${p.risk}</p>`;
    $('v-state').textContent = 'selected pair: ' + p.level.toLowerCase();
    drawV();
  }
  function drawV() {
    const canvas = document.querySelector('.v-canvas'), svg = document.querySelector('.v-lines'), base = canvas.getBoundingClientRect();
    if (!base.width) return;
    const box = el => { const r = el.getBoundingClientRect(); return {x: r.left - base.left, y: r.top - base.top, w: r.width, h: r.height, cx: r.left - base.left + r.width / 2, cy: r.top - base.top + r.height / 2}; };
    const left = pairs.map(p => box(canvas.querySelector(`[data-pair="${p.key}"][data-side="left"]`)));
    const right = pairs.map(p => box(canvas.querySelector(`[data-pair="${p.key}"][data-side="right"]`)));
    const build = box(canvas.querySelector('.v-build'));
    const sequence = [...left, build, ...[...right].reverse()];
    let s = '<defs><marker id="v-arrow" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0,0 L7,3.5 L0,7" fill="none" stroke="#5B6660"/></marker></defs>';
    for (let i = 0; i < sequence.length - 1; i++) {
      const a = sequence[i], b = sequence[i + 1], down = b.cy > a.cy;
      s += `<line x1="${a.cx}" y1="${down ? a.y + a.h + 3 : a.y - 3}" x2="${b.cx}" y2="${down ? b.y - 7 : b.y + b.h + 7}" stroke="#5B6660" stroke-width="1.5" marker-end="url(#v-arrow)"/>`;
    }
    pairs.forEach((p, i) => { const a = left[i], b = right[i]; s += `<line x1="${a.x + a.w + 3}" y1="${a.cy}" x2="${b.x - 3}" y2="${b.cy}" stroke="${p.key === selectedPair ? '#1E7A4C' : '#9AA6A0'}" stroke-width="${p.key === selectedPair ? 2 : 1}" stroke-dasharray="4 5"/>`; });
    svg.setAttribute('viewBox', `0 0 ${base.width} ${base.height}`); svg.innerHTML = s;
  }
  document.querySelectorAll('[data-pair]').forEach(b => b.addEventListener('click', () => selectPair(b.dataset.pair)));
  new ResizeObserver(drawV).observe(document.querySelector('.v-canvas'));
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(drawV);

  queue(); checker(); release(); renderOpening(); selectPair('rule');
})();
