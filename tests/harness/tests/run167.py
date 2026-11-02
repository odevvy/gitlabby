# v0.1.67: calm loading. The picker's spinner row (LoadingRow) is the one
# loading look: the issue view shows it once, only after 250 ms, where the
# description goes and then under Comments, with no bar and no other
# "Loading…"; its state and actions keep their place. A refresh you ask for
# says "Updating…" (at least half a second); the timer's keeps the time.
# Settings, Shortcuts and the issue view fade their bottom edge while there
# is more below. Usage: run167.py <src>
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from fixtures import BOARD
h = Harness(sys.argv[1], {"id": "odevvy.gitlab-board", "settingsRevision": 2, "defaultProject": "group/app", "defaultCollapsed": [], "boardStates": {}, "refreshIntervalSec": 60})
h.ev("panel.availableCardHeight = 900; panel.availableCardWidth = 1460")
cls_is = lambda it, n: it.metaObject().className().startswith(n)
named = lambda n: [it for it in h.walk() if it.objectName() == n]
shown = lambda n: [it for it in named(n) if it.isVisible()]
rows = lambda: h.visible(lambda it: cls_is(it, "LoadingRow"))
spinners = lambda: h.visible(lambda it: cls_is(it, "Spinner"))
loadings = lambda: [it for it in h.visible(lambda it: cls_is(it, "BoardText")) if "Loading" in str(it.property("text") or "")]
same = lambda a, c: abs(a.redF() - c.redF()) < 0.01 and abs(a.greenF() - c.greenF()) < 0.01 and abs(a.blueF() - c.blueF()) < 0.01
h.ev("root.opened = true"); h.spin(60); h.answer("board", BOARD); h.spin(200)
# --- the picker's loading row, now LoadingRow -----------------------------------------------
h.ev("root.openPicker()"); h.spin(120)
pl = shown("pickerLoading")
h.ok("L1 picker loading: one LoadingRow, its Spinner turning, 'Loading…'", h.running("projects") != [] and len(pl) == 1 and cls_is(pl[0], "LoadingRow") and len(spinners()) == 1 and [t.property("text") for t in loadings()] == ["Loading…"])
lbl = loadings()[0] if loadings() else None
h.ok("L2 ...dim and italic, the spinner just left of it", lbl is not None and len(spinners()) == 1 and lbl.property("font").italic() and same(lbl.property("color"), h.ev("root.dim"))
     and spinners()[0].mapToScene(QPointF(spinners()[0].width(), 0)).x() <= lbl.mapToScene(QPointF(0, 0)).x())
h.answer("projects", {"state": "error", "message": "GitLab said no."}); h.spin(80)
h.ok("L3 a failed list: the same row, the reason, no spinner", len(shown("pickerLoading")) == 1 and spinners() == [] and shown("pickerLoading")[0].property("text") == "GitLab said no.")
h.ev("root.back()"); h.spin(80)
sys.exit(h.finish())
