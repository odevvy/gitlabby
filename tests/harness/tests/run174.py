# v0.1.74: an alert notification opens its link as Settings > Open links in says
# (openLinks): an app window (omarchy-launch-webapp) or a browser tab
# (omarchy-launch-browser), https only. Setup as run136 (v0.1.36 desktop alerts).
# Was: v0.1.36: desktop alerts. Two "screens" share one BoardService (as run133);
# the notifier is Quickshell.execDetached, recorded by the stub (the fake
# notifier). Proves: one notification per event for both screens, nothing on
# the first load / a board switch / after a failed refresh / for his own move,
# batched review entries, background refresh only while an alert is on and
# only when due, the exact command Omarchy's bin/omarchy-notification-send
# accepts (run against the real script with busctl faked), Do Not Disturb not
# bypassed (Omarchy's own NotificationLogic.js), the body escaped.
# Usage: run136.py <src> [outdir]   (previews: settings-alerts, settings-alerts-on, notification-review, notification-batch, notification-idle)
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import two; P = two.P; two.start({"alerts": {P: {"review": True, "idle": False}}, "openLinks": "app"}, "ogb-h174-"); from two import *


D = board([row(1, ["todo"])], [], [row(4, ["review"]), row(2, ["review", "app-ui"], "Fix <b> & co"), row(3, ["review", "api"]), row(5, ["review"], "Five")])
spin(150)
ok("L0 alerts on, openLinks app: the watched board carries links: app", ev("a", "root.feed.watchers['group/app#7'] && Object.keys(root.feed.watchers['group/app#7']).map(function(o){ return root.feed.watchers['group/app#7'][o].links })") == ["app", "app"])
bg(); answer(A); age(); bg(); answer(B)
n = notes()
ok("L1 App window: a click opens #2 in an app window (omarchy-launch-webapp)", headlines(n) == ["#2 is in review"] and n[0][-3:] == ["--exec", "omarchy-launch-webapp", "https://gitlab.com/group/app/-/issues/2"], n and n[-1])
# Settings > Browser tab on both screens (one saved setting, two copies of the board)
for k in ("a", "b"): ev(k, "root.settings = Object.assign({}, root.settings, { openLinks: 'browser' })")
spin(100)
ok("L2 switched to Browser tab: the watch carries links: browser, the same board still watched", ev("a", "Object.keys(root.feed.watchers['group/app#7']).map(function(o){ return root.feed.watchers['group/app#7'][o].links })") == ["browser", "browser"])
age(); bg(); answer(C)
n = notes()
ok("L3 the switch kept the last answer: only #3 is new, and it opens in a browser tab (omarchy-launch-browser)", headlines(n) == ["#2 is in review", "#3 is in review"] and n[-1][-3:] == ["--exec", "omarchy-launch-browser", "https://gitlab.com/group/app/-/issues/3"], [x[-3:] for x in n])
for k in ("a", "b"): ev(k, "root.settings = Object.assign({}, root.settings, { openLinks: 'webapp' })")
spin(100); age(); bg(); answer(D)
n = notes()
ok("L4 only 'app' is an app window: a saved 'webapp' is a browser tab", headlines(n)[-1] == "#5 is in review" and n[-1][-2] == "omarchy-launch-browser", n and n[-1][-3:])
# The real omarchy-notification-send (busctl faked) and Omarchy's own argv check
fake = tempfile.mkdtemp(prefix="ogb-bus-")
open(fake + "/busctl", "w").write('#!/bin/bash\nprintf "%s\\0" "$@" > "$BUSLOG"\necho "u 1"\n'); os.chmod(fake + "/busctl", 0o755)
log = fake + "/log"; env = dict(os.environ, PATH=fake + ":" + os.environ["PATH"], BUSLOG=log)
argv = ev("a", "Logic.notifyArgv({ headline: '#2 is in review', body: 'b', url: 'https://gitlab.com/group/app/-/issues/2' }, 'app')")
r = subprocess.run([O406 + "/bin/omarchy-notification-send"] + argv[1:], env=env, capture_output=True, text=True)
bus = open(log).read().split("\0")[:-1] if os.path.exists(log) else []
hint = bus[bus.index("omarchy-exec-argv") + 2] if "omarchy-exec-argv" in bus else ""
nl = O406 + "/shell/plugins/notifications/NotificationLogic.js"
res = json.loads(subprocess.run(["node", "-e", "const N = require(%s); console.log(JSON.stringify(N.parseExecArgv(%s)))" % (json.dumps(nl), json.dumps(hint))], capture_output=True, text=True).stdout or "null")
ok("R1 the real script and Omarchy's argv check take the app-window click", r.returncode == 0 and res == ["omarchy-launch-webapp", "https://gitlab.com/group/app/-/issues/2"], (r.returncode, r.stderr, res))
loops = [w for w in warnings if "oop" in w]
ok("Z no binding-loop warnings", not loops, loops)
ok("Z no QML warnings", not warnings, warnings[:3])
print("passed", sum(results), "failed", len(results) - sum(results))
sys.stdout.flush(); os._exit(0 if all(results) else 1)
