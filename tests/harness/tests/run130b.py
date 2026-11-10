# v0.1.30: icon-button tooltips (IconTip): every icon button says what it does,
# with its key in brackets when it has one, and the key does what the click
# does; each tip stays inside the card. Settings in the new order (Refresh,
# Start collapsed, Bots, Account). And the 0.1.29 bug: his saved bots setting,
# handed over through Qt (lists as sequences), reads fine in the row and in
# Settings, and a busy toggle keeps the other columns.
# Usage: run130b.py <src> [outdir]  (previews: tip-refresh, tip-issue-close, tip-remove-bot, settings-order)
import sys, os, json, shutil; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from fixtures import BOARD

# v0.1.99: the longer Open links in note pushes Settings > Bots below the fold,
# so scroll the settings Flickable to an item before pointing at it.
_scene0 = Harness.scene
def _into_view(self, it, *a, **k):
    f = it.parentItem() if it is not None else None
    while f is not None and not f.metaObject().className().startswith("QQuickFlickable"): f = f.parentItem()
    if f is not None:
        y = it.mapToItem(f.property("contentItem"), QPointF(0, 0)).y()
        top, h_ = f.property("contentY"), f.height()
        if y < top or y + it.height() > top + h_:
            f.setProperty("contentY", max(0.0, min(y - 20, f.property("contentHeight") - h_)))
            QGuiApplication.processEvents()
    return _scene0(self, it, *a, **k)
Harness.scene = _into_view
out = sys.argv[2] if len(sys.argv) > 2 else None
cls_is = lambda it, n: it.metaObject().className().startswith(n)
ALL = []
def ok(n, c, e=""): ALL.append(bool(c)); h.ok(n, c, e)
def finish():  # one total for both harnesses (mutate.sh reads the first "passed" line)
    ok("Z no QML warnings", not h.warnings, h.warnings[:3]); shutil.rmtree(h.dir, ignore_errors=True)
def shot(name): out and h.grab_card(os.path.join(out, name + ".png"))
def tips():  # visible IconTips: (text, inside the card)
    area = h.ev("root.tipArea"); res = []
    for it in h.walk():
        for c in it.children():
            if cls_is(c, "IconTip") and c.property("visible"):
                x0 = it.mapToItem(area, QPointF(c.property("x"), 0)).x()
                res.append((str(c.property("text")), x0 >= -1 and x0 + c.property("width") <= area.width() + 1))
    return res
def hover(item):
    QTest.mouseMove(h.win, QPoint(1, 1)); h.spin(60)
    QTest.mouseMove(h.win, h.scene(item)); h.spin(650); return tips()
def tip_is(name, item, text):
    t = hover(item)
    ok(name + " " + repr(text) + ", inside the card", t == [(text, True)], t)
view = lambda: h.ev("root.view")
key = lambda ch: (h.key(getattr(Qt, "Key_" + {"?": "Question"}.get(ch, ch.upper())), ch), h.spin(100))
esc = lambda: (h.key(Qt.Key_Escape), h.spin(100))
glyph = lambda parent_cls: [it for it in h.visible(lambda it: cls_is(it, "GlyphButton")) if any(cls_is(p, parent_cls) for p in ancestors(it))]
def ancestors(it):
    while it is not None: yield it; it = it.parentItem()

# --- the 0.1.29 bug: his exact settings, handed over through Qt ------------------------
HIS = json.loads('''{"id":"odevvy.gitlabby","boardStates":{"my-group/my-project#11714661":{"collapsed":["open","research","closed"],"hidden":[]}},"bots":{"my-group/my-project":{"bots":[{"label":"app-ui","name":"App UI"},{"label":"api","name":"API Engineer"},{"label":"auth-mail","name":"Auth & Mail"},{"name":"Product Lead","label":""}],"busyLists":["approved","in progress","review"]}},"defaultBoardId":"","defaultBoardName":"","defaultCollapsed":["closed","research","open"],"defaultProject":"my-group/my-project","refreshIntervalSec":120,"settingsRevision":2}''')
Q = "my-group/my-project"
h = Harness(sys.argv[1], None)
h.ev("root").setProperty("settings", HIS)  # as Omarchy does: QVariantMap, lists as Qt sequences
ok("Q0 the lists really arrive as Qt sequences (Array.isArray false)", not h.ev("Array.isArray(root.settings.bots['my-group/my-project'].bots)"))
PB = json.loads(json.dumps(BOARD).replace('"group/app', '"' + Q))
for c in PB["columns"]:
    for i in c.get("issues", []): i["labels"] = list(i.get("labels", [])) + ["app-ui"]
h.ev("root.opened = true"); h.spin(80); h.answer("board", PB); h.spin(120)
ok("Q1 the board's bot row reads his four bots", [b["name"] for b in h.ev("root.botStates")] == ["App UI", "API Engineer", "Auth & Mail", "Product Lead"], h.ev("root.botStates"))
ok("Q2 his other settings read too: 2 min refresh, Open/research/Closed folded", h.ev("root.refreshIntervalSec") == 120 and sorted(h.ev("root.defaultCollapsed")) == ["closed", "open", "research"])
h.ev("root.showView('settings')"); h.spin(80); h.answer("whoami", {"state": "ready", "message": "", "user": "o_devvy"}); h.spin(60)
sec = h.cls("BotsSection"); c = h.ctx_of(sec); sev = lambda code: h.ev(code, c, sec)
ok("Q3 Settings > Bots: no 'isn't valid', the four bots listed, no invite", sev("problem.text") == "" and sev("bots.length") == 4 and not sev("invite.visible") and sev("pane.visible"), sev("problem.text"))
rm = sorted(glyph("BotsSection"), key=lambda g: g.mapToScene(QPointF(0, 0)).y())
tip_is("Q4 a bot's ✕:", rm[0], "Remove App UI")
QTest.mouseMove(h.win, h.scene(rm[0])); h.spin(650); shot("tip-remove-bot")
todo = [it for it in h.walk() if it.property("clickable") is not None and it.property("label") == "todo" and sev("busyRow").isAncestorOf(it)]
h.click(todo[0]); h.spin(80)
w = h.ev("root.bar.shell.writes") or []
last = json.loads(h.ev("JSON.stringify(root.bar.shell.writes[root.bar.shell.writes.length - 1])")) if w else {}
ok("Q5 ticking todo adds it and keeps the others; his bots and other keys unchanged",
   last.get("bots", {}).get(Q, {}).get("busyLists") == ["approved", "in progress", "review", "todo"] and last["bots"][Q]["bots"] == HIS["bots"][Q]["bots"]
   and last.get("refreshIntervalSec") == 120 and last.get("defaultCollapsed") == ["closed", "research", "open"] and last.get("boardStates") == HIS["boardStates"], last)
h.stop_all(); finish()

# --- the header ------------------------------------------------------------------
P = "group/app"
h = Harness(sys.argv[1], {"id": "odevvy.gitlabby", "settingsRevision": 2, "defaultProject": P})
h.ev("root.opened = true"); h.spin(80); h.answer("board", BOARD); h.spin(120)
tip_is("H1 refresh:", h.ev("header.refreshButton"), "Refresh (r)"); shot("tip-refresh")
h.stop_all(); key("r"); ok("H1k r refreshes", bool(h.running("board"))); h.answer("board", BOARD)
tip_is("H2 gear:", h.ev("header.gear"), "Settings (s)")
key("s"); ok("H2k s opens Settings", view() == "settings"); h.answer("whoami", {"state": "ready", "message": "", "user": "o_devvy"}); key("s"); ok("H2k' s again: back to the board", view() == "board")
tip_is("H3 keyboard:", h.ev("header.keysButton"), "Keyboard shortcuts (?)")
key("?"); ok("H3k ? opens the shortcuts", view() == "keys")
tip_is("H4 the Keys view's ✕:", glyph("KeysView")[0], "Back to the board (Esc)")
esc(); ok("H4k Esc: back to the board", view() == "board")
tip_is("H5 title and caret:", h.ev("header.chevron"), "Starred boards")
key("p"); ok("H5k p opens the picker", view() == "picker")
h.answer("projects", {"state": "ready", "projects": [{"id": 1, "path": P}]}); h.spin(60)
tip_is("H6 the picker's ✕:", [g for g in glyph("Picker") if g.property("glyph") == "\uf00d"][0], "Back to the board (Esc)")
h.ev("root.pickProject('group/app')"); h.spin(50); h.answer("boards", {"state": "ready", "boards": [{"id": 7, "name": "Development"}, {"id": 8, "name": "Ops"}]}); h.spin(80)
tip_is("H7 the board step's ‹:", [g for g in glyph("Picker") if g.property("glyph") == "\uf053"][0], "Back to projects")
stars = [it for it in h.visible(lambda it: cls_is(it, "BoardText") and it.property("text") in ("\uf005", "\uf006")) if any(cls_is(p, "Picker") for p in ancestors(it))]
t = [hover(s) for s in stars]
ok("H8 the picker's stars: favorites tip (Add / Remove), inside", sorted(x[0][0] for x in t if len(x) == 1) == sorted(["Add to starred boards"] * len(stars)) and all(x[0][1] for x in t), t)
esc(); ok("H6k Esc: back to the board", view() == "board")
dm = h.ev("header.defaultMark")
tip_is("H9 the header star (default board):", dm, "Your default board" if h.ev("root.onDefault") else "Default board")
# --- columns ---------------------------------------------------------------------------
strips = [it for it in h.visible(lambda it: cls_is(it, "QQuickMouseArea") and it.property("hoverEnabled")) if any(cls_is(p, "BoardView") for p in ancestors(it))]
names = [c["name"] for c in h.ev("root.columns")]
coll = [t for s in strips for t in [hover(s)] if t and (t[0][0].startswith("Expand ") or t[0][0].startswith("Collapse "))]
ok("C1 every column header says Collapse <name>, every strip Expand <name>, inside the card",
   coll and all(t[0][1] for t in coll) and {t[0][0].split(" ", 1)[1] for t in coll} == set(names), [t[0] for t in coll])
# --- the issue view ----------------------------------------------------------------------
ISSUE = {"iid": 2, "title": "Second issue with a longer title", "state": "opened", "labels": ["review"], "url": "https://gitlab.com/group/app/-/issues/2",
         "description": "Make the board faster.", "author": "dev1", "milestone": "", "assignees": ["dev1"], "createdAt": "2026-10-20T12:00:00Z", "updatedAt": "2026-10-29T12:00:00Z"}
def open_issue():
    h.ev("root.openIssue(root.columns[1].issues[0])"); h.spin(80)
    h.answer("issue", {"state": "ready", "message": "", "issue": ISSUE}); h.answer("notes", {"state": "ready", "message": "", "iid": 2, "more": False, "notes": []}); h.spin(80)
open_issue()
tip_is("I1 the issue's ✕:", glyph("IssueView")[0], "Back to the board (Esc)"); shot("tip-issue-close")
esc(); ok("I1k Esc: back to the board", view() == "board"); open_issue()
pillo = [it for it in h.visible(lambda it: cls_is(it, "Pill") and it.property("label") == "Open in browser ↗")][0]
tip_is("I2 Open in browser:", pillo, "Open in browser (o)")
edit = [it for it in h.visible(lambda it: cls_is(it, "BoardText") and str(it.property("text")).endswith("Edit labels"))][0]
tip_is("I3 Edit labels:", edit, "Edit labels (e)")
key("e"); h.answer("labels", {"state": "ready", "message": "", "status": [], "labels": [{"name": "review", "color": "#a855f7", "textColor": None}]}); h.spin(80)
ok("I3k e edits the labels", h.ev("issueView.editing"))
done = [it for it in h.visible(lambda it: cls_is(it, "BoardText") and str(it.property("text")).endswith("Done editing"))][0]
tip_is("I4 Done editing:", done, "Done editing (Esc)")
esc(); ok("I4k Esc: done editing", not h.ev("issueView.editing"))
st = [it for it in h.visible(lambda it: cls_is(it, "BoardText") and it.property("text") == "Close issue")][0]
tip_is("I5 Close issue:", st, "Close issue (x)")
key("x"); ok("I5k x asks to close it", h.ev("issueView.confirming")); esc()
n0 = len(h.launched()); key("o"); ok("I2k o opens it in the browser", len(h.launched()) == n0 + 1 and ISSUE["url"] in json.dumps(h.launched()[-1:]), h.launched()[-1:])
h.stop_all(); h.ev("root.opened = true"); h.spin(80); h.answer("board", BOARD); h.spin(80)

# --- Settings: the order, the ✕ ------------------------------------------------------
h.ev("root.showView('settings')"); h.spin(80); h.answer("whoami", {"state": "ready", "message": "", "user": "o_devvy"}); h.spin(60)
heads = sorted([(it.mapToScene(QPointF(0, 0)).y(), str(it.property("text"))) for it in h.walk() if it.isVisible() and str(it.property("text")) in ("Refresh every", "Start collapsed", "Bots", "Account")])
ok("O1 Settings in order: Refresh every, Start collapsed, Bots, Account", [t for _, t in heads] == ["Refresh every", "Start collapsed", "Bots", "Account"], heads)
tip_is("O2 Settings' ✕:", glyph("SettingsView")[0], "Back to the board (Esc)")
QTest.mouseMove(h.win, QPoint(1, 1)); h.spin(60); shot("settings-order")
esc(); ok("O2k Esc: back to the board", view() == "board")
h.stop_all()
finish()
print("passed %d failed %d" % (ALL.count(True), ALL.count(False)))
