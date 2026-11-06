# v0.1.47: the popup's key routing moved from Board.qml into BoardKeys.qml.
# keyCatcher is a BoardKeys handed root and every view by its Board.qml id;
# keys still reach the issue view, settings, the MR and key views and close.
# Usage: run147.py <src>
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
src = sys.argv[1]
ALL = []
def ok(n, c, e=""): ALL.append(bool(c)); h.ok(n, c, e)
h = Harness(src, {"id": "odevvy.gitlabby", "settingsRevision": 2, "defaultProject": "a/b"})
ok("K1 keyCatcher is a BoardKeys with root as its host",
   h.ev("keyCatcher.toString().indexOf('BoardKeys') === 0 && keyCatcher.host === root"), h.ev("keyCatcher.toString()"))
for name in ["issueView", "picker", "settingsView", "bulkBar", "mrsView", "setupView"]:
    ok("K2 keyCatcher.%s is Board.qml's %s" % (name, name), h.ev("keyCatcher.%s !== null && keyCatcher.%s === %s" % (name, name, name)))
h.ev("root.opened = true"); h.spin(60)
row = {"iid": 7, "title": "t", "url": "https://gitlab.com/a/b/-/issues/7", "labels": [], "state": "opened"}
h.ev("root.openIssue(%s)" % json.dumps(row)); h.spin(60)
h.ev("issueView.confirming = true; keyCatcher.forceActiveFocus()"); h.spin(30); h.key(Qt.Key_Escape)
ok("K3 Escape in the issue view drops its close question, the view stays", h.ev("issueView.confirming === false && root.view === 'issue'"), h.ev("root.view"))
h.key(Qt.Key_Escape)
ok("K3 Escape again goes back to the board", h.ev("root.view") == "board", h.ev("root.view"))
h.key(Qt.Key_M, "m"); ok("K4 m opens the merge requests view", h.ev("root.view") == "mrs", h.ev("root.view"))
h.key(Qt.Key_M, "m"); ok("K4 m again closes it", h.ev("root.view") == "board", h.ev("root.view"))
h.key(Qt.Key_Question, "?"); ok("K5 ? opens the keys view", h.ev("root.view") == "keys", h.ev("root.view"))
h.key(Qt.Key_Escape); h.stop_all(); h.key(Qt.Key_Escape)
ok("K6 Escape on the board closes the popup", h.ev("root.opened") is False, h.ev("root.opened"))
print("passed %d failed %d" % (sum(ALL), len(ALL) - sum(ALL)))
h.finish()
