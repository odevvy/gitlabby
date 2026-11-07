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
h = Harness(src, {"id": "odevvy.gitlabby", "settingsRevision": 2, "defaultProject": P, "defaultCollapsed": ["open", "closed"], "bots": {P: {"busyLists": ["review"], "bots": [{"name": "QA", "list": "review"}]}}})
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
h.click(h.ev("header.columnsButton")); QTest.mouseMove(h.win, QPoint(1, 1)); h.spin(120)
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
# --- stage 4: the column row on demand
chips = lambda: sorted(h.visible(lambda it: it.metaObject().className().startswith("Pill") and it.parentItem() is not None and it.parentItem().metaObject().className().startswith("QQuickFlow")), key=lambda it: it.mapToScene(QPointF(0, 0)).x())
bv = h.cls("BoardView")
top_closed = h.ev("boardView.children[1].y")
ok("C1 the column row is closed by default: no chips, the columns start at the top", len(chips()) == 0 and top_closed == 0, (len(chips()), top_closed))
h.ev("root.columnChips = true"); h.spin(200)
ok("C2 open: one chip per column, with counts, the columns below them", [str(c.property("label")) for c in chips()] == ["Open 1", "todo 0", "review 1", "Closed 1"] and h.ev("boardView.children[1].y") > 0, [str(c.property("label")) for c in chips()])
shot("board-columns")
h.click(chips()[1]); h.spin(150)
ok("C3 a chip still hides its column", h.ev("root.isHidden('todo')") is True)
h.click([c for c in chips() if str(c.property("label")).startswith("todo")][0]); h.spin(150)
h.ev("root.columnChips = false"); h.spin(200)
ok("C4 closed again: the board grows back to the top", h.ev("boardView.children[1].y") == 0)
# --- stage 5: columns and strips
heads = bt(lambda it: it.objectName() == "columnCount")
ok("K1 column counts are quiet numbers, no pills in the headers", sorted(str(x.property("text")) for x in heads) == ["0", "1"], [str(x.property("text")) for x in heads])
ok("K2 count colour quiet", heads and all(same(x.property("color"), col("quiet")) for x in heads))
names = txt("review") + txt("todo")
ok("K3 column names as written, not in capitals", names and all(x.property("font").capitalization() == QFont.MixedCase for x in names))
QTest.mouseMove(h.win, QPoint(1, 1)); h.spin(200)
ok("K4 a column with cards: name in the text colour; an empty one dim", same(txt("review")[0].property("color"), col("foreground")) and same(txt("todo")[0].property("color"), col("dim")))
panes = [it for it in h.walk() if it.metaObject().className().startswith("QQuickRectangle") and abs(it.property("radius") - h.ev("Style.space(8)")) < 0.1 and it.parentItem() is not None and it.parentItem().property("dropHot") is not None]
pw = lambda it, k: h.ev(k, QQmlEngine.contextForObject(it), it)
ok("K5 no outline on the column panes", len(panes) == 4 and all(pw(p, "border.width") == 0 for p in panes), [pw(p, "border.width") for p in panes])
strips = bt(lambda it: it.objectName() == "stripCount")
ok("K6 strips: the count as a dim number", sorted(str(x.property("text")) for x in strips) == ["1", "1"] and all(same(x.property("color"), col("dim")) for x in strips), [str(x.property("text")) for x in strips])
sname = txt("Open") + txt("Closed")
ok("K7 strip names as written, quiet", len(sname) == 2 and all(x.property("font").capitalization() == QFont.MixedCase and same(x.property("color"), col("quiet")) for x in sname))
ok("K8 no coloured rule under the column headers", not [it for it in h.walk() if it.metaObject().className() == "QQuickRectangle" and it.height() == max(1, h.ev("Style.space(2)")) and it.parentItem() is not None and it.parentItem().property("implicitHeight") is not None and any(c.objectName() == "columnCount" for c in h.walk() if it.parentItem().isAncestorOf(c))])
# --- stage 6: cards, empty columns, the bots row
card = h.visible(lambda it: it.property("movable") is not None and it.property("lifted") is not None)
title = txt("Magic link: expire after one use")
ok("D1 the card shows its title alone, plain", len(title) == 1 and "#" not in [x.property("text") for x in title][0], [x.property("text") for x in bt(lambda it: card and card[0].isAncestorOf(it))])
iid = bt(lambda it: it.objectName() == "cardIid")
ok("D2 '#135' on the quiet footer line, below the title", len(title) == 1 and len(iid) == 1 and iid[0].property("text") == "#135" and same(iid[0].property("color"), col("quiet")) and iid[0].mapToScene(QPointF(0, 0)).y() > title[0].mapToScene(QPointF(0, 0)).y())
meta = bt(lambda it: card and card[0].isAncestorOf(it) and str(it.property("text") or "").startswith("\uf075"))
ok("D3 comments and age quiet too", len(meta) == 1 and same(meta[0].property("color"), col("quiet")))
ok("D4 no outline at rest", card and pw(card[0], "border.color.a") == 0)
QTest.mouseMove(h.win, h.scene(card[0])); h.spin(250)
ok("D5 hovered: it lifts and lights as before", card[0].property("hovered") is True)
QTest.mouseMove(h.win, QPoint(1, 1)); h.spin(200)
empty = txt("No issues")
ok("D6 'No issues' quiet, upright", len(empty) == 1 and same(empty[0].property("color"), col("quiet")) and not empty[0].property("font").italic())
br = h.cls("BotsRow")
ok("D7 no rule under the bots row", br is not None and br.isVisible() and not [c for c in br.childItems() if c.metaObject().className().startswith("QQuickRectangle") and c.height() <= 1 and c.width() >= br.width() - 1])
shot("board")
print("passed %d failed %d" % (sum(ALL), len(ALL) - sum(ALL)))
h.finish()
