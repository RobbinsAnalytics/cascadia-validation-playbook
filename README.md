# Cascadia Validation Playbook

One Felix page, "Validating AI-Assisted Analytics", and this README, which carries the page's full text for readers whose network blocks the site.
The page is served at https://www.robbinsanalytics.com/cascadia-validation-playbook/ and runs a real SQLite query in your browser; the tables below stand in for its four experiments.

---

# Validating AI-Assisted Analytics

**From requirements to evidence, with clear ownership at every step.**

“How can you be confident in code you did not read or write in full?”

Confidence needs a trail of evidence: a clear requirement, an answer specified separately from the implementation, and a check that can expose a mistake. Reading code is part of that work. This small example shows what the check adds.


Fictional Harbor Dispatch rule: paid, unshipped orders at least 48 hours old; exclude canceled orders and repeated IDs. Expected IDs, specified separately: A102 and A105.

```sql
WITH eligible_orders AS (
    SELECT
        order_id
    FROM dispatch_orders
    WHERE paid = 1
      AND shipped = 0
      AND age_hours > 48
      AND canceled = 0
)
SELECT order_id
FROM eligible_orders
ORDER BY order_id;
```

Executing this SQL query on the six cases returns A105 twice. The count matches the expected two and the IDs do not: 48 > 48 is false, so A102 is excluded, and nothing collapses the repeated A105 row. Correcting > to >= alone returns A102, A105 and A105: three rows, A105 still repeated. Adding GROUP BY order_id then returns A102 and A105 once each. Line 7 is easy to inspect here, and the missing GROUP BY has no line to inspect at all. Now imagine 400 lines across six files, written overnight by an agent, and a review on Friday afternoon. The same known-answer check still catches both errors.

Corrected query, after both corrections:

```sql
WITH eligible_orders AS (
    SELECT
        order_id
    FROM dispatch_orders
    WHERE paid = 1
      AND shipped = 0
      AND age_hours >= 48
      AND canceled = 0
)
SELECT order_id
FROM eligible_orders
GROUP BY order_id
ORDER BY order_id;
```

| Order | Age | State | Purpose |
| --- | --- | --- | --- |
| A101 | 47 hours | Paid, unshipped | One hour too early |
| A102 | 48 hours | Paid, unshipped | Exactly at the boundary |
| A103 | 72 hours | Canceled | Canceled, despite its age |
| A104 | 60 hours | Shipped | Already shipped |
| A105 | 60 hours | Paid, unshipped | Eligible order |
| A105 | 60 hours | Paid, unshipped | Repeated copy of the same order |


## 1. Pair every promise with proof

The missing order is one broken link in the V: “at least 48 hours” did not survive implementation. Read down the left to define the work, then up the right to check it. Each expected result traces to a requirement, not to the code being tested.


| Define before building | Promise | Check afterward | Evidence | Proposed owner |
| --- | --- | --- | --- | --- |
| Intended use | Help staff review delayed orders | Owner tries the queue | Can staff identify the right orders and decide what to investigate? | Operations owner |
| Decision rule | Paid, unshipped, 48+ hours; not canceled | Compare with known answers | A102 and A105 appear once each. Boundary, exclusion and duplicate cases have fixed expectations. | Analytics lead |
| Data contract | One order per ID; source age ≤ 2 hours | Check inputs and failure handling | Repeated IDs collapse to one order. Old source data blocks the current release. | Technical reviewer |

Work sequence: intended use → decision rule → data contract → implementation → input checks → known-answer checks → owner tryout. Each check traces to its corresponding promise.


## 2. Where this comes from and why it fits AI

<div class="author-account" data-voice="author">

I learned this at Philips, on Class III medical devices. The quality owner who signed off the software had not written it. They read the requirements and the checks tied to them, then took responsibility for acceptance. That is the V: accountability supported by evidence linked to requirements.

AI changed who sits in the V. At Philips, separation came from different people: an analyst wrote the requirements, a developer built, and a tester checked. I built my analytics portfolio using AI tools. When one person and a set of agents do all of it, I have to construct that separation deliberately. The operating model starts with expected answers before implementation, a second path that receives rules and raw cases without the first implementation, and an accountable owner who accepts the intended use.

AI also makes another implementation easier to produce. I can give a second agent the rules document and raw cases without the first implementation or output. The work that remains is mine: choosing cases that could fail, naming shared assumptions, reviewing the second path and reading any disagreement.

Humans still read code. The review split is explicit: I read SQL, configuration and tests, where the business rule is expressed and checked. An engineer reviews the Python internals, scaled to what a wrong number would cost. The accountable owner reads the requirement in their own words and the evidence against it, then decides whether to accept the result for that use.

</div>

<p class="chart-limit author-caption"><strong>Proposed operating model:</strong> the review split and separate owner acceptance describe how the work should be organized, not completed portfolio sign-offs.</p>


| Level | Regulated software (the V with full ceremony) | AI-assisted analytics (the same V) |
| --- | --- | --- |
| Intended use | Approved use statement | Owner question, scope and acceptance |
| Rule | Controlled requirements | Versioned rule and expected cases |
| Specification | Design record and traceability matrix | Data contract and requirement-to-test links |
| Code | Reviewed release baseline | Versioned implementation and assigned review |
| Second path | Separately developed check, where used | Second agent receives rules and raw cases |
| Sign-off | Recorded approval of a release | Explicit acceptance linked to the reviewed commit |

The structure survived. The records moved into the repository. A commit identifies the version; the acceptance record names the decision and the owner.


Verification asks whether the implementation meets its requirements. Validation asks whether the result is suitable for its intended use. A passing queue test does not authorize automatic refunds.

## 3. Remove a control and watch the queue change

Harbor Dispatch has six input rows representing five orders. Its specified answer is **A102 and A105, once each**. Change the controls and compare identities as well as totals.


| Order | Age | State | Case |
| --- | --- | --- | --- |
| A101 | 47 hours | Paid, unshipped | One hour too early |
| A102 | 48 hours | Paid, unshipped | Exactly at the boundary |
| A103 | 72 hours | Canceled | Canceled, despite its age |
| A104 | 60 hours | Shipped | Already shipped |
| A105 | 60 hours | Paid, unshipped | Eligible order |
| A105 | 60 hours | Paid, unshipped | Repeated copy of the same order |

| Controls removed | Actual entries | Mismatch with A102 and A105 |
| --- | --- | --- |
| None | A102, A105 | None |
| 48-hour boundary | A105 | A102 missing |
| Cancellation exclusion | A102, A103, A105 | A103 ineligible |
| Duplicate collapse | A102, A105, A105 | A105 repeated |
| Boundary and duplicate collapse (same-count preset) | A105, A105 | Two entries, but A102 is missing and A105 is repeated |
| All three | A103, A105, A105 | A102 missing; A103 ineligible; A105 repeated |


The same-count preset returns two copies of A105 while losing A102. Two entries still make the wrong answer. Cases chosen before implementation give the checker something concrete to disagree with.

<details>
<summary>Real evidence: a fixture exposes a missing condition</summary>

Early Warning, a Cascadia analytics build, uses a synthetic fixture to check episode construction. Its October row exceeds the forecast range but fails a separate five-report condition. Omitting that condition changes the answer. The fixture establishes behavior for those cases, not detection usefulness. [Fixture](https://github.com/RobbinsAnalytics/cascadia-early-warning/blob/e7d1337ff1d5ab1d1f88f0fa018cae884f737676/tests/golden/golden_review_input.csv) · [Expected result](https://github.com/RobbinsAnalytics/cascadia-early-warning/blob/e7d1337ff1d5ab1d1f88f0fa018cae884f737676/tests/golden/golden_expected_review.csv) · [Harness](https://github.com/RobbinsAnalytics/cascadia-early-warning/blob/e7d1337ff1d5ab1d1f88f0fa018cae884f737676/src/test_golden.py)

</details>

## 4. Give a second agent a separate route to the answer

In this illustration, the first agent omits the cancellation rule. Checking through the same filter repeats that mistake. A second agent receives only the rules and raw cases, without the first agent's implementation or output.


| Canceled-order defect | Checker input | Result |
| --- | --- | --- |
| On | Second agent: rules and raw cases only | Build: 3; checker: 2. Mismatch exposes A103. |
| On | Original agent: existing filtered list | Both: 3. Agreement hides the same error. |
| Off | Second agent: rules and raw cases only | Both: 2. The specified case passes. |
| Off | Original agent: existing filtered list | Both: 2. Agreement gives no separate filter evidence. |


**The boundary stays:** both agents share the rule and source data, and may make similar reasoning errors. Agreement supports the behavior tested; it does not establish that the rule is right, the source is true or every case is covered. The illustrated agent outcomes are fixed teaching cases, not live model calls or measured success rates.

<details>
<summary>Real evidence: a second path names its exclusions</summary>

Early Warning documents which transformations its second path recomputes. It shares exported states and points, and does not repeat candidate fitting or promotion. Its agreement has that stated boundary. [Scope and exclusions](https://github.com/RobbinsAnalytics/cascadia-early-warning/blob/e7d1337ff1d5ab1d1f88f0fa018cae884f737676/src/validate_measures.py)

</details>

## 5. Make a failed check change what gets released

Detecting a problem and stopping release are separate controls. For Harbor Dispatch, the queue must match the known answer and its source must be no more than two hours old.


| Rule result | Source age | Gate | Current release |
| --- | --- | --- | --- |
| Fail, includes A103 | 1 hour | Enforced | Blocked |
| Fail, includes A103 | 1 hour | Not enforced | Wrong queue published despite failure |
| Pass | 8 hours | Enforced | Blocked for stale source |
| Pass | 8 hours | Not enforced | Old input published as current |
| Pass | 1 or 2 hours | Enforced | Published for staff review |

Rule and freshness checks are separate. Stopping either failure requires enforcement. A disabled gate can appear harmless on a clean run while providing no failure protection.


Record the failure, stop, correct and rerun. If an owner accepts an exception, retain the failed criterion and the restriction. Approval does not rewrite a failed check as a pass.

<details>
<summary>Real evidence: detection and enforcement can diverge</summary>

Early Warning's D16 records five of seven codes outside the preset coverage band. The build continued with three codes' review rules disabled as prescribed; the separate instruction to stop the build was not enforced. The owner subsequently accepted the outcome. D17 records a corrected rerun after the first run's output had been seen. Matter Ledger, another Cascadia build, had a nineteen-day stall discovered by a reader. These motivate enforced gates, retained run history and freshness monitoring; they do not establish that every control was deployed. [Numbers gate](https://github.com/RobbinsAnalytics/cascadia-early-warning/blob/e7d1337ff1d5ab1d1f88f0fa018cae884f737676/governance/numbers-gate.md) · [Decision record](https://github.com/RobbinsAnalytics/cascadia-early-warning/blob/e7d1337ff1d5ab1d1f88f0fa018cae884f737676/governance/decision-record.md) · [Stall incident](https://github.com/RobbinsAnalytics/cascadia-matter-ledger/commit/6a2f90a10631d528707474da0efb0bbd6ba452f7)

</details>

## 6. Keep five commitments with the build


**Proposed commitments**

| Commitment | Record |
| --- | --- |
| An owner-answerable question | Name the use and owner; record acceptance and restrictions against a version. |
| Expected results before implementation | Commit the cases and expected answers before the build being tested. |
| A separate calculation path | Re-derive the published figures; name shared inputs and the scope actually checked. |
| A check that must fail | Inject a known defect and confirm the named check rejects it. |
| Every run and its disposition | Keep status, stop reason and resolution, including original and corrected runs. |


**Confidence comes from evidence that can contradict the implementation, people who review the remaining risks, and a release decision that respects both.**

Across ten modules, the checks developed build by build. The [Build by Build matrix](https://www.robbinsanalytics.com/cascadia-build-by-build/) links each recorded check to its evidence.

---

## What is where

| Path | What |
|---|---|
| `content/manuscript.md` | The accepted v5 manuscript. Every sentence on the page comes from here, verbatim. |
| `docs/index.html` | The page, generated by `src/build_page.py` from the manuscript and `docs/template.html`. Published to the URL above from `main`. |
| `docs/assets/dispatch-scenario.json` | The six invented input rows and the expected IDs, specified separately from any implementation. |
| `docs/assets/dispatch-code.js` | The two SQL query strings. The defective one has `>` where the rule says at least, and no clause collapsing repeated IDs; the corrections are applied one click at a time, the operator first, then `GROUP BY order_id`, and nothing else changes. |
| `docs/assets/playbook.js`, `playbook.css` | The experiments and the page's own styles. The SQLite engine loads on the first click of the run button. |
| `docs/vendor/sql.js/` | sql.js 1.14.2 (SQLite compiled to asm.js), its MIT license and `provenance.json` with the archive integrity and file hashes. |
| `docs/assets/felix.src.css`, `felix.css` | The Felix design system's tokens and components, compiled by the Tailwind v4 CLI. Felix itself is referenced, not copied; see the decision record. |
| `docs/renders/` | Full-page renders at 390 and 1440 px, the exhibit renders the reading panel read, and `checks.json`, the last run of the behaviour gate. |
| `checks/check_page.py` | The behaviour gate: every experiment, five widths, from a local server and from disk. `checks/scan_text.py` is the em-dash, names and duration scan. |
| `evidence/source-links.md` | The thirteen pinned evidence links and the Build by Build link, pinned to commits. |
| `adopt/five-commitments.md` | The five commitments as a standalone file. `adopt/acceptance-record.md` is the long-form record template, deliberately not linked from the page. |
| `governance/decision-record.md` | Why a page and not a build, why one page, why Felix in a repository, the sql.js choice, the reduced panel. `governance/chart-review.md` is the Rule 7.4 panel record. |

Rebuild with `C:\Users\Ajayr\AppData\Local\Python\pythoncore-3.14-64\python.exe src\build_page.py`, then run `checks\check_page.py` with the same interpreter.
