# v0.1.54: a quieter Merge requests view (v152 design, direction A). No footer;
# a quiet "read-only · updated HH:MM" note beside the title; the scope as two
# text tabs, the current one underlined in the accent; plain quiet counts; the
# empty line quiet; the focused row a faint fill and a short accent bar, no
# outline; the status as coloured text, no pill; the meta line and age quiet.
# Usage: run154.py <src> [outdir]   (previews: mrs)
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from PySide6.QtGui import QColor
src = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else None
ALL = []
def ok(n, c, e=""): ALL.append(bool(c)); h.ok(n, c, e)
P = "group/app"
BOARD = {"state": "ready", "project": P, "updatedAt": "2026-10-31T13:20:00Z", "message": "", "labelColors": {}, "boards": [{"id": 1, "name": "Dev"}], "board": {"id": 1, "name": "Dev"}, "fallback": False,
  "columns": [{"name": "Open", "kind": "open", "issues": []}, {"name": "Closed", "kind": "closed", "issues": []}]}
def mr(iid, title, status):
    return {"iid": iid, "title": title, "url": "https://gitlab.com/%s/-/merge_requests/%d" % (P, iid), "draft": False, "project": P, "branch": "b%d" % iid,
            "updatedAt": "2026-10-31T13:00:00Z", "status": status, "author": {"username": "o", "name": "odevvy", "avatar": ""}, "pipeline": None, "reviewers": []}
ANS = {"state": "ready", "message": "", "scope": "all", "updatedAt": "2026-10-31T13:20:00Z", "review": [], "mine": [mr(132, "docs: apply #126", "mergeable"), mr(131, "feat: alerts", "conflict")]}
h = Harness(src, {"id": "odevvy.gitlabby", "settingsRevision": 2, "defaultProject": P, "defaultCollapsed": []})
h.ev("panel.availableCardHeight = 900; panel.availableCardWidth = 1460")
h.ev("root.opened = true"); h.spin(60); h.answer("board", BOARD); h.spin(150)
h.ev("root.showView('mrs')"); h.spin(80); h.answer("mrs", ANS); h.spin(150)
QTest.mouseMove(h.win, QPoint(1, 1)); h.spin(80)
mv = h.ev("mrsView")
same = lambda a, c: abs(a.redF() - c.redF()) < 0.01 and abs(a.greenF() - c.greenF()) < 0.01 and abs(a.blueF() - c.blueF()) < 0.01
col = lambda k: h.ev("root." + k)
pv = lambda it, k: h.ev(k, QQmlEngine.contextForObject(it), it)
x_of = lambda it: it.mapToScene(QPointF(0, 0)).x()
y_of = lambda it: it.mapToScene(QPointF(0, 0)).y()
inside = lambda pred: [it for it in h.visible(pred) if mv.isAncestorOf(it)]
named = lambda n: sorted(inside(lambda it: it.objectName() == n), key=lambda it: (round(y_of(it)), x_of(it)))
texts = lambda: [str(it.property("text") or "") for it in inside(lambda it: it.inherits("QQuickText"))]
ok("Q1 no footer: the keys are not spelled out under the lists", not any("j/k" in t or "Enter opens" in t for t in texts()), [t for t in texts() if "\u00b7" in t])
head = [it for it in inside(lambda it: it.inherits("QQuickText") and it.property("text") == "Merge requests")]
# A quiet "read-only": the note on the left, or (v0.1.71) a chip after the header's tabs (run171).
ro = h.visible(lambda it: it.inherits("QQuickText") and str(it.property("text") or "").startswith("read-only"))
ok("Q2 says read-only, quietly, once (the header's tab names the view)", len(ro) == 1 and len(head) == 0 and same(ro[0].property("color"), col("quiet")), [r.property("text") for r in ro])
pills = inside(lambda it: it.metaObject().className().startswith("Pill"))
ok("Q3 no pills left in the view (scope, counts, status)", pills == [], [p.property("label") for p in pills])
tabs = named("scopeTab")
lines = named("scopeUnderline")
ok("Q4 two text tabs; only the current one (All projects) is underlined in the accent", [t.property("label") for t in tabs] == ["All projects", "This project"]
   and len(lines) == 1 and tabs[0].isAncestorOf(lines[0]) and same(lines[0].property("color"), col("accent")) and lines[0].height() <= 2.5)
tt = lambda t: next(c for c in h.walk(t) if c.inherits("QQuickText"))
ok("Q5 the current tab's text is the foreground, the other quiet", same(tt(tabs[0]).property("color"), col("foreground")) and same(tt(tabs[1]).property("color"), col("quiet")))
ok("Q6 the tabs sit on the right half", len(tabs) == 2 and x_of(tabs[0]) > mv.width() / 2)
cnt = named("mrsCount")
ok("Q7 section counts are plain quiet numbers", [c.property("text") for c in cnt] == ["0", "2"] and all(same(c.property("color"), col("quiet")) for c in cnt))
empty = [it for it in inside(lambda it: it.inherits("QQuickText") and it.property("text") == "Nothing waiting on your review.")]
ok("Q8 the empty line is quiet and lines up with the view's left edge", len(empty) == 1 and same(empty[0].property("color"), col("quiet")) and abs(x_of(empty[0]) + empty[0].property("leftPadding") - x_of(mv)) < 1.5)
rows = named("mrRow")
ok("Q9 no outline on any row, focused or not", len(rows) == 2 and all(pv(r, "border.width") == 0 for r in rows))
ok("Q10 the focused row: a faint fill; the other none", pv(rows[0], "color.a") > 0 and pv(rows[0], "color.a") < 0.1 and pv(rows[1], "color.a") == 0, (pv(rows[0], "color.a"), pv(rows[1], "color.a")))
bars = named("mrFocusBar")
ok("Q11 a short accent bar on the focused row's left edge only", len(bars) == 1 and rows[0].isAncestorOf(bars[0]) and same(bars[0].property("color"), col("accent"))
   and abs(x_of(bars[0]) - x_of(rows[0])) < 0.5 and bars[0].width() <= 3 and bars[0].height() < rows[0].height(), [(x_of(b), b.width(), b.height()) for b in bars])
h.key(Qt.Key_J, "j"); h.spin(40)
bars = named("mrFocusBar")
ok("Q12 j moves the bar to the next row", len(bars) == 1 and rows[1].isAncestorOf(bars[0]))
st = named("mrStatus")
ok("Q13 status is coloured text: Ready green, Conflicts in its colour, no box", [s.property("text") for s in st] == ["Ready", "Conflicts"] and all(s.inherits("QQuickText") for s in st)
   and same(st[0].property("color"), QColor("#2da160")), [s.property("text") for s in st])
meta = [it for it in inside(lambda it: it.inherits("QQuickText") and "\u00b7" in str(it.property("text") or "") and rows[0].isAncestorOf(it))]
ok("Q14 the meta line is quiet", len(meta) == 1 and same(meta[0].property("color"), col("quiet")), [m.property("text") for m in meta])
import re as _re
ages = [it for it in inside(lambda it: it.inherits("QQuickText") and _re.fullmatch(r"\d+(m|h|d|w|mo|y)", str(it.property("text") or "")))]
ok("Q15 ages are quiet", len(ages) == 2 and all(same(a.property("color"), col("quiet")) for a in ages), [a.property("text") for a in ages])
gb = inside(lambda it: it.metaObject().className().startswith("GlyphButton"))
ok("Q17 no close button of its own: the header's Board tab and Esc go back", gb == [], len(gb))
h.click(tabs[1]); h.spin(60)
ok("Q16 clicking This project moves the underline", len(named("scopeUnderline")) == 1 and tabs[1].isAncestorOf(named("scopeUnderline")[0]) and h.ev("mrsView.mode") == "project")
h.click(tabs[0]); h.spin(60); h.key(Qt.Key_K, "k"); h.spin(40)
if out: QTest.mouseMove(h.win, QPoint(1, 1)); h.spin(300); os.makedirs(out, exist_ok=True); h.grab_card(out + "/mrs.png")
print("passed %d failed %d" % (sum(ALL), len(ALL) - sum(ALL)))
h.finish()
