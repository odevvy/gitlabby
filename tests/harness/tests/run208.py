# v0.1.108: the project picker says why it is empty. A filter that hides every
# project: "No projects match this filter." and a Clear filter action (mouse,
# or Enter on its outline) that empties the field and puts the cursor back.
# No projects at all: "No projects found for this account." Loading and errors
# keep their own row; the boards step is unchanged.
# Usage: run208.py <src>
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
P = "group/app"
BOARD = {"state": "ready", "project": P, "updatedAt": "2026-10-31T13:20:00Z", "message": "", "labelColors": {}, "boards": [{"id": 1, "name": "Dev"}], "board": {"id": 1, "name": "Dev"}, "fallback": False,
  "columns": [{"name": "Open", "kind": "open", "issues": []}, {"name": "Closed", "kind": "closed", "issues": []}]}
PROJECTS = {"state": "ready", "projects": [{"id": 1, "path": "group/app"}, {"id": 2, "path": "group/api"}]}
h = Harness(sys.argv[1], {"id": "odevvy.gitlabby", "settingsRevision": 2, "defaultProject": P, "defaultCollapsed": [], "favorites": [], "serverFavorites": {}})
h.ev("panel.availableCardHeight = 700; panel.availableCardWidth = 1460")
h.ev("root.opened = true"); h.spin(60); h.answer("board", BOARD); h.spin(150)
ev = h.ev
def named(n): return [it for it in h.walk() if it.objectName() == n and it.isVisible()]
def msg(): t = named("pickerEmptyText"); return t[0].property("text") if t else None
def clear(): return named("pickerClearFilter")

ev("root.openPicker()"); h.spin(60)
h.ok("L1 while loading: no empty message", msg() is None and named("pickerLoading"))
h.answer("projects", PROJECTS); h.spin(80)
h.ok("R1 projects listed: no empty message", msg() is None and len(ev("picker.rows")) == 2)
ev("picker.filterField.text = 'api'"); h.spin(40)
h.ok("R2 a filter that matches: no empty message", msg() is None and len(ev("picker.rows")) == 1)
ev("picker.filterField.text = 'nomatch'"); h.spin(40)
h.ok("F1 a filter that hides all: says so", msg() == "No projects match this filter.")
h.ok("F2 a Clear filter action in the accent", len(clear()) == 1 and clear()[0].property("color") == ev("root.accent"))
ev("root.kbFocus = null; keyCatcher.forceActiveFocus()"); h.spin(20)
h.ok("F2b the field has no cursor before", not ev("picker.filterField.activeFocus"))
h.click(clear()[0]); h.spin(60)
h.ok("F3 clicking it empties the filter, the projects come back, the cursor is in the field",
     ev("picker.filterField.text") == "" and len(ev("picker.rows")) == 2 and ev("picker.filterField.activeFocus") and msg() is None)
ev("picker.filterField.text = '  zz  '"); h.spin(40)
h.ok("F4 spaces around the filter count as a filter", msg() == "No projects match this filter.")
ev("keyCatcher.forceActiveFocus()"); h.spin(20)
for _ in range(30):
    QTest.keyClick(h.win, Qt.Key_Tab); h.spin(20)
    if clear() and ev("root.kbFocus") == clear()[0]: break
h.ok("K1 Tab reaches Clear filter, one outline", clear() and ev("root.kbFocus") == clear()[0] and len(named("focusRing")) == 1)
h.key(Qt.Key_Return); h.spin(60)
h.ok("K2 Enter clears it", ev("picker.filterField.text") == "" and len(ev("picker.rows")) == 2)

ev("root.back(); root.projects = []"); h.spin(40); ev("root.openPicker()"); h.spin(60)
h.answer("projects", {"state": "ready", "projects": []}); h.spin(80)
ev("picker.filterField.text = ''"); h.spin(40)
h.ok("U1 no projects at all: says so, no Clear filter", msg() == "No projects found for this account." and not clear())
ev("picker.filterField.text = '   '"); h.spin(40)
h.ok("U2 only spaces in the field is no filter", msg() == "No projects found for this account." and not clear())
ev("root.back(); root.projects = []"); h.spin(40); ev("root.openPicker()"); h.spin(60)
h.answer("projects", {"state": "error", "message": "GitLab did not answer."}); h.spin(80)
h.ok("E1 an error keeps its own row, no empty message", msg() is None and named("pickerLoading"))
ev("root.back(); root.projects = []"); h.spin(40); ev("root.openPicker()"); h.spin(60)
h.answer("projects", PROJECTS); h.spin(60)
ev("root.pickProject('group/app')"); h.spin(50)
h.answer("boards", {"state": "ready", "boards": []}); h.spin(80)
ev("root.pickerBoards = []"); h.spin(40)
h.ok("B1 the boards step shows no project message", msg() is None and ev("picker.rows").__len__() == 0)
sys.exit(h.finish())
