# v0.1.61: calm tooltips. Every IconTip (header icons, fold strips and column
# headers, ...) waits 500 ms of hovering, and none shows while a column folds
# (root.folding): the fold or unfold slides another target under the cursor,
# and its tip comes 500 ms after the fold ends, only if the cursor is still on it.
# Usage: run161.py <src>
import sys, os, time; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
src = sys.argv[1]
P = "firelink21/phrase41"
def iss(iid, labels): return {"iid": iid, "title": "Issue %d" % iid, "labels": labels, "url": "https://gitlab.com/%s/-/issues/%d" % (P, iid), "createdAt": "2026-10-31T09:00:00Z", "notes": 0, "assignees": []}
def col_(n, i, k): return {"name": n, "kind": "label", "listId": i, "color": "#5b9bd5", "issues": [iss(100 * i + j, [n]) for j in range(k)]}
BOARD = {"state": "ready", "project": P, "updatedAt": "2026-10-31T13:20:00Z", "message": "", "labelColors": {}, "boards": [{"id": 1, "name": "Development"}], "board": {"id": 1, "name": "Development"}, "fallback": False,
         "columns": [{"name": "Open", "kind": "open", "issues": []}] + [col_(n, i + 1, k) for i, (n, k) in enumerate([("research", 1), ("todo", 3), ("review", 1)])] + [{"name": "Closed", "kind": "closed", "issues": []}]}
h = Harness(src, {"id": "odevvy.gitlabby", "settingsRevision": 2, "defaultProject": P, "defaultCollapsed": ["open", "closed"]})
h.ev("panel.availableCardHeight = 1200; panel.availableCardWidth = 2400")
h.ev("root.opened = true"); h.spin(60); h.answer("board", BOARD); h.spin(300)
def tips(): return [str(c.property("text")) for it in h.walk() for c in it.children() if c.metaObject().className().startswith("IconTip") and c.property("visible")]
def tip_item(text): return next(it for it in h.walk() for c in it.children() if c.metaObject().className().startswith("IconTip") and c.property("text") == text)
def away(): QTest.mouseMove(h.win, QPoint(1, 1)); h.spin(80)
def wait_tip(item, fx=0.5):
    away(); QTest.mouseMove(h.win, h.scene(item, fx)); h.spin(450); early = tips(); h.spin(200); return early, tips()
early, late = wait_tip(h.ev("header.refreshButton"))
h.ok("H0 a header icon's tip waits: none after 450 ms, there after 650", early == [] and late == ["Refresh (r)"], (early, late))
early, late = wait_tip(tip_item("Collapse todo"), 0.05)
h.ok("H1 a column header's tip waits the same", early == [] and late == ["Collapse todo"], (early, late))
def fold(label):
    seen = []; QTest.mouseClick(h.win, Qt.LeftButton, Qt.NoModifier, h.last)
    folded = h.ev("root.folding"); t = time.perf_counter()
    while h.ev("root.folding") and time.perf_counter() - t < 1:
        h.spin(15); seen += tips()
    h.spin(400); after400 = tips(); h.spin(250)
    return folded, seen, after400, tips()
h.last = h.scene(tip_item("Collapse todo"), 0.05)
QTest.mouseMove(h.win, h.last); h.spin(650)
folded, seen, after400, last = fold("todo")
h.ok("F0 a click on the header folds: no tip at all while it folds", folded and seen == [], seen)
h.ok("F1 nor in the first 400 ms after the fold", after400 == [], after400)
h.ok("F2 then the strip now under the cursor shows its own tip", last == ["Expand todo"], last)
folded, seen, after400, last = fold("todo")
h.ok("F3 unfolding the same way: no tip while it folds or just after, then the header's", folded and seen == [] and after400 == [] and last == ["Collapse todo"], (seen, after400, last))
away(); h.spin(100)
h.ok("F4 the cursor gone: no tip", tips() == [], tips())
h.finish()
fails = [n for n, c in h.results if not c]
print("passed %d failed %d" % (len(h.results) - len(fails), len(fails)))
sys.exit(1 if fails else 0)
