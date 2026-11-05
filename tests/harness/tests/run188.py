# v0.1.88: Settings > Account says what glab's token may do, under "Signed in
# as": the scopes board-fetch access already read (no extra request), read
# only / read and write in words, "can't be read" for a browser sign-in, and
# nothing before that answer. Usage: run188.py <src>
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from fixtures import BOARD
P = "group/app"
h = Harness(sys.argv[1], {"id": "odevvy.gitlab-board", "settingsRevision": 2, "defaultProject": P, "defaultCollapsed": [], "boardStates": {}, "refreshIntervalSec": 60})
h.ev("panel.availableCardHeight = 620; panel.availableCardWidth = 1020")
h.ev("root.opened = true"); h.spin(60); h.answer("board", BOARD); h.spin(300)
ACC = lambda scopes: {"state": "ready", "message": "", "project": P, "level": 30, "scopes": scopes}
line = lambda: [it for it in h.visible(lambda it: it.objectName() == "accessLine")]
signed = lambda: next((it for it in h.visible(lambda it: str(it.property("text") or "").startswith("Signed in as"))), None)
ok = h.ok
h.ev("root.showView('settings')"); h.spin(100)
while h.running("whoami"): h.answer("whoami", {"state": "ready", "user": "o_devvy"})
h.spin(150)
ok("T1 before the access answer: no line", line() == [] and signed() is not None)
n = len(h.launched())
h.answer("access", ACC(["read_api"])); h.spin(150)
l = line()
ok("T2 read_api: a quiet line under Signed in as", len(l) == 1 and l[0].property("text") == "Access: read_api \u00b7 read only. Moving cards, labels and comments need api."
   and l[0].property("color").name() == h.ev("root.dim").name() and l[0].mapToScene(QPointF(0, 0)).y() >= signed().mapToScene(QPointF(0, signed().height())).y(), [x.property("text") for x in l])
ok("T3 no extra request for it", [c for c in h.launched()[n:] if c and "board-fetch" in str(c[0])] == [] and h.running("access") == [], h.launched()[n:])
h.ev("root.feed.access = ({})"); h.spin(30); h.ev("root.feed.setAccess(%r, Logic.accessEntry(JSON.stringify(%s)))" % (P, '{"state": "ready", "level": 30, "scopes": ["api"]}')); h.spin(100)
ok("T4 api: read and write, and when read_api is enough", [x.property("text") for x in line()] == ["Access: api \u00b7 read and write. Only moving cards, labels and comments need api; read_api is enough to look."], [x.property("text") for x in line()])
h.ev("root.feed.setAccess(%r, Logic.accessEntry(JSON.stringify(%s)))" % (P, '{"state": "ready", "level": 30, "scopes": null}')); h.spin(100)
ok("T5 a browser sign-in: can't be read", [x.property("text") for x in line()] == ["Access: can't be read for this sign-in (browser sign-in, not a token)."], [x.property("text") for x in line()])
h.ev("settingsView.confirming = true"); h.spin(60)
ok("T6 while Sign out asks: no line", line() == [])
sys.exit(h.finish())
