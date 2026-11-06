# v0.1.53: Settings in four sections (v152 design, direction A). General, Bots,
# Alerts and Account each sit under a thin rule and a small caps heading;
# settings are named in plain text with one quiet line of help; check boxes
# are an accent outline when ticked and line up in quarter-row columns; the
# refresh choice is tinted, not filled; the bot list has no box.
# Usage: run153.py <src> [outdir]   (preview: settings)
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from PySide6.QtGui import QFont
src = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else None
ALL = []
def ok(n, c, e=""): ALL.append(bool(c)); h.ok(n, c, e)
P = "group/app"
BOARD = {"state": "ready", "project": P, "updatedAt": "2026-10-31T13:20:00Z", "message": "", "labelColors": {}, "boards": [{"id": 1, "name": "Dev"}], "board": {"id": 1, "name": "Dev"}, "fallback": False,
  "columns": [{"name": "Open", "kind": "open", "issues": []}] + [{"name": n, "kind": "label", "listId": i, "color": "#5b9bd5", "issues": []} for i, n in enumerate(["research", "todo", "approved", "in progress", "review"])] + [{"name": "Closed", "kind": "closed", "issues": []}]}
BOTS = {P: {"busyLists": ["approved", "review"], "bots": [{"name": "App UI", "label": "app-ui"}, {"name": "Spec QA", "list": "review"}]}}
h = Harness(src, {"id": "odevvy.gitlabby", "settingsRevision": 2, "defaultProject": P, "defaultCollapsed": ["open", "closed"], "bots": BOTS, "alerts": {P: {"review": True}}})
h.ev("panel.availableCardHeight = 1400; panel.availableCardWidth = 1460")
h.ev("root.opened = true"); h.spin(60); h.answer("board", BOARD); h.spin(150)
h.ev("root.showView('settings')"); h.spin(150); h.answer("whoami", {"state": "ready", "message": "", "user": "o_devvy"}); h.spin(80)
sv = h.ev("settingsView")
same = lambda a, c: abs(a.redF() - c.redF()) < 0.01 and abs(a.greenF() - c.greenF()) < 0.01 and abs(a.blueF() - c.blueF()) < 0.01
col = lambda k: h.ev("root." + k)
y_of = lambda it: it.mapToScene(QPointF(0, 0)).y()
x_of = lambda it: it.mapToScene(QPointF(0, 0)).x()
bt = lambda pred: [it for it in h.visible(lambda it: it.inherits("QQuickText") and pred(it)) if sv.isAncestorOf(it)]  # BoardText and its inline kinds (Heading, Label, ...)
txt = lambda t: bt(lambda it: str(it.property("text") or "") == t)
pv = lambda it, k: h.ev(k, QQmlEngine.contextForObject(it), it)
checks = lambda inside: sorted([it for it in h.visible(lambda it: it.property("clickable") is not None and it.property("on") is not None) if inside(it)], key=lambda it: (round(y_of(it)), x_of(it)))
bs = h.cls("BotsSection")
# Not the Alerts boxes (their model is {kind, label}), however many there are.
start = checks(lambda it: sv.isAncestorOf(it) and not bs.isAncestorOf(it) and not (isinstance(it.property("modelData"), dict) and sorted(it.property("modelData")) == ["kind", "label"]))
box = lambda it: next(c for c in h.walk(it) if c.inherits("QQuickRectangle") and abs(c.width() - h.ev("Style.space(14)")) < 0.5)
def shot(name):
    if out: QTest.mouseMove(h.win, QPoint(1, 1)); h.spin(300); os.makedirs(out, exist_ok=True); h.grab_card(out + "/" + name + ".png")
QTest.mouseMove(h.win, QPoint(1, 1)); h.spin(150)
# --- stage 1: SettingsView
heads = sorted([(y_of(it), str(it.property("text"))) for it in bt(lambda it: str(it.property("text")) in ("General", "Bots", "Alerts", "Account"))])
ok("G1 four sections in order: General, Bots, Alerts, Account", [t for _, t in heads] == ["General", "Bots", "Alerts", "Account"], heads)
g = (txt("General") or txt("Account"))[0]
ok("G1b headings: small bold caps in the dim colour", g.property("font").capitalization() == QFont.AllUppercase and g.property("font").bold() and g.property("font").pixelSize() == h.ev("Style.font.caption") and same(g.property("color"), col("dim")))
rules = sorted([it for it in h.walk() if it.objectName() == "sectionRule" and it.isVisible() and sv.isAncestorOf(it)], key=y_of)
ys = [y for y, _ in heads]
ok("G2 a 1px rule above Bots, Alerts and Account, none above General", len(rules) == 3 and all(r.height() == 1 for r in rules)
   and ys[0] < y_of(rules[0]) < ys[1] and ys[1] < y_of(rules[1]) < ys[2] and ys[2] < y_of(rules[2]) < ys[3], [y_of(r) for r in rules])
ok("G2b the rule is the foreground at 12%", rules and abs(rules[0].property("color").alphaF() - 0.12) < 0.01)
re_ = txt("Refresh every")[0]
ok("G3 'Refresh every' is a plain name: not capitals, body-small, text colour", re_.property("font").capitalization() == QFont.MixedCase and re_.property("font").pixelSize() == h.ev("Style.font.bodySmall") and same(re_.property("color"), col("foreground")))
cur = [it for it in h.walk() if it.property("seconds") is not None and it.property("current") is True]
ok("G4 the current interval is tinted in the accent (not filled), its number in the accent", len(cur) == 1 and same(cur[0].property("color"), col("accent")) and cur[0].property("color").alphaF() < 0.3
   and [same(c.property("color"), col("accent")) for c in h.walk(cur[0]) if c.inherits("QQuickText")] == [True])
seg = cur[0].parentItem().parentItem() if cur else None
ok("G4b the segment track has no outline", seg is not None and pv(seg, "border.width") == 0, seg and pv(seg, "border.width"))
help1 = txt("New boards fold these. Your per-board choice wins.")
ok("G5 Start collapsed: one quiet line of help", len(help1) == 1 and same(help1[0].property("color"), col("quiet")) and help1[0].height() < 2 * help1[0].property("font").pixelSize() + 4)
xs = [round(x_of(c)) for c in start]
ok("G6 its check boxes line up: the second row starts under the first's columns", len(start) == 7 and xs[4] == xs[0] and xs[5] == xs[1] and xs[6] == xs[2] and len(set(xs[:4])) == 4, xs)
on = [c for c in start if c.property("on")]; off = [c for c in start if not c.property("on")]
b_on, b_off = box(on[0]), box(off[0])
ok("G7 ticked: accent outline, tinted fill, accent tick", same(pv(b_on, "border.color"), col("accent")) and pv(b_on, "color.a") < 0.3 and same(next(c for c in h.walk(b_on) if c.inherits("QQuickText")).property("color"), col("accent")))
ok("G8 unticked: a hairline square, no fill", pv(b_off, "color.a") == 0 and pv(b_off, "border.color.a") < 0.5)
name_in = lambda c, t: [c2 for c2 in h.walk(c) if c2.inherits("QQuickText") and str(c2.property("text")) == t]
ok("G9 an unticked name is dim, a ticked one in the text colour", same(name_in(start[2], "todo")[0].property("color"), col("dim")) and same(name_in(start[0], "Open")[0].property("color"), col("foreground")))
ah = bt(lambda it: str(it.property("text") or "").startswith("Desktop notifications for group/app."))
ok("G10 Alerts: its help is quiet", len(ah) == 1 and same(ah[0].property("color"), col("quiet")))
acc = bt(lambda it: str(it.property("text") or "") == "Signed in as o_devvy on gitlab.com")
ok("G11 Account: who is signed in, dim; Sign out in the accent", len(acc) == 1 and same(acc[0].property("color"), col("dim")) and same(txt("Sign out")[0].property("color"), col("accent")))
ok("G12 'Settings' as the view's title (subtitle size)", txt("Settings")[0].property("font").pixelSize() == h.ev("Style.font.subtitle"))
# --- stage 2: BotsSection
b = txt("Bots")[0]
ok("B1 the Bots heading matches the others", b.property("font").pixelSize() == g.property("font").pixelSize() and b.property("font").capitalization() == QFont.AllUppercase)
intro = txt("Dots under the header show who is working, read from the cards.")
ok("B2 one quiet line of intro", len(intro) == 1 and same(intro[0].property("color"), col("quiet")))
bc = txt("Busy when its card is in"); bh = txt("Open and Closed never count.")
ok("B3 'Busy when its card is in', its help on the same line", len(bc) == 1 and len(bh) == 1 and abs(y_of(bc[0]) + bc[0].property("baselineOffset") - y_of(bh[0]) - bh[0].property("baselineOffset")) < 1.5 and x_of(bh[0]) > x_of(bc[0]))
busy = checks(lambda it: bs.isAncestorOf(it))
bx = [round(x_of(c)) for c in busy]
ok("B4 the busy check boxes line up with Start collapsed's", len(busy) == 5 and bx[:4] == xs[:4], (bx, xs[:4]))
bon = [c for c in busy if c.property("on")]
ok("B5 ticked busy boxes: the same accent outline", bon and same(pv(box(bon[0]), "border.color"), col("accent")) and pv(box(bon[0]), "color.a") < 0.3)
lt = txt("On group/app")
ok("B6 the list is titled 'On group/app'", len(lt) == 1)
pn = [it for it in h.walk(bs) if it.inherits("QQuickRectangle") and any(str(c.property("text") or "") == "App UI" for c in h.walk(it) if c.inherits("QQuickText")) and it.width() >= bs.width() - 1]
ok("B7 the bot list has no box: no fill, no outline", pn and all(pv(p, "color.a") == 0 and pv(p, "border.width") == 0 for p in pn), [(pv(p, "color.a"), pv(p, "border.width")) for p in pn])
nm = txt("App UI")
ok("B8 bot names plain, not bold; rules quiet", nm and not nm[0].property("font").bold() and same(txt("cards labelled")[0].property("color"), col("quiet")))
shot("settings")
print("passed %d failed %d" % (sum(ALL), len(ALL) - sum(ALL)))
h.finish()
