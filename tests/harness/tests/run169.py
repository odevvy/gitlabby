# v0.1.69: refresh sits next to the status. Header icons, left to right:
# Updated · refresh · columns (board only) · keyboard · settings, 4 apart,
# each with its own tip; without the columns button refresh moves up to the
# keyboard button.
# Usage: run169.py <src>
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from fixtures import BOARD
h = Harness(sys.argv[1], {"id": "odevvy.gitlabby", "settingsRevision": 2, "defaultProject": "group/app", "defaultCollapsed": [], "boardStates": {}, "refreshIntervalSec": 60})
h.ev("panel.availableCardHeight = 900; panel.availableCardWidth = 1460")
h.ev("root.opened = true"); h.spin(80); h.answer("board", BOARD); h.spin(400)
S = lambda n: h.ev("Style.space(%d)" % n)
def xs(names): return [(round(h.ev("header.%s.x" % n)), round(h.ev("header.%s.x + header.%s.width" % (n, n)))) for n in names]
def row(names):
    b = xs(names); return [round(c[0] - a[1]) for a, c in zip(b, b[1:])], b
def status_left_of_refresh():
    return h.ev("header.status.x + header.status.width") <= h.ev("header.refreshButton.x") - S(8) + 0.5
gaps, b = row(["refreshButton", "keysButton", "gear"])
h.ok("H1 board: refresh, keyboard, settings 4 apart; columns after the tabs (v0.1.112)", h.ev("header.columnsButton.visible") and gaps == [S(4)] * 2 and h.ev("header.columnsButton.x") < h.ev("header.status.x"), b)
h.ok("H2 Updated sits just left of refresh", status_left_of_refresh() and h.ev("header.status.text") != "", (h.ev("header.status.x + header.status.width"), h.ev("header.refreshButton.x")))
h.ok("H3 each keeps its tip", [h.ev("header.%s.tip" % n) for n in ("refreshButton", "columnsButton")] == ["Refresh (r)", "Show or hide columns"])
h.click(h.ev("header.columnsButton")); h.spin(100)
h.ok("H4 the columns button opens the column chips", h.ev("root.columnChips") is True)
h.click(h.ev("header.columnsButton")); h.spin(100)
n0 = len([r for r in h.launched() if r and "board" in r])
h.click(h.ev("header.refreshButton")); h.spin(100)
h.ok("H5 the refresh button refreshes", h.running("board") or len([r for r in h.launched() if r and "board" in r]) > n0)
if h.running("board"): h.answer("board", BOARD)
h.spin(1200)
for v in ("mrs", "settings"):
    h.ev("root.showView('%s')" % v); h.spin(150)
    gaps, b = row(["refreshButton", "keysButton", "gear"])
    h.ok("H6 %s: no columns button, refresh right before the keyboard" % v, not h.ev("header.columnsButton.visible") and gaps == [S(4)] * 2 and status_left_of_refresh(), b)
h.ev("root.showView('board')"); h.spin(150)
gaps, b = row(["refreshButton", "keysButton", "gear"])
h.ok("H7 back on the board, columns returns after the tabs; the right three stay", h.ev("header.columnsButton.visible") and gaps == [S(4)] * 2, b)
sys.exit(h.finish())
