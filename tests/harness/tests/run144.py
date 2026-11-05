# v0.1.44: a bulk run is one board-fetch bulk process. Each card is one stdin
# line (the single-card write's arguments as JSON), answered by one stdout
# line; the next card goes in after the answer; the end of the run closes
# stdin. Same per-card results, cap, Esc stop and stop rules as before.
# Usage: run144.py <src>
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import os
os.environ["OGB_SCALE"] = "1.5"
import lib
from lib import *
src = sys.argv[1]
P = "firelink21/phrase41"
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "run134.py")).read().split("ALL = []")[0].split("P = \"firelink21/phrase41\"")[1])
ALL = []
def ok(n, c, e=""): ALL.append(bool(c)); h.ok(n, c, e)
h = Harness(src, {"id": "odevvy.gitlab-board", "settingsRevision": 2, "defaultProject": P, "defaultCollapsed": ["open", "research", "Closed"], "bots": FOUR})
h.ev("panel.availableCardHeight = %d; panel.availableCardWidth = 1460" % DESK)
h.ev("root.opened = true"); h.spin(60); h.answer("board", board()); h.spin(150)
col = lambda name: "root.columns.filter(function(c){ return c.name === %s })[0]" % json.dumps(name)
FINISH = "The last change is still finishing on GitLab. Try again in a moment."
rp = "(function(){ for (var i = 0; i < bulkBar.data.length; i++) { var c = bulkBar.data[i]; if (c && c.written !== undefined && c.stdout && c.stdout.read !== undefined) return c } return null })()"
bulk_wd = "(function(){ for (var i = 0; i < bulkBar.data.length; i++) if (bulkBar.data[i].interval !== undefined && bulkBar.data[i].triggered !== undefined && bulkBar.data[i].interval >= 45000) return bulkBar.data[i]; return null })()"
todo = h.ev(col("todo") + ".issues.map(function(i){ return i.iid })")[:3]
helper = h.ev("root.helperPath()")
def run(iids, verb="armClose"):
    for i in iids: h.ev("root.togglePick(%s, %d)" % (col("todo"), i))
    h.spin(40); h.ev("bulkBar.%s('')" % verb); h.spin(40); h.ev("bulkBar.confirm()"); h.spin(80)
lines = lambda: [json.loads(l) for l in h.ev(rp + ".written")]
starts = []
h.ev(rp).started.connect(lambda: starts.append(1))

run(todo)
ok("P1 one bulk process for the run, for this project", h.running("bulk") == [[helper, "bulk", "--project", P]] and h.ev(rp + ".stdinEnabled"), h.running())
ok("P2 the first card is one stdin line: close's own arguments", lines() == [["close", "--project", P, "--iid", str(todo[0])]], lines())
h.answer("close", {"state": "ready", "message": "Closed #%d." % todo[0]}); h.spin(80)
ok("P3 the next card goes in after the answer, same process", [l[4] for l in lines()] == [str(todo[0]), str(todo[1])] and len(starts) == 1, [lines(), starts])
h.answer("close", {"state": "error", "message": "Closing failed: 409 Conflict"}); h.spin(80)
ok("P4 an ordinary failure: the run goes on in the same process", [l[4] for l in lines()] == [str(i) for i in todo] and len(starts) == 1)
h.answer("close", {"state": "ready", "message": "Closed."}); h.spin(150)
ok("P5 the end of the run closes stdin and the process ends", not h.ev(rp + ".stdinEnabled") and h.running("bulk") == [] and h.ev("bulkBar.mode") == "results")
ok("P6 per-card results as before", h.ev("bulkBar.results.map(function(r){ return r.status })") == ["done", "failed", "done"] and h.ev("bulkBar.results[1].text") == "Closing failed: 409 Conflict")
h.answer("board", board()) if h.running("board") else None
h.ev("bulkBar.done()"); h.spin(60)

# Esc: stops after the current card; stdin closes once it has answered.
run(todo)
h.key(Qt.Key_Escape)
ok("E1 Esc while running: the current card still runs", h.ev("bulkBar.mode") == "running" and len(h.running("close")) == 1)
h.answer("close", {"state": "ready", "message": "Closed."}); h.spin(150)
ok("E2 after its answer: nothing more written, process ended", len(lines()) == 1 and h.running("bulk") == [] and h.ev("bulkBar.mode") == "results", [lines(), h.running()])
h.answer("board", board()) if h.running("board") else None
h.ev("bulkBar.done()"); h.spin(60)

# Signed out: stops the run.
run(todo)
h.answer("close", {"state": "logged-out", "message": "Not signed in to gitlab.com. Run: glab auth login"}); h.spin(150)
ok("S1 signed out stops: one line, process ended, rest not tried", len(lines()) == 1 and h.running("bulk") == [] and h.ev("bulkBar.results.map(function(r){ return r.status })") == ["failed", "untried", "untried"])
h.answer("board", board()) if h.running("board") else None
h.ev("bulkBar.done()"); h.spin(60)

# The process ends without answering its card: that card fails, the run goes on.
run(todo[:2])
h.ev("(function(){ var p = %s; p.running = false; p.exited(1, 0) })()" % rp); h.spin(150)
ok("X1 no answer: the card failed (no readable output), next card in a new process", h.ev("bulkBar.results[0].status") == "failed" and h.ev("bulkBar.results[0].text") == "board-fetch returned no readable output." and h.running("bulk") != [] and lines()[-1][4] == str(todo[1]), [h.ev("bulkBar.results"), h.running()])
h.answer("close", {"state": "ready", "message": "Closed."}); h.spin(150)
h.answer("board", board()) if h.running("board") else None
h.ev("bulkBar.done()"); h.spin(60)

# The watchdog gives up: stdin closes, but the process (and its card) still runs.
run(todo[:2])
h.ev(bulk_wd + ".triggered()"); h.spin(100)
ok("W1 watchdog: results, stdin closed, its card still running", h.ev("bulkBar.mode") == "results" and not h.ev(rp + ".stdinEnabled") and len(h.running("close")) == 1)
h.ev("bulkBar.done()"); h.spin(40)
h.ev("root.togglePick(%s, %d)" % (col("todo"), todo[1])); h.spin(40); h.ev("bulkBar.armClose('')"); h.spin(40)
ok("W2 arming meanwhile: the still-finishing note", h.ev("bulkBar.mode") == "" and h.ev("bulkBar.note") == FINISH)
h.answer("close", {"state": "ready", "message": "Closed."}); h.spin(150)
ok("W3 its late answer changes no result and the process ends", h.running("bulk") == [] and h.ev("bulkBar.mode") == "")
h.ev("bulkBar.armClose('')"); h.spin(40)
ok("W4 then arming works", h.ev("bulkBar.mode") == "armed")
h.stop_all()
print("passed %d failed %d" % (sum(ALL), len(ALL) - sum(ALL)))
h.finish()
