# v0.1.72 (v172 design A): copy a link. y copies the focused card's, the
# open issue's or the focused merge request's link with wl-copy (https only);
# a right-click on a card or a merge request does the same. The header's
# "Updated HH:MM" reads "Copied #N" / "Copied !N" for a moment, then returns.
# Usage: run172.py <src>
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from fixtures import BOARD
P = "group/app"
h = Harness(sys.argv[1], {"id": "odevvy.gitlabby", "settingsRevision": 2, "defaultProject": P, "defaultCollapsed": [], "boardStates": {}, "refreshIntervalSec": 60})
h.ev("panel.availableCardHeight = 620; panel.availableCardWidth = 1020")
h.ev("root.opened = true"); h.spin(60); h.answer("board", BOARD); h.spin(400)
h.ev("root.focusBoard()"); h.spin(60)
Y = lambda: h.key(Qt.Key_Y, "y")
status = lambda: h.ev("header.status.text")
since = lambda n: h.launched()[n:]
def mr(iid, title):
    return {"iid": iid, "title": title, "url": "https://gitlab.com/%s/-/merge_requests/%d" % (P, iid), "draft": False, "project": P, "branch": "b%d" % iid,
            "updatedAt": "2026-10-31T09:51:00Z", "status": "mergeable", "author": {"username": "dev1", "name": "Dev One", "avatar": ""}, "pipeline": None, "reviewers": []}
MRS = {"state": "ready", "message": "", "scope": "all", "updatedAt": "2026-10-31T10:19:00Z", "review": [mr(88, "Picker filter"), mr(86, "Label cache")], "mine": [mr(132, "Docs batch")]}
board_time = status()
# --- y ------------------------------------------------------------------------------------------
n = len(h.launched()); Y()
h.ok("A0 no card focused: y does nothing", since(n) == [] and status() == board_time, (since(n), status()))
h.key(Qt.Key_J, "j"); row = h.ev("root.cursorIssue()"); n = len(h.launched()); Y()
h.ok("A1 y copies the focused card's link with wl-copy, nothing else, the popup stays", since(n) == [["wl-copy", row["url"]]] and h.ev("root.opened") and h.ev("root.view") == "board", since(n))
h.ok("A2 the header says Copied #N, quiet", status() == "Copied #%d" % row["iid"] and h.ev("String(header.status.color) === String(root.quiet)"), status())
h.spin(1000); Y(); h.spin(1000)
h.ok("A3 y again keeps it a moment longer", status() == "Copied #%d" % row["iid"], status())
h.spin(700)
h.ok("A4 then the time comes back", status() == board_time, (status(), board_time))
h.key(Qt.Key_Return, "\r"); h.spin(200); n = len(h.launched()); Y()
h.ok("A5 in the issue: y copies the issue's link", h.ev("root.view") == "issue" and since(n) == [["wl-copy", row["url"]]] and status() == "Copied #%d" % row["iid"], (since(n), status()))
h.ev("issueView.focusBox()"); h.spin(100); n = len(h.launched()); Y()
h.ok("A6 typing a comment: y is a letter, nothing copied", since(n) == [], since(n))
h.ev("root.focusBoard()"); h.ev("root.back()"); h.spin(1700)
h.ev("root.openIssue(Object.assign({}, root.cursorIssue(), { url: 'file:///etc/passwd' }))"); h.spin(200); h.ev("root.focusBoard()"); n = len(h.launched()); Y()
h.ok("A7 https links only", h.ev("root.view") == "issue" and since(n) == [] and status() != "Copied #%d" % row["iid"], (since(n), status()))
h.ev("root.back()"); h.spin(100)
h.ev("root.showView('mrs')"); h.spin(100)
while h.running("mrs"): h.answer("mrs", MRS)
h.spin(300); h.ev("root.focusBoard()"); h.key(Qt.Key_J, "j"); n = len(h.launched()); Y()
h.ok("A8 on Merge requests: y copies the focused one's link, Copied !N", since(n) == [["wl-copy", MRS["review"][1]["url"]]] and status() == "Copied !86", (since(n), status()))
h.spin(1700); h.ev("root.showView('board')"); h.spin(200)
# --- right-click; the left button still opens, drags and picks ------------------------------------
h.ev("root.cursor = null"); h.spin(60)
texts = lambda: [str(it.property("text")) for it in h.visible(lambda it: it.metaObject().className().startswith("BoardText"))]
def card_text(t): return next(it for it in h.visible(lambda it: it.metaObject().className().startswith("BoardText") and t in str(it.property("text"))))
c = card_text("Second issue"); a = h.scene(c); url2 = "https://gitlab.com/group/app/-/issues/2"
n = len(h.launched()); QTest.mouseClick(h.win, Qt.RightButton, Qt.NoModifier, a); h.spin(150)
h.ok("B0 right-click a card: its link copied, Copied #2, still on the board, nothing picked", since(n) == [["wl-copy", url2]] and status() == "Copied #2" and h.ev("root.view") == "board" and h.ev("root.picked.length") == 0 and not h.ev("boardView.holding"), (since(n), status(), h.ev("boardView.holding")))
h.spin(1700)
target = card_text("No issues"); b = h.scene(target)
def drag(button):
    QTest.mousePress(h.win, button, Qt.NoModifier, a); h.spin(30)
    for k in range(1, 11): QTest.mouseMove(h.win, QPoint(a.x() + (b.x() - a.x()) * k // 10, a.y() + (b.y() - a.y()) * k // 10)); h.spin(15)
    held = h.ev("boardView.dragRow !== null")
    QTest.mouseRelease(h.win, button, Qt.NoModifier, b); h.spin(150); return held
held = drag(Qt.RightButton)
h.ok("B1 a right-button drag moves nothing", not held and h.ev("root.pendingMove") is None and h.ev("root.view") == "board", held)
h.spin(1700); n = len(h.launched())
held = drag(Qt.LeftButton)
h.ok("B2 a left drag still lifts the card and moves it", held and (h.ev("root.pendingMove") is not None or bool(h.running("move"))) and since(n) == [], (held, since(n)))
h.ev("root.pendingMove") is not None and h.key(Qt.Key_Escape); h.stop_all(); h.ev("root.moveDone(JSON.stringify({state: 'ready', message: ''}))"); h.spin(40); h.answer("board", BOARD); h.spin(300)
c = card_text("Second issue"); a = h.scene(c)
n = len(h.launched()); QTest.mouseClick(h.win, Qt.LeftButton, Qt.ControlModifier, a); h.spin(150)
h.ok("B3 Ctrl+click still picks, copies nothing", h.ev("root.picked.length") == 1 and since(n) == [] and not status().startswith("Copied"), (h.ev("root.picked.length"), since(n), status()))
QTest.mouseClick(h.win, Qt.LeftButton, Qt.ControlModifier, a); h.spin(150)
n = len(h.launched()); h.click(c)
h.ok("B4 a click still opens the issue, copies nothing", h.ev("root.view") == "issue" and since(n) == [], (h.ev("root.view"), since(n)))
h.ev("root.back()"); h.spin(100)
h.ev("root.showView('mrs')"); h.spin(100)
while h.running("mrs"): h.answer("mrs", MRS)
h.spin(300)
rows = sorted(h.visible(lambda it: it.objectName() == "mrRow"), key=lambda it: it.mapToScene(QPointF(0, 0)).y())
n = len(h.launched()); QTest.mouseClick(h.win, Qt.RightButton, Qt.NoModifier, h.scene(rows[2])); h.spin(150)
h.ok("B5 right-click a merge request: its link copied, Copied !132, still open", since(n) == [["wl-copy", MRS["mine"][0]["url"]]] and status() == "Copied !132" and h.ev("root.opened"), (since(n), status()))
n = len(h.launched()); h.click(rows[0])
h.ok("B6 a click still opens it in the browser", since(n) == [["omarchy-launch-browser", MRS["review"][0]["url"]]], since(n))
h.finish()
