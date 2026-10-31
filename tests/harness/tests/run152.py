# v0.1.52: a quieter board (v152 design, direction A). The header: "project /
# board", a quiet chevron and star, a quiet "Updated", and a columns button that
# opens the show/hide-columns row (closed by default). Columns: no outline, a
# dot, the name as written, the count as a quiet number. Strips: count, dot,
# name. Cards: no outline at rest, the title first, "#iid" on the quiet footer.
# The bots row loses its rule underneath.
# Usage: run152.py <src> [outdir]   (previews: board, board-columns)
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from PySide6.QtGui import QFont, QColor
src = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else None
ALL = []
def ok(n, c, e=""): ALL.append(bool(c)); h.ok(n, c, e)
P = "group/app"
def iss(iid, labels, title=None): return {"iid": iid, "title": title or "Issue %d" % iid, "labels": labels, "url": "https://gitlab.com/%s/-/issues/%d" % (P, iid), "createdAt": "2026-10-31T09:00:00Z", "notes": 2, "assignees": []}
BOARD = {"state": "ready", "project": P, "updatedAt": "2026-10-31T13:20:00Z", "message": "", "labelColors": {}, "boards": [{"id": 1, "name": "Dev"}], "board": {"id": 1, "name": "Dev"}, "fallback": False,
  "columns": [{"name": "Open", "kind": "open", "issues": [iss(101, [])]},
    {"name": "todo", "kind": "label", "listId": 2, "color": "#5b9bd5", "issues": []},
    {"name": "review", "kind": "label", "listId": 4, "color": "#a855f7", "issues": [iss(135, ["review"], "Magic link: expire after one use")]},
    {"name": "Closed", "kind": "closed", "issues": [iss(90, [])]}]}
h = Harness(src, {"id": "odevvy.gitlab-board", "settingsRevision": 2, "defaultProject": P, "defaultCollapsed": ["open", "closed"], "bots": {P: {"busyLists": ["review"], "bots": [{"name": "QA", "list": "review"}]}}})
h.ev("panel.availableCardHeight = 900; panel.availableCardWidth = 1460")
h.ev("root.opened = true"); h.spin(60); h.answer("board", BOARD); h.spin(200)
same = lambda a, c: abs(a.redF() - c.redF()) < 0.01 and abs(a.greenF() - c.greenF()) < 0.01 and abs(a.blueF() - c.blueF()) < 0.01
col = lambda k: h.ev("root." + k)
bt = lambda pred: h.visible(lambda it: it.metaObject().className().startswith("BoardText") and pred(it))
txt = lambda t: bt(lambda it: str(it.property("text") or "") == t)
def shot(name):
    if out: QTest.mouseMove(h.win, QPoint(1, 1)); h.spin(400); os.makedirs(out, exist_ok=True); h.grab_card(out + "/" + name + ".png")
# --- stage 2: header
lum = lambda c: 0.2126 * c.redF() + 0.7152 * c.greenF() + 0.0722 * c.blueF()
ok("H0 quiet is a third text level: fainter than dim, still above the background", lum(col("background")) < lum(col("quiet")) < lum(col("dim")) - 0.05, (lum(col("quiet")), lum(col("dim"))))
ok("H1 the title reads 'project / board'", h.ev("header.children.filter(function(c) { return c.text === 'group/app / Dev' }).length") == 1, h.ev("header.children.map(function(c) { return c.text || '' })"))
ok("H2 the chevron is quiet at rest", same(h.ev("header.chevron.color"), col("quiet")))
ok("H3 the star is not orange at rest", not same(h.ev("header.defaultMark.color"), col("accent")))
cb = h.ev("header.columnsButton.text")
ok("H4 a columns button sits in the header on the board, nothing hidden: just the glyph", cb == "\uf0db" and h.ev("header.columnsButton.visible") is True, cb)
ok("H5 its colour: dim while the row is closed", same(h.ev("header.columnsButton.color"), col("dim")) and h.ev("root.columnChips") is False)
h.click(h.ev("header.columnsButton"))
ok("H6 a click opens the column row; the button turns accent", h.ev("root.columnChips") is True and same(h.ev("header.columnsButton.color"), col("accent")))
h.click(h.ev("header.columnsButton"))
ok("H7 a second click closes it", h.ev("root.columnChips") is False)
h.ev("root.toggleHidden('todo')"); h.spin(150)
ok("H8 with a column hidden the button says how many", h.ev("header.columnsButton.text") == "\uf0db 1", h.ev("header.columnsButton.text"))
h.ev("root.toggleHidden('todo')"); h.spin(150)
h.ev("root.showView('settings')"); h.spin(100)
ok("H9 not on other views", h.ev("header.columnsButton.visible") is False)
h.ev("root.back()"); h.spin(100)
# --- stage 3: status
ok("S1 'Updated' is quiet, not dim", same(h.ev("header.status.color"), col("quiet")) and str(h.ev("header.status.text")).startswith("Updated"), h.ev("header.status.text"))
shot("board")
print("passed %d failed %d" % (sum(ALL), len(ALL) - sum(ALL)))
h.finish()
