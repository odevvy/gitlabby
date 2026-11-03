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
# --- App window ------------------------------------------------------------------------------------
w0 = len(writes()); h.ev("root.setLinkMode('app')"); h.spin(100)
last = writes()[-1] if len(writes()) > w0 else {}
h.ok("A2 setLinkMode('app') saves openLinks: app, the other settings kept", last.get("openLinks") == "app" and last.get("refreshIntervalSec") == 120 and last.get("defaultCollapsed") == ["closed"] and last.get("defaultProject") == P, last)
got, still = opened(URL)
h.ok("A4 a link opens in an app window (omarchy-launch-webapp), the popup closes", got == [["omarchy-launch-webapp", URL]] and not still and h.ev("root.linkMode") == "app", got)
bad = [u for u in ["file:///etc/passwd", "--app=https://x.org", "javascript:alert(1)", "http://gitlab.com/x", ""] if opened(u)[0] != []]
h.ok("A5 still https only in an app window", bad == [], bad)
# --- back to a tab, and odd saved values ------------------------------------------------------------
h.ev("root.setLinkMode('browser')"); h.spin(100)
got, still = opened(URL)
h.ok("A6 Browser tab again: saved, and a tab", writes()[-1].get("openLinks") == "browser" and got == [["omarchy-launch-browser", URL]], (writes()[-1].get("openLinks"), got))
h.ev("root.setLinkMode('webapp')"); h.spin(100)
h.ok("A6b only 'app' saves an app window", writes()[-1].get("openLinks") == "browser", writes()[-1].get("openLinks"))
odd = []
for v in ["tab", "APP", "webapp", 1, None]:
    h.ev("root.settings = Object.assign({}, root.settings, { openLinks: %s })" % json.dumps(v)); h.spin(40)
    if h.ev("root.linkMode") != "browser": odd.append(v)
h.ev("root.settings = Object.assign({}, root.settings, { openLinks: 'app' })"); h.spin(40)
h.ok("A7 anything but 'app' saved is a browser tab; 'app' an app window", odd == [] and h.ev("root.linkMode") == "app", odd)
h.ev("root.settings = Object.assign({}, root.settings, { openLinks: 'browser' })"); h.spin(40)
h.ev("root.showView('board')"); h.spin(100)
sys.exit(h.finish())
