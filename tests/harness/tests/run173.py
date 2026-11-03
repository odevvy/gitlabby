# v0.1.73 (v173 design B): Settings > General > "Open links in": Browser tab
# (omarchy-launch-browser, the default) or App window (omarchy-launch-webapp),
# saved as openLinks. openUrl stays https only and closes the popup.
# Usage: run173.py <src>
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from fixtures import BOARD
P = "group/app"
h = Harness(sys.argv[1], {"id": "odevvy.gitlab-board", "settingsRevision": 2, "defaultProject": P, "defaultCollapsed": ["closed"], "boardStates": {}, "refreshIntervalSec": 120})
h.ev("panel.availableCardHeight = 620; panel.availableCardWidth = 1020")
h.ev("root.opened = true"); h.spin(60); h.answer("board", BOARD); h.spin(300)
URL = "https://gitlab.com/group/app/-/issues/2"
since = lambda n: h.launched()[n:]
def opened(url):
    h.ev("root.opened = true"); h.spin(60); n = len(h.launched()); h.ev("root.openUrl(%s)" % json.dumps(url)); h.spin(60)
    return since(n), h.ev("root.opened")
def settings():
    h.ev("root.opened = true"); h.spin(60); h.ev("root.showView('settings')"); h.spin(80)
    while h.running("whoami"): h.answer("whoami", {"state": "ready", "user": "dev1"})
    h.spin(250); return h.cls("SettingsView")
def segs(sv): return sorted([it for it in h.walk(sv) if it.objectName() == "linkSegment" and it.isVisible()], key=lambda it: it.mapToScene(QPointF(0, 0)).x())
def label(it): return next(c.property("text") for c in it.childItems() if c.property("text") is not None)
writes = lambda: h.ev("root.bar.shell.writes")
# --- default: a browser tab ----------------------------------------------------------------------
got, still = opened(URL)
h.ok("A0 nothing saved: a link opens in a browser tab (omarchy-launch-browser), the popup closes", got == [["omarchy-launch-browser", URL]] and not still and h.ev("root.linkMode") == "browser", got)
sv = settings(); s = segs(sv)
h.ok("A1 Settings: 'Browser tab' then 'App window', the first current", [label(x) for x in s] == ["Browser tab", "App window"] and s[0].property("current") and not s[1].property("current"), [label(x) for x in s])
# --- App window ------------------------------------------------------------------------------------
w0 = len(writes()); h.click(s[1]); h.spin(100)
last = writes()[-1] if len(writes()) > w0 else {}
h.ok("A2 a click on App window saves openLinks: app, the other settings kept", last.get("openLinks") == "app" and last.get("refreshIntervalSec") == 120 and last.get("defaultCollapsed") == ["closed"] and last.get("defaultProject") == P, last)
s = segs(sv)
h.ok("A3 App window is current now", s[1].property("current") and not s[0].property("current") and h.ev("root.linkMode") == "app")
got, still = opened(URL)
h.ok("A4 a link opens in an app window (omarchy-launch-webapp), the popup closes", got == [["omarchy-launch-webapp", URL]] and not still, got)
bad = [u for u in ["file:///etc/passwd", "--app=https://x.org", "javascript:alert(1)", "http://gitlab.com/x", ""] if opened(u)[0] != []]
h.ok("A5 still https only in an app window", bad == [], bad)
# --- back to a tab, and odd saved values ------------------------------------------------------------
sv = settings(); s = segs(sv); h.click(s[0]); h.spin(100)
got, still = opened(URL)
h.ok("A6 Browser tab again: saved, and a tab", writes()[-1].get("openLinks") == "browser" and got == [["omarchy-launch-browser", URL]], (writes()[-1].get("openLinks"), got))
odd = []
for v in ["tab", "APP", "webapp", 1, None]:
    h.ev("root.settings = Object.assign({}, root.settings, { openLinks: %s })" % json.dumps(v)); h.spin(40)
    if h.ev("root.linkMode") != "browser": odd.append(v)
h.ev("root.settings = Object.assign({}, root.settings, { openLinks: 'app' })"); h.spin(40)
h.ok("A7 anything but 'app' saved is a browser tab; 'app' an app window", odd == [] and h.ev("root.linkMode") == "app", odd)
h.ev("root.settings = Object.assign({}, root.settings, { openLinks: 'browser' })"); h.spin(40)
# --- the row in Settings -----------------------------------------------------------------------------
NOTE = "App window: its own window, no tabs. Needs a Chromium-based browser."
sv = settings()
def texts(t): return [it for it in h.walk(sv) if it.property("text") == t and it.isVisible()]
y = lambda it: it.mapToItem(sv, QPointF(0, 0)).y()
x2 = lambda it: it.mapToItem(sv, QPointF(it.width(), 0)).x()
ctx = h.ctx_of(sv); row, ref = h.ev("linkRow", ctx, sv), h.ev("refreshRow", ctx, sv)
pace = texts("Slows down, up to 4x, while the board stays quiet; any change brings it back."); note = texts(NOTE); nxt = texts("Start collapsed")
h.ok("B1 under Refresh every and its note, then its own note, then Start collapsed", pace and note and nxt and y(ref) < y(pace[0]) < y(row) and y(row) + row.height() <= y(note[0]) < y(nxt[0]), [y(ref), pace and y(pace[0]), y(row), note and y(note[0])])
# The row after the note, whatever it is (spacers, one point wide, are part of the gap).
def after(it):
    kids = [k for k in it.parentItem().childItems() if k.isVisible()]
    return next((k for k in kids[kids.index(it) + 1:] if k.width() > 1), None)
below = after(note[0]) if note else None
gap_a = y(row) - (y(pace[0]) + pace[0].height()) if pace else -1; gap_b = y(below) - (y(note[0]) + note[0].height()) if below is not None else -1
h.ok("B2 the same space above it as below its note", pace and abs(gap_a - gap_b) < 1, (gap_a, gap_b))
help_ = texts("New boards fold these. Your per-board choice wins.")
h.ok("B3 the note is quiet, caption size, one line", note and help_ and note[0].property("color") == help_[0].property("color") and note[0].property("font").pixelSize() == help_[0].property("font").pixelSize() and note[0].property("lineCount") == 1)
pane = h.ev("linkPane", ctx, sv); seg = h.ev("segPane", ctx, sv)
h.ok("B4 the segments line up with Refresh every's on the right, same height", abs(x2(pane) - x2(seg)) < 1 and abs(pane.height() - seg.height()) < 1 and h.ev("linkRow.oneLine", ctx, sv), (x2(pane), x2(seg), pane.height(), seg.height()))
h.ev("panel.availableCardWidth = 760"); h.spin(300); note = texts(NOTE)
h.ok("B5 the narrowest popup (760): one line still, the note too", h.ev("linkRow.oneLine", ctx, sv) and note and note[0].property("lineCount") == 1)
h.ev("panel.availableCardWidth = 1020"); h.spin(200)
h.ev("root.showView('board')"); h.spin(100)
sys.exit(h.finish())
