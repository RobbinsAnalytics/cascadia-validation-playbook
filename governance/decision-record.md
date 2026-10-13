# Decision record - Cascadia Validation Playbook

*Owner: Aaron Robbins. Opened 2026-10-12 by the Phase 1 build session, from
Build Brief 1 of the same date. Each decision names what carries it. Later
entries append and never rewrite.*

---

## D1 · A page, not a build

The playbook is prose and four teaching experiments over six invented rows.
It has no data source, no freeze, no engine, no live edge and no numbers that
could be wrong in the way a module's can. It is therefore a **page**: one
`docs/index.html`, generated from a manuscript, with a behaviour gate instead
of a validation suite. Nothing under PRINCIPLES rule 1 (commit the raw
response) applies, because there is no response to commit; the six rows are
authored and sit in `docs/assets/dispatch-scenario.json` as the specification
they are.

*Counterfactual:* a module repository with `data/`, `governance/freeze.toml`
and `src/validate.py`, which would have dressed an invented example as a
dataset and asked a reader to trust a freeze of something that was never
retrieved.

**Carried by:** the repository layout; `CLAUDE.md`; `README.md`.

## D2 · One page, not a module plus a case study

Aaron's instruction (2026-10-12): like the Operating Charter, one page. The
manuscript is already one argument in six numbered sections with the method
and its evidence interleaved; splitting it into "the thing" and "the case
study of the thing" would duplicate the author account and the evidence notes
on both pages or orphan them on one. The README carries the whole page as
text so a reader whose network blocks the site loses nothing.

*Counterfactual:* `docs/index.html` plus `docs/case-study.html` on the Early
Warning pattern, with a second navigation entry and a second OG card.

**Carried by:** `docs/template.html` (one page); `src/build_page.py` writes
one HTML file and one README.

## D3 · A Felix page in its own repository, not a Quarto page in the site

The Charter lives in the Quarto site under the site's older theme. Aaron wants
this page in Felix. In this estate a Felix page is static HTML built in a
repository of its own and served from `docs/` under
`https://www.robbinsanalytics.com/<repo>/` by GitHub Pages; Early Warning
established the pattern on 2026-10-06 and its two pages are live that way.
The Quarto site gets a redirect stub, a home card, a Cascadia row and an OG
card in Phase 2, exactly as it did for Early Warning, so the page is reachable
from every place the Charter is.

How the custom-domain path works, read from `cascadia-early-warning` on disk:
nothing in that repository configures it. There is no `CNAME` under `docs/`
and no Pages workflow; Pages is set to serve `main` at `/docs` on GitHub, and
the account's user site (`RobbinsAnalytics.github.io`) carries the custom
domain, so every project page under the account is served beneath it. The
in-repo part is therefore `docs/` itself and nothing else. (Brief B2
confirmed, with the mechanism named.)

*Counterfactual:* a `.qmd` in the site, which would have put the Felix chrome
inside a Quarto layout and fought the site's theme on every element.

**Carried by:** `docs/`; Phase 2 steps 12 and 13 of the brief.

## D4 · Felix by pointer, not copy; the toolchain copied from Early Warning

Page chrome follows
`C:\Projects\cascadia-standards\design-system\felix-design-system.md`
**v1.0 at commit `1a41a5e`** (2026-10-06), which was also the current commit of
that file on the day of this build; the OneDrive copy in the package is the
same version. The one vendored piece of tooling, `docs/assets/felix.src.css`,
is copied from `cascadia-early-warning` at `e7d1337` (that repository's HEAD
on 2026-10-12; the file's own last change there is `3434e0f`) and is
unchanged, including its first-line attribution. It compiles with the Tailwind
v4.3.3 CLI pinned in `package.json`, copied from the same repository with only
the package name changed. The Felix page structure (site header, figure-frame
header, lime aside, hook panel, TOC and body grid, CTA banner, footer, the
scrolled-header and mobile-menu script) follows Early Warning's
`docs/template.html` at the same commit, re-authored for this page's content;
`favicon.svg` is copied unchanged. ECharts, the Cascadia theme, `page.js` and
the build script's data machinery were not carried: this page has no chart
canvas and the toolchain separates cleanly from them.

Early Warning's two directive decisions are inherited as written: text below
0.875rem uses `ink-soft` where Felix shows `muted`, and the four Felix font
families load from Google Fonts at runtime (its D14, 6a and 6b). **The font
collision is inherited, not resolved**: every other asset on this page is
local and the fonts are not. This page adds a fifth family to the same
request, Source Serif 4, because VIZ-PRINCIPLES names it for the serif voice
inside a chart and Early Warning's charts had fallen back to Georgia.

*Counterfactual:* copying the design system document into the repository, or
re-deriving the class strings from it, either of which drifts the moment the
document moves.

**Carried by:** `docs/assets/felix.src.css`; `package.json`;
`docs/template.html`; `docs/assets/playbook.css`.

## D5 · Inside the two exhibits, VIZ-PRINCIPLES v2.9 governs

The V diagram and the Experiment 1 queue bars are charts. Inside their frames
(`.cz-exhibit`) Felix stops: the Cascadia palette verbatim (Paper, Mist, Rain,
Basalt, Slate moss, Evergreen, Madrona, and Madrona's Rule 2.3.7 text ink),
Source Serif 4 for titles, captions and findings over the Segoe UI stack for
data, a 12 px floor on every text node (checked), flat marks, a Rule 4.2
provenance strip with Rule 4.4's fourth segment naming the exhibit's state
(the selected pair; the controls removed). The V is conceptual: no axis, no
scale, no implied magnitude. The queue bars keep one fixed 0 to 80 hour scale
with the 48-hour tick and text status on every row, so no state travels by
colour alone (Rule 2.3.2).

None of the package's stylesheets ship. Of the twelve hexes they carried,
nine are Felix tokens or Cascadia palette values; `#edf5ef`, `#f5f6f2` and
`#8fba9f` as a border are not and do not appear here. (Brief A9 overstated
this: it called eight of the twelve invented; six of those eight are the
Cascadia palette.)

**Pass and fail colour outside the exhibits.** Felix has no negative hue.
Experiments 0, 2 and 3 are Felix-styled, but a FAIL state needs a signal that
is not teal. They use Evergreen for pass and Madrona's text ink for fail, the
same pair the two exhibits use, so the page has one meaning for each colour,
and every state also carries its text (PASS, FAIL, "(wrong)"). Both hexes are
Cascadia palette values; no colour was invented.

**Carried by:** `docs/assets/playbook.css` (`:root` block and `.cz-exhibit`
rules); `src/build_page.py` (`provenance()`); `docs/assets/playbook.js`
(strip state); `checks/check_page.py` (the 12 px check, `minExhibitFont`).

## D6 · sql.js: the asm.js build, loaded on the first click

The vendored engine is sql.js 1.14.2's `sql-asm.js` (1,355,169 bytes), the
file the accepted package shipped, verified against the npm tarball
(sha512 matches `provenance.json`; the file matches byte for byte). The WASM
build is half the bytes but its `.wasm` is a second fetch, and a page opened
from `file://` cannot make it in Chromium. The gate review opens
`docs/index.html` from disk and the page must run there as well as served, so
the single-file build wins. Its cost is deferred: the script tag is injected
on the first click of "Run the known-answer check", with a visible loading
state, and `checks/check_page.py` asserts that no request for it precedes
that click and that one follows it. This is the one behaviour that differs
from the package, whose preview loaded the engine on page load and kept the
run button disabled until it was ready.

**Carried by:** `docs/vendor/sql.js/provenance.json`;
`docs/assets/playbook.js` (`loadEngine`); `checks/check_page.py`.

## D7 · The checks are Python Playwright, not Node

The package's checker is a Node script that needs the Playwright npm package.
That package is not on this machine; the Python package (1.62.0, with a
Chromium under `ms-playwright`) is, and it is what Early Warning's render
check uses. `checks/check_page.py` ports every assertion of the package's
checker, adds the engine-load assertions, the file:// pass, the 12 px check on
the experiment frames, the provenance segment count, the V's drawn-line count
and the console-error check, and writes the renders the gate and the panel
read. The brief named the file `check_page.mjs`; the extension changed with
the language and nothing else did.

**Carried by:** `checks/check_page.py`; `CLAUDE.md` (interpreter by path).

## D8 · The manuscript is the single source; the page and README are generated

`content/manuscript.md` is the accepted v5 text with its seven insertion
markers. `src/build_page.py` renders it into the template and into
`README.md` (the package's `PLAYBOOK.md` shape: both SQL versions, the outcome
tables standing in for the experiments, the evidence notes expanded, every
link absolute), and refuses to write either if the hook, the closing line, the
four author paragraphs, the six headings or the career references' confinement
to the author block do not hold. The strings the script adds are the only
drafted text on the page and are listed in the Phase 1 report.

**Carried by:** `src/build_page.py`; `CLAUDE.md`.

## D9 · The reading panel ran reduced, by the owner's instruction

Rule 7.4's floor is three domain seats plus one visualization seat. Aaron
scoped this page's panel (2026-10-12) to two exhibits, two seats, one round,
because the page carries one diagram and one bar exhibit. Experiments 0, 2
and 3 (code, status panels, tables), the comparison table and the commitment
cards are out of scope by decision. Both seats were given the renders at
1440 px and at 320 px, the narrowest supported width, so the one 7.4 FAIL
condition the reduction did not need to touch (design width only) is not
tripped. The record is `governance/chart-review.md`, in CHART-REVIEW v2.9's
format, with the reduction stated in the roster block.

**Carried by:** `governance/pre-panel-notes.md`; `governance/chart-review.md`.

## D10 · What stays in the repository unlinked

`adopt/acceptance-record.md` is the package's long-form acceptance template.
It is kept, under `adopt/` beside the five commitments, and is linked from
nowhere on the page: the page proposes five commitments, and a twenty-two-row
form next to them would read as a claim that the form has been filled.
`governance/chart-review.md` and this record are likewise repository
documents, reachable from the README's map and not from the page.

**Carried by:** `adopt/`; `README.md` (What is where).

## D11 · The em-dash gate exempts the guard kit

The brief asks for an em-dash scan over every tracked text file. The starter
kit's four guard files and `.gitattributes` are copied verbatim from
`cascadia-standards` and hash-pinned in its `hook_manifest.json`; three of
them carry em dashes in comments and none may be edited per repository.
`checks/scan_text.py` therefore reads everything tracked except
`.githooks/`, `.claude/hooks/` and `.gitattributes`, and says so in its
header. Everything rendered under `docs/`, the README, the manuscript, the
scripts and these records are inside the gate.

**Carried by:** `checks/scan_text.py` (`KIT`).

## D12 · The vendored engine is declared binary, in a per-directory attribute

The kit's `pre-commit` secret scan reads every added line of a staged diff.
Its tier-1 shape rules always fire and cannot be allowlisted, and line 98 of
`sql-asm.js` carries, inside its base64 payload, a 20-character run of the
AWS access key ID shape. The file is byte-identical to the npm archive and
is hash-pinned in `provenance.json`, so it may not be edited to carry a
pragma. `docs/vendor/.gitattributes` declares `sql.js/sql-asm.js binary`,
the treatment the kit already gives PNGs and zips; the scanner then sees
"Binary files differ" and skips it, and every authored file stays inside the
gate. The root `.gitattributes` is untouched.

*Counterfactual:* `--no-verify`, which the kit forbids, or a pragma in the
vendored file, which would break its recorded hash.

**Carried by:** `docs/vendor/.gitattributes`; `CLAUDE.md`.

## D13 · Commits name a real `python3` ahead of the Store stub

The kit's hook resolves `python3`, `python`, `py` in that order and fails
closed if the one it finds cannot run. On this machine `python3` on the
hook's PATH is the Microsoft Store alias, which exits non-zero with
"Python was not found", so the gate refused every commit until
`C:\Users\Ajayr\AppData\Local\Python\bin` was put ahead of it for the commit.
That is the gate behaving as designed; it is recorded because the symptom
reads as a broken hook rather than a PATH fact, and because every other
repository in the estate that commits from this machine meets the same
condition. Reported as an estate finding, not fixed here: the kit's resolver
is canon.

**Carried by:** `CLAUDE.md`.

## D14 · The opening query carries two defects, not one (Aaron, at the gate)

The accepted v5 package's opening query had one defect, `>` for "at least",
and deduplicated with `SELECT DISTINCT`; its checker enforced that the
operator was the sole difference between the two queries. At the gate on
2026-10-12 Aaron asked for a second, equally ordinary defect: the dedup
clause is missing. The defective query now has no DISTINCT and no GROUP BY,
so it returns A105 twice; the correction changes the operator and adds
`GROUP BY order_id`, and nothing else differs.

Why it is better, not only different: the defective run returns **two rows,
the expected count, with the wrong IDs**, which is the page's central
argument (the same-count preset in Experiment 1) demonstrated before the
reader reaches Experiment 1; and the two defects trace to two of the three V
pairs (the boundary to the decision rule, the dedup to the data contract's
"one order per ID"). The manuscript is unchanged: "the missing order is one
broken link in the V" remains true. The teaching cost is stated on the page:
in the defective state only line 7 can be marked, because a missing clause
has no line, and the lesson text says so.

What changed: `dispatch-code.js` (both strings; line 7 is still the boundary
line and the build asserts it), the experiment's result, history and lesson
wording, the corrected-state highlight (line 7 and the GROUP BY line), the
gate's assertions, the README's generated opening text, `CLAUDE.md`. Not
changed: the scenario, the expected IDs, the manuscript, the exhibits, the
panel record (Experiment 0 is outside its scope).

*Amended the same day, also at the gate:* the two corrections are applied
**one click at a time**, each click a rerun. The first click fixes the
boundary only and the check still fails, now with three rows (A102, A105,
A105); the second adds GROUP BY and passes. Three runs stay in the history,
so the reader sees that one correction exposed the second defect rather
than both vanishing at once. `dispatch-code.js` carries three strings
(`buggy`, `partial`, `fixed`), each derived from the last by one edit.

*Counterfactual:* keep one defect, or show GROUP BY without making it a
defect, which teaches nothing the reader has to find; or one click for both
corrections, which hides the step where fixing one thing changes the count.

**Carried by:** `docs/assets/dispatch-code.js`; `docs/assets/playbook.js`;
`src/build_page.py`; `checks/check_page.py`.
