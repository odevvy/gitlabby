# v0.1.109: the issue's open action says where it goes. Settings > Open links
# in > App window: "Open in app window ↗", its tip, the Truncated link and the
# key list say app window; Browser tab keeps "Open in browser".
# Usage: run209.py <src>
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
P = "group/app"
ISSUE = {"iid": 1, "title": "First issue", "url": "https://gitlab.com/group/app/-/issues/1", "labels": [], "assignees": [], "state": "opened"}
BOARD = {"state": "ready", "project": P, "updatedAt": "2026-10-31T13:20:00Z", "message": "", "labelColors": {}, "boards": [{"id": 1, "name": "Dev"}], "board": {"id": 1, "name": "Dev"}, "fallback": False,
  "columns": [{"name": "Open", "kind": "open", "issues": [ISSUE]}, {"name": "Closed", "kind": "closed", "issues": []}]}
h = Harness(sys.argv[1], {"id": "odevvy.gitlabby", "settingsRevision": 2, "defaultProject": P, "defaultCollapsed": [], "favorites": [], "serverFavorites": {}})
h.ev("panel.availableCardHeight = 700; panel.availableCardWidth = 1460")
h.ev("root.opened = true"); h.spin(60); h.answer("board", BOARD); h.spin(150)
ev = h.ev
def labels(): return [str(it.property("label")) for it in h.walk() if it.isVisible() and it.metaObject().className().startswith("Pill")]
def tips(): return [str(c.property("text")) for it in h.walk() for c in it.children() if c.metaObject().className().startswith("IconTip")]
def whats(): return [str(it.property("text")) for it in h.walk() if it.objectName() == "keyWhat"]
LONG = "word " * 4100

for mode, want in (("browser", "Open in browser"), ("app", "Open in app window")):
    ev("root.setLinkMode('%s')" % mode); h.spin(40)
    ev("root.openIssue(root.columns[0].issues[0])"); h.spin(80)
    h.answer("issue", {"state": "ready", "message": "", "issue": dict(ISSUE, description=LONG), "comments": []}); h.spin(120)
    ls = labels()
    h.ok("%s I1 the open pill says %s" % (mode, want), (want + " ↗") in ls, ls)
    h.ok("%s I2 its tip says it too" % mode, (want + " (o)") in tips(), tips())
    h.ok("%s I3 the Truncated link follows" % mode, ("Truncated · " + want + " for the rest ↗") in ls, ls)
    other = "Open in browser" if mode == "app" else "Open in app window"
    h.ok("%s I4 no wording for the other destination" % mode, not any(other in l for l in ls) and not any(other in t for t in tips()))
    ev("root.back()"); h.spin(40)
    ev("root.showView('keys')"); h.spin(80)
    w = whats()
    h.ok("%s K1 the key list says %s for o" % (mode, want), w.count(want) == 4 and other not in w, w)
    ev("root.back()"); h.spin(40)
sys.exit(h.finish())
