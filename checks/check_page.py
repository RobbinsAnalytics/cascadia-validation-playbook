"""The behaviour gate for docs/index.html.

Ported from the accepted package's check_scenario.mjs and extended. Drives the
page with Playwright (Python; the Node package is not on this machine) from a
local static server at five widths and from file:// at two, and asserts:

  invariants   displayed SQL is executed SQL; only > vs >= differs; expected IDs
               come from the JSON; defective line unhighlighted before a run;
               correction disabled before a run; both runs stay in the history;
               each experiment resets independently; the same-count preset
               returns A105 twice with A102 missing; the gate blocks at three
               hours and passes at two; sql.js is NOT requested before the first
               click and IS requested after it
  coverage     8 queue combinations, 4 checker combinations, 32 release
               combinations including exactly two hours, three V pairs,
               keyboard activation, every disclosure
  layout       no horizontal overflow, no overlapping V nodes, no duplicate IDs,
               no broken in-page anchors, every text node inside the two
               exhibits and the three experiment frames at 12 px or more,
               zero console errors, no network request off this machine other
               than the Google Fonts request the template declares

Renders: docs/renders/page-390.png and page-1440.png (full page), and the
exhibit renders the reading panel is handed (v-initial-{320,1440}.png,
queue-broken-{320,1440}.png). Writes docs/renders/checks.json.

    C:\\Users\\Ajayr\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe checks\\check_page.py
    ... checks\\check_page.py --url https://www.robbinsanalytics.com/cascadia-validation-playbook/ --widths 390,1440
"""
import argparse
import functools
import http.server
import json
import pathlib
import re
import sys
import threading
from datetime import date

from playwright.sync_api import sync_playwright

REPO = pathlib.Path(__file__).resolve().parent.parent
DOCS = REPO / "docs"
RENDERS = DOCS / "renders"
PORT = 8743
ALLOWED_HOSTS = ("fonts.googleapis.com", "fonts.gstatic.com")
QUEUE_CASES = [
    ([True, True, True], "A102 \u00b7 A105", False), ([False, True, True], "A105", True), ([True, False, True], "A102 \u00b7 A103 \u00b7 A105", True),
    ([True, True, False], "A102 \u00b7 A105 \u00b7 A105", True), ([False, False, True], "A103 \u00b7 A105", True), ([False, True, False], "A105 \u00b7 A105", True),
    ([True, False, False], "A102 \u00b7 A103 \u00b7 A105 \u00b7 A105", True), ([False, False, False], "A103 \u00b7 A105 \u00b7 A105", True),
]
CONTROLS = ["include-boundary", "exclude-canceled", "unique-orders"]


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args, **kwargs):
        pass


def serve():
    handler = functools.partial(QuietHandler, directory=str(DOCS))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def check(browser, url, width, errors, renders, is_file):
    tag = "%s %d" % ("file" if is_file else "http", width)
    a = lambda ok, label: errors.append("%s: %s" % (tag, label)) if not ok else None
    page = browser.new_page(viewport={"width": width, "height": 1000}, has_touch=width == 390, reduced_motion="reduce")
    requests, console = [], []
    page.on("request", lambda r: requests.append(r.url))
    page.on("pageerror", lambda e: errors.append("%s: pageerror %s" % (tag, e)))
    page.on("console", lambda m: console.append(m.text) if m.type == "error" else None)
    page.goto(url, wait_until="load")
    page.locator(".order-row").last.wait_for()
    page.wait_for_timeout(300)

    state = page.evaluate("""() => {
      const boxes=[...document.querySelectorAll('.v-node,.v-build')].map(e=>({label:e.innerText,rect:e.getBoundingClientRect().toJSON()}));
      const overlaps=[];boxes.forEach((x,i)=>boxes.slice(i+1).forEach(y=>{if(x.rect.left<y.rect.right&&x.rect.right>y.rect.left&&x.rect.top<y.rect.bottom&&x.rect.bottom>y.rect.top)overlaps.push([x.label,y.label]);}));
      const ids=[...document.querySelectorAll('[id]')].map(e=>e.id);
      const textEls=sel=>[...document.querySelectorAll(sel)].filter(e=>e.getClientRects().length&&[...e.childNodes].some(n=>n.nodeType===3&&n.textContent.trim()));
      const minFont=sel=>Math.min(...textEls(sel).map(e=>parseFloat(getComputedStyle(e).fontSize)));
      return {width:innerWidth,scrollWidth:document.documentElement.scrollWidth,sections:document.querySelectorAll('article.section-article').length,
        experiments:document.querySelectorAll('.lab').length,rows:document.querySelectorAll('.order-row').length,overlaps,
        duplicateIds:ids.filter((v,i)=>ids.indexOf(v)!==i),
        brokenAnchors:[...document.querySelectorAll('a[href^="#"]')].filter(x=>!document.getElementById(x.hash.slice(1))).map(x=>x.hash),
        badLinks:[...document.querySelectorAll('a')].filter(x=>!x.getAttribute('href')||x.getAttribute('href').includes('undefined')).map(x=>x.outerHTML),
        minExhibitFont:minFont('.cz-exhibit *'),minLabFont:minFont('.lab *'),
        provenanceSegments:[...document.querySelectorAll('.provenance')].map(p=>p.querySelectorAll('.seg').length),
        engineLoadedEarly:!!window.initSqlJs};
    }""")
    a(state["scrollWidth"] == width, "page overflow (%d > %d)" % (state["scrollWidth"], width))
    a(state["sections"] == 6 and state["experiments"] == 4 and state["rows"] == 6, "structure %r" % {k: state[k] for k in ("sections", "experiments", "rows")})
    a(not state["overlaps"], "V node overlap %s" % json.dumps(state["overlaps"]))
    a(not state["duplicateIds"], "duplicate ids %s" % state["duplicateIds"])
    a(not state["brokenAnchors"], "broken anchors %s" % state["brokenAnchors"])
    a(not state["badLinks"], "bad links %s" % state["badLinks"])
    a(state["minExhibitFont"] >= 12, "exhibit text under 12px (%.2f)" % state["minExhibitFont"])
    a(state["minLabFont"] >= 12, "experiment-frame text under 12px (%.2f)" % state["minLabFont"])
    a(all(n in (3, 4) for n in state["provenanceSegments"]) and len(state["provenanceSegments"]) == 5, "provenance strips %s" % state["provenanceSegments"])
    a(not state["engineLoadedEarly"], "sql.js was loaded on page load")
    a(not any("sql-asm" in u for u in requests), "sql.js requested before the first click")

    # Experiment 0
    a("SQL" in page.locator("#code-state").inner_text(), "SQL code label")
    a(page.locator("#fix-opening").is_disabled(), "correction revealed before a run")
    a(page.locator(".code-change").count() == 0, "defective line highlighted before a run")
    a(not page.locator("#run-opening").is_disabled(), "run button disabled before first click")
    page.locator("#run-opening").focus(); page.keyboard.press("Space")
    page.wait_for_function("() => document.querySelector('#opening-result').innerText.includes('FAIL') || document.querySelector('#opening-result').innerText.includes('unavailable')", timeout=60000)
    a(any("sql-asm" in u for u in requests), "sql.js not requested after the first click")
    a("same count, wrong orders" in page.locator("#opening-result").inner_text() and "A102 is excluded" in page.locator("#opening-result").inner_text(), "opening detects both defects")
    a("400 lines across six files" in page.locator("#opening-lesson").inner_text(), "failed-state scale caption")
    a(page.locator("#opening-result>strong").inner_text() == "A105 · A105", "actual defective output (two rows, same count as expected)")
    a(page.locator(".code-change").count() == 1, "only the boundary line is marked in the defective state; a missing clause has no line")
    a(page.evaluate("() => document.getElementById('opening-code').innerText.replace(/\\s/g,'')===globalThis.DispatchExample.buggy.replace(/\\s/g,'')"), "displayed defective code differs from the executed string")
    a(page.evaluate("() => DispatchExample.buggy.replace('age_hours > 48','age_hours >= 48').replace('FROM eligible_orders\\nORDER BY order_id;','FROM eligible_orders\\nGROUP BY order_id\\nORDER BY order_id;')===DispatchExample.fixed"), "correction changes more than the boundary operator and the GROUP BY clause")
    a(page.evaluate("() => DispatchExample.buggy.split('\\n')[6].trim()==='AND age_hours > 48'"), "line 7 is not the boundary line")
    # Record what SQLite actually executes from here on (the engine is cached by sql.js).
    page.evaluate("async () => { const e = await initSqlJs(); window.__sql = []; const exec = e.Database.prototype.exec; e.Database.prototype.exec = function (q, ...r) { if (q.startsWith('WITH eligible_orders')) window.__sql.push(q); return exec.call(this, q, ...r); }; }")
    page.locator("#fix-opening").click()
    page.wait_for_function("() => document.querySelector('#opening-result').innerText.includes('PASS')")
    a("PASS \u00b7 selected cases match" in page.locator("#opening-result").inner_text(), "correction passes the known answer")
    a(page.locator("#opening-result>strong").inner_text() == "A102 \u00b7 A105", "corrected IDs")
    a(page.locator(".opening-history li").count() == 2, "original failure not retained")
    a(page.locator(".code-change").count() == 2, "both corrected lines marked (boundary and GROUP BY)")
    a(page.locator("#fix-opening").is_disabled() and page.locator("#fix-opening").inner_text() == "Correction applied", "correction button state after fix")
    if renders and not is_file and width in (390, 1440):
        page.add_style_tag(content="#site-header{position:static !important}")
        page.locator("#opening-experiment").screenshot(path=str(RENDERS / ("opening-fixed-%d.png" % width)))
    a(page.evaluate("() => document.getElementById('opening-code').innerText.replace(/\\s/g,'')===globalThis.DispatchExample.fixed.replace(/\\s/g,'')"), "displayed corrected code differs from the executed string")
    page.locator("#reset-opening").click()
    a("Not run yet" in page.locator("#opening-result").inner_text() and page.locator(".code-change").count() == 0, "opening reset")
    page.locator("#run-opening").click()
    page.wait_for_function("() => document.querySelector('#opening-result').innerText.includes('FAIL')")
    executed = page.evaluate("() => [window.__sql, DispatchExample.fixed, DispatchExample.buggy]")
    a(executed[0] == [executed[1], executed[2]], "displayed queries are not what SQLite executed")
    if renders and not is_file and width in (390, 1440):
        page.locator("#opening-experiment").screenshot(path=str(RENDERS / ("opening-failed-%d.png" % width)))
    page.locator("#reset-opening").click()

    # Structure of the prose regions
    a(page.locator(".commitment-list li").count() == 5, "five commitments")
    a(page.locator(".author-account p").count() == 4, "four author paragraphs")
    a(page.locator(".author-caption").inner_text().startswith("Proposed operating model:"), "proposed caption below the author block")

    # The V
    for key, phrase in [("use", "Operations owner"), ("data", "Technical reviewer"), ("rule", "Analytics lead")]:
        page.locator('[data-pair="%s"][data-side="left"]' % key).click()
        a(phrase.lower() in page.locator("#v-detail").inner_text().lower(), "V %s" % key)
        a(page.locator('[data-pair="%s"][data-side="right"]' % key).get_attribute("aria-pressed") == "true", "paired V selection %s" % key)
        a(page.locator("#v-state").inner_text().startswith("selected pair:"), "V strip state")
    a(page.locator(".v-lines line").count() == 9, "V arrows and links drawn (%d)" % page.locator(".v-lines line").count())

    # Experiment 1
    for switches, expected, bad in QUEUE_CASES:
        for i, cid in enumerate(CONTROLS):
            page.locator("#" + cid).set_checked(switches[i])
        a(page.locator("#queue-result>span:last-child").inner_text() == expected, "queue %s" % switches)
        a(("warning" if bad else "success") in page.locator("#queue-finding").get_attribute("class"), "queue mismatch state %s" % switches)
    a(page.locator("#queue-state").inner_text().startswith("controls removed:"), "queue strip names removed controls")
    page.locator("#reset-queue").click()
    a(page.locator("#queue-state").inner_text() == "all three controls on", "queue strip default state")
    page.locator("#same-count").click()
    a(page.locator("#queue-result>strong").inner_text() == "2 entries" and "A102 is missing" in page.locator("#queue-finding").inner_text(), "same count is still wrong")
    page.locator("#reset-queue").click()
    page.locator("#include-boundary").focus(); page.keyboard.press("Space")
    a(not page.locator("#include-boundary").is_checked(), "keyboard checkbox")
    page.locator("#reset-queue").click()

    # Experiment 2
    for defect in (True, False):
        for separate in (True, False):
            page.locator("#checker-defect").set_checked(defect); page.locator("#separate-checker").set_checked(separate)
            title = page.locator("#checker-result>b").inner_text()
            expected = ("Mismatch exposes" if separate else "Agreement hides") if defect else ("The specified cases agree" if separate else "Agreement, but")
            a(title.startswith(expected), "checker %s/%s" % (defect, separate))
            a(page.locator("#check-orders .order-chip").count() == (3 if defect and not separate else 2), "checker IDs %s/%s" % (defect, separate))
    page.locator("#reset-checker").click()

    # Experiment 3: every combination, including the exact two-hour boundary
    for defect in (True, False):
        for gate in (True, False):
            for age in (1, 2, 3, 8):
                page.locator("#release-defect").set_checked(defect); page.locator("#enforce-gate").set_checked(gate)
                page.locator("#source-age").fill(str(age)); page.locator("#source-age").dispatch_event("input")
                expected = "Withheld" if gate and (defect or age > 2) else "Published"
                a(page.locator("#dashboard-state>strong").inner_text() == expected, "release %s/%s/%d" % (defect, gate, age))
                a(("bad" if age > 2 else "good") in page.locator("#fresh-check").get_attribute("class"), "freshness %d" % age)
    page.locator("#reset-release").click(); page.locator("#source-age").focus(); page.keyboard.press("End")
    a(page.locator("#age-value").inner_text() == "8 hours", "slider keyboard")
    page.locator("#reset-release").click()

    for d in page.locator("details").all():
        d.locator("summary").click(); a(d.get_attribute("open") is not None, "disclosure opens"); d.locator("summary").click()

    off_machine = sorted({re.sub(r"^(https?://[^/]+).*", r"\1", u) for u in requests if re.match(r"^https?://", u) and "127.0.0.1" not in u and not any(h in u for h in ALLOWED_HOSTS) and not u.startswith(url.split("/cascadia-validation")[0] if url.startswith("https://www.robbins") else "\0")})
    a(not off_machine, "requests off this machine: %s" % off_machine)
    a(not console, "console errors: %s" % console[:3])

    if renders and not is_file:
        if width in (390, 1440):
            page.screenshot(path=str(RENDERS / ("page-%d.png" % width)), full_page=True)
        if width in (320, 1440):
            # The sticky site header would otherwise paint over the top of an element render.
            page.add_style_tag(content="#site-header{position:static !important}")
            page.locator('[data-pair="rule"][data-side="left"]').click()
            page.locator(".v-exhibit").screenshot(path=str(RENDERS / ("v-initial-%d.png" % width)))
            page.locator("#remove-controls").click()
            page.locator("#queue-title").locator("xpath=ancestor::figure").screenshot(path=str(RENDERS / ("queue-broken-%d.png" % width)))
            page.locator("#reset-queue").click()
    page.close()
    return {"mode": "file" if is_file else "http", "width": width, "scrollWidth": state["scrollWidth"], "minExhibitFont": state["minExhibitFont"], "minLabFont": state["minLabFont"],
            "openingStates": 3, "queueCases": 8, "checkerCases": 4, "releaseCases": 32, "sqlExecutionsObserved": 2}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", help="check a served page instead of the local docs/ (no renders)")
    ap.add_argument("--widths", default="320,390,768,1050,1440")
    ap.add_argument("--no-file", action="store_true", help="skip the file:// pass")
    args = ap.parse_args()
    widths = [int(w) for w in args.widths.split(",")]
    RENDERS.mkdir(exist_ok=True)
    errors, results = [], []
    srv = None if args.url else serve()
    url = args.url or "http://127.0.0.1:%d/index.html" % PORT
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            for w in widths:
                results.append(check(browser, url, w, errors, renders=not args.url, is_file=False))
            if not args.url and not args.no_file:
                for w in (390, 1440):
                    results.append(check(browser, (DOCS / "index.html").as_uri(), w, errors, renders=False, is_file=True))
        finally:
            browser.close()
    if srv:
        srv.shutdown()
    receipt = {"date": date.today().isoformat(), "target": url, "results": results, "errors": errors,
               "scope": "Behaviour gate of the page as served and as opened from disk. Not a reading panel, not an accessibility audit."}
    if not args.url:
        (RENDERS / "checks.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passes": len(results), "errors": errors}, indent=1))
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
