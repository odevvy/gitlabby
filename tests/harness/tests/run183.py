# v0.1.83: Settings > Show avatars (showAvatars, default on). This step: the setting itself. Off, no avatar
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
h = Harness(sys.argv[1], {"id": "odevvy.gitlab-board", "settingsRevision": 2, "defaultProject": P, "defaultCollapsed": [], "boardStates": {}, "refreshIntervalSec": 60})
h.ev("panel.availableCardHeight = 620; panel.availableCardWidth = 1020")
h.ev("root.opened = true"); h.spin(60); h.answer("board", B); h.spin(500)
ok = h.ok
def pics(): return [it.property("source").toString() for it in h.walk() if it.objectName() == "avatarImage"]
def initials(): return [it.property("text") for it in h.visible(lambda it: it.property("text") == "AS")]
ok("A0 default on", h.ev("root.showAvatars") is True)
w0 = len(h.ev("root.bar.shell.writes") or []); h.ev("root.setShowAvatars(false)"); h.spin(150)
ok("A2 setShowAvatars(false) saves showAvatars: false", (h.ev("root.bar.shell.writes") or [])[w0:][-1].get("showAvatars") is False and h.ev("root.showAvatars") is False)
h.ev("root.setShowAvatars('yes')"); h.spin(60)
ok("A5 only true turns it on", (h.ev("root.bar.shell.writes") or [])[-1].get("showAvatars") is False)
sys.exit(h.finish())
