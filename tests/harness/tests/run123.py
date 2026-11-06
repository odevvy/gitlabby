# v0.1.23: a failed refresh keeps the board; ask before moves (confirmMoves) and
# Shift+H/L; no quick actions in comments; bots row "+N more" and titles;
# Sign out buttons; keys e/x; placeholder width.
# Usage: run123.py <src> [refresh-error.png bots-more.png move-confirm.png comment-slash.png signout.png help.png]
import sys, os, copy; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
# Settings grows over time: scroll its list so a click's target is on screen first.
_click = Harness.click
def _click_seen(self, it):
    if self.ev("root.view") == "settings":
        sv = self.ev("settingsView"); c = self.ctx_of(sv); fl = self.ev("flick", c, sv)
        top = it.mapToItem(fl.property("contentItem"), QPointF(0, 0)).y()
        self.ev("flick.contentY = Math.max(0, Math.min(flick.contentHeight - flick.height, %f - flick.height / 3))" % top, c, sv); self.spin(60)
    _click(self, it)
Harness.click = _click_seen
from fixtures import BOARD
pngs = dict(zip(["refresh", "bots", "move", "slash", "signout", "help"], sys.argv[2:8]))
shot = lambda name: pngs.get(name) and h.grab_card(pngs[name])
h = Harness(sys.argv[1], {"id": "odevvy.gitlabby", "settingsRevision": 2, "defaultProject": "group/app"})
button = lambda label: h.visible(lambda it: it.metaObject().className().startswith("ActionButton") and it.property("label") == label)
pill = lambda label: h.visible(lambda it: it.metaObject().className().startswith("Pill") and it.property("label") == label)
texts = lambda: [it.property("text") for it in h.visible(lambda it: it.metaObject().className().startswith("BoardText")) if it.property("text")]
same = lambda a, b: abs(a.redF() - b.redF()) < 0.01 and abs(a.greenF() - b.greenF()) < 0.01 and abs(a.blueF() - b.blueF()) < 0.01
helper = lambda: h.ev("root.helperPath()")
status = lambda: h.ev("root.statusText()")
def set_settings(extra): h.ev("root.settings = Object.assign({}, root.settings, " + json.dumps(extra) + ")"); h.spin(80)
def board_iids(): return {c["name"]: [i["iid"] for i in c["issues"]] for c in h.ev("root.columns")}
def shift(ch): h.key(getattr(Qt, "Key_" + ch), ch)

# --- U1: a failed refresh keeps the board -------------------------------------
h.ev("root.opened = true"); h.spin(80); h.answer("board", BOARD); h.spin(80)
before = board_iids()
h.ev("root.refresh()"); h.answer("board", {"state": "error", "message": "GitLab did not answer within 30 seconds."}); h.spin(80)
hhmm = h.ev("new Date(root.updatedAt).toLocaleTimeString(Qt.locale(), 'HH:mm')")
h.ok("R1 failed refresh: same board, still on screen", board_iids() == before and h.ev("boardView.visible") and not h.ev("setupView.visible"))
h.ok("R2 header: Couldn't refresh · showing HH:MM, in the urgent color", status() == "Couldn't refresh · showing " + hhmm and h.ev("root.refreshError") == "GitLab did not answer within 30 seconds.", status())
h.ok("R3 cards can still move (a move rechecks GitLab itself)", h.ev("root.canMove"))
shot("refresh")
h.ev("root.refresh()"); h.answer("board", BOARD); h.spin(600)  # past a refresh's "Updating…" (v0.1.67)
h.ok("R4 the next good refresh clears it", h.ev("root.refreshError") == "" and status().startswith("Updated"))
h.ev("root.refresh()"); h.answer("board", {"state": "logged-out", "message": "Not signed in to gitlab.com. Run: glab auth login"}); h.spin(60)
h.ok("R5 signed out on refresh: still the sign-in panel", h.ev("root.setup") == "logged-out" and h.ev("setupView.visible"))
h.ev("root.refresh()"); h.answer("board", BOARD); h.spin(60)
h.ev("root.switchTo('group/other', '', '')"); h.spin(40)
h.answer("board", {"state": "error", "message": "Could not load boards for group/other."}); h.spin(80)
h.ok("R6 nothing loaded: the error takes the board's place, with Try again; the header leaves it to the body",
     h.ev("setupView.visible") and "Could not reach GitLab" in texts() and "Could not load boards for group/other." in texts() and len(button("Try again")) == 1 and status() == "")
h.key(Qt.Key_Return)
h.ok("R7 Enter = Try again", bool(h.running("board")))
h.answer("board", dict(BOARD, project="group/other")); h.spin(60)
# a saved copy on screen, then the refresh fails: the saved copy stays, still no drags
h.stop_all(); h.ev("root.switchTo('group/app', '7', 'Development')"); h.spin(40)
h.answer("cached", dict(BOARD, cached=True)); h.spin(60)
h.answer("board", {"state": "error", "message": "offline"}); h.spin(60)
h.ok("R8 a saved copy stays on a failed refresh, drags still off", h.ev("root.cached") and len(h.ev("root.columns")) == 4 and not h.ev("root.canMove") and status().startswith("Couldn't refresh"))
h.ev("root.refresh()"); h.answer("board", BOARD); h.spin(60)

# --- U6: the placeholder opens at the width boards had this session ----------
w7 = h.ev("root.boardWidth")
h.ev("root.switchTo('group/app', '7', 'Development')"); h.spin(40)
h.ok("K1 placeholder as wide as this board was", h.ev("skeleton.visible") and h.ev("skeleton.implicitWidth") == w7, (h.ev("skeleton.implicitWidth"), w7))
h.ev("root.switchTo('group/new', '', '')"); h.spin(40)
h.ok("K2 a board not seen yet: as wide as the last one", h.ev("skeleton.implicitWidth") == w7)
h.stop_all(); h.ev("root.switchTo('group/app', '7', 'Development')"); h.spin(40); h.answer("board", BOARD); h.spin(60)

# --- S2 + U3: Shift+H/L, and ask first with confirmMoves -------------------------
h.key(Qt.Key_J, "j")  # first move shows the cursor: #2 in todo
h.ok("M0 cursor on #2 in todo", h.ev("root.cursorIssue().iid") == 2)
shift("L")
h.ok("M1 no confirmMoves: Shift+L moves #2 to review at once", h.running("move") and h.running("move")[0][-4:] == ["--from", "11", "--to", "12"], h.running("move"))
h.stop_all(); h.ev("root.moveDone(JSON.stringify({state: 'error', message: 'x'}))"); h.ev("root.refreshQueued = false; root.moveError = ''"); h.spin(40)
set_settings({"confirmMoves": ["Group/App"]})
h.ok("M2 confirmMoves matches the project in any case", h.ev("root.confirmMoves") and h.ev("(function(){ root.project = 'GROUP/app'; var on = root.confirmMoves; root.project = 'group/app'; return on })()"))
h.ev("root.cursor = null"); h.key(Qt.Key_J, "j"); shift("L")
q = "Move #2 from todo to review?"
h.ok("M3 Shift+L now asks: from, to, what it changes; nothing run, card not moved", q in texts() and "This changes its status label on GitLab." in texts()
     and not h.running("move") and board_iids()["todo"] == [2], texts())
mv, cancel = button("Move"), button("Cancel")
h.ok("M4 Move is the main button, Cancel the quiet one", len(mv) == 1 and mv[0].property("main") and len(cancel) == 1 and not cancel[0].property("main"))
h.ok("M5 the popup grows by the question", abs(h.ev("keyCatcher.implicitHeight") - (h.ev("header.implicitHeight") + h.ev("root.gap") * 2 + h.ev("moveConfirm.height") + h.ev("boardView.implicitHeight"))) < 1)
shot("move")
h.ev("root.refresh()"); h.spin(60)
h.ok("M6 a refresh waits while it asks (no fetch yet)", board_iids()["todo"] == [2] and h.ev("root.refreshQueued") and not h.running("board"))
h.age_feed(); h.key(Qt.Key_Escape)
h.ok("M7 Escape cancels: nothing run, popup still open, the waiting refresh runs", q not in texts() and not h.running("move") and h.ev("root.opened") and bool(h.running("board")))
h.answer("board", BOARD); h.spin(60)
h.ev("root.cursor = null"); h.key(Qt.Key_J, "j"); shift("L"); h.key(Qt.Key_Return)
h.ok("M8 Enter confirms: the move runs for #2, todo -> review", h.running("move") and h.running("move")[0] == [helper(), "move", "--project", "group/app", "--board", "7", "--iid", "2", "--from", "11", "--to", "12"], h.running("move"))
h.stop_all(); h.ev("root.moveDone(JSON.stringify({state: 'ready', message: 'Moved'}))"); h.spin(40); h.answer("board", BOARD); h.spin(60)
h.ev("root.cursor = null"); h.key(Qt.Key_J, "j"); shift("H")
h.ok("M9 Shift+H to the collapsed Open column asks too, with what it does", "Move #2 from todo to Open?" in texts() and "This removes its status label on GitLab." in texts())
h.click(button("Cancel")[0])
h.ok("M10 Cancel button: gone, nothing run", not h.running("move") and not button("Move"))
# a drag-and-drop asks too
card = next(it for it in h.visible(lambda it: it.metaObject().className().startswith("BoardText") and "Second issue" in str(it.property("text"))))
target = next(it for it in h.visible(lambda it: it.metaObject().className().startswith("BoardText") and it.property("text") == "No issues"))
a, b = h.scene(card), h.scene(target)
QTest.mousePress(h.win, Qt.LeftButton, Qt.NoModifier, a); h.spin(30)
for k in range(1, 11): QTest.mouseMove(h.win, QPoint(a.x() + (b.x() - a.x()) * k // 10, a.y() + (b.y() - a.y()) * k // 10)); h.spin(15)
QTest.mouseRelease(h.win, Qt.LeftButton, Qt.NoModifier, b); h.spin(120)
h.ok("M11 a drop asks too", q in texts() and not h.running("move"), texts())
h.click(button("Move")[0])
h.ok("M12 Move button runs it", bool(h.running("move")))
h.stop_all(); h.ev("root.moveDone(JSON.stringify({state: 'ready', message: 'Moved'}))"); h.spin(40); h.answer("board", BOARD); h.spin(60)
h.ev("root.cursor = null"); h.key(Qt.Key_J, "j"); shift("L"); h.ev("root.opened = false"); h.spin(40); h.ev("root.opened = true"); h.spin(60)
h.ok("M13 closing the popup drops the question", h.ev("root.pendingMove") is None and q not in texts())
h.stop_all(); h.answer("board", BOARD); h.spin(40)
set_settings({"confirmMoves": []})

# --- U2 + U7: bots row, 5 numbers then +N more, titles on hover ----------------
many = copy.deepcopy(BOARD)
todo = next(c for c in many["columns"] if c["name"] == "todo")
todo["issues"] = [dict(todo["issues"][0], iid=100 + i, title="Issue number %d" % (100 + i), labels=["todo"]) for i in range(8)]
set_settings({"bots": {"group/app": {"busyLists": ["todo", "review"], "bots": [{"name": "Product Lead", "label": ""}, {"name": "Dev", "label": "dev"}]}}})
h.ev("root.refresh()"); h.answer("board", many); h.spin(100)
t = texts()
h.ok("B1 two issue numbers, then +6, the column said once (v0.1.29)", "#100" in t and "· #101" in t and "· #102" not in t and "+6" in t and "in todo" in t, t)
row = h.cls("BotsRow")
h.ok("B2 the row fits the card", row.mapToScene(QPointF(row.width(), 0)).x() <= h.cls("KeyboardPanel").mapToScene(QPointF(h.cls("KeyboardPanel").width(), 0)).x())
tips = lambda: [c for it in h.walk() for c in it.children() if c.metaObject().className().startswith("PanelToolTip")]  # popups: QObject children, not items
more = next(it for it in h.visible(lambda it: it.metaObject().className().startswith("BoardText") and it.property("text") == "+6"))
QTest.mouseMove(h.win, h.scene(more)); h.spin(700)
shown = [tp for tp in tips() if tp.property("visible")]
inside = lambda tp: tp.property("x") + more.mapToItem(row, QPointF(0, 0)).x() + tp.property("width") <= row.width() + 1
h.ok("B3b its tooltip stays inside the row", shown and inside(shown[0]), [(tp.property("x"), tp.property("width")) for tp in shown])
h.ok("B3 hover +6: the rest, with titles", len(shown) == 1 and shown[0].property("text") == "\n".join("#%d  Issue number %d" % (i, i) for i in range(102, 108)), [tp.property("text") for tp in shown])
shot("bots")
ref = next(it for it in h.visible(lambda it: it.metaObject().className().startswith("BoardText") and it.property("text") == "#100" and row.isAncestorOf(it)))
QTest.mouseMove(h.win, h.scene(ref)); h.spin(700)
shown = [tp for tp in tips() if tp.property("visible")]
h.ok("B4 hover an issue number: its title", len(shown) == 1 and shown[0].property("text") == "#100 Issue number 100", [tp.property("text") for tp in shown])
QTest.mouseMove(h.win, QPoint(5, 5)); h.spin(100)
h.ok("B5 wrapped lines sit close: Flow spacing 6, bots 12 apart", h.ev("botsRow.children[0].spacing") == h.ev("Style.space(6)"))
h.ok("U7 dim text is a 35% blend", same(h.ev("root.dim"), h.ev("Qt.tint(root.foreground, Qt.rgba(root.background.r, root.background.g, root.background.b, 0.35))")))
set_settings({"bots": {}})
h.ev("root.refresh()"); h.answer("board", BOARD); h.spin(60)

# --- S1: comments, keys e and x --------------------------------------------------
h.ev("root.openIssue(root.columns[1].issues[0])"); h.spin(80)
ISSUE = {"iid": 2, "title": "Second issue with a longer title", "state": "opened", "labels": ["todo", "app-ui"], "url": "https://gitlab.com/group/app/-/issues/2",
         "description": "Make the board faster.", "author": "dev1", "milestone": "", "assignees": [], "createdAt": "2026-10-20T12:00:00Z", "updatedAt": "2026-10-29T12:00:00Z"}
h.answer("issue", {"state": "ready", "message": "", "issue": ISSUE}); h.answer("notes", {"state": "ready", "message": "", "iid": 2, "more": False, "notes": []})
iv = h.ctx_of(h.cls("IssueView"))
# v0.1.24: the hint is shorter.
h.ok("P1 the hint under the box says / lines aren't sent", "Posts as you. Lines starting with / aren't sent." in texts())
h.ev("box.text = 'Looks good\\n/label ~review'", iv); h.spin(40)
hint = "A line starts with /, which GitLab runs as a quick action, so this can't be posted. Wrap it in `backticks`."
h.ok("P2 a / line: the warning, in the urgent color; Post off", hint in texts() and not button("Post")[0].property("enabled"))
shot("slash")
h.ev("issueView.post()"); h.spin(40)
h.ok("P3 post() refuses it too: nothing run", not h.running("comment"))
h.ev("box.text = 'see a/b and `/close`'", iv); h.spin(40)
h.ok("P4 / inside a line or in backticks: Post on", button("Post")[0].property("enabled") and hint not in texts())
h.click(button("Post")[0])
h.ok("P5 posts", bool(h.running("comment")))
h.answer("comment", {"state": "commands", "message": "GitLab ran this as quick actions instead of posting a comment. Check the issue."}); h.spin(60)
h.ok("P6 GitLab ran quick actions anyway: said in red, issue, comments and board reload, text kept",
     "GitLab ran this as quick actions instead of posting a comment. Check the issue." in texts() and bool(h.running("issue")) and bool(h.running("notes")) and bool(h.running("board"))
     and h.ev("box.text", iv) == "see a/b and `/close`")
h.stop_all(); h.answer("issue", {"state": "ready", "message": "", "issue": ISSUE}); h.answer("notes", {"state": "ready", "message": "", "iid": 2, "more": False, "notes": []})
h.ev("box.text = ''", iv); h.ev("keyCatcher.forceActiveFocus()"); h.spin(40)
h.key(Qt.Key_E, "e")
h.ok("E1 e: the label editor opens and loads (the filter is focused once they load, run120)", h.ev("issueView.editing") and bool(h.running("labels")))
h.key(Qt.Key_Escape)
h.ok("E2 Escape closes it", not h.ev("issueView.editing"))
h.stop_all(); h.ev("keyCatcher.forceActiveFocus()"); h.spin(30)
h.key(Qt.Key_X, "x")
h.ok("X1 x: asks to close (nothing run yet)", "Close #2? This closes it on GitLab." in texts() and not h.running("close"))
h.key(Qt.Key_Escape)
h.ok("X2 Escape: the question goes, still on the issue", h.ev("root.view") == "issue" and not h.ev("issueView.confirming"))
h.key(Qt.Key_X, "x"); h.key(Qt.Key_Return)
h.ok("X3 x then Enter: closes #2", h.running("close") == [[helper(), "close", "--project", "group/app", "--iid", "2"]])
h.answer("close", {"state": "ready", "message": "Closed #2.", "issueState": "closed", "labels": ["todo"]}); h.spin(60); h.stop_all()
h.key(Qt.Key_X, "x")
h.ok("X4 x on a closed issue: reopens, no question", h.running("reopen") == [[helper(), "reopen", "--project", "group/app", "--iid", "2"]])
h.stop_all(); h.ev("root.back()"); h.spin(60)

# --- U4: Sign out buttons ------------------------------------------------------
h.ev("root.showView('settings')"); h.spin(40); h.answer("whoami", {"state": "ready", "message": "", "user": "o_devvy"}); h.spin(40)
# v0.1.24: Sign out is a text action now (run124 checks it); the confirm keeps U4's buttons.
link = lambda: h.visible(lambda it: it.metaObject().className().startswith("BoardText") and it.property("text") == "Sign out")
h.ok("O1 Sign out is offered, never as a pill", len(link()) == 1 and not pill("Sign out"))
h.click(link()[0])
yes = button("Yes, sign out")
h.ok("O2 confirm: Yes in the urgent color, Cancel quiet; both square", len(yes) == 1 and yes[0].property("danger") and same(h.ev("tone", QQmlEngine.contextForObject(yes[0]), yes[0]), h.ev("root.urgent"))
     and len(button("Cancel")) == 1 and not pill("Yes, sign out"))
shot("signout")
h.click(button("Cancel")[0])
h.ok("O3 Cancel: nothing run", not h.running("logout") and len(link()) == 1)

# --- U3: the cheat sheet -------------------------------------------------------
h.ev("root.showView('keys')"); h.spin(60)
t = texts()
h.ok("H1 ? lists the keys, grouped, as keycaps (v0.1.29)", all(k in t for k in ["Shift", "H", "L", "e", "x"]) and "Confirm a move or a close" in t and "Issue" in t, t)
shot("help")
h.ev("root.back()"); h.spin(40)
sys.exit(h.finish())
