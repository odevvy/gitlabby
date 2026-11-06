# v0.1.75 (v175 design A, alerts only): after an alert, a small accent dot at
# the bar icon's top right, on every screen, until a popup opens; an alert
# while a popup is open never lights it. Settings > General "Keep the bar icon
# unlit" (iconUnlit) turns it off. Setup as run174 / run136 (two screens).
# Usage: run175.py <src>
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import two; P = two.P; two.start({"alerts": {P: {"review": True, "idle": False}}}, "ogb-h175-"); from two import *


D = board([row(1, ["todo"])], [], [row(4, ["review"]), row(2, ["review", "app-ui"], "Fix <b> & co"), row(3, ["review", "api"]), row(5, ["review"], "Five")])
E = board([], [], [row(4, ["review"]), row(2, ["review", "app-ui"], "Fix <b> & co"), row(3, ["review", "api"]), row(5, ["review"], "Five"), row(1, ["review"])])
dots = lambda: [bool(ev(k, "alertDot.visible")) for k in ("a", "b")]
tips = lambda: [ev(k, "button.tooltipText") for k in ("a", "b")]
def settle():
    for _ in range(4):
        if not running(): break
        answer(LAST[0]); spin(60)
LAST = [A]
def feed_answer(data): LAST[0] = data; answer(data)
spin(150)
ok("D0 no alert yet: no dot on either screen", dots() == [False, False] and tips() == ["GitLabby · group/app"] * 2, (dots(), tips()))
bg(); feed_answer(A)
ok("D1 the first load announces nothing: no dot", dots() == [False, False])
age(); bg(); feed_answer(B)
ok("D2 an alert: a dot on both screens, and the tip says why", len(notes()) == 1 and dots() == [True, True] and tips() == ["GitLabby · group/app · an alert came"] * 2, (len(notes()), dots(), tips()))
w, h_, dx, dy, ds = (ev("a", e) for e in ("button.width", "button.height", "alertDot.x", "alertDot.y", "alertDot.width"))
ok("D3 small (5 points), round, at the icon's top right, inside the button", ds == 5 and ev("a", "alertDot.radius") == 2.5 and dx > w / 2 and dx + ds <= w and dy >= 0 and dy + ds < h_ / 2, (w, h_, dx, dy, ds))
ok("D4 in the accent", ev("a", "String(alertDot.color) === String(root.accent)"))
ev("b", "root.opened = true"); spin(120); settle()
ok("D5 opening the popup on one screen clears both", dots() == [False, False] and ev("a", "root.feed.unseenAlerts") == 0 and tips() == ["GitLabby · group/app"] * 2, (dots(), tips()))
age(); ev("b", "root.refresh(true)"); spin(60); feed_answer(C); spin(100)
ok("D6 an alert while a popup is open: no dot", len(notes()) == 2 and dots() == [False, False], (len(notes()), dots()))
ev("b", "root.opened = false"); spin(120)
ok("D7 closing it: still none", dots() == [False, False])
age(); bg(); feed_answer(D)
ok("D8 the next alert with the popups closed: the dot again", len(notes()) == 3 and dots() == [True, True], (len(notes()), dots()))
ev("a", "root.opened = true"); spin(120); settle(); ev("a", "root.opened = false"); spin(80)
# --- Keep the bar icon unlit (iconUnlit) ------------------------------------------------------------
age(); bg(); feed_answer(E)
ok("U0 lit again after the next alert", len(notes()) == 4 and dots() == [True, True], (len(notes()), dots()))
w0 = len(ev("a", "root.bar.shell.writes") or []); ev("a", "root.setIconUnlit(true)"); spin(60)
wr = (ev("a", "root.bar.shell.writes") or [])[w0:]
ok("U1 setIconUnlit(true) saves iconUnlit: true with the rest", wr and wr[-1].get("iconUnlit") is True and wr[-1].get("alerts") == SETTINGS["alerts"] and wr[-1].get("defaultProject") == P, wr and wr[-1])
for k in ("a", "b"): ev(k, "root.settings = Object.assign({}, root.settings, { iconUnlit: true })")
spin(60)
ok("U2 kept unlit: no dot on either screen, the plain tip, the alert still sent", dots() == [False, False] and tips() == ["GitLabby · group/app"] * 2 and len(notes()) == 4, (dots(), tips()))
odd = []
for v in ["true", 1, "yes"]:
    for k in ("a", "b"): ev(k, "root.settings = Object.assign({}, root.settings, { iconUnlit: %s })" % json.dumps(v))
    spin(40)
    if dots() != [True, True]: odd.append(v)
ok("U3 only true keeps it unlit", odd == [], odd)
ev("a", "root.setIconUnlit('yes')"); spin(40)
ok("U4 setIconUnlit saves only true or false", (ev("a", "root.bar.shell.writes") or [])[-1].get("iconUnlit") is False)
for k in ("a", "b"): ev(k, "root.settings = Object.assign({}, root.settings, { iconUnlit: false })")
spin(40)
# --- Settings > General: the check box ----------------------------------------------------------------
from PySide6.QtTest import QTest
ev("a", "root.opened = true"); spin(120); settle(); ev("a", "root.showView('settings')"); spin(300)
for _ in range(3): answer_proc("a", "whoami", {"state": "ready", "user": "dev1"})
spin(200)
def walk(it):
    yield it
    for c in it.childItems(): yield from walk(c)
items = list(walk(wins["w1"].contentItem()))
by = lambda n: next((it for it in items if it.objectName() == n and it.isVisible()), None)
row, check, note, link = by("unlitRow"), by("unlitCheck"), by("unlitNote"), by("linkNote")
sv = next(it for it in items if it.metaObject().className().startswith("SettingsView"))
y = lambda it: it.mapToItem(sv, QPointF(0, 0)).y()
start = next((it for it in items if it.property("text") == "Start collapsed" and it.isVisible()), None)
help_ = next((it for it in items if it.property("text") == "New boards fold these. Your per-board choice wins." and it.isVisible()), None)
ok("S1 under Open links in and its note: the box, 'Keep the bar icon unlit', its note, then Start collapsed", row and note and link and start and y(link) < y(row) and y(row) + row.height() <= y(note) < y(start),
   [row is not None, note is not None])
ok("S2 the note: quiet, caption size, one line, the words", note and help_ and note.property("text") == "Otherwise a small dot on it after an alert, until you open the board." and note.property("color") == help_.property("color") and note.property("font").pixelSize() == help_.property("font").pixelSize() and note.property("lineCount") == 1)
ok("S3 off by default: the box unticked", check and check.property("on") is False)
w0 = len(ev("a", "root.bar.shell.writes") or [])
c = check.mapToScene(QPointF(check.width() / 2, check.height() / 2)); QTest.mouseClick(wins["w1"], Qt.LeftButton, Qt.NoModifier, QPoint(int(c.x()), int(c.y()))); spin(120)
wr = (ev("a", "root.bar.shell.writes") or [])[w0:]
ok("S4 a click on the box saves iconUnlit: true", wr and wr[-1].get("iconUnlit") is True, wr and wr[-1])
ev("a", "root.settings = Object.assign({}, root.settings, { iconUnlit: true })"); spin(80)
ok("S5 ticked once saved", check.property("on") is True)
lab = next(it for it in items if it.property("text") == "Keep the bar icon unlit" and it.isVisible())
c = lab.mapToScene(QPointF(lab.width() / 2, lab.height() / 2)); QTest.mouseClick(wins["w1"], Qt.LeftButton, Qt.NoModifier, QPoint(int(c.x()), int(c.y()))); spin(120)
ok("S6 a click on the words unticks it: iconUnlit: false", (ev("a", "root.bar.shell.writes") or [])[-1].get("iconUnlit") is False)
ev("a", "root.settings = Object.assign({}, root.settings, { iconUnlit: false })"); ev("a", "root.opened = false"); spin(80)
loops = [w for w in warnings if "oop" in w]
ok("Z no binding-loop warnings", not loops, loops)
ok("Z no QML warnings", not warnings, warnings[:3])
print("passed", sum(results), "failed", len(results) - sum(results))
sys.stdout.flush(); os._exit(0 if all(results) else 1)
