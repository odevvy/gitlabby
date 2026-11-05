# v0.1.86: the Merge requests view loads like To-do. The first load is one
# LoadingRow (the accent spinner and the dim italic line), no header refresh;
# a reload with lists shown keeps them and the header shows it; an error is the
# same row, still, with how to retry. Usage: run186.py <src>
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from fixtures import BOARD
P = "group/app"
h = Harness(sys.argv[1], {"id": "odevvy.gitlab-board", "settingsRevision": 2, "defaultProject": P, "defaultCollapsed": [], "boardStates": {}, "refreshIntervalSec": 60})
h.ev("panel.availableCardHeight = 620; panel.availableCardWidth = 1020")
h.ev("root.opened = true"); h.spin(60); h.answer("board", BOARD); h.spin(400)
def named(n): return h.visible(lambda it: it.objectName() == n)
def mr(i): return {"iid": i, "title": "MR %d" % i, "url": "https://gitlab.com/%s/-/merge_requests/%d" % (P, i), "project": P, "sourceBranch": "b%d" % i,
                   "author": {"username": "alice", "name": "Alice", "avatar": ""}, "reviewers": [], "draft": False, "detailedMergeStatus": "mergeable", "pipeline": None}
ANS = {"state": "ready", "message": "", "scope": "all", "updatedAt": "2026-11-05T15:00:00Z", "review": [mr(1)], "mine": [mr(2)]}
ok = h.ok
h.ev("root.showView('mrs')"); h.spin(150)
m = named("mrsMessage")
ok("L1 the first load: one spinner row with the loading line", len(m) == 1 and m[0].property("text") == "Loading merge requests\u2026" and m[0].property("spinning") is True
   and any(it.metaObject().className().startswith("Spinner") and it.property("running") is True for it in h.visible(lambda it: True)), [x.property("text") for x in m])
ok("L2 the first load: no header refresh", h.ev("root.refreshActive") is False, h.ev("root.refreshActive"))
h.answer("mrs", ANS); h.spin(300)
ok("L3 answered: the spinner row gone, the rows shown", named("mrsMessage") == [] and len(named("mrRow")) == 2, len(named("mrRow")))
h.ev("mrsView.refresh()"); h.spin(60)
ok("L4 r with the lists shown: they stay, the header shows the refresh", len(h.running("mrs")) == 1 and len(named("mrRow")) == 2 and named("mrsMessage") == [] and h.ev("root.refreshActive") is True)
h.answer("mrs", {"state": "error", "message": "Could not load merge requests."}); h.spin(200)
m = named("mrsMessage")
ok("L5 an error: the same row, still, and how to retry", len(m) == 1 and m[0].property("spinning") is False and m[0].property("text") == "Could not load merge requests.  Press r to try again.", [x.property("text") for x in m])
sys.exit(h.finish())
