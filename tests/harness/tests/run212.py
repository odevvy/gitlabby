# v0.1.112: a steady header. The board-only buttons (columns, bots) sit right
# after the tabs; on Merge requests and To-do the read-only chip takes that
# spot. Updated, refresh, keyboard and settings stay put on every view, and the
# popup keeps its width. Header icon buttons have no fill: off is a dim glyph,
# hover brightens it to the foreground, on is accent, a hovered on icon a
# lighter accent. The Tab outline (v0.1.103) still frames them.
# Usage: run212.py <src> [outdir]
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
src = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else None
P = "group/app"
def iss(i, t, l): return {"iid": i, "title": t, "labels": l, "url": "https://gitlab.com/%s/-/issues/%d" % (P, i), "createdAt": "2026-11-07T09:00:00Z", "notes": 0, "assignees": []}
BOARD = {"state": "ready", "project": P, "updatedAt": "2026-11-07T14:10:00Z", "message": "", "labelColors": {}, "boards": [{"id": 1, "name": "Development"}], "board": {"id": 1, "name": "Development"}, "fallback": False,
  "columns": [{"name": "Open", "kind": "open", "issues": [iss(118, "Ideas", ["app-ui"])]}, {"name": "todo", "kind": "label", "listId": 1, "issues": [iss(116, "Share page", ["todo", "app-ui"])]},
              {"name": "in progress", "kind": "label", "listId": 3, "issues": [iss(114, "Digest wording", ["in progress", "api"])]}, {"name": "review", "kind": "label", "listId": 4, "issues": [iss(113, "Paginate", ["review", "api"])]},
              {"name": "Closed", "kind": "closed", "issues": []}]}
BOTS = {P: {"busyLists": ["in progress", "review"], "bots": [{"name": "App UI", "label": "app-ui"}, {"name": "API Engineer", "label": "api"}]}}
def mr(i, t): return {"iid": i, "title": t, "url": "https://gitlab.com/%s/-/merge_requests/%d" % (P, i), "draft": False, "project": P, "branch": "b%d" % i, "updatedAt": "2026-11-07T14:00:00Z", "status": "mergeable", "author": {"username": "o", "name": "odevvy", "avatar": ""}, "pipeline": None, "reviewers": []}
MRS = {"state": "ready", "message": "", "scope": "all", "updatedAt": "2026-11-07T14:10:00Z", "review": [], "mine": [mr(132, "docs: apply #126"), mr(131, "feat: alerts")]}
TODOS = {"state": "ready", "message": "", "updatedAt": "2026-11-07T14:10:00Z", "todos": []}
h = Harness(src, {"id": "odevvy.gitlabby", "settingsRevision": 2, "defaultProject": P, "defaultCollapsed": [], "bots": BOTS})
h.ev("panel.availableCardHeight = 900; panel.availableCardWidth = 1460")
h.ev("root.opened = true"); h.spin(80); h.answer("board", BOARD); h.spin(1300)
S = lambda n: h.ev("Style.space(%d)" % n)
same = lambda a, c: abs(a.redF() - c.redF()) < 0.01 and abs(a.greenF() - c.greenF()) < 0.01 and abs(a.blueF() - c.blueF()) < 0.01
col = lambda n: h.ev("root." + n)
def rest(): QTest.mouseMove(h.win, QPoint(1, 1)); h.spin(150)
def hover(n): QTest.mouseMove(h.win, h.scene(h.ev("header." + n))); h.spin(150)
glyph = lambda n: h.ev("header.%s.color" % n)
# Where the steady parts are: the right edge of each (refresh measured at its centre, it may be turning).
def steady():
    return {"card": round(h.cls("KeyboardPanel").width()), "status": round(h.ev("header.status.x + header.status.width")),
            "refresh": round(h.ev("header.refreshButton.x + header.refreshButton.width / 2")), "keys": round(h.ev("header.keysButton.x")), "gear": round(h.ev("header.gear.x"))}
def shot(name):
    if out: rest(); h.grab_card(os.path.join(out, name + ".png"))
rest(); b0 = steady()
tabsEnd = h.ev("header.tabs.x + header.tabs.width")
h.ok("L1 board: columns 10 after the tabs, bots 4 after it", h.ev("header.columnsButton.visible") and h.ev("header.botsButton.visible")
     and abs(h.ev("header.columnsButton.x") - (tabsEnd + S(10))) < 1 and abs(h.ev("header.botsButton.x") - (h.ev("header.columnsButton.x + header.columnsButton.width") + S(4))) < 1, (tabsEnd, h.ev("header.columnsButton.x"), h.ev("header.botsButton.x")))
h.ok("L2 board: Updated starts after the bots, ends 8 before refresh", h.ev("header.status.x") >= h.ev("header.botsButton.x + header.botsButton.width") + S(12) - 0.5
     and abs(h.ev("header.status.x + header.status.width") - (h.ev("header.refreshButton.x") - S(8))) < 1)
shot("header-board")
for v, data in (("mrs", MRS), ("todos", TODOS)):
    h.ev("root.showView('%s')" % v); h.spin(100)
    if h.running(v): h.answer(v, data)
    h.spin(1300); rest()
    h.ok("L3 %s: the board-only buttons gone, the read-only chip after the tabs" % v, not h.ev("header.columnsButton.visible") and not h.ev("header.botsButton.visible")
         and h.ev("header.readOnlyChip.visible") and abs(h.ev("header.readOnlyChip.x") - (h.ev("header.tabs.x + header.tabs.width") + S(10))) < 1, h.ev("header.readOnlyChip.x"))
    h.ok("L4 %s: Updated, refresh, keyboard, settings and the popup width as on the board" % v, steady() == b0, (steady(), b0))
    shot("header-" + v)
h.ev("root.showView('board')"); h.spin(1300); rest()
h.ok("L5 back on the board: nothing on the right moved", steady() == b0, (steady(), b0))
# --- colours ----------------------------------------------------------------------
h.ok("C0 no fill behind any header icon button", not [it for it in h.walk(h.ev("header")) if it.objectName() == "headFill" and it.parentItem().property("active") is not None])
h.ok("C1 off: a dim glyph (columns closed)", h.ev("root.columnChips") is False and same(glyph("columnsButton"), col("dim")))
h.ok("C2 on: an accent glyph (bots shown)", h.ev("header.botsButton.active") and same(glyph("botsButton"), col("accent")))
hover("columnsButton")
h.ok("C3 hovering an off icon: the foreground", same(glyph("columnsButton"), col("foreground")))
hover("botsButton")
lighter = h.ev("Qt.lighter(root.accent, 1.2)")
h.ok("C4 hovering an on icon: a lighter accent", same(glyph("botsButton"), lighter) and not same(lighter, col("accent")))
rest()
h.ok("C5 the pointer gone: accent again", same(glyph("botsButton"), col("accent")))
h.ev("root.columnChips = true"); h.spin(60)
h.ok("C6 columns on: accent", same(glyph("columnsButton"), col("accent")))
h.ev("root.columnChips = false"); h.ev("root.toggleView('settings')"); h.spin(200); rest()
h.ok("C7 Settings open: an accent gear", same(glyph("gear"), col("accent")))
hover("gear")
h.ok("C8 hovering the open gear: the lighter accent", same(glyph("gear"), lighter))
rest(); h.ev("root.toggleView('settings')"); h.spin(200)
h.ok("C9 Settings closed: a dim gear", same(glyph("gear"), col("dim")))
# --- the Tab outline still frames them ------------------------------------------------
for n in ("columnsButton", "botsButton"):
    h.ev("root.kbFocus = header.%s" % n); h.spin(60)
    ring = [it for it in h.walk(h.ev("header." + n)) if it.objectName() == "focusRing"]
    h.ok("F1 Tab focus on %s: the outline shows" % n, ring and ring[0].isVisible())
order = h.ev("root.focusOrder().map(function(o){ return o.tip || '' })")
h.ok("F2 Tab order follows the eye: columns and bots before refresh", order.index("Show or hide columns") < order.index("Hide bots (b)") < order.index("Refresh (r)") < order.index("Keyboard shortcuts (?)"), order)
sys.exit(h.finish())
