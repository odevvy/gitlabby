# v0.1.55: header buttons and view tabs (v155 design B, keyboard button kept).
# Board · Merge requests are tabs after the star (hairline before them, accent
# underline on the current one, 28 px high, a faint fill on hover), shown on
# those two views only. Right: Updated, then columns (board only), refresh,
# keyboard and settings as 28 px buttons with 14 px glyphs, 4 apart, a faint
# fill on hover and the accent tint while their view is open. The header keeps
# its height; the title is never cut more than before (Updated gives way first,
# then the Merge requests tab reads "MRs").
# Usage: run155.py <src> [outdir]   (previews: header, header-hover, header-mrs, header-narrow)
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
src = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else None
ALL = []
def ok(n, c, e=""): ALL.append(bool(c)); h.ok(n, c, e)
P = "firelink21/phrase41"
def col_(n, i): return {"name": n, "kind": "label", "listId": i, "color": "#5b9bd5", "issues": []}
def board(names):
    return {"state": "ready", "project": P, "updatedAt": "2026-10-31T13:20:00Z", "message": "", "labelColors": {}, "boards": [{"id": 1, "name": "Development"}], "board": {"id": 1, "name": "Development"}, "fallback": False,
            "columns": [{"name": "Open", "kind": "open", "issues": []}] + [col_(n, i) for i, n in enumerate(names)] + [{"name": "Closed", "kind": "closed", "issues": []}]}
WIDE = board(["research", "todo", "approved", "in progress", "review"])
def mr(iid): return {"iid": iid, "title": "MR %d" % iid, "url": "https://gitlab.com/%s/-/merge_requests/%d" % (P, iid), "draft": False, "project": P, "branch": "b", "updatedAt": "2026-10-31T13:00:00Z",
                     "status": "mergeable", "author": {"username": "a", "name": "A", "avatar": ""}, "pipeline": None, "reviewers": []}
ANS = {"state": "ready", "message": "", "scope": "all", "updatedAt": "2026-10-31T13:20:00Z", "review": [mr(1), mr(2)], "mine": []}
h = Harness(src, {"id": "odevvy.gitlab-board", "settingsRevision": 2, "defaultProject": P, "defaultCollapsed": ["open", "closed"]})
h.ev("panel.availableCardHeight = 900; panel.availableCardWidth = 1460")
h.ev("root.opened = true"); h.spin(60); h.answer("board", WIDE); h.spin(200)
same = lambda a, c: abs(a.redF() - c.redF()) < 0.01 and abs(a.greenF() - c.greenF()) < 0.01 and abs(a.blueF() - c.blueF()) < 0.01 and abs(a.alphaF() - c.alphaF()) < 0.02
col = lambda k: h.ev("root." + k)
hd = lambda k: h.ev("header." + k)
sx = lambda it: it.mapToScene(QPointF(0, 0)).x()
sy = lambda it: it.mapToScene(QPointF(0, 0)).y()
kids = lambda it, pred: [c for c in h.walk(it) if pred(c)]
fill = lambda it: kids(it, lambda c: c.objectName() == "headFill")[0]
glyph = lambda it: kids(it, lambda c: c.objectName() in ("headGlyph", "tabText"))[0]
line = lambda it: kids(it, lambda c: c.objectName() == "tabUnderline")[0]
S = lambda n: h.ev("Style.space(%d)" % n)
def rest(): QTest.mouseMove(h.win, QPoint(1, 1)); h.spin(120)
def hover(it): QTest.mouseMove(h.win, h.scene(it)); h.spin(150)
def shot(name):
    if out: rest(); os.makedirs(out, exist_ok=True); h.grab_card(out + "/" + name + ".png")
title = hd("children[0]")
bt, mt = hd("boardTab"), hd("mrsButton")
rest()
# --- tabs ----------------------------------------------------------------------
ok("T1 the tabs come after the star, past a hairline", hd("tabs.visible") and sx(hd("defaultMark")) + hd("defaultMark.width") < sx(hd("tabs")) and [glyph(bt).property("text"), glyph(mt).property("text")] == ["Board", "Merge requests"])
ok("T2 both tabs 28 px high", bt.height() == S(28) and mt.height() == S(28), (bt.height(), mt.height()))
ok("T3 on the board: Board underlined in the accent, bold; Merge requests not", line(bt).isVisible() and same(line(bt).property("color"), col("accent")) and glyph(bt).property("font").bold()
   and not line(mt).isVisible() and not glyph(mt).property("font").bold())
ok("T4 the header keeps its height (the 28 px targets reach into the gap)", hd("height") == max(title.property("implicitHeight"), hd("status.implicitHeight")) and hd("height") < S(28), hd("height"))
ub = sy(line(bt)) + line(bt).height(); hb = sy(h.ev("header")) + hd("height")
ok("T5 the underline ends above where the refresh bar runs", ub <= hb + round((h.ev("root.gap") - max(2, S(2))) / 2) + 0.01, (ub, hb))
hover(mt)
ok("T6 hovering a tab: a faint fill, its tip with the key", same(fill(mt).property("color"), hd("hoverFill")) and mt.property("tip") == "Merge requests (m)" and same(glyph(mt).property("color"), col("foreground")))
shot("header-hover-tab")
hover(bt)
ok("T7 the current tab gets no hover fill", fill(bt).property("color").alphaF() == 0)
rest()
# --- buttons -------------------------------------------------------------------
btns = [hd(n) for n in ("columnsButton", "refreshButton", "keysButton", "gear")]
ok("B1 four buttons on the board: columns, refresh, keyboard, settings", all(b.isVisible() for b in btns) and [glyph(b).property("text") for b in btns] == ["\uf0db", "\uf021", "\uf11c", "\uf013"])
ok("B2 each at least 28 x 28, glyphs at the title size (14)", all(b.width() >= S(28) and b.height() == S(28) and glyph(b).property("font").pixelSize() == h.ev("Style.font.title") for b in btns), [(b.width(), b.height()) for b in btns])
gaps = [round(b.x() - (a.x() + a.width())) for a, b in zip(btns, btns[1:])]
ok("B3 4 apart, the gear at the right edge", gaps == [S(4)] * 3 and abs(btns[-1].x() + btns[-1].width() - hd("width")) < 1, gaps)
ok("B4 at rest: no fill, dim glyphs", all(fill(b).property("color").alphaF() == 0 and same(glyph(b).property("color"), col("dim")) for b in btns))
hover(hd("gear"))
ok("B5 hovering a button: a faint fill, the glyph in the foreground", same(fill(hd("gear")).property("color"), hd("hoverFill")) and same(glyph(hd("gear")).property("color"), col("foreground")))
ok("B6 tips keep their keys", [b.property("tip") for b in btns[1:]] == ["Refresh (r)", "Keyboard shortcuts (?)", "Settings (s)"])
shot("header-hover")
h.click(hd("gear")); h.spin(100); rest()
ok("B7 Settings open: the gear in the accent tint", h.ev("root.view") == "settings" and same(fill(hd("gear")).property("color"), hd("activeFill")) and same(glyph(hd("gear")).property("color"), col("accent")))
ok("B8 Settings has its own heading: no tabs there", not hd("tabs.visible"))
ok("B9 the title stays whole in narrow Settings (Updated gives way first)", title.width() >= title.property("implicitWidth") - 0.5, (title.width(), title.property("implicitWidth"), hd("width")))
h.ev("root.showView('board')"); h.spin(100)
h.ev("root.refresh()"); h.spin(260)
rb = hd("refreshButton"); r = rb.rotation()
ok("B10 refresh spins, its fill stays square", r % 360 != 0 and abs(fill(rb).rotation() + r) < 0.01, (r, fill(rb).rotation()))
if h.running("board"): h.answer("board", WIDE)
h.spin(1200); rest()
# --- the merge requests tab ------------------------------------------------------
h.click(mt); h.spin(80)
if h.running("mrs"): h.answer("mrs", ANS); h.spin(120)
rest()
ok("M1 the Merge requests tab opens the view and takes the underline", h.ev("root.view") == "mrs" and line(mt).isVisible() and not line(bt).isVisible() and glyph(mt).property("font").bold())
ok("M2 in the MRs view the title is whole and the tab reads in full", title.width() >= title.property("implicitWidth") - 0.5 and glyph(mt).property("text") == "Merge requests", (title.width(), title.property("implicitWidth"), hd("width")))
ok("M3 no columns button there; refresh, keyboard, settings remain", not hd("columnsButton.visible") and all(hd(n + ".visible") for n in ("refreshButton", "keysButton", "gear")))
shot("header-mrs")
h.click(bt); h.spin(80); rest()
badge = [c for c in h.walk(mt) if c.objectName() == "mrsBadge"][0]
ok("M4 the Board tab goes back; the badge counts what waits on his review", h.ev("root.view") == "board" and badge.isVisible() and kids(badge, lambda c: c.inherits("QQuickText"))[0].property("text") == "2")
ok("M5 Board's tip: back, with its key, off the board only", bt.property("tip") == "" and (h.ev("root.showView('mrs')") or True) and bt.property("tip") == "Back to the board (Esc)")
h.key(Qt.Key_Escape, ""); h.spin(80)
ok("M6 Esc still goes back from the MRs view", h.ev("root.view") == "board")
shot("header")
# --- a narrow board: Updated gives way, then "MRs" ---------------------------------
h.ev("root.refresh()"); h.spin(60); h.answer("board", board(["todo", "review"])); h.spin(250); rest()
ok("N1 a narrow board: the Merge requests tab reads 'MRs' (tip in full)", hd("compactTabs") and glyph(mt).property("text") == "MRs" and mt.property("tip") == "Merge requests (m)", (hd("width"), hd("freeWidth")))
ok("N2 ... Updated shrinks to 48 points and the title gets all the rest", hd("status.width") <= S(48) + S(4) and title.width() >= hd("freeWidth") - S(48) - S(12) - 1, (title.width(), hd("status.width"), hd("freeWidth")))
shot("header-narrow")
print("passed %d failed %d" % (sum(ALL), len(ALL) - sum(ALL)))
h.finish()
