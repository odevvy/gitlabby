# v0.1.71 (v171 design 1A, 2, 3A): even 10 px gaps between the title, the
# bots, the column chips and the columns; one "Updated" on Merge requests
# (the header's, with the lists' read time); a quiet "read-only" chip after
# the tabs there, the row under it only the scope.
# Usage: run171.py <src>
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from fixtures import BOARD
P = "group/app"
BOTS = {P: {"busyLists": ["in progress", "review"], "bots": [{"name": "App UI", "label": "app-ui"}, {"name": "Spec QA", "list": "review"}]}}
h = Harness(sys.argv[1], {"id": "odevvy.gitlab-board", "settingsRevision": 2, "defaultProject": P, "defaultCollapsed": [], "boardStates": {}, "refreshIntervalSec": 60, "bots": BOTS})
h.ev("panel.availableCardHeight = 620; panel.availableCardWidth = 1020")
h.ev("root.opened = true"); h.spin(60); h.answer("board", BOARD); h.spin(400)
S = lambda n: h.ev("Style.space(%d)" % n)
card = h.cls("KeyboardPanel")
Y = lambda it: it.mapToItem(card, QPointF(0, 0)).y()
# --- 1A: even gaps ---------------------------------------------------------------------------
bots = h.cls("BotsRow"); bv = h.cls("BoardView"); hd = h.ev("header")
texts = [it for it in h.walk(bots) if it.inherits("QQuickText") and it.isVisible() and it.property("text")]
bot_bottom = max(Y(t) + t.height() for t in texts) if texts else -1
h.ok("A0 the bots row shows", bots.isVisible() and texts != [], len(texts))
h.ok("A1 title → bots 10", round(Y(bots) - (Y(hd) + hd.height())) == S(10), (Y(hd) + hd.height(), Y(bots)))
h.ok("A2 no empty space under the bots: the row ends with its text", abs(Y(bots) + bots.height() - bot_bottom) < 1, (Y(bots) + bots.height(), bot_bottom))
h.ok("A3 bots → columns 10, the same", round(Y(bv) - (Y(bots) + bots.height())) == S(10), (Y(bots) + bots.height(), Y(bv)))
h.ev("root.columnChips = true"); h.spin(300)
chips = [it for it in h.walk(bv) if it.metaObject().className().startswith("Pill") and it.isVisible()]
top = min(Y(c) for c in chips) if chips else -1; low = max(Y(c) + c.height() for c in chips) if chips else -1
fl = h.ev("flick", h.ctx_of(bv), bv)
h.ok("A4 chips open: bots → chips 10, chips → columns 10", chips and round(top - (Y(bots) + bots.height())) == S(10) and round(Y(fl) - low) == S(10), (Y(bots) + bots.height(), top, low, Y(fl)))
h.ev("root.columnChips = false"); h.spin(300)
# --- 2: one Updated on Merge requests ----------------------------------------------------------
board_time = h.ev("header.status.text")
h.ev("root.showView('mrs')"); h.spin(100)
while h.running("mrs"): h.answer("mrs", {"state": "ready", "message": "", "review": [], "mine": []})
h.spin(700)
mv = h.cls("MrsView")
said = [str(it.property("text")) for it in h.walk(mv) if it.inherits("QQuickText") and it.isVisible() and ("updated" in str(it.property("text")).lower() or "refreshing" in str(it.property("text")))]
h.ok("B1 Merge requests: no second 'updated' under the header", said == [], said)
want = "Updated " + h.ev("Qt.formatTime(new Date(mrsView.entry.startedAt), 'HH:mm')")
h.ok("B2 the header's Updated is when the lists were read", h.ev("header.status.text") == want and want != board_time, (h.ev("header.status.text"), want, board_time))
h.key(Qt.Key_R, "r"); h.spin(60)
said = [str(it.property("text")) for it in h.walk(mv) if it.inherits("QQuickText") and it.isVisible() and "refreshing" in str(it.property("text"))]
h.ok("B3 r: the header alone says Updating…", h.ev("header.status.text") == "Updating\u2026" and said == [], (h.ev("header.status.text"), said))
while h.running("mrs"): h.answer("mrs", {"state": "ready", "message": "", "review": [], "mine": []})
h.spin(800)
h.ev("root.showView('board')"); h.spin(150)
h.ok("B4 back on the board: the board's time", h.ev("header.status.text") == board_time, (h.ev("header.status.text"), board_time))
# --- 3A: the read-only chip after the tabs ------------------------------------------------------
chip = h.ev("header.readOnlyChip")
h.ok("C0 the header has a read-only chip", chip is not None)
if chip is not None:
  h.ok("C1 the board: no chip", not chip.isVisible())
  h.ev("root.showView('mrs')"); h.spin(100)
  while h.running("mrs"): h.answer("mrs", {"state": "ready", "message": "", "review": [], "mine": []})
  h.spin(400)
  txt = [c for c in h.walk(chip) if c.inherits("QQuickText")][0]
  quiet = h.ev("root.quiet")
  near = lambda a, b: all(abs(x - y) < 0.01 for x, y in zip(a.getRgbF(), b.getRgbF()))
  h.ok("C2 Merge requests: a quiet outlined 'read-only' chip", chip.isVisible() and txt.property("text") == "read-only" and near(txt.property("color"), quiet)
       and chip.property("color").alphaF() == 0 and h.ev("header.readOnlyChip.border.width") == 1, (txt.property("text"), txt.property("color"), quiet))
  tabs = h.ev("header.tabs"); hd = h.ev("header")
  cy = lambda it: it.mapToItem(hd, QPointF(0, it.height() / 2)).y()
  h.ok("C3 right after the tabs (10 apart), centred on them", round(chip.x() - (tabs.x() + tabs.width())) == S(10) and abs(cy(chip) - cy(tabs)) < 1, (chip.x(), tabs.x() + tabs.width()))
  h.ok("C4 clear of the status and the buttons", chip.x() + chip.width() <= h.ev("header.status.x") + 0.5 and chip.x() + chip.width() < h.ev("header.refreshButton.x"))
  mv = h.cls("MrsView")
  ro = [it for it in h.walk(mv) if it.inherits("QQuickText") and it.isVisible() and "read-only" in str(it.property("text"))]
  h.ok("C5 the row under the header holds only the scope", ro == [] and not any(it.objectName() == "mrsNote" for it in h.walk(mv)))
  # Short of room the chip goes with the long tab name; the status keeps its 48 points.
  title = [it for it in h.walk(hd) if it.inherits("QQuickText") and str(it.property("text")).startswith(P)][0]
  seen, bad = set(), []
  for w in (760, 700, 660, 640, 600, 560):
      h.ev("panel.availableCardWidth = %d" % w); h.spin(200)
      tight = h.ev("header.compactTabs"); seen.add(tight)
      room = h.ev("header.refreshButton.x") - (chip.x() + chip.width() if chip.isVisible() else tabs.x() + tabs.width())
      if chip.isVisible() == tight or room < S(12 + 48) - 0.5 or title.width() < min(title.property("implicitWidth"), h.ev("header.titleRoom")) - 0.5:
          bad.append((w, tight, chip.isVisible(), room, title.width(), title.property("implicitWidth")))
  h.ok("C6 narrower: the chip goes with the long tab name, the status keeps 48 points, the title its room", bad == [] and seen == {True, False}, bad)
  h.ev("panel.availableCardWidth = 1020"); h.spin(300)
  h.ev("root.showView('settings')"); h.spin(100)
  h.ok("C7 Settings: no chip", not chip.isVisible())
  h.ev("root.showView('board')"); h.spin(100)
sys.exit(h.finish())
