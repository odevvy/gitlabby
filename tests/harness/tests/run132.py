# v0.1.32: Review cards show their merge request's head pipeline (board-fetch adds
# card.pipeline {status, url, mr}): a glyph per status in its color, a tooltip
# saying which and on which MR, a click that opens the pipeline (https only) and
# not the issue; nothing for cards without one or with an unknown status.
# Usage: run132.py <src> [outdir]   (previews: review-pipelines, review-tip, review-tip-nolink)
import sys, os, json, copy; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from fixtures import BOARD
out = sys.argv[2] if len(sys.argv) > 2 else None
h = Harness(sys.argv[1], {"id": "odevvy.gitlabby", "settingsRevision": 2, "defaultProject": "group/app", "defaultCollapsed": ["closed"]})
P = "https://gitlab.com/group/app/-/pipelines/"
def card(iid, title, pipeline=None, **kw):
    c = {"iid": iid, "title": title, "labels": ["review"], "url": "https://gitlab.com/group/app/-/issues/%d" % iid,
         "createdAt": "2026-10-27T12:00:00Z", "notes": kw.get("notes", 0), "assignees": kw.get("assignees", [])}
    if pipeline is not None: c["pipeline"] = pipeline
    return c
people = [{"username": u, "name": u.title(), "avatar": ""} for u in ("ana", "bo", "cy")]
review = [card(3, "Passed: an open MR", {"status": "passed", "url": P + "31", "mr": "!31"}, notes=4, assignees=people),
          card(4, "Failed on the merged MR", {"status": "failed", "url": P + "42", "mr": "!42"}, notes=1),
          card(7, "Running", {"status": "running", "url": P + "77", "mr": "!77"}),
          card(8, "Pending", {"status": "pending", "url": P + "88", "mr": "!88"}),
          card(10, "Canceled, link not https", {"status": "canceled", "url": "", "mr": "!101"}),
          card(5, "No merge request"),
          card(9, "A manual pipeline", {"status": "manual", "url": P + "91", "mr": "!91"})]
board = copy.deepcopy(BOARD)
for c in board["columns"]:
    if c["name"] == "review": c["issues"] = review
h.ev("root.opened = true"); h.spin(80); h.answer("board", board); h.spin(200)
marks = lambda: [it for it in h.walk() if it.metaObject().className().startswith("PipelineMark")]
def mark(iid):
    for m in marks():
        p = h.ev("(function(m){ return m.pipeline ? m.pipeline.mr : '' })", obj=m)
        if m.property("pipeline") is not None and (m.property("pipeline").toVariant() if hasattr(m.property("pipeline"), "toVariant") else m.property("pipeline")) == next((c.get("pipeline") for c in review if c["iid"] == iid), "x"): return m
    return None
want = {3: ("\uf058", "#2da160", "Pipeline passed on !31: open it on GitLab"), 4: ("\uf057", "#ec5941", "Pipeline failed on !42: open it on GitLab"),
        7: ("\uf192", "#428fdc", "Pipeline running on !77: open it on GitLab"), 8: ("\uf017", "#c17d10", "Pipeline pending on !88: open it on GitLab"),
        10: ("\uf05e", "#89888d", "Pipeline canceled on !101")}
shown = {}
for m in marks():
    if not m.isVisible(): continue
    pv = m.property("pipeline"); pv = pv.toVariant() if hasattr(pv, "toVariant") else pv
    iid = next(c["iid"] for c in review if c.get("pipeline") == pv)
    shown[iid] = m
h.ok("P1 a mark on exactly the cards with a known status (not none, not manual)", sorted(shown) == [3, 4, 7, 8, 10], sorted(shown))
for iid, (g, col, tip) in want.items():
    m = shown.get(iid)
    ok = m is not None and m.property("text") == g and m.property("color").name() == col
    h.ok("P2 #%d: its glyph and color" % iid, ok, m and (m.property("text"), m.property("color").name()))
# Placement: inside its card, on the footer row, left of the comment count and age, right of the avatars.
def rect(it): p = it.mapToScene(QPointF(0, 0)); return (p.x(), p.y(), p.x() + it.width(), p.y() + it.height())
def cardOf(m):
    it = m.parentItem()
    return it
m3 = shown[3]; c3 = cardOf(m3); r, rc = rect(m3), rect(c3)
meta = next(it for it in h.walk(c3) if it.metaObject().className().startswith("BoardText") and "\uf075" in (it.property("text") or ""))
people_row = next(it for it in h.walk(c3) if it.metaObject().className() == "QQuickRow")
rm, rp = rect(meta), rect(people_row)
h.ok("P3 inside the card, left of the age, right of three avatars, on their row",
     rc[0] <= r[0] and r[2] <= rc[2] and r[2] <= rm[0] - 4 and r[0] >= rp[2] + 2 and abs((r[1] + r[3]) / 2 - (rm[1] + rm[3]) / 2) < 3, (r, rm, rp, rc))
shot = lambda name: out and h.grab_card(os.path.join(out, name + ".png"))
QTest.mouseMove(h.win, QPoint(1, 1)); h.spin(80); shot("review-pipelines")
# Hover: the tooltip.
def tipOf(m): return next((t for t in m.children() if t.metaObject().className().startswith("IconTip")), None)
QTest.mouseMove(h.win, h.scene(shown[4])); h.spin(650)
t = tipOf(shown[4])
h.ok("P4 hover: 'Pipeline failed on !42: open it on GitLab'", t is not None and t.property("visible") and t.property("text") == want[4][2], t and (t.property("visible"), t.property("text")))
shot("review-tip")
QTest.mouseMove(h.win, h.scene(shown[10])); h.spin(650)
t = tipOf(shown[10])
h.ok("P5 no https link: the tooltip says so by leaving out 'open it'", t is not None and t.property("visible") and t.property("text") == want[10][2], t and t.property("text"))
shot("review-tip-nolink")
h.ok("P6 hand cursor only with a link", shown[4].childItems()[0].property("cursorShape") == Qt.PointingHandCursor and shown[10].childItems()[0].property("cursorShape") == Qt.ArrowCursor)
# Click: opens the pipeline, not the issue.
before = len(h.launched())
h.click(shown[7]); h.spin(80)
l = h.launched()
h.ok("P7 click: the pipeline opens in the browser", len(l) == before + 1 and l[-1] == ["omarchy-launch-browser", P + "77"], l[-1:] )
h.ok("P8 ...and the issue view does not", h.ev("root.view") != "issue")
h.ev("root.opened = true"); h.spin(80); h.answer("board", board); h.spin(200)
shown10 = [m for m in marks() if m.isVisible() and m.property("text") == "\uf05e"][0]
before = len(h.launched()); h.click(shown10); h.spin(80)
h.ok("P9 click without a link: nothing opens, the issue doesn't either", len(h.launched()) == before and h.ev("root.view") == "board")
# The rest of the card still opens the issue.
c4 = cardOf([m for m in marks() if m.isVisible() and m.property("text") == "\uf057"][0])
QTest.mouseClick(h.win, Qt.LeftButton, Qt.NoModifier, h.scene(c4, 0.3, 0.3)); h.spin(150)
h.ok("P10 the card itself still opens the issue", h.ev("root.view") == "issue" and h.ev("issueView.issue.iid") == 4, h.ev("root.view"))
# A refresh with the pipeline gone takes the mark away.
h.stop_all(); h.ev("root.back()"); h.ev("root.refresh()"); h.spin(40)
b2 = copy.deepcopy(board)
for c in b2["columns"]:
    if c["name"] == "review": c["issues"] = [dict(c3i, pipeline=None) if c3i["iid"] == 3 else c3i for c3i in c["issues"]]
h.answer("board", b2); h.spin(200)
h.ok("P11 a refresh without it: no mark on #3, the others stay", len([m for m in marks() if m.isVisible()]) == 4)
h.finish()
