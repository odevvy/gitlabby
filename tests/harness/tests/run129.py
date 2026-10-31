# v0.1.29: the redesigned Settings > Bots (a labelled form; busy columns as
# check boxes above the list; a disabled Add says why), the keyboard button
# in the header opening the grouped Keys view, and a busy dot that falls back
# to the accent when its column color is too close to the background.
# Usage: run129.py <src> [outdir]   (previews: bots-empty, bots-adding-specqa,
# bots-filled, bots-560, busy-row, header, keys)
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from PySide6.QtGui import QColor
src = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else None
P = "firelink21/phrase41"
COLS = [("Open", "open", None), ("research", "label", "#e5e7eb"), ("todo", "label", "#3b82f6"), ("approved", "label", "#dc2626"), ("in progress", "label", "#eab308"), ("review", "label", "#86efac"), ("Closed", "closed", None)]
LC = {"app-ui": "#9ca3af", "api": "#6366f1", "auth-mail": "#14b8a6", "needs-decision": "#f97316", "research": "#e5e7eb", "todo": "#3b82f6", "approved": "#dc2626", "in progress": "#eab308", "review": "#86efac"}
def card(i, labels): return {"iid": i, "title": "Issue %d" % i, "labels": labels, "url": "https://gitlab.com/%s/-/work_items/%d" % (P, i), "createdAt": "2026-10-29T12:00:00Z", "notes": 0, "assignees": []}
ISSUES = {"in progress": [card(40, ["in progress", "auth-mail"]), card(41, ["in progress"])], "review": [card(50, ["review", "api"]), card(51, ["review"]), card(52, ["review"]), card(53, ["review"]), card(54, ["review"])],
          "approved": [card(30, ["approved", "app-ui"])], "todo": [card(20, ["todo", "app-ui"])]}
def board(cols=COLS):
    return {"state": "ready", "project": P, "updatedAt": "2026-10-29T20:10:00Z", "labelColors": {k: {"color": v, "textColor": None} for k, v in LC.items()},
            "boards": [{"id": 7, "name": "Development"}], "board": {"id": 7, "name": "Development"}, "fallback": False, "message": "",
            "columns": [dict({"name": n, "kind": k, "issues": ISSUES.get(n, [])}, **({"listId": i, "color": c} if c else {})) for i, (n, k, c) in enumerate(cols)]}
LABELS = {"state": "ready", "message": "", "status": ["approved", "in progress", "research", "review", "todo"], "labels": [{"name": k, "color": v, "textColor": None} for k, v in LC.items()]}
FOUR = {P: {"busyLists": ["approved", "in progress", "review"], "bots": [{"name": "App UI", "label": "app-ui"}, {"name": "API Engineer", "label": "api"}, {"name": "Auth & Mail", "label": "auth-mail"}, {"name": "Product Lead", "label": ""}]}}
cls_is = lambda it, n: it.metaObject().className().startswith(n)
same = lambda a, b: QColor(a).name() == QColor(b).name()
ALL = []
def start(bots, width=790):
    global h, sec, sev
    s = {"id": "odevvy.gitlab-board", "settingsRevision": 2, "defaultProject": P, "defaultCollapsed": ["open", "research"]}
    if bots is not None: s["bots"] = bots
    h = Harness(src, s)
    h.ev("panel.availableCardHeight = 1000")
    if width: h.ev("panel.contentWidth = %d" % width)  # None: the popup's own width binding
    h.ev("root.opened = true"); h.spin(60); h.answer("board", board()); h.spin(120)
def settings():
    global sec, sev
    h.ev("panel.contentHeight = 1000")
    h.ev("root.showView('settings')"); h.spin(60); h.answer("whoami", {"state": "ready", "message": "", "user": "o_devvy"}); h.spin(60)
    sec = h.cls("BotsSection"); c = h.ctx_of(sec); sev = lambda code: h.ev(code, c, sec)
    if h.running("labels"): h.answer("labels", LABELS); h.spin(60)
def ok(n, c, e=""): ALL.append(bool(c)); h.ok(n, c, e)
def finish(): h.stop_all()
def shot(name): QTest.mouseMove(h.win, QPoint(1, 1)); h.spin(60); out and h.grab_card(os.path.join(out, name + ".png"))
texts = lambda: [it.property("text") for it in h.visible(lambda it: cls_is(it, "BoardText")) if it.property("text")]
pill = lambda label: [it for it in h.visible(lambda it: it.property("clickable") is not None and not cls_is(it, "LabelChip") and it.property("label") == label) if sec.isAncestorOf(it)]
fpill = lambda label: [it for it in pill(label) if sev("form").isAncestorOf(it)]
y_of = lambda it: it.mapToScene(QPointF(0, 0)).y()

# --- the busy dot: low contrast falls back to the accent ---------------------
start(FOUR)
bg = str(h.ev("String(root.background)"))
def dots():  # bot name -> its dot (the Rectangle before the name)
    out = {}
    for d in h.visible(lambda it: it.objectName() == "busyDot"):
        kids = d.parentItem().childItems(); out[str(kids[kids.index(d) + 1].property("text"))] = d
    return out
d = dots(); pen = lambda n: h.ev("border.color", QQmlEngine.contextForObject(d[n]), d[n])
ok("D1 App UI waits on #30 (approved): a ring in approved's red; Auth & Mail works on #40: filled in progress yellow",
   d["App UI"].property("color").alpha() == 0 and same(pen("App UI"), "#dc2626") and same(d["Auth & Mail"].property("color"), "#eab308"), [pen("App UI").name(), d["Auth & Mail"].property("color").name()])
shot("busy-row")
low = [(n, k, (bg[:1] + bg[3:] if len(bg) == 9 else bg) if n == "approved" else c) for n, k, c in COLS]  # approved painted as the background
h.ev("root.refresh()"); h.answer("board", board(low)); h.spin(150)
d = dots(); pen = lambda n: h.ev("border.color", QQmlEngine.contextForObject(d[n]), d[n])
ok("D2 a column colored like the background: the ring falls back to the accent", same(pen("App UI"), h.ev("root.accent")), [bg, pen("App UI").name()])
# a long name pushes "+3" to the right edge: its tooltip still stays in the row
row = h.cls("BotsRow")
long = json.loads(json.dumps(FOUR))
for n in range(0, 200, 4):  # grow the name until "+3" is in the last ~80px of the row
    long[P]["bots"][3]["name"] = "Product Lead " + "x" * n
    h.ev("root.settings = Object.assign({}, root.settings, { bots: " + json.dumps(long) + " })"); h.spin(40)
    more = [it for it in h.visible(lambda it: cls_is(it, "BoardText") and it.property("text") == "+3")]
    if more and more[0].mapToItem(row, QPointF(more[0].width(), 0)).x() > row.width() - 80: break
QTest.mouseMove(h.win, h.scene(more[0])); h.spin(700)
tip = [c for c in more[0].children() if c.metaObject().className().startswith(("PanelToolTip", "IconTip")) and c.property("visible")]
tip = tip or [c for it in h.walk() for c in it.children() if c.metaObject().className().startswith(("PanelToolTip", "IconTip")) and c.property("visible")]
end = tip and more[0].mapToItem(row, QPointF(tip[0].property("x") + tip[0].property("width"), 0)).x()
ok("D3 '+3' near the right edge: its tooltip ends inside the row", tip and end <= row.width() + 1, [end, row.width(), more[0].mapToItem(row, QPointF(0, 0)).x()])
QTest.mouseMove(h.win, QPoint(1, 1)); h.spin(100)
h.ev("root.settings = Object.assign({}, root.settings, { bots: " + json.dumps(FOUR) + " })"); h.spin(150)
finish()
# --- the keyboard button (the popup keeps its own width binding) ---------------
start(FOUR, None)
kb, rb, gb = h.ev("header.keysButton"), h.ev("header.refreshButton"), h.ev("header.gear")
x = lambda it: it.mapToScene(QPointF(0, 0)).x()
ok("K1 the keyboard button sits between refresh and the gear", kb.isVisible() and x(rb) < x(kb) < x(gb), [x(rb), x(kb), x(gb)])
shot("header")
QTest.mouseMove(h.win, h.scene(kb)); h.spin(900)
tips = [str(c.property("text")) for it in h.walk() for c in it.children() if c.metaObject().className().startswith(("PanelToolTip", "IconTip")) and c.property("visible")]
ok("K2 hovering it says 'Keyboard shortcuts (?)'", tips == ["Keyboard shortcuts (?)"], tips)
card = h.cls("KeyboardPanel"); cx1 = card.mapToScene(QPointF(card.width(), 0)).x()
tip = [c for it in h.walk() for c in it.children() if c.metaObject().className().startswith(("PanelToolTip", "IconTip")) and c.property("visible")]
ok("K2b its tooltip ends inside the card", tip and kb.mapToScene(QPointF(tip[0].property("x") + tip[0].property("width"), 0)).x() <= cx1 + 1, [tip and tip[0].property("x"), tip and tip[0].property("width"), x(kb), cx1])
h.click(kb); h.spin(200)
kv = h.cls("KeysView")
ok("K3 a click opens the Keys view; the popup widens for two columns", h.ev("root.view") == "keys" and h.ev("twoColumns", h.ctx_of(kv), kv) and h.ev("panel.contentWidth") > h.ev("Style.space(700)"), [kv.width(), h.ev("panel.contentWidth")])
t = texts()
ok("K4 grouped by where they work", all(g in t for g in ("Board", "Anywhere", "Issue", "Comment box", "Pickers and filters", "Setup panel")), t[:20])
shot("keys")
h.click(kb); h.spin(150)
ok("K5 a second click returns to the board", h.ev("root.view") == "board")
finish()

# --- Settings > Bots: empty ----------------------------------------------------
start(None)
settings()
ok("E1 no bots: the invite, no busy check boxes, no list", sev("invite.visible") and not sev("busyRow.visible") and not sev("listTitle.visible"))
shot("bots-empty")
h.click(sev("invite")); h.spin(80)
ok("E2 the form opens with labelled rows and a reason for the dim Add", sev("adding") and not sev("addButton.enabled") and sev("reason") == "Name the bot to add it."
   and all(s in texts() for s in ("Name", "Busy with", "Label")), sev("reason"))
finish()

# --- adding Spec QA (the report: Add was blank and dim, no reason) --------------
start(FOUR)
settings()
ok("S1 busy columns sit above the bots, check boxes for every label column", y_of(sev("busyRow")) < y_of(sev("listTitle")) and sev("labelColumns.length") == 5)
checks = [it for it in h.walk() if it.property("clickable") is not None and it.property("label") in ("research", "todo", "approved", "in progress", "review") and sev("busyRow").isAncestorOf(it)]
ok("S2 three ticked (approved, in progress, review), research and todo not", sorted(str(c.property("label")) for c in checks if c.property("on")) == ["approved", "in progress", "review"] and len(checks) == 5)
ok("S3 'Open and Closed never count.' is said", "Open and Closed never count." in [str(x.property("text")) for x in h.walk() if sev("busyRow").isAncestorOf(x) and x.isVisible()])
h.click(sev("addLink")); h.spin(60)
sev("nameField.text = 'Spec QA'"); h.spin(60)
ok("S4 with a name: Add stays dim and says to choose a label", not sev("addButton.enabled") and sev("reason") == "Choose a label to add Spec QA.")
none = fpill("cards no bot owns")
ok("S5 'cards no bot owns' is shown but off: Product Lead has it", len(none) == 1 and not none[0].property("enabled"))
h.click(fpill("every card in a column")[0]); h.spin(80)
ok("S6 'every card in a column': the column list opens at once; Add says to choose one", sev("menuOpen") and sev("reason") == "Choose a column to add Spec QA."
   and all(fpill(n) for n in ("research", "todo", "approved", "in progress", "review")))
shot("bots-adding-specqa")
h.click(fpill("review")[0]); h.spin(80)
ok("S7 review picked: the list closes, Add is ready, no reason", not sev("menuOpen") and sev("pick") == "review" and sev("addButton.enabled") and sev("reason") == "")
h.click(sev("addButton")); h.spin(80)
w = h.ev("root.bar.shell.writes") or []
bots = json.loads(h.ev("JSON.stringify(root.bar.shell.writes[root.bar.shell.writes.length - 1].bots)"))[P]["bots"] if w else []
ok("S8 saved as {name: Spec QA, list: review}", bots[-1:] == [{"name": "Spec QA", "list": "review"}], bots)
ok("S9 the list: 'every card in' review, 'cards no other bot owns' for Product Lead", "every card in" in texts() and "cards no other bot owns" in texts())
shot("bots-filled")
h.click(sev("addLink")); sev("nameField.text = 'api engineer'"); h.spin(60)
ok("S10 a taken name: the reason says so", sev("reason") == "There's already a bot named api engineer." and not sev("addButton.enabled"))
before = len(w)
tc = [c for c in checks if c.property("label") == "todo"][0]
h.click(tc); h.spin(80)
last = json.loads(h.ev("JSON.stringify(root.bar.shell.writes[root.bar.shell.writes.length - 1].bots)"))[P]
ok("S11 ticking todo saves it as busy at once", "todo" in last["busyLists"] and len(h.ev("root.bar.shell.writes")) == before + 1, last.get("busyLists"))
finish()

# --- 560 wide: everything stays inside -----------------------------------------
start(FOUR, 560)
settings()
h.click(sev("addLink")); sev("nameField.text = 'Spec QA'"); h.spin(60)
h.click(fpill("every card in a column")[0]); h.spin(200)
sx0 = sec.mapToScene(QPointF(0, 0)).x(); sx1 = sx0 + sec.width()
outside = [(str(it.property("label") or it.property("text")), round(it.mapToScene(QPointF(0, 0)).x()), round(it.mapToScene(QPointF(it.width(), 0)).x()))
           for it in h.visible(lambda it: (it.property("clickable") is not None or cls_is(it, "BoardText")) and sec.isAncestorOf(it))
           if it.width() > 0 and (it.mapToScene(QPointF(0, 0)).x() < sx0 - 0.5 or it.mapToScene(QPointF(it.width(), 0)).x() > sx1 + 0.5)]
ok("N1 popup 560 wide: every control and text of the section stays inside it", not outside, outside[:6])
shot("bots-560")
finish()
print("passed %d failed %d" % (ALL.count(True), ALL.count(False)))
