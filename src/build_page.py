"""Build docs/index.html and README.md from the accepted manuscript.

Inputs, all tracked:
    content/manuscript.md               the v5 manuscript, verbatim, with seven
                                        <!-- visual:* --> insertion markers
    evidence/source-links.md            the pinned reference definitions
    docs/assets/dispatch-scenario.json  the six invented rows and the expected IDs
    docs/assets/dispatch-code.js        the two SQL query strings (read, not executed)
    docs/template.html                  the Felix page chrome with @@tokens@@

Outputs, both generated and never hand-edited:
    docs/index.html                     the page
    README.md                           the whole page as text, links absolute,
                                        tables standing in for the experiments

Every sentence of prose on the page comes from the manuscript through this
script. The strings this script adds (eyebrows, figure titles, button labels,
alt text, the aside's anchor labels, table headers) are listed in the Phase 1
report and are the only drafted text on the page.

    C:\\Users\\Ajayr\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe src\\build_page.py
"""
import html
import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
MANUSCRIPT = REPO / "content" / "manuscript.md"
LINKS = REPO / "evidence" / "source-links.md"
SCENARIO = REPO / "docs" / "assets" / "dispatch-scenario.json"
CODE = REPO / "docs" / "assets" / "dispatch-code.js"
TEMPLATE = REPO / "docs" / "template.html"
OUT_HTML = REPO / "docs" / "index.html"
OUT_README = REPO / "README.md"

SITE_URL = "https://www.robbinsanalytics.com/"
CASCADIA_URL = "https://www.robbinsanalytics.com/cascadia.html"
PAGE_URL = "https://www.robbinsanalytics.com/cascadia-validation-playbook/"
REPO_URL = "https://github.com/RobbinsAnalytics/cascadia-validation-playbook"
THUMB_URL = "https://www.robbinsanalytics.com/assets/thumb-validation-playbook.png"
ENGINE = "vendor/sql.js/sql-asm.js"

META_DESCRIPTION = ("How can you be confident in code you did not read or write in full? One invented "
                    "dispatch rule, a known answer specified before the code, and four experiments in the "
                    "browser that show what a check adds to reading.")

# Short labels for the sticky table of contents, the lime aside and the footer. Drafted.
TOC_LABELS = ["Promise and proof", "Where this comes from", "The queue", "A second agent", "The release gate", "Five commitments"]
# The pill at the top of each section article names what the section carries. Drafted.
SECTION_PILLS = ["The V", "Author account", "Experiment 1", "Experiment 2", "Experiment 3", "Commitments"]

# The V's three pairs, the five commitments and the six comparison rows are carried
# over from the accepted package's builder (build_scenario.mjs) unchanged.
PAIRS = [
    {"key": "use", "level": "Intended use", "promise": "Help staff review delayed orders", "check": "Owner tries the queue",
     "proof": "Can staff identify the right orders and decide what to investigate?", "owner": "Operations owner",
     "risk": "A correct list can still be used for an unapproved decision, such as automatic refunds.", "left": 1, "right": 7},
    {"key": "rule", "level": "Decision rule", "promise": "Paid, unshipped, 48+ hours; not canceled", "check": "Compare with known answers",
     "proof": "Orders A102 and A105 appear once each. Boundary, exclusion and duplicate cases have fixed expectations.", "owner": "Analytics lead",
     "risk": "The list can look plausible while dropping a required order or adding an ineligible one.", "left": 2, "right": 6},
    {"key": "data", "level": "Data contract", "promise": "One order per ID; source age \u2264 2 hours", "check": "Check inputs and failure handling",
     "proof": "Repeated IDs collapse to one order. Old source data blocks the current release.", "owner": "Technical reviewer",
     "risk": "Duplicate rows inflate the queue, or an old list looks current.", "left": 3, "right": 5},
]
RECORD_ROWS = [
    ["An owner-answerable question", "Name the use and owner; record acceptance and restrictions against a version."],
    ["Expected results before implementation", "Commit the cases and expected answers before the build being tested."],
    ["A separate calculation path", "Re-derive the published figures; name shared inputs and the scope actually checked."],
    ["A check that must fail", "Inject a known defect and confirm the named check rejects it."],
    ["Every run and its disposition", "Keep status, stop reason and resolution, including original and corrected runs."],
]
CEREMONY_ROWS = [
    ["Intended use", "Approved use statement", "Owner question, scope and acceptance"],
    ["Rule", "Controlled requirements", "Versioned rule and expected cases"],
    ["Specification", "Design record and traceability matrix", "Data contract and requirement-to-test links"],
    ["Code", "Reviewed release baseline", "Versioned implementation and assigned review"],
    ["Second path", "Separately developed check, where used", "Second agent receives rules and raw cases"],
    ["Sign-off", "Recorded approval of a release", "Explicit acceptance linked to the reviewed commit"],
]


def esc(s):
    return html.escape(s, quote=False)


def load_links():
    links = {}
    for line in LINKS.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\[([^\]]+)\]:\s*(\S+)", line)
        if m:
            links[m.group(1)] = m.group(2)
    return links


def inline_html(md, links):
    """Markdown inline to HTML: **bold** and [text][ref]. Everything else is text."""
    out = esc(md)
    out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)

    def link(m):
        key = m.group(2)
        if key not in links:
            raise SystemExit("unresolved link reference [%s]" % key)
        return '<a href="%s">%s</a>' % (links[key], m.group(1))
    return re.sub(r"\[([^\]]+)\]\[([^\]]+)\]", link, out)


def inline_md(md, links):
    """Markdown inline to Markdown with absolute links: [text][ref] -> [text](url)."""
    def link(m):
        key = m.group(2)
        if key not in links:
            raise SystemExit("unresolved link reference [%s]" % key)
        return "[%s](%s)" % (m.group(1), links[key])
    return re.sub(r"\[([^\]]+)\]\[([^\]]+)\]", link, md)


def parse(text):
    """The manuscript as a list of blocks: h1, h2, p, visual, div (author block), rawp, details."""
    lines = text.split("\n")
    blocks, i = [], 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.startswith("# "):
            blocks.append(("h1", line[2:].strip())); i += 1
        elif line.startswith("## "):
            blocks.append(("h2", line[3:].strip())); i += 1
        elif (m := re.match(r"<!-- visual:(\w+) -->", line)):
            blocks.append(("visual", m.group(1))); i += 1
        elif line.startswith("<div"):
            j = i + 1
            inner = []
            while lines[j].strip() != "</div>":
                inner.append(lines[j]); j += 1
            paras = [" ".join(p.split("\n")) for p in "\n".join(inner).strip().split("\n\n") if p.strip()]
            blocks.append(("div", line.strip(), paras)); i = j + 1
        elif line.startswith("<details>"):
            j = i + 1
            inner = []
            while lines[j].strip() != "</details>":
                inner.append(lines[j]); j += 1
            summary = re.match(r"<summary>(.*)</summary>", inner[0].strip()).group(1)
            body = " ".join(l for l in inner[1:] if l.strip())
            blocks.append(("details", summary, body)); i = j + 1
        elif line.startswith("<p "):
            blocks.append(("rawp", line.strip())); i += 1
        else:
            j = i
            para = []
            while j < len(lines) and lines[j].strip() and not lines[j].startswith(("#", "<")):
                para.append(lines[j].strip()); j += 1
            blocks.append(("p", " ".join(para))); i = j
    return blocks


def split_sections(blocks):
    sections, current = [], {"heading": None, "items": []}
    for b in blocks:
        if b[0] == "h2":
            sections.append(current)
            current = {"heading": b[1], "items": []}
        else:
            current["items"].append(b)
    sections.append(current)
    return sections


# ---------------------------------------------------------------- widgets (HTML)

def table(headers, rows):
    head = "".join('<th scope="col">%s</th>' % h for h in headers)
    body = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % c for c in r) for r in rows)
    return '<div class="table-wrap"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (head, body)


def provenance(extra, state_id=None):
    segs = ['<span class="seg">Harbor Dispatch</span>', '<span class="seg">invented teaching cases</span>', '<span class="seg">%s</span>' % extra]
    if state_id:
        segs.append('<span class="seg" id="%s"></span>' % state_id)
    return '<div class="provenance" role="note" aria-label="Provenance"><span class="segs">%s</span></div>' % "".join(segs)


def control(cid, label, checked=True, sub=""):
    return ('<label class="control"><input type="checkbox" id="%s"%s><span class="state" aria-hidden="true"></span><span><b>%s</b>%s</span></label>'
            % (cid, " checked" if checked else "", label, "<small>%s</small>" % sub if sub else ""))


def reset(rid):
    return '<button type="button" class="reset" id="%s">Reset experiment \u21ba</button>' % rid


def note(summary, body_html):
    return '<details class="note"><summary>%s</summary><div class="note-body">%s</div></details>' % (summary, body_html)


def widgets(scenario, buggy):
    raw_rows = [[r["id"], "%d hours" % r["age"], "Canceled" if r["canceled"] else "Shipped" if r["shipped"] else "Paid, unshipped", r["note"]] for r in scenario["rows"]]
    w = {}
    w["opening"] = (
        '<figure class="lab code-lab" id="opening-experiment" aria-labelledby="opening-title">'
        '<div class="exhibit-heading"><div><span class="mini-label">EXPERIMENT 0 / INVENTED HARBOR DISPATCH CASE</span>'
        '<h3 id="opening-title">Read the code. Then check the answer.</h3></div>%s</div>'
        '<p class="opening-rule"><b>The rule:</b> include paid, unshipped orders <strong>at least 48 hours old</strong>. Exclude cancellations and repeated IDs.</p>'
        '<p class="code-invite">Inspect the code for mismatches with that rule. Then run the check.</p>'
        '<div class="code-layout"><div class="code-pane"><span class="mini-label" id="code-state">IMPLEMENTATION / SQL</span>'
        '<pre aria-label="SQL query displayed and executed by this experiment"><code id="opening-code">%s</code></pre></div>'
        '<div class="answer-pane"><span class="mini-label">EXPECTED / SPECIFIED SEPARATELY</span><strong>A102 \u00b7 A105</strong>'
        '<p>A102 is exactly 48 hours old. A105 is 60 hours old. Each belongs once.</p>'
        '<div id="opening-result" class="opening-result" aria-live="polite"><b>Not run yet</b><p>The expected IDs are fixed before this implementation is checked.</p></div></div></div>'
        '<div class="opening-actions"><button type="button" class="btn btn-primary" id="run-opening" data-engine="%s">Run the known-answer check</button>'
        '<button type="button" class="btn btn-outline" id="fix-opening" disabled>Correct the boundary and rerun</button></div>'
        '<p class="chart-limit" id="opening-lesson">The check compares order IDs and multiplicity, not just the total. Reading and testing supply different evidence.</p>'
        '%s%s</figure>'
        % (reset("reset-opening"), esc(buggy), ENGINE,
           note("Inspect the six invented input rows", table(["Order", "Age", "State", "Purpose"], raw_rows)),
           provenance("displayed code executes locally; expected IDs are separate from the implementation")))

    rows_html = ""
    for i, p in enumerate(PAIRS):
        pressed = "true" if i == 1 else "false"
        middle = '<span class="v-middle">Each check traces<br>back to its promise</span>' if i == 0 else ""
        rows_html += ('<div class="v-row level-%d">'
                      '<button type="button" class="v-node define" data-pair="%s" data-side="left" aria-pressed="%s" aria-controls="v-detail"><span class="node-meta">%d / %s</span><b>%s</b></button>%s'
                      '<button type="button" class="v-node verify" data-pair="%s" data-side="right" aria-pressed="%s" aria-controls="v-detail"><span class="node-meta">%d / %s</span><b>%s</b></button></div>'
                      % (i + 1, p["key"], pressed, p["left"], p["level"], p["promise"], middle, p["key"], pressed, p["right"], p["level"], p["check"]))
    w["vmodel"] = (
        '<figure class="cz-exhibit v-exhibit" aria-labelledby="v-title">'
        '<div class="exhibit-heading"><div><span class="mini-label">THE V MODEL / ADAPTED FOR ANALYTICS</span><h3 id="v-title">Specify the promise. Plan its proof.</h3></div><span class="hint">Select a matching pair</span></div>'
        '<div class="v-canvas"><div class="v-direction left">DEFINE <span>\u2193 before building</span></div><div class="v-direction right">CHECK <span>\u2191 after building</span></div>'
        '<svg class="v-lines" aria-hidden="true"></svg>%s'
        '<div class="v-row build-row"><div class="v-build"><span class="node-meta">4 / IMPLEMENTATION</span><b>Build the queue</b><span>AI agents work to the specification</span></div></div></div>'
        '<div id="v-detail" class="v-detail" aria-live="polite"><b>Decision rule \u2192 known answers</b><p>A102 and A105 should appear once each.</p></div>'
        '<figcaption>Solid arrows show the work sequence. Dashed links pair a requirement with its check. Define the expected evidence before coding; perform and review the checks afterward.</figcaption>'
        '%s</figure>' % (rows_html, provenance("conceptual method; proposed roles", "v-state")))

    w["ceremony"] = ('<div class="ceremony"><h3>Same V, less ceremony</h3>%s'
                     '<p class="chart-limit">The structure survived. The records moved into the repository. A commit identifies the version; the acceptance record names the decision and the owner.</p></div>'
                     % table(["Level", "Regulated software (the V with full ceremony)", "AI-assisted analytics (the same V)"], CEREMONY_ROWS))

    w["queue"] = (
        '<figure class="lab" aria-labelledby="queue-title">'
        '<div class="exhibit-heading"><div><span class="mini-label">EXPERIMENT 1 / THE RULE</span><h3 id="queue-title">Two orders belong in this queue.</h3></div>%s</div>'
        '<div class="control-grid three">%s%s%s</div>'
        '<div class="preset-actions"><button type="button" class="text-button" id="remove-controls">Remove all three controls</button>'
        '<button type="button" class="text-button" id="same-count">Show the same count with the wrong answer</button></div>'
        '<div class="queue-comparison"><div class="expected-box"><span class="mini-label">SPECIFIED ANSWER</span><strong>2 orders</strong><span>A102 \u00b7 A105</span></div>'
        '<div class="actual-box" id="queue-result" aria-live="polite"></div></div>'
        '<div class="cz-exhibit queue-exhibit"><div id="order-chart" role="group" aria-label="Each input row, its age and its queue decision"></div>'
        '<p class="chart-key">Vertical tick on each bar: 48 hours. Rust marks a decision that differs from the specified answer, whether a wrong inclusion or a wrong exclusion; green is a correct inclusion; grey is a correct exclusion. The status text names each.</p>'
        '<div class="finding" id="queue-finding" aria-live="polite"></div>%s</div>'
        '%s</figure>'
        % (reset("reset-queue"),
           control("include-boundary", "Include exactly 48 hours", True, "Avoid changing \u201cat least\u201d to \u201cmore than\u201d."),
           control("exclude-canceled", "Exclude canceled orders", True, "Age alone does not make an order eligible."),
           control("unique-orders", "Collapse repeated IDs", True, "Count orders, not input rows."),
           provenance("ages fixed at the teaching snapshot; paid and shipped checks stay active", "queue-state"),
           note("Inspect all six input rows", table(["Order", "Age at 4 p.m.", "State", "Why this case exists"], raw_rows))))

    w["checker"] = (
        '<figure class="lab" aria-labelledby="checker-title">'
        '<div class="exhibit-heading"><div><span class="mini-label">EXPERIMENT 2 / THE AGENT BOUNDARY</span><h3 id="checker-title">What does the checking agent receive?</h3></div>%s</div>'
        '<div class="control-grid two">%s%s</div>'
        '<div class="branch-source">SIX RAW INPUT ROWS <span>\u2192 two calculation paths</span></div>'
        '<div class="branch-grid"><div class="branch build-branch"><span class="mini-label">FIRST AGENT / BUILD</span><h4>Produce the queue</h4><p id="build-method"></p><div id="build-orders" class="order-chips"></div></div>'
        '<div class="branch check-branch"><span class="mini-label">CHECKING ARRANGEMENT</span><h4 id="checking-agent">Original agent checks itself</h4><p id="check-method"></p><div id="check-orders" class="order-chips"></div></div></div>'
        '<div id="checker-result" class="finding" aria-live="polite"></div>'
        '<p class="chart-limit">In this seeded case, the separate path catches the omitted cancellation rule. Shared rules, source data and possible reasoning errors remain.</p>'
        '%s</figure>'
        % (reset("reset-checker"),
           control("checker-defect", "Inject the canceled-order defect", True, "The build incorrectly includes A103."),
           control("separate-checker", "Give the check to a second agent", False, "Rules and raw cases only; no first implementation or output."),
           provenance("illustrated agent behavior; no live model calls or complete-independence claim")))

    w["release"] = (
        '<figure class="lab" aria-labelledby="release-title">'
        '<div class="exhibit-heading"><div><span class="mini-label">EXPERIMENT 3 / THE RELEASE GATE</span><h3 id="release-title">A red check matters only if it changes the next step.</h3></div>%s</div>'
        '<div class="control-grid two">%s%s</div>'
        '<div class="age-control"><label for="source-age">Source age <output id="age-value" for="source-age">1 hour</output></label>'
        '<p class="age-policy">Release requires source age \u2264 2 hours.</p>'
        '<input id="source-age" type="range" min="1" max="8" step="1" value="1"><span>1 hour</span><span>8 hours</span></div>'
        '<div class="release-flow"><div class="check-stack"><div id="rule-check"></div><div id="fresh-check"></div></div>'
        '<div class="gate-state" id="gate-state"></div><div class="dashboard-state" id="dashboard-state"></div></div>'
        '<div id="release-result" class="finding" aria-live="polite"></div>'
        '%s</figure>'
        % (reset("reset-release"),
           control("release-defect", "Inject the canceled-order defect", True, "A103 enters the proposed queue."),
           control("enforce-gate", "Enforce the release gate", True, "Stop when either the rule or freshness check fails."),
           provenance("simulated current release; no real system is changed")))

    items = ""
    for n, (title, record) in enumerate(RECORD_ROWS, 1):
        last = n == len(RECORD_ROWS)
        items += ('<li%s><span class="accent" aria-hidden="true"></span><p class="index">%02d<small>Commitment</small></p><b>%s</b><span class="record">%s</span>%s</li>'
                  % (' class="inverted"' if last else "", n, title, record, '<span class="pill">Proposed</span>' if last else ""))
    w["record"] = '<div class="commitments five-commitments"><span class="mini-label">PROPOSED / FIVE COMMITMENTS</span><ol class="commitment-list">%s</ol></div>' % items
    return w


# ---------------------------------------------------------------- widgets (Markdown, for the README)

def md_table(headers, rows):
    return "\n| %s |\n| %s |\n%s\n" % (" | ".join(headers), " | ".join("---" for _ in headers), "\n".join("| " + " | ".join(r) + " |" for r in rows))


def md_widgets(scenario, buggy, fixed):
    raw_rows = [[r["id"], "%d hours" % r["age"], "Canceled" if r["canceled"] else "Shipped" if r["shipped"] else "Paid, unshipped", r["note"]] for r in scenario["rows"]]
    return {
        "opening": ("\nFictional Harbor Dispatch rule: paid, unshipped orders at least 48 hours old; exclude canceled orders and repeated IDs. Expected IDs, specified separately: A102 and A105.\n\n```sql\n"
                    + buggy + "\n```\n\nExecuting this SQL query on the six cases returns A105 twice. The count matches the expected two and the IDs do not: 48 > 48 is false, so A102 is excluded, and nothing collapses the repeated A105 row. Correcting > to >= alone returns A102, A105 and A105: three rows, A105 still repeated. Adding GROUP BY order_id then returns A102 and A105 once each. Line 7 is easy to inspect here, and the missing GROUP BY has no line to inspect at all. Now imagine 400 lines across six files, written overnight by an agent, and a review on Friday afternoon. The same known-answer check still catches both errors.\n\nCorrected query, after both corrections:\n\n```sql\n"
                    + fixed + "\n```\n" + md_table(["Order", "Age", "State", "Purpose"], raw_rows)),
        "ceremony": md_table(["Level", "Regulated software (the V with full ceremony)", "AI-assisted analytics (the same V)"], CEREMONY_ROWS)
                    + "\nThe structure survived. The records moved into the repository. A commit identifies the version; the acceptance record names the decision and the owner.\n",
        "vmodel": md_table(["Define before building", "Promise", "Check afterward", "Evidence", "Proposed owner"], [[p["level"], p["promise"], p["check"], p["proof"], p["owner"]] for p in PAIRS])
                  + "\nWork sequence: intended use \u2192 decision rule \u2192 data contract \u2192 implementation \u2192 input checks \u2192 known-answer checks \u2192 owner tryout. Each check traces to its corresponding promise.\n",
        "queue": md_table(["Order", "Age", "State", "Case"], raw_rows)
                 + md_table(["Controls removed", "Actual entries", "Mismatch with A102 and A105"],
                            [["None", "A102, A105", "None"], ["48-hour boundary", "A105", "A102 missing"], ["Cancellation exclusion", "A102, A103, A105", "A103 ineligible"],
                             ["Duplicate collapse", "A102, A105, A105", "A105 repeated"], ["Boundary and duplicate collapse (same-count preset)", "A105, A105", "Two entries, but A102 is missing and A105 is repeated"],
                             ["All three", "A103, A105, A105", "A102 missing; A103 ineligible; A105 repeated"]]),
        "checker": md_table(["Canceled-order defect", "Checker input", "Result"],
                            [["On", "Second agent: rules and raw cases only", "Build: 3; checker: 2. Mismatch exposes A103."], ["On", "Original agent: existing filtered list", "Both: 3. Agreement hides the same error."],
                             ["Off", "Second agent: rules and raw cases only", "Both: 2. The specified case passes."], ["Off", "Original agent: existing filtered list", "Both: 2. Agreement gives no separate filter evidence."]]),
        "release": md_table(["Rule result", "Source age", "Gate", "Current release"],
                            [["Fail, includes A103", "1 hour", "Enforced", "Blocked"], ["Fail, includes A103", "1 hour", "Not enforced", "Wrong queue published despite failure"],
                             ["Pass", "8 hours", "Enforced", "Blocked for stale source"], ["Pass", "8 hours", "Not enforced", "Old input published as current"], ["Pass", "1 or 2 hours", "Enforced", "Published for staff review"]])
                   + "\nRule and freshness checks are separate. Stopping either failure requires enforcement. A disabled gate can appear harmless on a clean run while providing no failure protection.\n",
        "record": "\n**Proposed commitments**\n" + md_table(["Commitment", "Record"], RECORD_ROWS),
    }


# ---------------------------------------------------------------- page assembly

def render_section(n, section, w, links):
    parts = []
    prose = []

    def flush():
        if prose:
            parts.append('<div class="rich prose section-prose">%s</div>' % "".join("<p>%s</p>" % p for p in prose))
            prose.clear()
    for item in section["items"]:
        kind = item[0]
        if kind == "p":
            prose.append(inline_html(item[1], links))
        elif kind == "visual":
            flush(); parts.append(w[item[1]])
        elif kind == "div":
            flush()
            paras = "".join("<p>%s</p>" % inline_html(p, links) for p in item[2])
            parts.append('<div class="author-panel grain"><div class="glow" aria-hidden="true"></div>'
                         '<p class="eyebrow-dark">Author account / first person</p>'
                         '<div class="author-account" data-voice="author">%s</div></div>' % paras)
        elif kind == "rawp":
            flush(); parts.append(item[1])
        elif kind == "details":
            flush(); parts.append(note(item[1], "<p>%s</p>" % inline_html(item[2], links)))
    flush()
    bars = '<span class="section-pill-bars" aria-hidden="true"><span style="height:5px"></span><span style="height:8px"></span><span style="height:11px"></span></span>'
    return ('<article id="s%d" class="section-article">'
            '<span class="ghost-numeral" aria-hidden="true">%02d</span>'
            '<span class="pill">%s%s</span>'
            '<h2 class="section-heading">%s</h2>%s</article>' % (n, n, bars, SECTION_PILLS[n - 1], esc(section["heading"]), "".join(parts)))


def build():
    links = load_links()
    scenario = json.loads(SCENARIO.read_text(encoding="utf-8"))
    js = CODE.read_text(encoding="utf-8")
    buggy = re.search(r"const buggy = `(.*?)`;", js, re.S).group(1)
    partial = buggy.replace("age_hours > 48", "age_hours >= 48")
    fixed = partial.replace("FROM eligible_orders\nORDER BY order_id;", "FROM eligible_orders\nGROUP BY order_id\nORDER BY order_id;")
    assert buggy.count("age_hours > 48") == 1 and "GROUP BY" not in buggy and fixed.count("GROUP BY order_id") == 1
    assert buggy.split("\n")[6].strip() == "AND age_hours > 48", "line 7 must be the boundary line; the lesson text names it"
    manuscript = MANUSCRIPT.read_text(encoding="utf-8")
    blocks = parse(manuscript)
    sections = split_sections(blocks)
    if len(sections) != 7:
        raise SystemExit("expected a preamble and six sections, found %d" % (len(sections) - 1))

    pre = sections[0]["items"]
    title = next(b[1] for b in blocks if b[0] == "h1")
    paras = [b[1] for b in pre if b[0] == "p"]
    subtitle = re.fullmatch(r"\*\*(.+)\*\*", paras[0]).group(1)
    hook_question, hook_para = paras[1], paras[2]
    assert [b[1] for b in pre if b[0] == "visual"] == ["opening"]

    w = widgets(scenario, buggy)
    sections_html = "\n".join(render_section(n, sections[n], w, links) for n in range(1, 7))

    # The closing of section 6 is a statement: give the bold line Felix's statement treatment.
    sections_html = sections_html.replace('<p><strong>Confidence comes from evidence', '<p class="closing-statement"><strong>Confidence comes from evidence', 1)

    toc = "\n".join('            <li><a class="-ml-px block border-l-2 py-1.5 pl-4 text-sm transition-colors border-transparent text-ink-soft hover:text-ink" href="#s%d">%02d %s</a></li>' % (n, n, TOC_LABELS[n - 1]) for n in range(1, 7))
    # The lime aside carries no in-page links (Aaron, 2026-10-12, at the gate): the sticky
    # TOC already has them and the card was taking the header's height.
    footer = "\n".join('        <li><a class="group inline-flex min-h-10 items-center gap-1.5 py-1 text-white/65 transition-colors hover:text-white md:min-h-0" href="#s%d">%s</a></li>' % (n, esc(sections[n]["heading"])) for n in range(1, 7))

    tokens = {
        "title": esc(title), "subtitle": inline_html(subtitle, links), "meta_description": esc(META_DESCRIPTION),
        "hook_question": "<p>%s</p>" % inline_html(hook_question, links), "hook_para": "<p>%s</p>" % inline_html(hook_para, links),
        "opening": w["opening"], "sections": sections_html, "toc": toc, "footer_anchors": footer,
        "scenario_json": json.dumps({"scenario": scenario, "pairs": PAIRS}, ensure_ascii=False).replace("</", "<\\/"),
        "site_url": SITE_URL, "cascadia_url": CASCADIA_URL, "page_url": PAGE_URL, "repo_url": REPO_URL, "thumb_url": THUMB_URL,
        "build_matrix_url": links["build-matrix"],
    }
    page = TEMPLATE.read_text(encoding="utf-8")
    for k, v in tokens.items():
        page = page.replace("@@%s@@" % k, v)

    # Invariants on the rendered page.
    problems = []
    if "@@" in page:
        problems.append("unfilled token: " + re.search(r"@@\w+@@", page).group(0))
    if "\u2014" in page:
        problems.append("em dash in the rendered page")
    for needle, label in [(esc(hook_question), "the hook"), ("<strong>Confidence comes from evidence", "the closing line"),
                          ("I learned this at Philips, on Class III medical devices.", "author paragraph 1")]:
        if needle not in page:
            problems.append("missing: " + label)
    if page.count('class="author-account"') != 1 or len(re.findall(r"<div class=\"author-account\"[^>]*>(.*?)</div>", page, re.S)[0].split("<p>")) - 1 != 4:
        problems.append("the author block must hold exactly four paragraphs")
    for n in range(1, 7):
        if 'id="s%d"' % n not in page or esc(sections[n]["heading"]) not in page:
            problems.append("section %d missing" % n)
    public = re.sub(r"<div class=\"author-account\"[^>]*>.*?</div>", "", page, flags=re.S)
    if re.search(r"Philips|Class III", public):
        problems.append("career reference outside the author block")
    if problems:
        raise SystemExit("build refused:\n  " + "\n  ".join(problems))
    OUT_HTML.write_text(page, encoding="utf-8", newline="\n")

    # README: the page as text, every link absolute.
    mdw = md_widgets(scenario, buggy, fixed)
    body = re.sub(r"<!-- visual:(\w+) -->", lambda m: mdw[m.group(1)], manuscript)
    body = inline_md(body, links)
    readme = (
        "# Cascadia Validation Playbook\n\n"
        "One Felix page, \"Validating AI-Assisted Analytics\", and this README, which carries the page's full text for readers whose network blocks the site.\n"
        "The page is served at %s and runs a real SQLite query in your browser; the tables below stand in for its four experiments.\n\n"
        "---\n\n%s\n\n---\n\n"
        "## What is where\n\n"
        "| Path | What |\n|---|---|\n"
        "| `content/manuscript.md` | The accepted v5 manuscript. Every sentence on the page comes from here, verbatim. |\n"
        "| `docs/index.html` | The page, generated by `src/build_page.py` from the manuscript and `docs/template.html`. Published to the URL above from `main`. |\n"
        "| `docs/assets/dispatch-scenario.json` | The six invented input rows and the expected IDs, specified separately from any implementation. |\n"
        "| `docs/assets/dispatch-code.js` | The two SQL query strings. The defective one has `>` where the rule says at least, and no clause collapsing repeated IDs; the corrections are applied one click at a time, the operator first, then `GROUP BY order_id`, and nothing else changes. |\n"
        "| `docs/assets/playbook.js`, `playbook.css` | The experiments and the page's own styles. The SQLite engine loads on the first click of the run button. |\n"
        "| `docs/vendor/sql.js/` | sql.js 1.14.2 (SQLite compiled to asm.js), its MIT license and `provenance.json` with the archive integrity and file hashes. |\n"
        "| `docs/assets/felix.src.css`, `felix.css` | The Felix design system's tokens and components, compiled by the Tailwind v4 CLI. Felix itself is referenced, not copied; see the decision record. |\n"
        "| `docs/renders/` | Full-page renders at 390 and 1440 px, the exhibit renders the reading panel read, and `checks.json`, the last run of the behaviour gate. |\n"
        "| `checks/check_page.py` | The behaviour gate: every experiment, five widths, from a local server and from disk. `checks/scan_text.py` is the em-dash, names and duration scan. |\n"
        "| `evidence/source-links.md` | The thirteen pinned evidence links and the Build by Build link, pinned to commits. |\n"
        "| `adopt/five-commitments.md` | The five commitments as a standalone file. `adopt/acceptance-record.md` is the long-form record template, deliberately not linked from the page. |\n"
        "| `governance/decision-record.md` | Why a page and not a build, why one page, why Felix in a repository, the sql.js choice, the reduced panel. `governance/chart-review.md` is the Rule 7.4 panel record. |\n\n"
        "Rebuild with `C:\\Users\\Ajayr\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe src\\build_page.py`, then run `checks\\check_page.py` with the same interpreter.\n"
        % (PAGE_URL, body.strip()))
    if "\u2014" in readme:
        raise SystemExit("em dash in README")
    OUT_README.write_text(readme, encoding="utf-8", newline="\n")
    print(json.dumps({"sections": 6, "experiments": 4, "rows": len(scenario["rows"]), "expected": scenario["expectedIds"],
                      "page_bytes": len(page.encode("utf-8")), "readme_bytes": len(readme.encode("utf-8"))}))


if __name__ == "__main__":
    build()
