# v0.1.36: desktop alerts. Two "screens" share one BoardService (as run133);
# the notifier is Quickshell.execDetached, recorded by the stub (the fake
# notifier). Proves: one notification per event for both screens, nothing on
# the first load / a board switch / after a failed refresh / for his own move,
# batched review entries, background refresh only while an alert is on and
# only when due, the exact command Omarchy's bin/omarchy-notification-send
# accepts (run against the real script with busctl faked), Do Not Disturb not
# bypassed (Omarchy's own NotificationLogic.js), the body escaped.
# Usage: run136.py <src> [outdir]   (previews: settings-alerts, settings-alerts-on, notification-review, notification-batch, notification-idle)
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import two; P = two.P; two.start({"alerts": {P: {"review": True, "idle": True}}}, "ogb-h6-"); from two import *

# --- both screens, popups closed --------------------------------------------------
spin(150)
ok("W1 both screens watch the one board in the one service; the background timer runs", ev("a", "root.feed.watchedKeys") == ["group/app#7"] and len(ev("a", "Object.keys(root.feed.watchers['group/app#7'])")) == 2 and ev("a", "root.feed.children.length >= 0") is not None and ev("a", "!root.opened && !b.opened") is not False)
ok("W2 popups closed, alerts on: the background timer runs (15 s)", ev("a", "(function(){ for (var i = 0; i < root.feed.data.length; i++) { var t = root.feed.data[i]; if (t && t.interval === 15000) return t.running } return false })()"))
ok("G1 a background tick fetches the watched board (nothing saved yet)", bg() and running() and running()[0][1] == "board")
answer(A)
ok("G2 the first load: no notification", notes() == [])
ok("G3 a tick right after: not due, no fetch", not bg())
age(); bg(); answer(B)
n = notes()
ok("N1 #2 entered review: exactly one notification for two screens", headlines(n) == ["#2 is in review"], headlines(n))
ok("N2 the command: our app name, low urgency, glyph, headline, escaped body, --exec omarchy-launch-browser with the issue link",
   n and n[0] == ["omarchy-notification-send", "--app-name", "GitLab board", "-u", "low", "-g", "\uf296", "#2 is in review", "#2 Fix &lt;b&gt; &amp; co · group/app", "--exec", "omarchy-launch-browser", "https://gitlab.com/group/app/-/issues/2"], n and n[0])
age(); bg(); answer(B)
ok("N3 the same board again: nothing new", len(notes()) == 1)
age(); bg(); answer(C)
n = notes()[1:]
ok("N4 API's card left in progress: 'Stopped working: API', the board's link; #3 into review too", sorted(headlines(n)) == ["#3 is in review", "Stopped working: API"] and all(x[-1] == "https://gitlab.com/group/app/-/boards/7" for x in n if x[7].startswith("Stopped")), n)
k = len(notes())
D = copy.deepcopy(C); D["columns"][2]["issues"] = []; D["columns"][3]["issues"] += [row(1, ["review"]), row(5, ["review"]), row(6, ["review"]), row(7, ["review"])]
age(); bg(); answer(D)
n = notes()[k:]
ok("N5 four cards at once: one notification, the board's link", headlines(n) == ["4 cards entered review"] and n[0][8] == "#1 Card 1, #5 Card 5, #6 Card 6 +1 more · group/app" and n[0][-1].endswith("/-/boards/7"), n)
k = len(notes())
age(); bg(); answer(A); k = len(notes())
age(); bg(); answer({"state": "error", "message": "GitLab is down"})
age(); bg(); answer(B)
ok("F1 after a failed refresh: the next good answer is a fresh start (#2's move into review isn't announced)", len(notes()) == k, headlines(notes()[k:]))
age(); bg(); answer(C)
ok("F2 and the change after it is announced", sorted(headlines(notes()[k:])) == ["#3 is in review", "Stopped working: API"], headlines(notes()[k:]))
k = len(notes())
# --- his own move, from screen 1 --------------------------------------------------
ev("a", "root.opened = true"); spin(60)
age(); ev("a", "root.refresh()"); spin(40); answer(A)
k = len(notes())
ev("a", "root.moveIssue(root.columns[1].issues[1], root.columns[1], root.columns[3])"); spin(60)
answer_proc("a", "move", {"state": "ready", "message": "Moved #2 to Review."}); spin(150)
answer(B)
ok("O1 his own move into review: no notification", len(notes()) == k, headlines(notes()[k:]))
E = copy.deepcopy(B); E["columns"][1]["issues"] = []; E["columns"][3]["issues"] += [row(1, ["review"])]
ev("a", "root.refresh()"); spin(40); answer(E)
ok("O2 someone else's move after it still is", headlines(notes()[k:]) == ["#1 is in review"], headlines(notes()[k:]))
ev("a", "root.refresh()"); spin(40); answer(A)
k = len(notes())
ev("a", "root.refresh()"); spin(40); answer(B)
ok("O3 later, someone else moving #2 into review again is announced (his move is forgotten once seen)", headlines(notes()[k:]) == ["#2 is in review"], headlines(notes()[k:]))
k = len(notes())
# --- a board switch on screen 1 --------------------------------------------------
ev("a", "root.switchTo('group/app', '8', 'Lean')"); spin(60)
ok("S1 screen 1 on another board: both boards watched", sorted(ev("a", "root.feed.watchedKeys")) == ["group/app#7", "group/app#8"])
answer(board([], [], [row(9, ["review"])], 8, "Lean"))
ok("S2 its first answer: nothing announced (the review card was already there)", len(notes()) == k)
ev("a", "root.switchTo('group/app', '7', 'Development')"); spin(60)
ok("S3 back: board 8 is no longer watched", ev("a", "root.feed.watchedKeys") == ["group/app#7"])
while running(): answer(E)
# --- alerts off on both copies: no watching, no background ------------------------
for k2 in ("a", "b"):
    ev(k2, "root.settings = " + json.dumps(dict(SETTINGS, alerts={P: {"review": False, "idle": False}})))
spin(80)
ok("X1 both alerts off: nothing watched, the background timer stops", ev("a", "root.feed.watchedKeys") == [] and not ev("a", "(function(){ for (var i = 0; i < root.feed.data.length; i++) { var t = root.feed.data[i]; if (t && t.interval === 15000) return t.running } return true })()"))
ok("X2 and a tick fetches nothing", not bg())
ev("a", "root.feed.watch('probe', { key: 'group/app#7', project: 'group/app', boardId: '7', review: false, idle: false, bots: null, base: 60 })")
ok("X2b the service itself ignores a watch with both alerts off", ev("a", "root.feed.watchedKeys") == [])
ev("a", "root.feed.watch('probe', null)")
ev("b", "root.settings = " + json.dumps(dict(SETTINGS, alerts={P: {"review": False, "idle": True}})))
spin(80)
ok("X3 one copy with an alert on is enough to watch", ev("a", "root.feed.watchedKeys") == ["group/app#7"])

# --- signed out: no background fetch ---------------------------------------------
ev("b", "root.refresh()"); spin(40); answer({"state": "logged-out", "message": "Not signed in."}); spin(60)
age()
ok("L1 signed out: the background doesn't fetch", not bg())
ev("a", "root.feed.watch('probe', { key: 'group/app#7', project: 'group/app', boardId: '7', review: true, idle: false, bots: null, base: 60 })"); age()
ok("L3 the service itself skips a board whose last answer was 'logged-out'", not bg())
ev("a", "root.feed.watch('probe', null)")
ev("a", "root.feed.forget()"); spin(40)
ok("L2 signed out: nothing watched (the sign-in panel shows instead)", ev("a", "root.feed.watchedKeys") == [])
# --- the real omarchy-notification-send with busctl faked --------------------------
fake = tempfile.mkdtemp(prefix="ogb-bus-")
open(fake + "/busctl", "w").write('#!/bin/bash\nprintf "%s\\0" "$@" > "$BUSLOG"\necho "u 1"\n'); os.chmod(fake + "/busctl", 0o755)
def run_send(argv):
    log = fake + "/log"; env = dict(os.environ, PATH=fake + ":" + os.environ["PATH"], BUSLOG=log)
    r = subprocess.run([O406 + "/bin/omarchy-notification-send"] + argv[1:], env=env, capture_output=True, text=True)
    return r.returncode, (open(log).read().split("\0")[:-1] if os.path.exists(log) else []), r.stderr
argv = ["omarchy-notification-send", "--app-name", "GitLab board", "-u", "low", "-g", "\uf296", "#2 is in review", "#2 Fix &lt;b&gt; &amp; co · group/app", "--exec", "omarchy-launch-browser", "https://gitlab.com/group/app/-/issues/2"]
rc, bus, err = run_send(argv)
i = bus.index("susssasa{sv}i") if "susssasa{sv}i" in bus else -1
ok("R1 the real script takes our command: app name, summary, body in their D-Bus slots", rc == 0 and i > 0 and bus[i + 1:i + 6] == ["GitLab board", "0", "", "#2 is in review", "#2 Fix &lt;b&gt; &amp; co · group/app"], (rc, err, bus[i + 1:i + 6] if i > 0 else bus))
hint = bus[bus.index("omarchy-exec-argv") + 2] if "omarchy-exec-argv" in bus else ""
ok("R2 low urgency (byte 0), the glyph, and the click command as one JSON argv", "urgency" in bus and bus[bus.index("urgency") + 2] == "0" and "omarchy-glyph" in bus and json.loads(hint or "null") == ["omarchy-launch-browser", "https://gitlab.com/group/app/-/issues/2"], (bus, hint))
nl = O406 + "/shell/plugins/notifications/NotificationLogic.js"
js = "const N = require(%s); const n = { appName: 'GitLab board', urgency: 0 }; console.log(JSON.stringify([N.shouldBypassDnd(n, 2), N.isEphemeralApp('GitLab board'), N.parseExecArgv(%s), N.styledBody(%s, 'GitLab board', '')]))" % (json.dumps(nl), json.dumps(hint), json.dumps(argv[8]))
res = json.loads(subprocess.run(["node", "-e", js], capture_output=True, text=True).stdout or "null")
ok("D1 Omarchy's own rules: Do Not Disturb not bypassed; kept in history while silenced (not ephemeral)", res and res[0] is False and res[1] is False, res)
ok("D2 the click command passes Omarchy's argv check; the body shows the title's <b> as text", res and res[2] == ["omarchy-launch-browser", "https://gitlab.com/group/app/-/issues/2"] and res[3] == "#2 Fix &lt;b&gt; &amp; co · group/app", res)
rc2, _, err2 = run_send(["x", "--app-name", "GitLab board", "-u", "low", "#1 is in review", "-u", "--exec", "xdg-open", "https://x"])
ok("D3 (control) why bodies never start with '-': the script would read '-u' there as an option", rc2 != 0, (rc2, err2))
loops = [w for w in warnings if "oop" in w]
ok("Z no binding-loop warnings", not loops, loops)
ok("Z no QML warnings", not warnings, warnings[:3])
print("passed", sum(results), "failed", len(results) - sum(results))
sys.stdout.flush(); os._exit(0 if all(results) else 1)
