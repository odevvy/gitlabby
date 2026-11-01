# v0.1.62: the shortcuts screen laid out like Settings. Nine groups in soft
# cards (Board's four on the left), each with a caption heading; the title as
# in Settings; every shortcut one 26 px line: compact caps (a chord's caps
# joined, a quiet "/" between choices), short words and a quiet note, nothing
# wrapped or clipped at the popup's width (760 px or more).
# Usage: run162.py <src>
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from fixtures import BOARD
h = Harness(sys.argv[1], None)
h.ev("panel.availableCardHeight = 1200; panel.availableCardWidth = 1460")
h.ev("root.opened = true"); h.spin(80); h.answer("board", BOARD); h.spin(200)
h.ev("root.showView('keys')"); h.spin(300)
kv = h.cls("KeysView"); kev = lambda code, it=kv: h.ev(code, QQmlEngine.contextForObject(it), it)
S = lambda n: h.ev("Style.space(%d)" % n)
named = lambda n: [it for it in h.walk(kv) if it.objectName() == n and it.isVisible()]
ok = h.ok
ok("K0 two columns at the popup's width (760 or more)", kev("twoColumns") and h.ev("panel.contentWidth") >= S(760) - 1, h.ev("panel.contentWidth"))
title = [it for it in h.walk(kv) if it.property("text") == "Keyboard shortcuts"]
ok("K1 the title is Settings' (subtitle, bold)", title and title[0].property("font").pixelSize() == h.ev("Style.font.subtitle") and title[0].property("font").bold())
cards = named("keyGroup")
ok("K2 nine groups, each a soft card with Settings' pane fill", len(cards) == 9 and all(abs(c.property("color").alphaF() - 0.035) < 0.01 and c.property("radius") == S(8) for c in cards), len(cards))
left = sorted([c for c in cards if c.mapToItem(kv, QPointF(0, 0)).x() < kv.width() / 2], key=lambda c: c.mapToItem(kv, QPointF(0, 0)).y())
ltitles = [h.ev("modelData.title", QQmlEngine.contextForObject(c), c) for c in left]
ok("K3 the board's four groups on the left, in order", ltitles == ["Board", "Picked cards", "Confirm a move or a close", "Setup panel"], ltitles)
rows = named("keyRow")
ok("K4 all 33 shortcuts, one row each", len(rows) == 33, len(rows))
ok("K5 every row one line (26 px), its caps and words fit", all(r.height() == S(26) and r.property("fits") for r in rows), [h.ev("modelData[1]", QQmlEngine.contextForObject(r), r) for r in rows if not r.property("fits")])
def row(text): return next(r for r in rows if h.ev("modelData[1]", QQmlEngine.contextForObject(r), r) == text)
def caps(r): return sorted([c for c in h.walk(r) if c.objectName() == "keyCap" and c.isVisible()], key=lambda c: c.mapToItem(r, QPointF(0, 0)).x())
mv = row("Move left / right · asks first"); cs = caps(mv)
gap = lambda a, b: b.mapToItem(mv, QPointF(0, 0)).x() - (a.mapToItem(mv, QPointF(0, 0)).x() + a.width())
ok("K6 Shift H / L: Shift and H joined (2 px), then a quiet /, then L", [c.childItems()[0].property("text") for c in cs] == ["Shift", "H", "L"] and abs(gap(cs[0], cs[1]) - S(2)) < 0.5 and gap(cs[1], cs[2]) > S(8)
   and [(s.property("text"), s.property("color").name()) for s in h.walk(mv) if s.objectName() == "keySep" and s.isVisible()] == [("/", h.ev("root.quiet").name())], [gap(cs[0], cs[1]), gap(cs[1], cs[2])])
ok("K7 h j k l is one cap", [c.childItems()[0].property("text") for c in caps(row("Move between cards"))] == ["h j k l", "← ↓ ↑ →"])
notes = [n for n in h.walk(mv) if n.objectName() == "keyNote" and n.isVisible()]
words = [n for n in h.walk(mv) if n.objectName() == "keyWhat" and n.isVisible()]
ok("K8 the note after the words, quiet", words and words[0].property("text") == "Move left / right" and notes and notes[0].property("text") == "asks first" and notes[0].property("color").name() == h.ev("root.quiet").name(), notes and (notes[0].property("text"), notes[0].property("color").name(), h.ev("root.quiet").name()))
fl = next(it for it in h.walk(kv) if it.metaObject().className() == "QQuickFlickable")
fl.setProperty("contentY", max(0, fl.property("contentHeight") - fl.height())); h.spin(100)
last = max(cards, key=lambda c: c.mapToItem(fl, QPointF(0, c.height())).y())
ok("K9 nothing out of reach: what doesn't fit scrolls, and the last card ends inside the view", fl.property("interactive") is not False and last.mapToItem(fl, QPointF(0, last.height())).y() <= fl.height() + 0.5, (fl.property("contentHeight"), fl.height()))
fl.setProperty("contentY", 0); h.spin(60)
for c in cards:
    p = c.mapToItem(fl, QPointF(0, 0))
    if p.x() < -0.5 or p.x() + c.width() > fl.width() + 0.5: ok("K10 card inside the view", False, p.x()); break
else: ok("K10 every card inside the view's width", True)
h.finish()
fails = [n for n, c in h.results if not c]
print("passed %d failed %d" % (len(h.results) - len(fails), len(fails)))
sys.exit(1 if fails else 0)
