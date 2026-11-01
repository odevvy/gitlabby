# v0.1.64: one frame for every view: the board's width (760 at least) and a
# fixed 640 height (960 at scale 1.5), or the free height on a short screen.
# Views fit or scroll inside; switching views never resizes the popup, only a
# fold changes its width. (v0.1.34 grew Settings and Keys past the cap.) The compact
# Settings (Refresh every on one line, Start collapsed as wrapping check boxes,
# the busy row's wrap gap). Rendered at scale 1.5 (his screenshot) with the
# stubs in harness15/. Screens: 1440 tall (free 1385) and an 800 laptop (745).
# Usage: run134.py <src> [outdir]   (previews: settings-1440, settings-800,
# settings-800-end, settings-narrow, keys-1440, keys-800, keys-narrow-1440,
# board-1440, issue-1440)
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import lib
lib.HERE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "harness15")
from lib import *
src = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else None
P = "firelink21/phrase41"
COLS = [("Open", "open", None), ("research", "label", "#e5e7eb"), ("todo", "label", "#3b82f6"), ("approved", "label", "#dc2626"), ("in progress", "label", "#eab308"), ("review", "label", "#86efac"), ("Closed", "closed", None)]
LC = {"app-ui": "#9ca3af", "api": "#6366f1", "auth-mail": "#14b8a6", "research": "#e5e7eb", "todo": "#3b82f6", "approved": "#dc2626", "in progress": "#eab308", "review": "#86efac"}
def card(i, labels): return {"iid": i, "title": "Issue %d: a card title of a usual length" % i, "labels": labels, "url": "https://gitlab.com/%s/-/work_items/%d" % (P, i), "createdAt": "2026-10-29T12:00:00Z", "notes": 0, "assignees": []}
def board(n=1):
    iss = {"in progress": [card(40, ["in progress", "auth-mail"]), card(41, ["in progress"])], "review": [card(50, ["review", "api"]), card(51, ["review"])], "approved": [card(30, ["approved", "app-ui"])],
           "todo": [card(20 + k, ["todo"] + (["app-ui"] if k == 0 else [])) for k in range(3 * n)], "Closed": [card(9, [])]}
    return {"state": "ready", "project": P, "updatedAt": "2026-10-30T15:26:00Z", "labelColors": {k: {"color": v, "textColor": None} for k, v in LC.items()},
            "boards": [{"id": 7, "name": "Development"}], "board": {"id": 7, "name": "Development"}, "fallback": False, "message": "",
            "columns": [dict({"name": c, "kind": k, "issues": iss.get(c, [])}, **({"listId": i, "color": col} if col else {})) for i, (c, k, col) in enumerate(COLS)]}
LABELS = {"state": "ready", "message": "", "status": ["approved", "in progress", "research", "review", "todo"], "labels": [{"name": k, "color": v, "textColor": None} for k, v in LC.items()]}
FOUR = {P: {"busyLists": ["approved", "in progress", "review"], "bots": [{"name": "App UI", "label": "app-ui"}, {"name": "API Engineer", "label": "api"}, {"name": "Auth & Mail", "label": "auth-mail"}, {"name": "Product Lead", "label": ""}]}}
DESC = "\n\n".join(["Paragraph %d. The board should show what each bot is doing without opening every card; this stands in for a long description." % i for i in range(1, 13)])
ISSUE = {"iid": 30, "title": "Approved work for the App UI bot", "state": "opened", "labels": ["approved", "app-ui"], "url": "https://gitlab.com/%s/-/issues/30" % P,
         "description": DESC, "author": "o_devvy", "milestone": "", "assignees": [], "createdAt": "2026-10-20T12:00:00Z", "updatedAt": "2026-10-29T12:00:00Z"}
DESK, LAPTOP = 1440 - 39 - 16, 800 - 39 - 16  # free height: screen - bar - gap - margin (KeyboardPanel.qml availableCardHeight)
ALL = []
def ok(n, c, e=""): ALL.append(bool(c)); h.ok(n, c, e)
def shot(name): QTest.mouseMove(h.win, QPoint(1, 1)); h.spin(80); out and h.grab_card(os.path.join(out, name + ".png"))
cls_is = lambda it, n: it.metaObject().className().startswith(n)
def start(free, width=1460, n=1):
    global h
    h = Harness(src, {"id": "odevvy.gitlab-board", "settingsRevision": 2, "defaultProject": P, "defaultCollapsed": ["open", "research", "Closed"], "bots": FOUR})
    h.ev("panel.availableCardHeight = %d; panel.availableCardWidth = %d" % (free, width))
    h.ev("root.opened = true"); h.spin(60); h.answer("board", board(n)); h.spin(150)
def settings():
    h.ev("root.showView('settings')"); h.spin(60); h.answer("whoami", {"state": "ready", "message": "", "user": "o_devvy"}); h.spin(60)
    if h.running("labels"): h.answer("labels", LABELS); h.spin(60)
    h.spin(120)
H = lambda: h.ev("panel.contentHeight")
need = lambda: round(h.ev("keyCatcher.implicitHeight") + h.ev("panel.verticalContentInset"))
def flick(view): return next(it for it in h.walk(h.ev(view)) if cls_is(it, "QQuickFlickable"))
scrolls = lambda f: f.property("contentHeight") > f.property("height") + 0.5
vis_order = lambda its: sorted(its, key=lambda it: (round(it.mapToScene(QPointF(0, 0)).y()), it.mapToScene(QPointF(0, 0)).x()))
sv_checks = lambda: vis_order([it for it in h.visible(lambda it: it.property("clickable") is not None and it.property("on") is not None) if h.ev("settingsView").isAncestorOf(it) and not h.cls("BotsSection").isAncestorOf(it) and not (isinstance(it.property("modelData"), dict) and it.property("modelData").get("kind") in ("review", "idle"))])
busy_checks = lambda: [it for it in h.visible(lambda it: it.property("clickable") is not None and it.property("on") is not None) if h.cls("BotsSection").isAncestorOf(it)]
y_of = lambda it: it.mapToScene(QPointF(0, 0)).y()

# --- his screen: 1440 tall --------------------------------------------------------
start(DESK)
h0 = H()
W = lambda: h.ev("panel.contentWidth")
w0 = W()
ok("B1 a short board still gets the full frame: 640 (x1.5 = 960)", h0 == 960 and need() < 960, (h0, need()))
ok("W1 the frame is the board's width, 760 (x1.5 = 1140) at least", w0 >= 1140 and abs(w0 - min(1460, max(1140, h.ev("root.shownBoardWidth") + h.ev("panel.padding") * 2 + h.ev("Style.space(4)")))) <= 1, w0)
settings()
ok("S1 Settings in the same frame, scrolling what's below", H() == 960 and W() == w0 and scrolls(flick("settingsView")) == (need() > 960), (H(), W(), need()))
ok("S2 compact Settings (with 0.1.36's Alerts section) still fits under the old cap's 1198", H() < 1198, H())
row = next(it for it in h.walk(h.ev("settingsView")) if it.property("oneLine") is not None)
ok("S3 Refresh every: heading and segments on one line", row.property("oneLine") and row.property("height") < 60, row.property("height"))
cb = sv_checks()
ok("S4 Start collapsed: one check box per column (7), in two lines at most", len(cb) == 7 and len(set(round(y_of(c)) for c in cb)) <= 2, [round(y_of(c)) for c in cb])
ok("S5 the saved ones are ticked: Open, research, Closed", [c.property("on") for c in cb] == [True, True, False, False, False, False, True], [c.property("on") for c in cb])
before = len(h.ev("root.bar.shell.writes"))
h.click(cb[2])
ok("S6 a click on todo saves it to defaultCollapsed", len(h.ev("root.bar.shell.writes")) == before + 1 and "todo" in [x.lower() for x in h.ev("root.defaultCollapsed")] and sv_checks()[2].property("on"), h.ev("root.defaultCollapsed"))
h.click(sv_checks()[2])
ok("S6b and a second click takes it out again", "todo" not in [x.lower() for x in h.ev("root.defaultCollapsed")])
ys = sorted(set(round(y_of(c)) for c in cb)); bc = busy_checks(); bys = sorted(set(round(y_of(c)) for c in bc))
gap = lambda its, ys: ys[1] - ys[0] - its[0].property("height") if len(ys) > 1 else 6 * 1.5
ok("S7 rows of check boxes wrap with a small gap (space(6) = 9), Start collapsed and busy alike", abs(gap(cb, ys) - 9) < 1 and abs(gap(bc, bys) - 9) < 1, (ys, bys, cb[0].property("height")))
shot("settings-1440")
h.ev("root.showView('keys')"); h.spin(150)
ok("K1 Keys in the same frame", H() == 960 and W() == w0 and scrolls(flick("keysView")) == (need() > 960), (H(), W(), need()))
shot("keys-1440")
h.ev("root.showView('board')"); h.spin(150)
ok("J1 back to the board: nothing moves", H() == h0 and W() == w0, (H(), h0, W()))
h.ev("root.openIssue(root.columns[3].issues[0])"); h.spin(80)
h.answer("issue", {"state": "ready", "message": "", "issue": ISSUE}); h.answer("notes", {"state": "ready", "message": "", "iid": 30, "more": False, "notes": []}); h.spin(150)
ok("C1 an issue in the same frame (960), scrolling past it", H() == 960 and W() == w0, (need(), H(), W()))
shot("issue-1440")
h.ev("root.showView('board')"); h.spin(150)
ok("J2 issue -> board: the same frame", H() == h0 and W() == w0)
h.ev("root.toggleCollapsed('todo')"); h.spin(400)
ok("W2 a fold is what changes the width (and keeps the 1140 floor)", W() != w0 and W() >= 1140 and H() == 960, (W(), w0))
h.ev("root.toggleCollapsed('todo')"); h.spin(400)
for c in ["approved", "in progress", "review"]: h.ev("root.toggleCollapsed(%s)" % json.dumps(c))
h.spin(400)
ok("W3 a narrow board (most columns folded): the 760 floor (x1.5 = 1140)", W() == 1140 and h.ev("root.shownBoardWidth") + 2 * h.ev("panel.padding") < 1140, (W(), h.ev("root.shownBoardWidth")))
for c in ["approved", "in progress", "review"]: h.ev("root.toggleCollapsed(%s)" % json.dumps(c))
h.spin(400)
shot("board-1440")
h.stop_all()
# A tall board keeps the cap too.
start(DESK, n=8)
ok("C2 a tall board keeps the cap (960)", need() > 960 and H() == 960, (need(), H()))
settings()
ok("J3 tall board -> Settings: the same 960", H() == 960, H())
h.ev("root.showView('board')"); h.spin(150)
ok("J4 and back: 960 again", H() == 960)
h.stop_all()
# A narrow screen: Keys in one column, scrolling inside the 960 frame.
start(DESK, width=760)
h.ev("root.showView('keys')"); h.spin(150)
ok("K2 Keys in one column (narrow screen): the 960 frame, scrolling", need() > 960 and H() == 960 and W() == 760 and scrolls(flick("keysView")), (need(), H(), W()))
shot("keys-narrow-1440")
h.stop_all()

# --- an 800 laptop -----------------------------------------------------------------
start(LAPTOP)
settings()
ok("L1 Settings stops at the free height (745) and scrolls", H() == LAPTOP and scrolls(flick("settingsView")), (H(), need()))
shot("settings-800")
f = flick("settingsView"); f.setProperty("contentY", f.property("contentHeight") - f.property("height")); h.spin(120)
acct = [it for it in h.visible(lambda it: cls_is(it, "BoardText") and it.property("text") == "Sign out")]
pc = h.cls("KeyboardPanel")
ok("L2 scrolled to the end, Account and Sign out are inside the popup", acct and y_of(acct[0]) + acct[0].property("height") <= pc.mapToScene(QPointF(0, pc.height())).y(), acct and y_of(acct[0]))
shot("settings-800-end")
h.ev("root.showView('keys')"); h.spin(150)
ok("L3 Keys stops at 745 and scrolls", H() == LAPTOP and scrolls(flick("keysView")))
shot("keys-800")
h.ev("root.showView('board')"); h.spin(150)
ok("L4 back to the board: the same 745", H() == LAPTOP)
h.stop_all()

# --- a narrow popup: Refresh every stacks instead of overlapping ----------------------
start(DESK)
settings()
h.ev("panel.contentWidth = 470"); h.spin(150)
row = next(it for it in h.walk(h.ev("settingsView")) if it.property("oneLine") is not None)
kids = row.childItems(); head, seg = kids[0], kids[1]
ok("N1 too narrow for one line: the segments go under the heading, inside the popup", not row.property("oneLine") and seg.property("y") >= head.property("height") and seg.property("x") == 0 and seg.property("width") <= row.property("width") + 1, (seg.property("y"), seg.property("width"), row.property("width")))
shot("settings-narrow")
h.stop_all()

loops = [w for w in h.warnings if "oop" in w]
ok("Z no binding-loop warnings", not loops, loops)
ok("Z no QML warnings", not h.warnings, h.warnings[:3])
print("passed", sum(ALL), "failed", len(ALL) - sum(ALL))
sys.stdout.flush(); os._exit(0 if all(ALL) else 1)
