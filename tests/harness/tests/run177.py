# v0.1.77 (v177 design A): the To-do tab. The service side: board-fetch todos
# (one GraphQL query: your pending to-dos and the open issues assigned to you)
# runs only when asked (the view opens, its scope changes, or r), never on
# popup open or a timer; an answer under a minute old is reused; one query
# serves both screens; sign-out forgets. Setup as run176 (two screens).
# Usage: run177.py <src>
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import two; P = two.P; two.start({}, "ogb-h177-"); from two import *



def todos_running(): return [c for c in running() if c[1] == "todos"]
def answer_todos(data):
    r = ev("a", "(function(){ var p = " + SCAN + "(root.feed).filter(function(p){ return p.running && p.command[1] === 'todos' })[0]; if (!p) return false; p.stdout.text = %s; p.stdout.streamFinished(); p.running = false; p.exited(0, 0); return true })()" % json.dumps(json.dumps(data)))
    spin(150); return r
def td(i, action, kind="issue", title=None):
    return {"id": "gid://gitlab/Todo/%d" % i, "action": action, "kind": kind, "iid": i, "title": title or "Item %d" % i,
            "url": "https://gitlab.com/%s/-/%s/%d" % (P, "issues" if kind == "issue" else "merge_requests", i), "project": P, "author": {"username": "alice", "name": "Alice"}, "at": "2026-11-03T18:00:00Z"}
def asg(i, labels): return {"iid": i, "title": "Card %d" % i, "url": "https://gitlab.com/%s/-/issues/%d" % (P, i), "project": P, "labels": labels, "updatedAt": "2026-11-03T17:00:00Z", "notes": 2}
def tans(todos, assigned, scope="all"): return {"state": "ready", "message": "", "scope": scope, "updatedAt": "2026-11-03T19:00:00Z", "todos": todos, "assigned": assigned}
def stale(): ev("a", "(function(){ var f = root.feed, a = {}; for (var k in f.todoAnswers) a[k] = Object.assign({}, f.todoAnswers[k], { startedAt: 0 }); f.todoAnswers = a })()")
H = lambda: ev("a", "root.feed.helperPath()")
spin(150)
ok("T0 nothing asked at start", todos_running() == [] and ev("a", "Object.keys(root.feed.todoAnswers).length") == 0, running())
ev("a", "root.opened = true"); spin(150)
ok("T1 opening the popup doesn't ask for to-dos", todos_running() == [], running())
while running(): answer(A); spin(40)
ev("a", "root.feed.requestTodos('all', false)"); ev("b", "root.feed.requestTodos('all', false)"); spin(40)
ok("T2 asked from both screens: one todos query, no project", todos_running() == [[H(), "todos", "--hostname", "gitlab.com"]], running())
ok("T3 ... and todoRunning names its scope", ev("a", "root.feed.todoRunning") == "all")
answer_todos(tans([td(31, "mentioned"), td(7, "build_failed", "mr")], [asg(3, ["in progress"])]))
ok("T4 the answer kept for the scope, checked", ev("a", "root.feed.todoAnswers.all.data.todos.length") == 2 and ev("a", "root.feed.todoAnswers.all.data.assigned[0].iid") == 3 and ev("a", "root.feed.todoRunning") == "", ev("a", "JSON.stringify(root.feed.todoAnswers)"))
ev("a", "root.feed.requestTodos('all', false)"); spin(40)
ok("T5 asked again within a minute: reused, nothing runs", todos_running() == [], running())
ev("a", "root.feed.requestTodos('all', true)"); spin(40)
ok("T6 forced (r): runs again", len(todos_running()) == 1, running())
ev("a", "root.feed.requestTodos('all', true)"); spin(40)
ok("T6b r again while it loads: not queued twice", len(todos_running()) == 1 and ev("a", "root.feed.todoPending") is None, ev("a", "JSON.stringify(root.feed.todoPending)"))
ev("a", "root.feed.requestTodos(%s, false)" % json.dumps(P)); spin(40)
ok("T7 another scope while one loads: waits its turn", len(todos_running()) == 1 and ev("a", "root.feed.todoPending.scope") == P, running())
answer_todos(tans([], []))
ok("T8 ... then runs, with the project", todos_running() == [[H(), "todos", "--project", P, "--hostname", "gitlab.com"]], running())
answer_todos(tans([td(31, "mentioned")], [], P))
ok("T9 both scopes kept", sorted(ev("a", "Object.keys(root.feed.todoAnswers)")) == sorted(["all", P]) and ev("a", "root.feed.todoAnswers.all.data.todos.length") == 0)
stale(); ev("a", "root.feed.requestTodos('all', false)"); spin(40)
ok("T10 over a minute old: asked again", len(todos_running()) == 1, running())
ev("a", "root.feed.background()"); spin(40)
ok("T11 a background refresh doesn't ask for to-dos", len(todos_running()) == 1, running())
ev("a", "root.feed.forget()"); spin(40)
answer_todos(tans([td(1, "assigned")], []))
ok("T12 sign out (forget): answers gone, a late answer dropped", ev("a", "Object.keys(root.feed.todoAnswers).length") == 0 and ev("a", "root.feed.todoPending") is None, ev("a", "JSON.stringify(root.feed.todoAnswers)"))
ev("a", "root.feed.requestTodos('all', false)"); spin(40); answer_todos({"state": "logged-out", "message": "Sign in with glab."})
ok("T13 a logged-out answer kept as such", ev("a", "root.feed.todoAnswers.all.data.state") == "logged-out")
ev("a", "root.feed.requestTodos('all', true)"); spin(40); answer_todos("junk")
ok("T14 an unreadable answer: an error state, not raw text", ev("a", "root.feed.todoAnswers.all.data.state") == "error" and ev("a", "root.feed.todoAnswers.all.data.todos.length") == 0)
while running(): answer(A); spin(40)
loops = [w for w in warnings if "oop" in w]
ok("Z no binding-loop warnings", not loops, loops)
ok("Z no QML warnings", not warnings, warnings[:3])
print("passed", sum(results), "failed", len(results) - sum(results))
sys.stdout.flush(); os._exit(0 if all(results) else 1)
