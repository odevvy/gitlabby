# v0.1.35: adaptive refresh. The shared BoardService keeps a pace per board
# (calm answers in a row, cards in progress); the popup's timer and the
# "due" check use Logic.adaptiveInterval of the setting and that pace. Fake
# time: the age of the last answer is set by hand (startedAt), the timer is
# fired by hand. Scale 1.5 stubs (harness15/) for the previews.
# Usage: run135.py <src> [outdir]   (previews: tip-setting, tip-fast, tip-slow, tip-active)
import sys, os, json, copy; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import lib
lib.HERE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "harness15")
from lib import *
src = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else None
P = "firelink21/phrase41"
COLS = [("Open", "open", None), ("todo", "label", "#3b82f6"), ("in progress", "label", "#eab308"), ("review", "label", "#86efac"), ("Closed", "closed", None)]
def card(i, labels): return {"iid": i, "title": "Issue %d" % i, "labels": labels, "url": "https://gitlab.com/%s/-/work_items/%d" % (P, i), "createdAt": "2026-10-29T12:00:00Z", "notes": 0, "assignees": []}
def board(todo=(20, 21), review=(50,), progress=(), stamp="15:26"):
    iss = {"todo": [card(i, ["todo"]) for i in todo], "review": [card(i, ["review"]) for i in review], "in progress": [card(i, ["in progress"]) for i in progress]}
    return {"state": "ready", "project": P, "updatedAt": "2026-10-30T%s:00Z" % stamp, "labelColors": {}, "boards": [{"id": 7, "name": "Development"}], "board": {"id": 7, "name": "Development"},
            "fallback": False, "message": "", "columns": [dict({"name": n, "kind": k, "issues": iss.get(n, [])}, **({"listId": i, "color": c} if c else {})) for i, (n, k, c) in enumerate(COLS)]}
ALL = []
def ok(n, c, e=""): ALL.append(bool(c)); h.ok(n, c, e)
h = Harness(src, {"id": "odevvy.gitlab-board", "settingsRevision": 2, "defaultProject": P, "refreshIntervalSec": 60})
cad = lambda: h.ev("root.cadence")
tickets = lambda: h.ev("root.feed.tickets")
def age(sec): h.ev("(function(){ var f = root.feed, a = {}; for (var k in f.answers) a[k] = Object.assign({}, f.answers[k], { startedAt: Date.now() - %d }); f.answers = a })()" % (sec * 1000))
def tick(): t = tickets(); h.ev("refreshTimer.triggered()"); h.spin(40); return tickets() > t
def same(n, **kw):
    for _ in range(n): h.ev("root.refresh()"); h.spin(30); h.answer("board", board(**kw)); h.spin(30)
def tip():
    st = h.ev("header.status"); QTest.mouseMove(h.win, h.scene(st, 0.97, 0.5)); h.spin(700)
    t = [str(c.property("text")) for it in h.walk() for c in it.children() if c.metaObject().className().startswith("IconTip") and c.property("visible")]
    return t
def shot(name): out and h.grab_card(os.path.join(out, name + ".png"))

h.ev("root.opened = true"); h.spin(60)
ok("A0 before any answer: the setting (60 s)", cad() == {"sec": 60, "why": "your setting"}, cad())
h.answer("board", board()); h.spin(60)
ok("A1 first answer: the setting; the timer at 60 s", cad()["sec"] == 60 and h.ev("refreshTimer.interval") == 60000 and h.ev("refreshTimer.running"))
ok("A2 the pace lives in the shared service", h.ev("root.feed.paces[root.fetchKey].calm") == 2)
ok("A3 hovering 'Updated': how often and why", tip() == ["Refreshes every 1 min while open · your setting"], tip())
shot("tip-setting"); QTest.mouseMove(h.win, QPoint(1, 1)); h.spin(60)
age(35)
ok("T1 a tick 35 s after the last fetch (setting 60 s): no fetch", not tick())
same(3)
ok("B1 nothing changed in 4 answers: 2 min, 'nothing changed lately'", cad() == {"sec": 120, "why": "nothing changed lately"} and h.ev("refreshTimer.interval") == 120000, cad())
age(70)
ok("T2 a tick 70 s after (would fetch at 60 s): no fetch now", not tick())
age(125)
ok("T3 a tick 125 s after: fetches", tick())
ok("T4 'Refreshing…' while it runs", h.ev("header.status.text") == "Refreshing…" and h.ev("root.loading"), h.ev("header.status.text"))
h.answer("board", board()); h.spin(40)
same(6)
ok("B2 a long calm: 4 min, never more (4x the setting)", cad()["sec"] == 240, cad())
shot_tip = tip(); shot("tip-slow"); QTest.mouseMove(h.win, QPoint(1, 1)); h.spin(60)
ok("B3 its tip", shot_tip == ["Refreshes every 4 min while open · nothing changed lately"], shot_tip)
h.ev("root.refresh()"); h.spin(30)
ok("M1 Refresh still fetches at once, whatever the pace", h.running("board") != [])
h.answer("board", board(todo=(20,), review=(50, 21))); h.spin(40)
ok("F1 a card moved: 30 s, 'cards moved recently'", cad() == {"sec": 30, "why": "cards moved recently"} and h.ev("refreshTimer.interval") == 30000, cad())
f = tip(); shot("tip-fast"); QTest.mouseMove(h.win, QPoint(1, 1)); h.spin(60)
ok("F2 its tip", f == ["Refreshes every 30 s while open · cards moved recently"], f)
age(35)
ok("F3 a tick 35 s after: fetches (faster than the setting)", tick())
h.answer("board", board(todo=(20,), review=(50, 21))); h.spin(40)
ok("F4 one calm answer after the move: still 30 s", cad()["sec"] == 30)
same(1, todo=(20,), review=(50, 21))
ok("F5 two calm answers: back to the setting", cad()["sec"] == 60)
same(1, todo=(20,), review=(50, 21), progress=(40,))
ok("F6 a card in progress counts as a change (it came into that column)", cad()["sec"] == 30)
same(8, todo=(20,), review=(50, 21), progress=(40,))
ok("C1 cards in progress: no slower than the setting", cad() == {"sec": 60, "why": "cards in progress"}, cad())
c = tip(); shot("tip-active"); QTest.mouseMove(h.win, QPoint(1, 1)); h.spin(60)
ok("C2 its tip", c == ["Refreshes every 1 min while open · cards in progress"], c)
h.ev("root.setRefreshInterval(30)"); h.spin(40)
ok("S1 setting 30 s: 30 s (the floor)", cad()["sec"] == 30 and h.ev("refreshTimer.interval") == 30000)
h.ev("root.setRefreshInterval(900)"); h.spin(40)
same(8, todo=(20,), review=(50, 21))
ok("S2 setting 15 min, calm: 60 min at most", cad()["sec"] == 3600, cad())
h.ev("root.refresh()"); h.spin(30); h.answer("board", {"state": "error", "message": "GitLab is down"}); h.spin(40)
ok("E1 a failed refresh keeps the pace", cad()["sec"] == 3600)
h.ev("root.feed.forget()"); h.spin(40)
ok("E2 sign out forgets it: the setting again", cad() == {"sec": 900, "why": "your setting"}, cad())
h.stop_all()
loops = [w for w in h.warnings if "oop" in w]
ok("Z no binding-loop warnings", not loops, loops)
ok("Z no QML warnings", not h.warnings, h.warnings[:3])
print("passed", sum(ALL), "failed", len(ALL) - sum(ALL))
sys.stdout.flush(); os._exit(0 if all(ALL) else 1)
