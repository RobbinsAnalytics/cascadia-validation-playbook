"""Text gates over the tracked files: em dashes, names, durations.

    python checks/scan_text.py

Exit 1 on any em dash in a tracked text file or any name from the list in a
tracked file. Duration hits (months, years, since) in docs/index.html and
README.md are reported and do not fail the run: the report lists each with a
one-line reason. Standard library only, so the pre-commit hook could call it.
"""
import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
TEXT_EXT = {".md", ".html", ".js", ".css", ".py", ".json", ".txt", ".toml", ".yml", ".yaml", ".svg", ".gitignore", ".gitattributes"}
SELF = pathlib.Path("checks/scan_text.py")
# The guard kit is copied verbatim from cascadia-standards and hash-pinned in its
# hook_manifest.json; its files carry em dashes in comments and are never edited
# per repo, so the em-dash gate does not read them. Everything else tracked is read.
KIT = (".githooks/", ".claude/hooks/", ".gitattributes")
NAMES = re.compile(r"\b(T-Mobile|Stryker|McDonald|Simmering|Knopf|Nicholson|Courtney|Chris|Brett|Jenny|Sam)\b", re.I)
DURATION = re.compile(r"\b(months?|years?|since)\b", re.I)
EM_DASH = chr(0x2014)  # spelled as a code point so this file passes its own gate


def tracked():
    out = subprocess.run(["git", "ls-files", "-z"], cwd=REPO, capture_output=True, check=True).stdout
    return [pathlib.Path(p) for p in out.decode("utf-8").split("\0") if p]


def main():
    failures, duration_hits = [], []
    for rel in tracked():
        path = REPO / rel
        if rel.suffix not in TEXT_EXT and rel.name not in TEXT_EXT:
            continue
        if rel.as_posix().startswith(KIT):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for n, line in enumerate(text.split("\n"), 1):
            if EM_DASH in line:
                failures.append("%s:%d: em dash" % (rel.as_posix(), n))
            if rel != SELF and (m := NAMES.search(line)):
                failures.append("%s:%d: name %r" % (rel.as_posix(), n, m.group(0)))
            if rel.as_posix() in ("docs/index.html", "README.md") and (m := DURATION.search(line)):
                duration_hits.append("%s:%d: %r in: %s" % (rel.as_posix(), n, m.group(0), line.strip()[:160]))
    for h in duration_hits:
        print("DURATION  " + h)
    for f in failures:
        print("FAIL      " + f)
    print("scan_text: %d failure(s), %d duration hit(s) to explain" % (len(failures), len(duration_hits)))
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
