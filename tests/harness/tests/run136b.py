# v0.1.36: Settings > Alerts in one window at scale 1.5 (harness15/): off by
# default, a click saves settings.alerts for the project and makes the shared
# service watch the board; previews of the section and of the notifications as
# Omarchy would show them (a mock card; the body through Omarchy's own
# NotificationLogic.styledBody, StyledText as in NotificationCard.qml).
# Usage: run136b.py <src> [outdir]
import sys, os, json, subprocess; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import lib
lib.HERE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "harness15")
from lib import *
src = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else None
P = "firelink21/phrase41"
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "run134.py")).read().split("ALL = []")[0].split("P = \"firelink21/phrase41\"")[1])
ALL = []
def ok(n, c, e=""): ALL.append(bool(c)); h.ok(n, c, e)
h = Harness(src, {"id": "odevvy.gitlab-board", "settingsRevision": 2, "defaultProject": P, "defaultCollapsed": ["open", "research", "Closed"], "bots": FOUR})
h.ev("panel.availableCardHeight = %d; panel.availableCardWidth = 1460" % DESK)
h.ev("root.opened = true"); h.spin(60); h.answer("board", board()); h.spin(150)
h.ev("root.showView('settings')"); h.spin(60); h.answer("whoami", {"state": "ready", "message": "", "user": "o_devvy"}); h.spin(60)
if h.running("labels"): h.answer("labels", LABELS); h.spin(60)
h.spin(120)
boxes = lambda: sorted([it for it in h.visible(lambda it: it.property("clickable") is not None and it.property("on") is not None and it.property("modelData") is not None) if isinstance(it.property("modelData"), dict) and it.property("modelData").get("kind") in ("review", "idle")], key=lambda it: it.mapToScene(QPointF(0, 0)).x())
bx = boxes()
ok("A1 Alerts: two check boxes, both off by default", [b.property("modelData")["label"] for b in bx] == ["A card enters review", "A bot stops working"] and not any(b.property("on") for b in bx), [b.property("modelData") for b in bx])
ok("A2 nothing watched, no background refresh", h.ev("root.feed.watchedKeys") == [])
# Settings may scroll inside the popup: bring Alerts into view first.
sf = next(it for it in h.walk(h.ev("settingsView")) if it.metaObject().className().startswith("QQuickFlickable"))
sf.setProperty("contentY", max(0, min(bx[0].mapToItem(sf.property("contentItem"), QPointF(0, 0)).y() - 60, sf.property("contentHeight") - sf.height()))); h.spin(120)
pc = h.cls("KeyboardPanel"); top, bottom = pc.mapToScene(QPointF(0, 0)).y(), pc.mapToScene(QPointF(0, pc.height())).y()
ok("A3 the Alerts boxes are in view inside the popup (scrolled to if needed)", all(top <= b.mapToScene(QPointF(0, 0)).y() and b.mapToScene(QPointF(0, b.height())).y() <= bottom for b in boxes()), [b.mapToScene(QPointF(0, 0)).y() for b in boxes()])
def shot(name): QTest.mouseMove(h.win, QPoint(1, 1)); h.spin(80); out and h.grab_card(os.path.join(out, name + ".png"))
shot("settings-alerts")
h.click(bx[0]); h.spin(60)
w = h.ev("root.bar.shell.writes")
# The two card and bot flags (later versions save more alerts beside them, off).
two = lambda a: {k: {x: y for x, y in v.items() if x in ("review", "idle") or y} for k, v in (a or {}).items()}
ok("A4 a click saves alerts for this project only (review on, idle off); other settings kept", w and two(w[-1].get("alerts")) == {P: {"review": True, "idle": False}} and w[-1].get("bots") == FOUR, w and w[-1].get("alerts"))
ok("A5 the box is ticked; the service watches this board", boxes()[0].property("on") and h.ev("root.feed.watchedKeys") == [P + "#"], h.ev("root.feed.watchedKeys"))
shot("settings-alerts-on")
h.click(boxes()[0]); h.spin(60)
ok("A6 off again: nothing watched", h.ev("root.feed.watchedKeys") == [] and two(h.ev("root.bar.shell.writes")[-1].get("alerts")) == {P: {"review": False, "idle": False}})
h.stop_all()
# --- notification mock renders ------------------------------------------------------
NL = os.path.join(os.environ.get("OMARCHY_PATH", os.path.expanduser("~/.local/share/omarchy")), "shell/plugins/notifications/NotificationLogic.js")
CASES = [("notification-review", "#42 is in review", "#42 Login form shows the wrong error &lt;401&gt; · firelink21/phrase41"),
         ("notification-batch", "3 cards entered review", "#42 Login form shows the wrong…, #43 Rate limit the mail…, #47 Settings page +0 more · firelink21/phrase41".replace(" +0 more", "")),
         ("notification-idle", "Stopped working: API Engineer", "On firelink21/phrase41: API Engineer is waiting in review")]
for name, head, body in CASES:
    styled = json.loads(subprocess.run(["node", "-e", "console.log(JSON.stringify(require(%s).styledBody(%s, 'GitLab board', '')))" % (json.dumps(NL), json.dumps(body))], capture_output=True, text=True).stdout)
    qml = """import QtQuick
Rectangle { width: 560; height: col.implicitHeight + 36; color: "#1f2530"; border { width: 2; color: "#e68e59" }
  Text { id: g; x: 18; y: 18; text: "\\uf296"; color: "#e68e59"; font { family: "JetBrainsMono Nerd Font"; pixelSize: 26 } }
  Column { id: col; x: 64; y: 18; width: parent.width - 82; spacing: 6
    Text { width: parent.width; text: "GitLab board  ·  now"; color: "#8a8f98"; font { family: "JetBrainsMono Nerd Font"; pixelSize: 14 } }
    Text { width: parent.width; text: %s; textFormat: Text.PlainText; color: "#e8e3d8"; elide: Text.ElideRight; font { family: "JetBrainsMono Nerd Font"; pixelSize: 17; bold: true } }
    Text { width: parent.width; text: %s; textFormat: Text.StyledText; wrapMode: Text.Wrap; color: "#c3beb4"; font { family: "JetBrainsMono Nerd Font"; pixelSize: 15 } } } }
""" % (json.dumps(head), json.dumps(styled))
    item = h.ev("Qt.createQmlObject(%s, root.Window.contentItem)" % json.dumps(qml))
    h.spin(150)
    if out:
        img = h.win.grabWindow(); s = img.width() / h.win.width()
        img.copy(QRect(0, 0, int(560 * s), int(item.property("height") * s))).save(os.path.join(out, name + ".png"))
    item.deleteLater(); h.spin(60)
loops = [x for x in h.warnings if "oop" in x]
ok("Z no binding-loop warnings", not loops, loops)
ok("Z no QML warnings", not h.warnings, h.warnings[:3])
print("passed", sum(ALL), "failed", len(ALL) - sum(ALL))
sys.stdout.flush(); os._exit(0 if all(ALL) else 1)
