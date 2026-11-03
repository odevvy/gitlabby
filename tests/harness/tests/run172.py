# v0.1.72 (v172 design A): copy a link. y copies the focused card's, the
# open issue's or the focused merge request's link with wl-copy (https only);
# a right-click on a card or a merge request does the same. The header's
# "Updated HH:MM" reads "Copied #N" / "Copied !N" for a moment, then returns.
# Usage: run172.py <src>
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from fixtures import BOARD
P = "group/app"
h = Harness(sys.argv[1], {"id": "odevvy.gitlab-board", "settingsRevision": 2, "defaultProject": P, "defaultCollapsed": [], "boardStates": {}, "refreshIntervalSec": 60})
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
h.finish()
