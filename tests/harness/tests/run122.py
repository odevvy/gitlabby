# v0.1.22: busy/idle markers per bot (settings.bots[project]), from the board on screen.
# Usage: run122.py <src> [bots.png none.png]
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from PySide6.QtGui import QColor
pngs = sys.argv[2:5]
h = Harness(sys.argv[1], {"id": "odevvy.gitlab-board", "settingsRevision": 2, "defaultProject": "firelink21/phrase41"})
def iss(iid, title, labels, notes=0): return {"iid": iid, "title": title, "labels": labels, "url": "https://gitlab.com/firelink21/phrase41/-/issues/%d" % iid, "createdAt": "2026-10-29T09:00:00Z", "notes": notes, "assignees": []}
C = {"todo": "#64748b", "approved": "#0ea5e9", "in progress": "#f59e0b", "review": "#a855f7"}
def board(moved=False):
    prog = [iss(114, "WORKFLOW: weekly digest wording", ["in progress"])] + ([] if moved else [iss(112, "Cover picker keyboard focus", ["in progress", "app-ui"], 2)])
    rev = [iss(113, "Stories list: paginate past 50", ["review", "api"], 1)] + ([iss(112, "Cover picker keyboard focus", ["review", "app-ui"], 2)] if moved else [])
    return {"state": "ready", "project": "firelink21/phrase41", "updatedAt": "2026-10-29T15:20:00Z", "message": "",
      "labelColors": {**{k: {"color": v, "textColor": "#ffffff"} for k, v in C.items()}, "app-ui": {"color": "#16a34a"}, "api": {"color": "#2563eb"}, "auth-mail": {"color": "#db2777"}},
      "boards": [{"id": 1, "name": "Development"}], "board": {"id": 1, "name": "Development"}, "fallback": False,
      "columns": [{"name": "Open", "kind": "open", "issues": [iss(118, "Ideas: story covers v2", ["app-ui"])]},
        {"name": "todo", "kind": "label", "listId": 1, "color": C["todo"], "issues": [iss(116, "Share page: copy link feedback", ["todo", "app-ui"]), iss(117, "Rate-limit magic link resend", ["todo", "auth-mail"])]},
        {"name": "approved", "kind": "label", "listId": 2, "color": C["approved"], "issues": [iss(115, "Timeline: round markers", ["approved", "app-ui"])]},
        {"name": "in progress", "kind": "label", "listId": 3, "color": C["in progress"], "issues": prog},
        {"name": "review", "kind": "label", "listId": 4, "color": C["review"], "issues": rev},
        {"name": "Closed", "kind": "closed", "issues": [iss(109, "Cover picker: 5 object covers", ["auth-mail", "in progress"])]}]}
BOTS = {"firelink21/phrase41": {"busyLists": ["approved", "in progress", "review"], "bots": [
  {"name": "App UI", "label": "app-ui"}, {"name": "API Engineer", "label": "api"}, {"name": "Auth & Mail", "label": "auth-mail"},
  {"name": "Product Lead", "label": ""}, {"name": "Spec QA", "list": "review"}]}}
rows = lambda: h.visible(lambda it: it.metaObject().className().startswith("BotsRow"))
texts = lambda: [it.property("text") for it in h.visible(lambda it: it.metaObject().className().startswith("BoardText")) if it.property("text")]
ref = lambda t: [it for it in h.visible(lambda it: it.metaObject().className().startswith("BoardText") and it.property("text") == t)]
same = lambda a, b: abs(a.redF() - b.redF()) < 0.01 and abs(a.greenF() - b.greenF()) < 0.01 and abs(a.blueF() - b.blueF()) < 0.01
def dot(name):
    t = ref(name)[0]; r = t.parentItem()
    return next(c for c in r.childItems() if c.metaObject().className().startswith("QQuickRectangle"))
def board_top(): return h.cls("BoardView").mapToScene(QPointF(0, 0)).y()

h.ev("root.opened = true"); h.spin(80); h.answer("board", board())
h0 = h.ev("keyCatcher.implicitHeight"); top0 = board_top()
under_header = lambda: h.ev("header.mapToItem(null, 0, header.height).y + root.gap")
h.ok("N1 no settings.bots: no row, and the board sits right under the header", not rows() and len(h.ev("root.botStates")) == 0 and abs(top0 - under_header()) < 1, (top0, under_header()))
if len(pngs) > 1: h.grab_card(pngs[1])
h.ev("root.settings = Object.assign({}, root.settings, { bots: " + json.dumps(BOTS) + " })"); h.spin(150)
r = rows()
h.ok("B1 configured for this project: the row shows under the header", len(r) == 1 and r[0].mapToScene(QPointF(0, 0)).y() > h.ev("header.y"))
h.ok("B2 the popup grows by exactly the row (no stale height), the board sits below it",
     abs(h.ev("keyCatcher.implicitHeight") - h0 - (r[0].height() + h.ev("root.gap"))) < 1 and board_top() >= r[0].mapToScene(QPointF(0, r[0].height())).y(), (h.ev("keyCatcher.implicitHeight"), h0, r[0].height()))
t = texts()
h.ok("B3 App UI: #115 approved · #112 in progress", "#115 approved" in t and "· #112 in progress" in t, t)
h.ok("B4 #113 (api) in review is Spec QA's alone (v0.1.49): it shows once, 'in review' once, API Engineer idle", t.count("#113") == 1 and t.count("in review") == 1 and "#113 review" not in t and [s["state"] for s in h.ev("root.botStates") if s["name"] == "API Engineer"] == ["idle"], t)
h.ok("B5 Auth & Mail idle (todo and Closed don't count)", [s["state"] for s in h.ev("root.botStates") if s["name"] == "Auth & Mail"] == ["idle"] and "#117 todo" not in t and not [x for x in t if "#109" in x])
h.ok("B6 Product Lead owns #114 (no owner label), 'in progress' said once; #118 in Open doesn't count", "#114" in t and "in progress" in t and not [x for x in t if "#118" in x])
acc, dim = h.ev("root.accent"), h.ev("root.dim")
pen = lambda n: h.ev("border.color", QQmlEngine.contextForObject(dot(n)), dot(n))
col = lambda hexs: QColor(hexs)
h.ok("B7 dots (v0.1.29): filled = working, ring = waiting, in the column's color; dim ring = idle",
     same(dot("App UI").property("color"), col(C["in progress"])) and same(dot("Spec QA").property("color"), col(C["review"])) and same(dot("Product Lead").property("color"), col(C["in progress"]))
     and dot("API Engineer").property("color").alpha() == 0 and same(pen("API Engineer"), dim)
     and dot("Auth & Mail").property("color").alpha() == 0 and same(pen("Auth & Mail"), dim),
     [dot(n).property("color").name() for n in ("App UI", "Spec QA", "Product Lead", "API Engineer")])
h.ok("B8 idle names are dim, busy ones bold", same(ref("Auth & Mail")[0].property("color"), dim) and ref("App UI")[0].property("font").bold())
if pngs: h.grab_card(pngs[0])
h.click(ref("· #112 in progress")[0])
h.ok("C1 clicking #112 opens that issue", h.ev("root.view") == "issue" and h.ev("issueView.issue.iid") == 112 and not rows())
h.stop_all(); h.ev("root.back()"); h.spin(80)
h.ok("C2 back on the board, the row is back", len(rows()) == 1)
h.ev("root.refresh()"); h.answer("board", board(moved=True)); h.spin(100)
t = texts()
h.ok("U1 a refresh updates it: #112 in review is Spec QA's alone; App UI now waits on #115: a ring in approved's color", "· #112 review" not in t and "in approved" in t and dot("App UI").property("color").alpha() == 0 and same(pen("App UI"), col(C["approved"])), t)
h.ok("U2 Spec QA lists both reviews", "· #112" in t)
one = r[0].height(); grown = h.ev("keyCatcher.implicitHeight")
wide = json.loads(json.dumps(BOTS)); wide["firelink21/phrase41"]["bots"][3]["name"] = "Product Lead (triage, specs, planning, release notes, and everything else nobody owns yet on this board)"
h.ev("root.settings = Object.assign({}, root.settings, { bots: " + json.dumps(wide) + " })"); h.spin(150)
r = rows()
h.ok("W1 a longer row wraps to two lines and the popup grows with it, live", r[0].height() > one + 5 and abs(h.ev("keyCatcher.implicitHeight") - grown - (r[0].height() - one)) < 1 and board_top() >= r[0].mapToScene(QPointF(0, r[0].height())).y(), (one, r[0].height()))
if len(pngs) > 2: h.grab_card(pngs[2])
h.ev("root.settings = Object.assign({}, root.settings, { bots: {} })"); h.spin(150)
h.ok("H1 config removed: row gone, height back to before (no stale height)", not rows() and abs(h.ev("keyCatcher.implicitHeight") - h0) < 1 and abs(board_top() - top0) < 1, (h.ev("keyCatcher.implicitHeight"), h0))
h.ev("root.settings = Object.assign({}, root.settings, { bots: " + json.dumps({"other/project": BOTS["firelink21/phrase41"]}) + " })"); h.spin(100)
h.ok("H2 configured for another project only: no row", not rows())
h.ev("root.settings = Object.assign({}, root.settings, { bots: " + json.dumps(BOTS) + " })"); h.spin(100)
h.ev("root.showView('settings')"); h.spin(80)
h.ok("H3 only on the board view", not rows())
h.ev("root.back()"); h.spin(80); h.ev("root.boardState = 'loading'"); h.spin(80)
h.ok("H3b hidden while the board isn't ready, and takes no space", not rows() and abs(h.ev("botsRow.height")) < 0.5 and abs(board_top() - under_header()) < 1)
h.ev("root.boardState = 'ready'"); h.spin(80)
h.ev("root.back()"); h.spin(80)
h.ok("H4 settings keeps the bots entry when the plugin saves", (h.ev("root.persist(); root.settings.bots") or {}).get("firelink21/phrase41") is not None)
sys.exit(h.finish())
