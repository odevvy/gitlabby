# v0.1.60: one shared round mask for every avatar (Board.qml avatarMask)
# instead of a layer-backed mask item per avatar; and the last 10 issues
# opened stay in memory (IssueView recent): reopening one shows its
# description and comments at once while both are fetched again.
# Usage: run160.py <src>
import sys, os, tempfile; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from PySide6.QtGui import QImage, QColor
src = sys.argv[1]
P = "firelink21/phrase41"
png = tempfile.mkdtemp() + "/face.png"; im = QImage(64, 64, QImage.Format_ARGB32); im.fill(QColor("#ff0000")); im.save(png)
def who(n): return {"username": n, "name": n.title(), "avatar": "file://" + png}
def iss(iid, labels, people): return {"iid": iid, "title": "Issue %d" % iid, "labels": labels, "url": "https://gitlab.com/%s/-/issues/%d" % (P, iid), "createdAt": "2026-10-31T09:00:00Z", "notes": 0, "assignees": [who("u%d" % k) for k in range(people)]}
BOARD = {"state": "ready", "project": P, "updatedAt": "2026-10-31T13:20:00Z", "message": "", "labelColors": {}, "boards": [{"id": 1, "name": "Development"}], "board": {"id": 1, "name": "Development"}, "fallback": False,
         "columns": [{"name": "Open", "kind": "open", "issues": []}, {"name": "todo", "kind": "label", "listId": 1, "color": "#5b9bd5", "issues": [iss(10 + i, ["todo"], 1 + i % 3) for i in range(6)]}, {"name": "Closed", "kind": "closed", "issues": []}]}
h = Harness(src, {"id": "odevvy.gitlab-board", "settingsRevision": 2, "defaultProject": P, "defaultCollapsed": ["open", "closed"]})
h.ev("panel.availableCardHeight = 1200; panel.availableCardWidth = 2400")
h.ev("root.opened = true"); h.spin(60); h.answer("board", BOARD); h.spin(600)
ok = h.ok
avs = [it for it in h.walk() if it.metaObject().className().startswith("Avatar") and it.isVisible()]
layered = lambda root: [it for it in h.walk(root) if h.ev("layer.enabled", QQmlEngine.contextForObject(it), it) is True]
ok("M0 avatars on the board", len(avs) == 12, len(avs))
ok("M1 no avatar holds its own layer-backed mask", sum(len(layered(a)) for a in avs) == 0, sum(len(layered(a)) for a in avs))
mask = h.ev("root.avatarMask")
ok("M2 one shared mask, a layer, not drawn", mask is not None and h.ev("root.avatarMask.layer.enabled") and not h.ev("root.avatarMask.visible"))
# The offscreen harness draws with the software backend, which skips shader
# effects, so the round cut itself is checked on a real display (preview).
fx = [c for a in avs for c in h.walk(a) if c.metaObject().className() == "QQuickMultiEffect"]
same = lambda c: c.property("maskEnabled") and c.property("maskSource") is not None and c.property("maskSource").objectName() == "sharedAvatarMask"
ok("M3 every avatar's effect is masked by the shared mask", len(fx) == len(avs) and all(same(c) for c in fx), [(c.property("maskEnabled"), c.property("maskSource")) for c in fx][:2])
# --- the issue cache -------------------------------------------------------------
iv = lambda k: h.ev("issueView." + k)
def full(iid, desc): return {"iid": iid, "title": "Issue %d (as fetched)" % iid, "labels": ["todo"], "state": "opened", "description": desc, "url": "https://gitlab.com/%s/-/issues/%d" % (P, iid), "author": "ann", "assignees": []}
def note(i, body): return {"id": i, "body": body, "createdAt": "2026-10-31T10:00:00Z", "author": {"username": "bob", "name": "Bob", "avatar": ""}}
def open_(row): h.ev("root.openIssue(root.columns[1].issues[%d])" % row); h.spin(80)
def answer(iid, desc, notes): h.answer("issue", {"state": "ready", "message": "", "issue": full(iid, desc)}); h.answer("notes", {"state": "ready", "message": "", "iid": iid, "more": False, "notes": notes})
def back(): h.ev("root.back()"); h.spin(80)
open_(0)
ok("C0 first visit: loading, nothing cached", iv("described") is False and iv("notes.length") == 0)
answer(10, "First text", [note(1, "hello")]); back()
open_(1); answer(11, "Text 1", []); back()  # another issue in between drops the shown thread
open_(0)
ok("C1 reopened: the description at once, before any answer", iv("described") and iv("issue.description") == "First text" and not iv("issueReady"))
ok("C2 ... and its comments", iv("notes.length") == 1)
ok("C3 ... but editing stays locked until the fresh answers", iv("loaded") is False)
ok("C4 ... and both are fetched again", len(h.running("issue")) == 1 and len(h.running("notes")) == 1, (h.running("issue"), h.running("notes")))
answer(10, "Second text", [note(1, "hello"), note(2, "again")])
ok("C5 the fresh answers replace it and unlock", iv("issue.description") == "Second text" and iv("issue.title") == "Issue 10 (as fetched)" and iv("notes.length") == 2 and iv("loaded"))
back()
for r in range(1, 6):
    open_(r); answer(10 + r, "Text %d" % r, []); back()
ok("C6 one entry per issue", sorted(h.ev("Object.keys(issueView.recent)")) == sorted("%s#%d" % (P, 10 + r) for r in range(6)))
h.ev("root.columns = root.columns.map(function(c, i) { if (i !== 1) return c; var d = JSON.parse(JSON.stringify(c)); for (var k = 0; k < 8; k++) d.issues.push(Object.assign({}, d.issues[0], { iid: 100 + k })); return d })"); h.spin(100)
for r in range(6, 12):
    open_(r); answer(h.ev("root.columns[1].issues[%d].iid" % r), "More", []); back()
ok("C7 at most 10 kept; the oldest goes first", len(h.ev("Object.keys(issueView.recent)")) == 10 and ("%s#10" % P) not in h.ev("Object.keys(issueView.recent)") and ("%s#11" % P) not in h.ev("Object.keys(issueView.recent)"))
open_(5)
ok("C8 the card's own row wins over the cached one (fresher labels)", iv("issue.title") == "Issue 15" and iv("issue.description") == "Text 5")
back()
h.ev("root.signingOut = true"); h.spin(30)
ok("C9 signing out forgets every cached issue", len(h.ev("Object.keys(issueView.recent)")) == 0)
h.ev("root.signingOut = false"); h.stop_all(); h.spin(30)
h.finish()
fails = [n for n, c in h.results if not c]
print("passed %d failed %d" % (len(h.results) - len(fails), len(fails)))
sys.exit(1 if fails else 0)
