# v0.1.68: vim keys next to every arrow. j/k and ↓/↑ scroll Settings, the
# shortcuts and an issue (never while typing in a field); in the project
# filter Ctrl+j / Ctrl+n and Ctrl+k / Ctrl+p move the cursor while typing.
# Usage: run168.py <src>
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from fixtures import BOARD
h = Harness(sys.argv[1], {"id": "odevvy.gitlab-board", "settingsRevision": 2, "defaultProject": "group/app", "defaultCollapsed": [], "boardStates": {}, "refreshIntervalSec": 60})
h.ev("panel.availableCardHeight = 520; panel.availableCardWidth = 1460")
h.ev("root.opened = true"); h.spin(60); h.answer("board", BOARD); h.spin(200)
def ctx(cls): v = h.cls(cls); return h.ctx_of(v), v
def y(cls): c, v = ctx(cls); return h.ev("flick.contentY", c, v)
def ymax(cls): c, v = ctx(cls); return h.ev("Math.max(0, flick.contentHeight - flick.height)", c, v)
CHARS = {Qt.Key_J: "j", Qt.Key_K: "k", Qt.Key_L: "l", Qt.Key_H: "h", Qt.Key_N: "n", Qt.Key_P: "p"}
def kev(k, mod=Qt.NoModifier):  # a real key: its text (a control character with Ctrl)
    t = CHARS.get(k, "\x1b" if k == Qt.Key_Escape else "")
    if t and mod & Qt.ControlModifier: t = chr(ord(t) & 0x1f)
    for typ in (QEvent.KeyPress, QEvent.KeyRelease): QGuiApplication.sendEvent(h.win, QKeyEvent(typ, k, mod, t))
def press(k, mod=Qt.NoModifier): kev(k, mod); h.spin(220)
def typed(s):
    for ch in s:
        for typ in (QEvent.KeyPress, QEvent.KeyRelease): QGuiApplication.sendEvent(h.win, QKeyEvent(typ, getattr(Qt, "Key_" + ch.upper()), Qt.NoModifier, ch))
        h.spin(30)
# --- scrolling ----------------------------------------------------------------------------------
h.ev("root.showView('settings')"); h.spin(80)
while h.running("whoami"): h.answer("whoami", {"state": "ready", "user": "dev1"})
h.spin(200); h.ev("root.focusBoard()"); h.spin(60)
h.ok("A0 Settings goes on below the edge here", ymax("SettingsView") > 0 and y("SettingsView") == 0)
press(Qt.Key_J); y1 = y("SettingsView")
h.ok("A1 j scrolls Settings down (about three lines)", y1 > 0 and h.ev("root.view") == "settings", y1)
press(Qt.Key_K)
h.ok("A2 k scrolls it back up", y("SettingsView") == 0, y("SettingsView"))
press(Qt.Key_Down); press(Qt.Key_Down)
h.ok("A3 ↓ does the same as j", abs(y("SettingsView") - min(2 * y1, ymax("SettingsView"))) < 1, (y("SettingsView"), y1))
press(Qt.Key_Up)
h.ok("A4 ↑ the same as k", abs(y("SettingsView") - min(2 * y1, ymax("SettingsView")) + y1) < 1 or y("SettingsView") < min(2 * y1, ymax("SettingsView")))
for _ in range(40): kev(Qt.Key_J); h.spin(10)
h.spin(250)
h.ok("A5 never past the end", abs(y("SettingsView") - ymax("SettingsView")) < 1, (y("SettingsView"), ymax("SettingsView")))
for _ in range(40): kev(Qt.Key_K); h.spin(10)
h.spin(250)
h.ok("A6 never past the top", y("SettingsView") == 0)
press(Qt.Key_L); press(Qt.Key_Right)
h.ok("A7 h/l and ←/→ don't scroll", y("SettingsView") == 0 and h.ev("root.view") == "settings")
c, v = ctx("SettingsView"); h.ev("hostField.forceActiveFocus()", c, v); h.spin(40)
kev(Qt.Key_End); typed("jk"); h.spin(220)
h.ok("A8 typing in a field: j and k are letters, nothing scrolls", h.ev("hostField.text", c, v).endswith("jk") and y("SettingsView") == 0, h.ev("hostField.text", c, v))
kev(Qt.Key_Escape); h.spin(60)
h.ev("root.showView('keys')"); h.spin(200); h.ev("root.focusBoard()"); h.spin(40)
press(Qt.Key_J)
h.ok("A9 j scrolls the shortcuts", ymax("KeysView") > 0 and y("KeysView") > 0, (y("KeysView"), ymax("KeysView")))
ISSUE = {"iid": 2, "title": "Second issue", "state": "opened", "labels": ["todo"], "url": "https://gitlab.com/group/app/-/issues/2",
         "description": "\n\n".join("Paragraph %d of a long description that goes on." % i for i in range(40)), "author": "dev1", "milestone": "", "assignees": [],
         "createdAt": "2026-10-20T12:00:00Z", "updatedAt": "2026-10-29T12:00:00Z"}
card = [i for col in h.ev("root.columns") for i in col["issues"] if i["iid"] == 2][0]
h.ev("root.openIssue(%s)" % json.dumps(card)); h.spin(60)
h.answer("issue", {"state": "ready", "message": "", "issue": ISSUE}); h.answer("notes", {"state": "ready", "message": "", "iid": 2, "more": False, "notes": []}); h.spin(300)
press(Qt.Key_J)
h.ok("A10 j scrolls an issue", y("IssueView") > 0 and h.ev("root.view") == "issue", y("IssueView"))
c, v = ctx("IssueView"); h.ev("box.forceActiveFocus()", c, v); h.spin(40); y2 = y("IssueView")
typed("jj"); h.spin(220)
h.ok("A11 typing a comment: j is a letter", h.ev("box.text", c, v) == "jj" and y("IssueView") == y2, h.ev("box.text", c, v))
kev(Qt.Key_Escape); h.spin(60)
h.ev("root.back()"); h.spin(80)
# --- the project filter: Ctrl+j/k, Ctrl+n/p ---------------------------------------------------
h.ev("root.openPicker()"); h.spin(80)
h.answer("projects", {"state": "ready", "projects": [{"id": i, "path": "group/app%d" % i} for i in range(1, 6)]}); h.spin(150)
pv = h.cls("Picker"); pc = h.ctx_of(pv); pev = lambda e: h.ev(e, pc, pv)
h.ok("B0 the filter has the keys, the cursor on none", pev("filter.activeFocus") is True and pev("view.cursor") == -1, (pev("filter.activeFocus"), pev("view.cursor")))
typed("app"); h.spin(60)
press(Qt.Key_J, mod=Qt.ControlModifier); press(Qt.Key_J, mod=Qt.ControlModifier)
h.ok("B1 Ctrl+j moves down while typing", pev("view.cursor") == 1, pev("view.cursor"))
press(Qt.Key_N, mod=Qt.ControlModifier)
h.ok("B2 Ctrl+n too", pev("view.cursor") == 2)
pev("filter.cursorPosition = 1")  # Ctrl+K in a plain field would cut "pp"
press(Qt.Key_K, mod=Qt.ControlModifier)
h.ok("B3 Ctrl+k moves up, and the filter keeps its text (not delete-to-end)", pev("view.cursor") == 1 and pev("filter.text") == "app", pev("filter.text"))
press(Qt.Key_P, mod=Qt.ControlModifier)
h.ok("B4 Ctrl+p too", pev("view.cursor") == 0)
press(Qt.Key_Down)
h.ok("B5 ↓ still works", pev("view.cursor") == 1)
typed("j"); h.spin(60)
h.ok("B6 plain j is typed into the filter", pev("filter.text") == "ajpp", pev("filter.text"))
kev(Qt.Key_Escape); h.spin(80)
sys.exit(h.finish())
