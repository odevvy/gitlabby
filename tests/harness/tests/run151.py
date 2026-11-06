# v0.1.51: idle bots without the word. An idle bot keeps its place in the row
# with a dim hollow dot and a dim name; pointing at either says
# "Name · idle, nothing in a busy column". Busy bots are unchanged.
# Usage: run151.py <src> [outdir]   (previews: bots-idle, bots-idle-tooltip)
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
src = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else None
ALL = []
def ok(n, c, e=""): ALL.append(bool(c)); h.ok(n, c, e)
P = "group/app"
def iss(iid, labels): return {"iid": iid, "title": "Issue %d" % iid, "labels": labels, "url": "https://gitlab.com/%s/-/issues/%d" % (P, iid), "createdAt": "2026-10-31T09:00:00Z", "notes": 0, "assignees": []}
BOARD = {"state": "ready", "project": P, "updatedAt": "2026-10-31T13:20:00Z", "message": "", "labelColors": {}, "boards": [{"id": 1, "name": "Dev"}], "board": {"id": 1, "name": "Dev"}, "fallback": False,
  "columns": [{"name": "Open", "kind": "open", "issues": []},
    {"name": "in progress", "kind": "label", "listId": 3, "color": "#f59e0b", "issues": [iss(112, ["in progress", "app-ui"])]},
    {"name": "review", "kind": "label", "listId": 4, "color": "#a855f7", "issues": [iss(135, ["review", "auth-mail"])]},
    {"name": "Closed", "kind": "closed", "issues": []}]}
BOTS = {P: {"busyLists": ["in progress", "review"], "bots": [{"name": "App UI", "label": "app-ui"}, {"name": "Auth & Mail", "label": "auth-mail"}, {"name": "Spec QA", "list": "review"}]}}
h = Harness(src, {"id": "odevvy.gitlabby", "settingsRevision": 2, "defaultProject": P, "defaultCollapsed": [], "bots": BOTS})
h.ev("panel.availableCardHeight = 900; panel.availableCardWidth = 1460")
h.ev("root.opened = true"); h.spin(60); h.answer("board", BOARD); h.spin(150)
row = h.cls("BotsRow")
texts = lambda: [it.property("text") for it in h.visible(lambda it: it.metaObject().className().startswith("BoardText") and row.isAncestorOf(it))]
ref = lambda t: [it for it in h.visible(lambda it: it.metaObject().className().startswith("BoardText") and str(it.property("text")).startswith(t) and row.isAncestorOf(it))]
same = lambda a, b: abs(a.redF() - b.redF()) < 0.01 and abs(a.greenF() - b.greenF()) < 0.01 and abs(a.blueF() - b.blueF()) < 0.01
def dot(name): return next(c for c in ref(name)[0].parentItem().childItems() if c.objectName() == "busyDot")
pen = lambda n: h.ev("border.color", QQmlEngine.contextForObject(dot(n)), dot(n))
dim = h.ev("root.dim")
t = texts()
ok("I1 no 'idle' word anywhere in the row", not [x for x in t if "idle" in str(x).lower()], t)
ok("I2 the order is the setting's: App UI, Auth & Mail (idle), Spec QA", ref("App UI")[0].mapToScene(QPointF(0, 0)).x() < ref("Auth & Mail")[0].mapToScene(QPointF(0, 0)).x() < ref("Spec QA")[0].mapToScene(QPointF(0, 0)).x(), t)
ok("I3 idle: a hollow dot with a dim 1px ring, a dim name, not bold", dot("Auth & Mail").property("color").alpha() == 0 and same(pen("Auth & Mail"), dim)
   and h.ev("border.width", QQmlEngine.contextForObject(dot("Auth & Mail")), dot("Auth & Mail")) == 1
   and same(ref("Auth & Mail")[0].property("color"), dim) and not ref("Auth & Mail")[0].property("font").bold())
ok("I4 busy bots unchanged: filled dots, bold names, their issues", dot("App UI").property("color").alpha() > 0 and ref("App UI")[0].property("font").bold() and "#112" in t and "#135" in t, t)
# ToolTips are popups, not items: found as children, 400 ms delay.
tips = lambda: [str(c.property("text")) for it in h.walk() for c in it.children() if c.metaObject().className().startswith("PanelToolTip") and c.property("visible")]
ok("I5 no tooltip until pointed at", tips() == [], tips())
if out: QTest.mouseMove(h.win, QPoint(1, 1)); h.spin(100); h.grab_card(os.path.join(out, "bots-idle.png"))
QTest.mouseMove(h.win, h.scene(ref("Auth & Mail")[0])); h.spin(600)
ok("I6 pointing at the idle name: 'Auth & Mail · idle, nothing in a busy column'", tips() == ["Auth & Mail · idle, nothing in a busy column"], tips())
if out: h.grab_card(os.path.join(out, "bots-idle-tooltip.png"))
QTest.mouseMove(h.win, QPoint(1, 1)); h.spin(150)
QTest.mouseMove(h.win, h.scene(dot("Auth & Mail"))); h.spin(600)
ok("I7 pointing at its dot says it too", tips() == ["Auth & Mail · idle, nothing in a busy column"], tips())
QTest.mouseMove(h.win, QPoint(1, 1)); h.spin(150)
QTest.mouseMove(h.win, h.scene(ref("App UI")[0])); h.spin(600)
ok("I8 a busy bot's name has no idle tooltip", not [x for x in tips() if "idle" in x], tips())
QTest.mouseMove(h.win, QPoint(1, 1)); h.spin(100)
# Goes busy: the tooltip area stops, the look turns busy; idle again: back.
h.ev("root.refresh()"); B2 = json.loads(json.dumps(BOARD)); B2["columns"][1]["issues"].append(iss(140, ["in progress", "auth-mail"])); h.answer("board", B2); h.spin(150)
QTest.mouseMove(h.win, h.scene(ref("Auth & Mail")[0])); h.spin(600)
ok("I9 when it gets work: filled dot, bold name, no idle tooltip", dot("Auth & Mail").property("color").alpha() > 0 and ref("Auth & Mail")[0].property("font").bold() and not [x for x in tips() if "idle" in x], tips())
print("passed %d failed %d" % (sum(ALL), len(ALL) - sum(ALL)))
h.finish()
