# v0.1.57: keyed cards. Columns and cards come from keyed ListModels
# (Logic.keyOps), so a refresh that changes one card updates that card in
# place: the other cards, their avatars and the columns are not rebuilt.
# Usage: run157.py <src>
import sys, os, json, copy, time; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
src = sys.argv[1]
P = "firelink21/phrase41"
def who(n): return {"username": n, "name": n.title(), "avatar": ""}
def iss(iid, labels, notes=0): return {"iid": iid, "title": "Issue %d" % iid, "labels": labels, "url": "https://gitlab.com/%s/-/issues/%d" % (P, iid), "createdAt": "2026-10-31T09:00:00Z", "notes": notes, "assignees": [who("ann"), who("bob")]}
def col_(n, i, iids): return {"name": n, "kind": "label", "listId": i, "color": "#5b9bd5", "issues": [iss(x, [n]) for x in iids]}
BASE = {"state": "ready", "project": P, "updatedAt": "2026-10-31T13:20:00Z", "message": "", "labelColors": {}, "boards": [{"id": 1, "name": "Development"}], "board": {"id": 1, "name": "Development"}, "fallback": False,
        "columns": [{"name": "Open", "kind": "open", "issues": []}, col_("todo", 1, [11, 12, 13, 14]), col_("doing", 2, [21, 22]), col_("review", 3, [31]), {"name": "Closed", "kind": "closed", "issues": []}]}
h = Harness(src, {"id": "odevvy.gitlab-board", "settingsRevision": 2, "defaultProject": P, "defaultCollapsed": ["open", "closed"]})
h.ev("panel.availableCardHeight = 1200; panel.availableCardWidth = 2400")
h.ev("root.opened = true"); h.spin(60); h.answer("board", BASE); h.spin(300)
def md(it): v = it.property("modelData"); return v.toVariant() if hasattr(v, "toVariant") else v
def cards(): return [it for it in h.walk() if it.property("picked") is not None and it.property("keyed") is not None and it.isVisible()]
def columns(): return [it.parentItem().parentItem() for it in h.walk() if it.objectName() == "stripCount"]
def avatars(): return [it for it in h.walk() if it.metaObject().className().startswith("Avatar")]
def mark():
    for it in cards() + columns() + avatars(): it.setProperty("seen157", True)
new = lambda its: [it for it in its if not it.property("seen157")]
def layout():  # column name -> card iids, in screen order
    out = {}
    for c in columns():
        name = md(c)["name"]; its = [it for it in cards() if c.isAncestorOf(it)]
        out[name] = [md(it)["iid"] for it in sorted(its, key=lambda it: it.mapToScene(QPointF(0, 0)).y())]
    return out
def refresh(data):
    h.ev("root.refresh(false)"); h.spin(30); t = time.perf_counter(); h.answer("board", data); h.spin(150)
ok = h.ok
ok("K0 the board is on screen", layout().get("todo") == [11, 12, 13, 14] and len(cards()) == 7, layout())
# --- one card changes ---------------------------------------------------------------
from PySide6.QtCore import SIGNAL
touched = set()
for it in cards():  # a card whose data object is replaced re-runs every binding on it
    QObject.connect(it, SIGNAL("modelDataChanged()"), lambda it=it: touched.add(md(it)["iid"]))
mark(); d = copy.deepcopy(BASE); d["columns"][1]["issues"][1]["notes"] = 5; refresh(d)
c12 = [it for it in cards() if md(it)["iid"] == 12]
ok("K1 one card's comment count changes: no card rebuilt", not new(cards()) and len(cards()) == 7, len(new(cards())))
ok("K2 and no column rebuilt", not new(columns()))
ok("K3 the other cards' avatars stay (the changed card's may follow it)", len(new(avatars())) <= 2, len(new(avatars())))
ok("K3b only the changed card gets new data; the others keep theirs (no binding re-runs)", touched == {12}, sorted(touched))
ok("K4 the changed card shows the new count", c12 and md(c12[0])["notes"] == 5)
# --- one card moves ---------------------------------------------------------------------
mark(); d2 = copy.deepcopy(d); moved = d2["columns"][1]["issues"].pop(2); moved["labels"] = ["doing"]; d2["columns"][2]["issues"].insert(0, moved); refresh(d2)
ok("K5 a card moves to another column: the board shows it there", layout().get("todo") == [11, 12, 14] and layout().get("doing") == [13, 21, 22], layout())
ok("K6 only the moved card is new", [md(it)["iid"] for it in new(cards())] == [13], [md(it)["iid"] for it in new(cards())])
# --- order change, add, remove ----------------------------------------------------------
mark(); d3 = copy.deepcopy(d2); t = d3["columns"][1]["issues"]; t.reverse(); t.append(iss(15, ["todo"])); d3["columns"][2]["issues"] = d3["columns"][2]["issues"][:2]; refresh(d3)
ok("K7 reordered, added and removed cards end in the new order", layout().get("todo") == [14, 12, 11, 15] and layout().get("doing") == [13, 21], layout())
ok("K8 only the added card is new", [md(it)["iid"] for it in new(cards())] == [15], [md(it)["iid"] for it in new(cards())])
# --- a column appears ------------------------------------------------------------------------
mark(); d4 = copy.deepcopy(d3); d4["columns"].insert(3, col_("qa", 4, [41])); refresh(d4)
names = [md(c)["name"] for c in sorted(columns(), key=lambda c: c.mapToScene(QPointF(0, 0)).x())]
ok("K9 a new column shows in its place; the others are kept", names == ["Open", "todo", "doing", "qa", "review", "Closed"] and [md(c)["name"] for c in new(columns())] == ["qa"], names)
ok("K10 no card of the other columns is rebuilt", [md(it)["iid"] for it in new(cards())] == [41])
# --- the keyboard cursor follows the keyed columns ------------------------------------------------
h.ev("root.cursor = { col: 3, row: 0, iid: 41 }"); h.spin(30)
ok("K11 the keyboard cursor marks the card in the new column", [md(it)["iid"] for it in cards() if it.property("keyed")] == [41])
# --- a whole new board ----------------------------------------------------------------------------
refresh(BASE)
ok("K12 back to the first board: same cards as at the start", layout().get("todo") == [11, 12, 13, 14] and layout().get("doing") == [21, 22] and "qa" not in layout(), layout())
h.finish()
fails = [n for n, c in h.results if not c]
print("passed %d failed %d" % (len(h.results) - len(fails), len(fails)))
sys.exit(1 if fails else 0)
