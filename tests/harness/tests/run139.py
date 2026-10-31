# v0.1.39: the view-only hint at scale 1.5 (harness15/). board-fetch access runs
# once per project per session (GETs only) when its board loads; below Planner
# (15), or after a write refused with 403, moves, bulk picks, labels and close
# are off and AccessHint says why, with GitLab's https token page (read_api)
# and glab auth login; a token without api gets its own note; Not now is saved
# per project. Usage: run139.py <src> [outdir]
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import lib
lib.HERE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "harness15")
from lib import *
from PySide6.QtGui import QKeyEvent
src = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else None
P = "firelink21/phrase41"
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "run134.py")).read().split("ALL = []")[0].split("P = \"firelink21/phrase41\"")[1])
ALL = []
def ok(n, c, e=""): ALL.append(bool(c)); h.ok(n, c, e)
def shot(name):
    QTest.mouseMove(h.win, QPoint(1, 1)); h.spin(80)
    if out: h.grab_card(os.path.join(out, name + ".png"))
def shift(k, t):
    for typ in (QEvent.KeyPress, QEvent.KeyRelease): QGuiApplication.sendEvent(h.win, QKeyEvent(typ, k, Qt.ShiftModifier, t))
    h.spin(60)
def start(settings=None):
    global h
    base = {"id": "odevvy.gitlab-board", "settingsRevision": 2, "defaultProject": P, "defaultCollapsed": ["open", "research", "Closed"], "bots": FOUR}
    base.update(settings or {})
    h = Harness(src, base)
    h.ev("panel.availableCardHeight = %d; panel.availableCardWidth = 1460" % DESK)
    h.ev("root.opened = true"); h.spin(60); h.answer("board", board()); h.spin(150)
def to_card(iid):
    h.ev("root.cursor = (function(){ for (var c = 0; c < root.lanes.length; c++) { var l = root.lanes[c]; if (l && l.indexOf(%d) !== -1) return { col: c, row: l.indexOf(%d), iid: %d } } return null })()" % (iid, iid, iid)); h.spin(40)
access = lambda: h.running("access")
ACC = lambda level, scopes=None: {"state": "ready", "message": "", "project": P, "level": level, "scopes": scopes}
hint_vis = lambda: h.ev("accessHint.visible")
text_of = lambda name: next((it.property("text") for it in h.visible(lambda it: it.objectName() == name)), None)
btn = lambda name: next((it for it in h.visible(lambda it: it.objectName() == name)), None)
browser = lambda: [c for c in h.launched() if c and c[0] == "omarchy-launch-browser"]

start()
ok("V0 the board loaded: one access check for this project, GET-only command", [c[1:] for c in access()] == [["access", "--project", P]], access())
ok("V0b no answer yet: writes stay on, no hint", h.ev("root.writable") and not hint_vis())
h.answer("access", ACC(10, ["api", "read_user"])); h.spin(100)
ok("V1 a Guest: the hint says why", hint_vis() and text_of("accessTitle") == "View-only on %s: you're a Guest, so moves, labels and close are off here." % P, text_of("accessTitle"))
body = text_of("accessBody") or ""
ok("V2 the steps: a read_api token, glab auth login in a terminal, glab read-only too", "read_api scope" in body and "glab auth login --hostname gitlab.com in a terminal" in body and "becomes read-only too" in body, body)
ok("V3 writes off: no drag move, header says View-only", not h.ev("root.canMove") and not h.ev("root.requestMove(root.columns[2].issues[0], root.columns[2], root.columns[3])") and h.ev("header.status.text").startswith("View-only"), h.ev("header.status.text"))
to_card(20); shift(Qt.Key_L, "L"); h.key(Qt.Key_V, "v")
ok("V4 Shift+L and v do nothing: no move, no pick", h.running("move") == [] and h.ev("root.pendingMove") is None and h.ev("root.picked") == [])
h.ev("root.refresh()"); h.spin(60); h.answer("board", board()); h.spin(100)
ok("V5 a refresh doesn't ask again", access() == [])
shot("hint-view-only")
h.click(btn("accessTokenPage"))
ok("V6 the button opens GitLab's token page only: https, read_api, no token", browser() == [["omarchy-launch-browser", "https://gitlab.com/-/user_settings/personal_access_tokens?name=GitLab+board&description=Read-only+token+for+the+Omarchy+GitLab+board&scopes=read_api"]], browser())
h.ev("root.opened = true"); h.spin(100)
if h.running("board"): h.answer("board", board())
# the issue view
h.ev("root.openIssue(root.columns[2].issues[0])"); h.spin(80)
if h.running("issue"): h.answer("issue", {"state": "ready", "message": "", "issue": dict(ISSUE, iid=20, labels=["todo", "app-ui"])})
if h.running("notes"): h.answer("notes", {"state": "ready", "message": "", "iid": 20, "more": False, "notes": []})
h.spin(100)
words = [it.property("text") for it in h.visible(lambda it: isinstance(it.property("text"), str))]
ok("V7 issue view: no Edit labels, no Close issue", not any("Edit labels" in w or w == "Close issue" for w in words), [w for w in words if "label" in w.lower() or "Close" in w][:5])
h.key(Qt.Key_E, "e"); h.key(Qt.Key_X, "x")
ok("V8 e and x do nothing there", not h.ev("issueView.editing") and not h.ev("issueView.confirming") and h.running("labels") == [])
shot("issue-view-only")
h.key(Qt.Key_Escape); h.spin(60)
# Not now
h.click(btn("accessNotNow"))
w = h.ev("root.bar.shell.writes")[-1]
ok("V9 Not now: saved for this project, hint gone, writes still off", w.get("accessHintDismissed") == [P] and not hint_vis() and not h.ev("root.canMove"), w.get("accessHintDismissed"))
ok("V10 nothing token-shaped saved", not any(k for k in w if "token" in k.lower()) and "glpat" not in json.dumps(w))
shot("hint-dismissed")
ok("Z phase 1: no QML warnings", not h.warnings, h.warnings[:3])
R1 = h.results  # one total at the end (mutate.sh reads the first "passed" line)

# --- another start: the setting is read back; another project; 403; read token ---
start({"accessHintDismissed": ["FireLink21/Phrase41"]})
h.answer("access", ACC(10)); h.spin(80)
ok("D1 dismissed (any case): no hint after a restart; still view-only", not hint_vis() and not h.ev("root.writable"))
h.ev("root.switchTo('group/app', '7', 'Dev')"); h.spin(60)
B = board(); B["project"] = "group/app"
h.answer("board", B); h.spin(80)
ok("D2 another project: its own check", [c[1:] for c in access()] == [["access", "--project", "group/app"]], access())
h.answer("access", dict(ACC(30, None), project="group/app")); h.spin(80)
ok("D3 a Developer: writes on, no hint", h.ev("root.writable") and not hint_vis() and h.ev("root.canMove"))
to_card(20); shift(Qt.Key_L, "L")
ok("D4 a move runs", len(h.running("move")) == 1)
h.answer("move", {"state": "error", "message": "Move failed: 403 Forbidden"}); h.spin(120)
ok("D5 a 403 on a write: view-only from then on, said so", hint_vis() and "GitLab refused a change (403)" in text_of("accessTitle") and not h.ev("root.canMove"), text_of("accessTitle"))
h.ev("root.switchTo('" + P + "', '7', 'Development')"); h.spin(60); h.answer("board", board()); h.spin(80)
ok("D6 back: no new check for a project already known", access() == [])
h.ev("root.feed.setAccess('" + P + "', Logic.accessEntry(JSON.stringify({ state: 'ready', level: 30, scopes: ['read_api'] })))"); h.spin(80)
ok("D7 a read-only token on a dismissed project: hidden there too", not hint_vis() and not h.ev("root.writable"))
h.ev("root.settings = Object.assign({}, root.settings, { accessHintDismissed: [] })"); h.spin(80)
ok("D8 a read-only token: its own note, writes off, no token-page button", hint_vis() and text_of("accessTitle") == "Signed in with a read-only token, so moves, labels and close are off." and btn("accessTokenPage") is None and not h.ev("root.writable"), text_of("accessTitle"))
shot("hint-read-token")
h.ev("root.feed.forget()"); h.spin(60)
ok("D9 sign out forgets access", h.ev("Object.keys(root.feed.access).length") == 0 and h.ev("root.writable"))
h.ev("root.feed.requestAccess('a/b'); root.feed.requestAccess('c/d'); root.feed.requestAccess('c/d')"); h.spin(40)
ok("D10 one check at a time; others wait once each", [c[3] for c in access()] == ["a/b"] and h.ev("root.feed.accessWaiting") == ["c/d"], (access(), h.ev("root.feed.accessWaiting")))
h.answer("access", {"state": "error", "message": "Could not load a/b."}); h.spin(150)
ok("D11 an error counts as unknown (writes on) and is not asked again; the next one runs", h.ev("root.feed.access['a/b'].known") is False and [c[3] for c in access()] == ["c/d"], access())
h.results = R1 + h.results
code = h.finish()
sys.exit(code or (0 if all(ALL) else 1))
