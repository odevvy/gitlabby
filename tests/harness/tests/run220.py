# R2-01: signing out on one screen clears every screen. Two screens share one
# BoardService (two.py); the other one drops its cards, projects, account,
# remembered issues and late answers, and shows the sign-in panel.
# Usage: run220.py <src>
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import two; two.start({"showAvatars": False, "defaultCollapsed": []}, "ogb-h220-"); from two import *
for k in ("a", "b"): ev(k, "root.opened = true; root.refresh()")
spin(80); answer(A)
titles = "root.columns.reduce(function(a, c){ return a.concat(c.issues.map(function(r){ return r.title })) }, [])"
ok("S0 both screens show the private board", ev("a", "root.boardState") == "ready" and len(ev("b", titles)) == 4)
ev("a", "root.signOut()"); answer_proc("a", "logout", {"state": "error", "message": "glab could not sign out."})
ok("S9 a sign-out that fails leaves the other screen as it was", ev("b", "root.boardState") == "ready" and len(ev("b", titles)) == 4 and ev("a", "root.accountError") == "glab could not sign out.")
ev("b", "root.account = 'me'; root.projects = [{ path: 'group/app' }]; root.pickerBoards = [{ id: 7 }]")
ev("b", "issueView.remember('group/app#1', { issue: { title: 'Private' } })")
ev("b", "root.openIssue(root.columns[1].issues[0])"); spin(30)
ev("b", "issueView.notes = [{ body: 'Private comment' }]; issueView.box.text = 'Private draft'; issueView.allLabels = [{ name: 'secret' }]; issueView.labelsFor = root.projectKey")
session_b = ev("b", "root.session")
ev("a", "root.signOut()"); answer_proc("a", "logout", {"state": "logged-out", "message": "Signed out."})
for k, name in (("a", "the screen that signed out"), ("b", "the other screen")):
    ok("S1 %s shows the sign-in panel" % name, ev(k, "root.boardState") == "logged-out" and ev(k, "root.view") == "board", (ev(k, "root.boardState"), ev(k, "root.view")))
    ok("S2 %s keeps no card" % name, ev(k, "root.columns.length") == 0 and ev(k, titles) == [])
    ok("S3 %s says why" % name, ev(k, "root.message") == "Signed out.")
ok("S4 the other screen forgets account, projects and boards", ev("b", "root.account") == "" and ev("b", "root.projects.length") == 0 and ev("b", "root.pickerBoards.length") == 0)
ok("S5 the other screen forgets remembered issues", ev("b", "Object.keys(issueView.recent).length") == 0 and ev("b", "issueView.recentOrder.length") == 0)
ok("S10 the other screen forgets the open issue, its thread, draft and labels", ev("b", "issueView.issue.iid") is None and ev("b", "issueView.notes.length") == 0 and ev("b", "issueView.box.text") == "" and ev("b", "issueView.allLabels.length") == 0 and ev("b", "issueView.labelsFor") == "")
ok("S6 the other screen drops answers still on their way", ev("b", "root.session") == session_b + 1)
ev("b", "root.opened = false"); ev("b", "root.opened = true"); spin(80)
ok("S7 reopening the other screen shows no private card while it refreshes", ev("b", "root.columns.length") == 0 and ev("b", titles) == [])
ok("S8 the sign-out runs once", ev("a", "root.signingOut") is False and ev("b", "root.signingOut") is False)
ok("Z no QML warnings", not warnings, warnings[:3])
print("passed", sum(results), "failed", len(results) - sum(results))
sys.stdout.flush(); os._exit(0 if all(results) else 1)
