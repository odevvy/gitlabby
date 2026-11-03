# v0.1.65: another GitLab server (settings.gitlabHost), plumbing only. Proves:
# gitlab.com stays as before (every command ends with --hostname gitlab.com,
# the same saved keys, the same sign-in command); the setting is read as a bare
# name (https:// and a trailing / dropped; http, a port or a path count as
# gitlab.com); every board-fetch command, the widget's and the service's, names
# the server; switching server forgets the last one's board, saved copy,
# projects, account, merge requests and answers on their way; bots, alerts,
# confirm moves, column state and the default board are per server, and
# switching back finds gitlab.com's again. Usage: run165.py <src>
import sys, os, json, copy; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
P, H = "group/app", "gitlab.example.com"
BOTS = {"busyLists": ["in progress", "review"], "bots": [{"name": "App UI", "label": "app-ui"}, {"name": "API", "label": "api"}]}
SETTINGS = {"id": "odevvy.gitlab-board", "settingsRevision": 2, "defaultProject": P, "defaultBoardId": "7", "defaultBoardName": "Development",
            "refreshIntervalSec": 60, "defaultCollapsed": ["closed"], "boardStates": {}, "bots": {P: BOTS}, "alerts": {P: {"review": True, "idle": True}}}
def row(i, labels, host="gitlab.com"): return {"iid": i, "title": "Card %d" % i, "labels": labels, "url": "https://%s/%s/-/issues/%d" % (host, P, i), "createdAt": "2026-10-29T12:00:00Z", "notes": 0, "assignees": []}
def board(prog, review, host="gitlab.com"):
    cols = [("todo", 11, [row(1, ["todo"], host)]), ("in progress", 12, prog), ("Review", 13, review)]
    return {"state": "ready", "project": P, "updatedAt": "2026-10-30T15:00:00Z", "labelColors": {}, "boards": [{"id": 7, "name": "Development"}], "board": {"id": 7, "name": "Development"},
            "fallback": False, "message": "", "columns": [{"name": "Open", "kind": "open", "issues": []}] + [{"name": n, "kind": "label", "listId": l, "issues": r} for n, l, r in cols] + [{"name": "Closed", "kind": "closed", "issues": []}]}
A = lambda host="gitlab.com": board([row(3, ["in progress", "api"], host)], [row(4, ["review"], host)], host)
C = lambda host="gitlab.com": board([], [row(4, ["review"], host), row(3, ["review", "api"], host)], host)

h = Harness(sys.argv[1], SETTINGS)
writes = lambda: h.ev("root.bar.shell.writes") or []
def setting(**kw):  # a settings change from outside (the shell), as Settings > Server will make
    s = dict(h.ev("root.savedSettings")); s.update(kw); h.ev("root.settings = " + json.dumps(s)); h.spin(80)
def drain(kind, data):
    while h.running(kind): h.answer(kind, data)
def tail_ok(cmds, host): return len(cmds) > 0 and all(c[-2:] == ["--hostname", host] and c.count("--hostname") == 1 for c in cmds)

# --- gitlab.com, as before -------------------------------------------------------
h.ok("G0 no setting: gitlab.com, the bare project key", h.ev("root.gitlabHost") == "gitlab.com" and h.ev("root.projectKey") == P and h.ev("root.feed.host") == "gitlab.com")
h.ev("root.opened = true"); h.spin(60)
start = h.running(raw=True)
h.ok("G1 every command ends with --hostname gitlab.com (cached, board)", tail_ok(start, "gitlab.com") and {c[1] for c in start} >= {"cached", "board"}, start)
h.ok("G2 ...and reads as before without it", ["cached", "--project", P, "--board", "7"] in [c[1:] for c in h.running()], h.running())
h.answer("cached", {"state": "none"}); h.answer("board", A())
h.ok("G3 board loaded; its bots from settings.bots[project]", h.ev("root.boardState") == "ready" and len(h.ev("root.botStates")) == 2)
h.ok("G4 column state key as before", h.ev("root.stateKey") == P + "#7")
h.ev("root.showView('settings')"); h.spin(60)
h.ok("G5 whoami on gitlab.com", tail_ok(h.running("whoami", raw=True), "gitlab.com"))
h.answer("whoami", {"state": "ready", "user": "dev1"}); h.answer("access", {"state": "ready", "project": P, "level": 40, "scopes": ["api"]})
h.ok("G5b Settings' label list (Bots) on gitlab.com", [c[1:] for c in h.running("labels", raw=True)] == [["labels", "--project", P, "--hostname", "gitlab.com"]], h.running(raw=True))
drain("labels", {"state": "ready", "labels": []})
h.ok("G5c ...kept under the bare project key", h.ev("settingsView.labelsFor") == P)
h.ev("root.showView('board')"); h.spin(60)
h.ev("root.signIn()"); h.spin(40)
h.ok("G6 sign in: plain glab auth login, as before", h.launched()[-1:] == [["omarchy-launch-floating-terminal-with-presentation", "glab auth login"]], h.launched()[-1:])
h.ev("root.opened = true"); h.spin(60)  # signing in closed it
h.answer("board", A()) if h.running("board") else None
h.ev("root.persist()"); w = writes()[-1]
h.ok("G7 a write on gitlab.com: the same keys as before (no server keys added)", "serverDefaults" not in w and "gitlabHost" not in w and w["defaultProject"] == P and w["defaultBoardId"] == "7", sorted(w))
h.ev("root.feed.requestMrs('all', false)"); h.spin(40)
h.ok("G8 the service's merge requests on gitlab.com too", tail_ok(h.running("mrs", raw=True), "gitlab.com"), h.running(raw=True))
h.answer("mrs", {"state": "ready", "review": [], "mine": []})
h.ok("G9 merge requests kept (until the server changes)", len(h.ev("Object.keys(root.feed.mrAnswers)")) == 1)

# --- the setting, read as a bare name ----------------------------------------------
for raw, want in [("https://GitLab.Example.com/", H), (" gitlab.example.com// ", H), ("http://gitlab.example.com", "gitlab.com"),
                  ("gitlab.example.com:8443", "gitlab.com"), ("gitlab.example.com/gitlab", "gitlab.com"), ("x.com --hostname y", "gitlab.com"), ("", "gitlab.com")]:
    h.ok("S1 gitlabHost %r reads as %s" % (raw, want), h.ev("Logic.serverHost(%s) || 'gitlab.com'" % json.dumps(raw)) == want)

# --- switching to another server ----------------------------------------------------
h.answer("board", A()) if h.running("board") else None
h.ev("root.refresh()"); h.spin(40)  # a fetch on its way to gitlab.com when the server changes
inflight = h.running("board")
h.ev("root.runAux('projects', [])"); h.spin(20); h.answer("projects", {"state": "ready", "projects": [{"path": "old/gitlab-com"}]})
h.ok("W0 gitlab.com's project list loaded", len(h.ev("root.projects")) == 1)
h.ev("root.runAux('projects', [])"); h.spin(20)  # and another on its way
setting(gitlabHost="https://" + H + "/")
h.ok("W1 the server: a bare name, the service follows", h.ev("root.gitlabHost") == H and h.ev("root.feed.host") == H)
h.ok("W2 nothing of gitlab.com's left: no project (no default here), board, projects, account",
     h.ev("root.project") == "" and h.ev("root.columns").__len__() == 0 and h.ev("root.projects").__len__() == 0 and h.ev("root.account") == "" and h.ev("root.cached") is False, [h.ev("root.project"), h.ev("root.account")])
h.ok("W3 the service forgot its answers, merge requests and access", h.ev("Object.keys(root.feed.answers).length") == 0 and h.ev("Object.keys(root.feed.mrAnswers).length") == 0 and h.ev("Object.keys(root.feed.access).length") == 0)
h.ok("W4 a fetch was on its way", len(inflight) == 1)
h.answer("board", A())  # gitlab.com's answer arrives late
h.ok("W5 ...its late answer is dropped", h.ev("root.columns").__len__() == 0 and h.ev("Object.keys(root.feed.answers).length") == 0)
h.answer("projects", {"state": "ready", "projects": [{"path": "old/gitlab-com"}]})
h.ok("W5b ...and so is its project list's", h.ev("root.projects").__len__() == 0)
h.ev("root.persist()")
h.ok("W5c a write here before any board is picked saves no default for it", "serverDefaults" not in writes()[-1] and writes()[-1]["defaultProject"] == P, writes()[-1].get("serverDefaults"))
proj = h.running("projects", raw=True)
h.ok("W6 the open popup asks this server for its projects (the picker's first step)", tail_ok(proj, H), h.running(raw=True))
drain("projects", {"state": "ready", "projects": [{"path": P, "name": "app"}]})
h.ok("W7 the old server's project list never shows", [p.get("path") for p in h.ev("root.projects")] == [P], h.ev("root.projects"))
h.ok("W8 sign in names the server", (h.ev("root.signIn()"), h.spin(40), h.launched()[-1])[2] == ["omarchy-launch-floating-terminal-with-presentation", "glab auth login --hostname " + H])
h.ev("root.opened = true"); h.spin(60)
drain("projects", {"state": "ready", "projects": [{"path": P, "name": "app"}]})
h.ok("W9 signed-out fallback text names it too", h.ev("root.loginCommand") == "glab auth login --hostname " + H)

# --- per-server settings --------------------------------------------------------------
h.ev("root.pickProject(%s)" % json.dumps(P)); h.spin(40)
h.ok("K1 boards from this server", tail_ok(h.running("boards", raw=True), H))
h.answer("boards", {"state": "ready", "boards": [{"id": 7, "name": "Development"}]})
h.ev("root.pickBoard({id: 7, name: 'Development'})"); h.spin(60)
w = writes()[-1]
h.ok("K2 the first board here becomes this server's default; gitlab.com's stays",
     w.get("serverDefaults") == {H: {"project": P, "id": "7", "name": "Development"}} and w["defaultProject"] == P and w["defaultBoardId"] == "7", w.get("serverDefaults"))
h.ok("K3 key: the server's name first", h.ev("root.projectKey") == H + ":" + P and h.ev("root.stateKey") == H + ":" + P + "#7")
cmds = h.running(raw=True)
h.ok("K4 board and saved copy from this server", tail_ok(cmds, H) and {c[1] for c in cmds} >= {"board"}, cmds)
drain("cached", {"state": "none"}); h.answer("board", A(H))
h.ok("K5 gitlab.com's bots for the same path don't show here", h.ev("root.boardState") == "ready" and h.ev("root.botStates").__len__() == 0)
h.ok("K6 nor its alerts", h.ev("root.alerts.review") is False and h.ev("root.alerts.idle") is False and h.ev("root.watchCfg") is None)
h.ev("root.saveBots(%s)" % json.dumps({P: BOTS, H + ":" + P: BOTS})); h.spin(40)
h.ok("K7 this server's own bots", h.ev("root.botStates").__len__() == 2)
bs = h.cls("BotsSection"); bctx = h.ctx_of(bs)
ONE = {"busyLists": BOTS["busyLists"], "bots": BOTS["bots"][1:]}
h.ev("root.saveBots(%s)" % json.dumps({P: BOTS, H + ":" + P: ONE})); h.spin(40)
h.ok("K7b Settings > Bots lists this server's", h.ev("sec.bots.length", bctx) == 1 and h.ev("sec.bots[0].name", bctx) == "API")
h.ev("sec.remove(0)", bctx); h.spin(40)
h.ok("K7c removing one there changes this server's only", writes()[-1]["bots"].get(H + ":" + P, {}).get("bots", []) == [] and writes()[-1]["bots"][P] == BOTS, writes()[-1]["bots"])
h.ev("root.saveBots(%s)" % json.dumps({P: BOTS, H + ":" + P: ONE})); h.spin(40)
h.ev("sec.toggleBusy('todo')", bctx); h.spin(40)
h.ok("K7d busy columns too", "todo" in writes()[-1]["bots"].get(H + ":" + P, {}).get("busyLists", []) and writes()[-1]["bots"][P] == BOTS, writes()[-1]["bots"])
h.ev("sec.open()", bctx); h.spin(40)
h.ok("K7e adding one is for this server's project", h.ev("sec.addFor", bctx) == H + ":" + P)
h.ev("sec.cancel()", bctx); drain("labels", {"state": "ready", "labels": []})
h.ev("root.saveBots(%s)" % json.dumps({P: BOTS, H + ":" + P: BOTS})); h.spin(40)
h.ev("root.setAlert('idle', true)"); h.spin(40)
two = lambda a: {k: {x: y for x, y in v.items() if x in ("review", "idle") or y} for k, v in (a or {}).items()}  # later versions save more flags, off
h.ok("K8 alerts saved under this server's key; gitlab.com's untouched", two(writes()[-1]["alerts"]) == {P: {"review": True, "idle": True}, H + ":" + P: {"review": False, "idle": True}}, writes()[-1]["alerts"])
h.ok("K9 the watch carries the server", (h.ev("root.watchCfg") or {}).get("host") == H)
h.ok("K10 the service's access check names the server", tail_ok(h.running("access", raw=True), H), h.running(raw=True))
h.answer("access", {"state": "ready", "project": P, "level": 40, "scopes": ["api"]})
before = len(h.launched())
h.ev("root.refresh()"); h.spin(40); h.answer("board", A(H))  # the first answer watched: the baseline
h.ev("root.refresh()"); h.spin(40); h.answer("board", C(H))
note = [c for c in h.launched()[before:] if c and c[0] == "omarchy-notification-send"]
h.ok("K11 an alert here links this server's board", len(note) == 1 and note[0][-1] == "https://%s/%s/-/boards/7" % (H, P), note)
h.ev("root.feed.requestMrs('all', true)"); h.spin(40)
h.ok("K12 merge requests from this server", tail_ok(h.running("mrs", raw=True), H), h.running(raw=True))
h.answer("mrs", {"state": "ready", "review": [], "mine": []})
h.ok("K13 confirm moves per server: gitlab.com's entry doesn't count here",
     (setting(confirmMoves=[P]), h.ev("root.confirmMoves"))[1] is False and (setting(confirmMoves=[P, H + ":" + P]), h.ev("root.confirmMoves"))[1] is True)
setting(confirmMoves=[])
h.ev("root.requestMove(root.columns[3].issues[0], root.columns[3], root.columns[2])"); h.spin(40)
mv = h.running("move", raw=True)
h.ok("K14 a move goes to this server", tail_ok(mv, H) and mv[0][1:13] == ["move", "--project", P, "--board", "7", "--iid", "4", "--from", "13", "--to", "12", "--hostname"], mv)
h.answer("move", {"state": "ready"})
drain("board", C(H))
# Bulk actions (BulkBar.qml): the label list and the one bulk process, on this server.
h.ev("root.picked = [root.columns[3].kind + ':' + root.columns[3].listId + '|4']"); h.spin(40)
h.ev("bulkBar.loadLabels()"); h.spin(40)
h.ok("U1 the bulk label list from this server", [c[1:] for c in h.running("labels", raw=True) if "--hostname" in c] == [["labels", "--project", P, "--hostname", H]], h.running(raw=True))
drain("labels", {"state": "ready", "labels": [{"name": "ux"}]})
h.ev("bulkBar.armClose('')"); h.spin(40); h.ev("bulkBar.confirm()"); h.spin(40)
bk = [c for c in h.running(raw=True) if c[1] == "bulk"]
h.ok("U2 the bulk run on this server", len(bk) == 1 and bk[0][1:] == ["bulk", "--project", P, "--hostname", H], h.running(raw=True))
h.answer("close", {"state": "ready"}); h.spin(80); h.ev("bulkBar.done()"); drain("board", C(H))
# The issue view (IssueView.qml): every read and write on this server.
ISSUE = {"iid": 4, "title": "Card 4", "state": "opened", "labels": ["review"], "description": "", "author": {"username": "me", "name": "Me"}, "url": "https://%s/%s/-/issues/4" % (H, P), "createdAt": "2026-10-29T12:00:00Z", "assignees": []}
h.ev("root.openIssue(root.columns[3].issues[0])"); h.spin(60)
iss = [c for c in h.running(raw=True) if c[1] in ("issue", "notes")]
h.ok("I1 the issue and its comments from this server", len(iss) == 2 and tail_ok(iss, H), h.running(raw=True))
h.answer("issue", {"state": "ready", "issue": ISSUE}); h.answer("notes", {"state": "ready", "notes": []})
h.ok("I2 remembered under this server's key", h.ev("Object.keys(issueView.recent)") == [H + ":" + P + "#4"], h.ev("Object.keys(issueView.recent)"))
h.ev("issueView.loadLabels()"); h.spin(40)
h.ok("I3 its label list from this server", [c[1:] for c in h.running("labels", raw=True) if "--hostname" in c] == [["labels", "--project", P, "--hostname", H]], h.running(raw=True))
h.answer("labels", {"state": "ready", "labels": [{"name": "ux"}]})
h.ev("issueView.relabel('add', 'ux')"); h.spin(40)
h.ok("I4 a label change on this server", tail_ok(h.running("relabel", raw=True), H), h.running(raw=True))
h.answer("relabel", {"state": "ready", "labels": ["review", "ux"]}); drain("issue", {"state": "ready", "issue": ISSUE})
h.ev("issueView.setState('close')"); h.spin(40)
h.ok("I5 close on this server", tail_ok(h.running("close", raw=True), H), h.running(raw=True))
h.answer("close", {"state": "ready", "issueState": "closed"}); drain("board", C(H)); drain("issue", {"state": "ready", "issue": ISSUE})
iv = h.ctx_of(h.cls("IssueView"))
h.ev("box.text = 'Looks good'", iv); h.spin(40); h.ev("issueView.post()"); h.spin(40)
h.ok("I6 a comment on this server", tail_ok(h.running("comment", raw=True), H), h.running(raw=True))
h.answer("comment", {"state": "ready", "note": {"id": 1, "body": "Looks good", "author": {"username": "me"}}}); drain("notes", {"state": "ready", "notes": []})
h.ev("root.back()"); h.spin(40)
# View-only here (AccessHint.qml): the login and the token page are this server's; Not now is per server.
VIEW_ONLY = "root.feed.setAccess(%s, {known: true, level: 10, scopes: null, refused: ''})" % json.dumps(P)
h.ev(VIEW_ONLY); h.spin(60)
body = next((it.property("text") for it in h.visible(lambda it: it.objectName() == "accessBody")), "")
h.ok("V1 the hint's login names this server", "run glab auth login --hostname %s in a terminal" % H in body, body)
before = len(h.launched())
h.click(next(it for it in h.visible(lambda it: it.objectName() == "accessTokenPage"))); h.spin(40)
h.ok("V2 the token page is this server's", [c for c in h.launched()[before:] if c[0] == "omarchy-launch-browser"] == [["omarchy-launch-browser", "https://%s/-/user_settings/personal_access_tokens?name=GitLab+board&description=Read-only+token+for+the+Omarchy+GitLab+board&scopes=read_api" % H]], h.launched()[before:])
h.ev("root.opened = true"); h.spin(60); drain("board", C(H))
h.ev("root.dismissHint()"); h.spin(40)
h.ok("V3 Not now: saved under this server's key", writes()[-1]["accessHintDismissed"] == [H + ":" + P] and h.ev("root.hintDismissed"), writes()[-1].get("accessHintDismissed"))
h.ev("root.refreshIntervalSec = 120; root.persist()"); w = writes()[-1]
h.ok("K15 another write here keeps both defaults as saved", w["defaultProject"] == P and w["defaultBoardId"] == "7" and w.get("serverDefaults", {}).get(H, {}).get("id") == "7", w.get("serverDefaults"))

# --- back to gitlab.com -----------------------------------------------------------------
h.answer("board", A(H)) if h.running("board") else None
setting(gitlabHost="gitlab.com")
h.ok("I7 another server: the issues seen on the last one are forgotten", h.ev("Object.keys(issueView.recent)") == [])
h.ok("B1 back: gitlab.com's default board, its bots and alerts", h.ev("root.project") == P and h.ev("root.boardId") == "7" and h.ev("root.projectKey") == P
     and h.ev("root.alerts.review") is True and h.ev("root.feed.host") == "gitlab.com")
cmds = h.running(raw=True)
cmds = [c for c in cmds if c[1] in ("board", "cached")]  # the other server's last answer may still be on its way (dropped: W5)
h.ok("B2 its board loads from gitlab.com", tail_ok(cmds, "gitlab.com") and "board" in [c[1] for c in cmds], cmds)
drain("cached", {"state": "none"}); h.answer("board", A())
h.ok("B3 gitlab.com's bots show again", h.ev("root.botStates").__len__() == 2)
h.ev(VIEW_ONLY); h.spin(60)
h.ok("B3b the other server's Not now doesn't hide gitlab.com's hint; its words as before", not h.ev("root.hintDismissed")
     and "run glab auth login --hostname gitlab.com in a terminal" in next((it.property("text") for it in h.visible(lambda it: it.objectName() == "accessBody")), ""))
h.ev("root.signOut()"); h.spin(40)
h.ok("B4 sign out names the server", tail_ok(h.running("logout", raw=True), "gitlab.com"))
h.answer("logout", {"state": "logged-out", "message": "Signed out of gitlab.com."})
setting(gitlabHost=H)
h.ok("B5 the other server's default board comes back with it", h.ev("root.project") == P and h.ev("root.boardId") == "7" and h.ev("root.projectKey") == H + ":" + P)
h.ev("root.showView('settings')"); h.spin(40); drain("whoami", {"state": "ready", "user": "dev2"})
texts = lambda: [it.property("text") for it in h.visible(lambda it: it.metaObject().className().startswith("BoardText")) if it.property("text")]
h.ok("T1 Settings says which server the account is on", "Signed in as dev2 on " + H in texts(), [t for t in texts() if "Signed" in t])
h.ev("settingsView.confirming = true"); h.spin(40)
h.ok("T2 ...and which one Sign out leaves", any(t.startswith("Sign out of glab on %s? " % H) for t in texts()), [t for t in texts() if "Sign out" in t])
h.ev("settingsView.confirming = false"); drain("labels", {"state": "ready", "labels": []})
h.ev("settingsView.labelsState = ''; settingsView.loadLabels()"); h.spin(40)
h.ok("T3 Settings' label list (Bots) from this server", [c[1:] for c in h.running("labels", raw=True)] == [["labels", "--project", P, "--hostname", H]], h.running(raw=True))
drain("labels", {"state": "ready", "labels": []})
h.ok("T4 ...kept under this server's key", h.ev("settingsView.labelsFor") == H + ":" + P)
setting(gitlabHost="gitlab.com")
h.ok("B6 switching in settings asks the new server who is signed in", tail_ok(h.running("whoami", raw=True), "gitlab.com") and h.ev("root.account") == "", h.running(raw=True))
sys.exit(h.finish())
