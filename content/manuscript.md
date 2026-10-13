# Validating AI-Assisted Analytics

**From requirements to evidence, with clear ownership at every step.**

“How can you be confident in code you did not read or write in full?”

Confidence needs a trail of evidence: a clear requirement, an answer specified separately from the implementation, and a check that can expose a mistake. Reading code is part of that work. This small example shows what the check adds.

<!-- visual:opening -->

## 1. Pair every promise with proof

The missing order is one broken link in the V: “at least 48 hours” did not survive implementation. Read down the left to define the work, then up the right to check it. Each expected result traces to a requirement, not to the code being tested.

<!-- visual:vmodel -->

## 2. Where this comes from and why it fits AI

<div class="author-account" data-voice="author">

I learned this at Philips, on Class III medical devices. The quality owner who signed off the software had not written it. They read the requirements and the checks tied to them, then took responsibility for acceptance. That is the V: accountability supported by evidence linked to requirements.

AI changed who sits in the V. At Philips, separation came from different people: an analyst wrote the requirements, a developer built, and a tester checked. I built my analytics portfolio using AI tools. When one person and a set of agents do all of it, I have to construct that separation deliberately. The operating model starts with expected answers before implementation, a second path that receives rules and raw cases without the first implementation, and an accountable owner who accepts the intended use.

AI also makes another implementation easier to produce. I can give a second agent the rules document and raw cases without the first implementation or output. The work that remains is mine: choosing cases that could fail, naming shared assumptions, reviewing the second path and reading any disagreement.

Humans still read code. The review split is explicit: I read SQL, configuration and tests, where the business rule is expressed and checked. An engineer reviews the Python internals, scaled to what a wrong number would cost. The accountable owner reads the requirement in their own words and the evidence against it, then decides whether to accept the result for that use.

</div>

<p class="chart-limit author-caption"><strong>Proposed operating model:</strong> the review split and separate owner acceptance describe how the work should be organized, not completed portfolio sign-offs.</p>

<!-- visual:ceremony -->

Verification asks whether the implementation meets its requirements. Validation asks whether the result is suitable for its intended use. A passing queue test does not authorize automatic refunds.

## 3. Remove a control and watch the queue change

Harbor Dispatch has six input rows representing five orders. Its specified answer is **A102 and A105, once each**. Change the controls and compare identities as well as totals.

<!-- visual:queue -->

The same-count preset returns two copies of A105 while losing A102. Two entries still make the wrong answer. Cases chosen before implementation give the checker something concrete to disagree with.

<details>
<summary>Real evidence: a fixture exposes a missing condition</summary>

Early Warning, a Cascadia analytics build, uses a synthetic fixture to check episode construction. Its October row exceeds the forecast range but fails a separate five-report condition. Omitting that condition changes the answer. The fixture establishes behavior for those cases, not detection usefulness. [Fixture][fixture-input] · [Expected result][fixture-expected] · [Harness][fixture-test]

</details>

## 4. Give a second agent a separate route to the answer

In this illustration, the first agent omits the cancellation rule. Checking through the same filter repeats that mistake. A second agent receives only the rules and raw cases, without the first agent's implementation or output.

<!-- visual:checker -->

**The boundary stays:** both agents share the rule and source data, and may make similar reasoning errors. Agreement supports the behavior tested; it does not establish that the rule is right, the source is true or every case is covered. The illustrated agent outcomes are fixed teaching cases, not live model calls or measured success rates.

<details>
<summary>Real evidence: a second path names its exclusions</summary>

Early Warning documents which transformations its second path recomputes. It shares exported states and points, and does not repeat candidate fitting or promotion. Its agreement has that stated boundary. [Scope and exclusions][second-path]

</details>

## 5. Make a failed check change what gets released

Detecting a problem and stopping release are separate controls. For Harbor Dispatch, the queue must match the known answer and its source must be no more than two hours old.

<!-- visual:release -->

Record the failure, stop, correct and rerun. If an owner accepts an exception, retain the failed criterion and the restriction. Approval does not rewrite a failed check as a pass.

<details>
<summary>Real evidence: detection and enforcement can diverge</summary>

Early Warning's D16 records five of seven codes outside the preset coverage band. The build continued with three codes' review rules disabled as prescribed; the separate instruction to stop the build was not enforced. The owner subsequently accepted the outcome. D17 records a corrected rerun after the first run's output had been seen. Matter Ledger, another Cascadia build, had a nineteen-day stall discovered by a reader. These motivate enforced gates, retained run history and freshness monitoring; they do not establish that every control was deployed. [Numbers gate][numbers-gate] · [Decision record][decisions] · [Stall incident][incident]

</details>

## 6. Keep five commitments with the build

<!-- visual:record -->

**Confidence comes from evidence that can contradict the implementation, people who review the remaining risks, and a release decision that respects both.**

Across ten modules, the checks developed build by build. The [Build by Build matrix][build-matrix] links each recorded check to its evidence.
