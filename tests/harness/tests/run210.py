# v0.1.110: opening the popup refreshes the board when its last fetch is older
# than the Refresh every setting (not the slowed pace), loudly: "Updating…" and
# the spinning icon. Fresh enough: "Up to date · HH:MM" for 2 s, then
# "Updated HH:MM". A fetch on its way is joined; a held board queues. Landing
# on Merge requests or To-do uses the same rule for its list.
# Usage: run210.py <src>
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
P = "group/app"
BOARD = {"state": "ready", "project": P, "updatedAt": "2026-10-31T13:20:00Z", "message": "", "labelColors": {}, "boards": [{"id": 1, "name": "Dev"}], "board": {"id": 1, "name": "Dev"}, "fallback": False,
  "columns": [{"name": "Open", "kind": "open", "issues": []}, {"name": "Closed", "kind": "closed", "issues": []}]}
LISTS = {"state": "ready", "message": "", "scope": "all", "updatedAt": "2026-10-31T13:20:00Z", "review": [], "mine": [], "todos": [], "assigned": []}
h = Harness(sys.argv[1], {"id": "odevvy.gitlabby", "settingsRevision": 2, "defaultProject": P, "defaultCollapsed": [], "favorites": [], "serverFavorites": {}})
ev = h.ev
tickets = lambda: ev("root.feed.tickets")
status = lambda: ev("root.statusText()")
def age(ms):  # the last board answer started ms earlier
    ev("var a = root.feed.answers; var k = root.fetchKey; a[k] = Object.assign({}, a[k], {startedAt: a[k].startedAt - %d}); root.feed.answers = a" % ms)
def reopen():
    ev("root.opened = false"); h.spin(30); ev("root.opened = true"); h.spin(60)

ev("root.opened = true"); h.spin(60); h.answer("board", BOARD); h.spin(120)
t0 = tickets()
reopen()
h.ok("S1 fresh: no fetch on open", tickets() == t0)
h.ok("S2 it says Up to date with the time", status().startswith("Up to date · ") and status()[-5:] == ev("new Date(root.updatedAt).toLocaleTimeString(Qt.locale(), 'HH:mm')"), status())
h.ok("S3 not loud: no spin, no Updating", not ev("root.loudRefresh") and not ev("root.updating") and not ev("root.refreshActive"))
h.spin(2200)
h.ok("S4 after 2 s: Updated HH:MM", status().startswith("Updated "), status())

# Slowed pace (4x the setting) no longer delays the open refresh.
ev("var p = {}; p[root.fetchKey] = { sig: 'x', calm: 9, active: false }; root.feed.paces = p"); h.spin(20)
h.ok("P0 the pace is slowed past the setting", ev("root.cadence.sec") > ev("root.refreshIntervalSec"), ev("root.cadence.sec"))
age(ev("root.refreshIntervalSec") * 1000 + 1000)
reopen()
h.ok("P1 older than the setting: opening fetches", tickets() == t0 + 1)
h.ok("P2 loud: Updating…, the icon spins", status() == "Updating…" and ev("root.manualRefresh") and ev("root.refreshActive"), status())
h.answer("board", BOARD); h.spin(100)
h.ok("P2b a quick answer still reads Updating… for half a second", status() == "Updating…", status())
h.spin(600)
h.ok("P3 then Updated HH:MM", status().startswith("Updated "), status())
age(ev("root.refreshIntervalSec") * 1000 - 5000)
t1 = tickets(); reopen()
h.ok("P4 just under the setting: no fetch, Up to date", tickets() == t1 and status().startswith("Up to date"), status())

# The timer keeps the slowed pace and stays quiet.
age(ev("root.cadence.sec") * 1000 + 1000)
ev("root.refresh(true)"); h.spin(40)
h.ok("T1 the timer's refresh stays quiet", tickets() == t1 + 1 and not ev("root.manualRefresh") and not status().startswith("Up to date"), status())
h.answer("board", BOARD); h.spin(200)
ev("root.refresh(true)"); h.spin(40)
h.ok("T2 a skipped timer tick says nothing new", not ev("root.upToDate"))

# A fetch on its way is joined, not doubled; it is loud.
ev("root.refresh()"); h.spin(30); t2 = tickets()
ev("root.opened = false"); h.spin(20); ev("root.opened = true"); h.spin(40)
h.ok("J1 opening during a fetch joins it", tickets() == t2 and ev("root.manualRefresh") and not ev("root.upToDate"))
h.answer("board", BOARD); h.spin(700)

# Up to date ends early on a refresh, another view, or closing.
reopen(); h.ok("E0 Up to date", ev("root.upToDate"))
ev("root.showView('settings')"); h.spin(30); h.ok("E1 another view ends it", not ev("root.upToDate"))
ev("root.showView('board')"); reopen(); ev("root.opened = false"); h.spin(20); h.ok("E2 closing ends it", not ev("root.upToDate"))
ev("root.opened = true"); h.spin(40); ev("root.refresh()"); h.spin(30); h.ok("E3 Refresh ends it", not ev("root.upToDate"))
h.answer("board", BOARD); h.spin(700)

# Lists: landing on one uses the same rule.
ev("root.showView('mrs')"); h.spin(60)
h.ok("L1 first visit loads the list", h.running("mrs"))
h.answer("mrs", LISTS); h.spin(120)
ev("root.showView('board')"); h.spin(30); ev("root.showView('mrs')"); h.spin(60)
h.ok("L2 fresh list: no fetch, Up to date", not h.running("mrs") and status().startswith("Up to date · "), status())
ev("root.showView('board')"); h.spin(30)
ev("var f = root.feed.mrs; var a = f.answers; for (var k in a) a[k] = { data: a[k].data, startedAt: a[k].startedAt - (root.refreshIntervalSec * 1000 + 1000) }; f.answers = a"); h.spin(20)
ev("root.showView('mrs')"); h.spin(60)
h.ok("L3 older than the setting: refetched", bool(h.running("mrs")) and not ev("root.upToDate"))
h.answer("mrs", LISTS); h.spin(120)
ev("root.setRefreshInterval(600)"); h.spin(20)
ev("var f = root.feed.mrs; var a = f.answers; for (var k in a) a[k] = { data: a[k].data, startedAt: a[k].startedAt - 120000 }; f.answers = a"); h.spin(20)
ev("root.showView('board')"); h.spin(30); ev("root.showView('mrs')"); h.spin(60)
h.ok("L4 a 10 min setting keeps a 2 min old list (not the old 60 s rule)", not h.running("mrs") and ev("root.upToDate"))
sys.exit(h.finish())
