# v0.1.99: merge request and to-do rows (ScopedList) leave the plugin, so each
# shows a quiet arrow at its right (dim, accent on row hover) and a tip saying
# where it opens, by Settings > Open links in. Settings help copy updated.
# Usage: run199.py <src>
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from fixtures import BOARD
P = "group/app"
h = Harness(sys.argv[1], {"id": "odevvy.gitlabby", "settingsRevision": 2, "defaultProject": P, "defaultCollapsed": [], "boardStates": {}, "refreshIntervalSec": 60})
h.ev("panel.availableCardHeight = 620; panel.availableCardWidth = 1020")
h.ev("root.opened = true"); h.spin(60); h.answer("board", BOARD); h.spin(300)
def named(n): return h.visible(lambda it: it.objectName() == n)
def mr(i): return {"iid": i, "title": "MR %d" % i, "url": "https://gitlab.com/%s/-/merge_requests/%d" % (P, i), "project": P, "sourceBranch": "b%d" % i,
                   "author": {"username": "alice", "name": "Alice", "avatar": ""}, "reviewers": [], "draft": False, "detailedMergeStatus": "mergeable", "pipeline": None}
h.ev("root.showView('mrs')"); h.spin(150)
h.answer("mrs", {"state": "ready", "message": "", "scope": "all", "updatedAt": "2026-11-05T15:00:00Z", "review": [mr(1)], "mine": [mr(2)]}); h.spin(300)
rows, hints = named("mrRow"), named("openHint")
h.ok("H1 every MR row has the open hint", len(rows) == 2 and len(hints) == 2, (len(rows), len(hints)))
h.ok("H2 the hint is the arrow glyph", all(x.property("text") == "\u2197" for x in hints))
def col(it): return h.ev("(function(o){ return String(o.color) })", ) if False else str(it.property("color").name())
dim, acc = h.ev("String(root.dim)"), h.ev("String(root.accent)")
QTest.mouseMove(h.win, QPoint(1, 1)); h.spin(80)
h.ok("H3 idle hint is dim", col(hints[0]) == dim and col(hints[1]) == dim, (col(hints[0]), dim))
hint0 = sorted(hints, key=lambda it: it.mapToScene(QPointF(0, 0)).y())[0]
row0 = sorted(rows, key=lambda it: it.mapToScene(QPointF(0, 0)).y())[0]
r0 = row0.mapToScene(QPointF(0, 0)); a0 = hint0.mapToScene(QPointF(0, 0))
h.ok("H4 hint sits at the row's right edge", a0.x() + hint0.width() <= r0.x() + row0.width() and a0.x() > r0.x() + row0.width() * 0.8, (a0.x(), r0.x(), row0.width()))
QTest.mouseMove(h.win, h.scene(row0, 0.3, 0.5)); h.spin(700)
h.ok("H5 row hover lights the hint", col(hint0) == acc, (col(hint0), acc))
def hint_tips(visible_only=True):
    out = []
    for it in h.walk():
        for c in it.children():
            if c.objectName() == "openHintTip" and (c.property("visible") or not visible_only): out.append(c)
    return out
tips = hint_tips()
h.ok("H6 browser mode tip", [t.property("text") for t in tips] == ["Opens in a browser tab"], [t.property("text") for t in tips])
h.ev("root.persist({ openLinks: 'app' })"); h.spin(60)
_t = [x.property("text") for x in hint_tips(False)]
h.ok("H7 app mode tip", h.ev("root.linkMode") == "app" and _t and all(x == "Opens in an app window" for x in _t), (h.ev("root.linkMode"), _t))
# Clicks unchanged: the row still opens its link (Board.openUrl)
h.ev("root.persist({ openLinks: 'browser' })"); h.spin(40)
h.ok("H8 to-do rows share the same delegate (ScopedList)", h.ev("todoView.names.row") == "todoRow")
# Settings copy
NOTE = "Board issues still open inside GitLabby. Merge requests, to-dos, and Open in browser leave the plugin. They open in a browser tab, or in an app window with no tabs (needs a Chromium-based browser)."
h.ev("root.showView('settings')"); h.spin(150); h.answer("whoami", {"state": "ready", "message": "", "user": "o_devvy"}); h.spin(80)
n = named("linkNote")
h.ok("S1 settings link note copy", len(n) == 1 and n[0].property("text") == NOTE, [x.property("text") for x in n])
h.ok("S2 the note wraps inside the settings width", bool(n) and n[0].property("lineCount") >= 2 and n[0].property("paintedWidth") <= n[0].width() + 1, (n[0].property("lineCount"), n[0].property("paintedWidth"), n[0].width()))
h.ok("S3 no em dash in the note", "\u2014" not in NOTE)
sys.exit(h.finish())
