# v0.1.83: Settings > Show avatars (showAvatars, default on). Off, no avatar
# picture is requested (every Image source is empty) and the initials circle
# stays; on, the picture URL is asked for as before. Usage: run183.py <src>
import sys, os, copy; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from fixtures import BOARD
from PySide6.QtGui import QImage, QColor
import tempfile, atexit, shutil
P = "group/app"
pic_dir = tempfile.mkdtemp(prefix="ogb-h183-"); atexit.register(shutil.rmtree, pic_dir, True)
im = QImage(8, 8, QImage.Format_ARGB32); im.fill(QColor("#3b6ea8")); im.save(pic_dir + "/a.png")
PIC = "file://" + pic_dir + "/a.png"  # a local picture: the test makes no network request
B = copy.deepcopy(BOARD)
first = next(i for c in B["columns"] for i in c["issues"])
first["assignees"] = [{"username": "alice", "name": "Alice Smith", "avatar": PIC}]
second = [i for c in B["columns"] for i in c["issues"]][1]
second["assignees"] = [{"username": "alice", "name": "Alice Smith", "avatar": ""}, {"username": "bob", "name": "Bob", "avatar": ""}]
h = Harness(sys.argv[1], {"id": "odevvy.gitlabby", "settingsRevision": 2, "defaultProject": P, "defaultCollapsed": [], "boardStates": {}, "refreshIntervalSec": 60})
h.ev("panel.availableCardHeight = 620; panel.availableCardWidth = 1020")
h.ev("root.opened = true"); h.spin(60); h.answer("board", B); h.spin(500)
ok = h.ok
def pics(): return [it.property("source").toString() for it in h.walk() if it.objectName() == "avatarImage"]
def initials(): return [it.property("text") for it in h.visible(lambda it: it.property("text") == "AS")]
ok("A1 default on: the picture is asked for, its initials go once it loads (the other alice has no picture)", h.ev("root.showAvatars") is True and PIC in pics() and h.until(lambda: len(initials()) == 1), (pics(), initials()))
w0 = len(h.ev("root.bar.shell.writes") or []); h.ev("root.setShowAvatars(false)"); h.spin(150)
ok("A2 setShowAvatars(false) saves showAvatars: false", (h.ev("root.bar.shell.writes") or [])[w0:][-1].get("showAvatars") is False)
ok("A3 off: no picture is requested anywhere", h.ev("root.showAvatars") is False and pics() != [] and all(p == "" for p in pics()), pics())
ok("A4 off: the initials circle shows instead", initials() != [], initials())
h.ev("root.setShowAvatars('yes')"); h.spin(60)
ok("A5 only true turns it on", (h.ev("root.bar.shell.writes") or [])[-1].get("showAvatars") is False)
# Initials circle colour: the same username always gets the same colour (two
# cards with alice), from the theme accent, and another name can differ.
def circles():
    out = []
    for it in h.walk():
        if it.metaObject().className().startswith("Avatar"):
            p = it.property("person"); p = p.toVariant() if hasattr(p, "toVariant") else p
            out.append(((p or {}).get("username"), it.property("color").name()))
    return out
cs = circles(); al = [c for u, c in cs if u == "alice"]; ot = [c for u, c in cs if u == "bob"]
ok("C1 the initials circle is tinted (not the old flat faint grey)", cs and all(c != QColor(h.ev("root.faint.toString()")).name() for _, c in cs), cs)
ok("C2 alice has the same colour on both cards", len(al) == 2 and al[0] == al[1], cs)
ok("C3 another name gets its own colour", ot and ot[0] != al[0], cs)
h.ev("root.setShowAvatars(true)"); h.spin(150)
ok("A6 on again: the picture again", PIC in pics(), pics())
# Settings: the box under "Keep the bar icon unlit", its note, then Start collapsed
h.ev("root.showView('settings')"); h.spin(300)
by = lambda n: next((it for it in h.walk() if it.objectName() == n and it.isVisible()), None)
row, check, note, unlit = by("avatarsRow"), by("avatarsCheck"), by("avatarsNote"), by("unlitNote")
y = lambda it: it.mapToScene(QPointF(0, 0)).y()
ok("S1 Show avatars sits under the bar-icon note, its note under it", row and note and unlit and y(unlit) < y(row) and y(row) + row.height() <= y(note))
ok("S2 the note says where pictures come from", note and "Gravatar" in note.property("text") and "IP" in note.property("text"), note and note.property("text"))
ok("S3 ticked while on", check and check.property("on") is True)
h.click(check); h.spin(150)
ok("S4 a click turns it off and saves it", h.ev("root.showAvatars") is False and (h.ev("root.bar.shell.writes") or [])[-1].get("showAvatars") is False and check.property("on") is False)
h.click(check); h.spin(150)
ok("S5 a second click turns it back on", h.ev("root.showAvatars") is True and (h.ev("root.bar.shell.writes") or [])[-1].get("showAvatars") is True)
sys.exit(h.finish())
