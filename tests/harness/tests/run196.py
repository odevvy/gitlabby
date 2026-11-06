# v0.1.96: jump/default menus opaque and above BotsRow/board (header z while open).
# Usage: run196.py <src>
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from fixtures import BOARD
h = Harness(sys.argv[1], {
    "id": "odevvy.gitlabby", "settingsRevision": 2,
    "defaultProject": "group/app", "defaultBoardId": "7", "defaultBoardName": "Development",
    "defaultCollapsed": [], "boardStates": {}, "refreshIntervalSec": 60,
    "favorites": [{"project": "group/other", "id": "9", "name": "Ops"}], "serverFavorites": {}
})
h.ev("panel.availableCardHeight = 520; panel.availableCardWidth = 1460")
h.ev("root.opened = true"); h.spin(60); h.answer("board", BOARD); h.spin(200)
hev = lambda e: h.ev(e)

def menu(name):
    return next((it for it in h.walk() if it.objectName() == name and it.isVisible()), None)

h.ok("Z0 header z is 0 with menus closed", hev("header.z") == 0 and hev("root.headerMenu") == "")

h.ev("root.openJumpMenu()"); h.spin(60)
h.ok("Z1 jump menu open raises BoardHeader", hev("root.headerMenu") == "jump" and hev("header.z") == 40, (hev("root.headerMenu"), hev("header.z")))
jm = menu("jumpMenu")
h.ok("Z2 jumpMenu visible", jm is not None)
# Opaque fill: alpha channel is 1
a = hev("(function(){ var m=null; function w(o){ if(!o) return; if(o.objectName==='jumpMenu') m=o; var ch=o.children||[]; for(var i=0;i<ch.length;i++) w(ch[i]) } w(header); return m ? m.color.a : -1 })()")
h.ok("Z3 jumpMenu fill is opaque (a=1)", a == 1, a)

h.ev("root.headerMenu = ''"); h.spin(40)
h.ok("Z4 closing jump clears elevated z", hev("header.z") == 0)

# Default menu (need !onDefault)
h.ev("root.switchTo('group/other', '9', 'Ops')"); h.spin(60)
h.answer("board", dict(BOARD, project="group/other", board={"id": 9, "name": "Ops"}, boards=[{"id": 9, "name": "Ops"}]))
h.spin(120)
h.ok("Z5 off default", hev("root.onDefault") is False)
h.ev("root.openDefaultMenu()"); h.spin(40)
h.ok("Z6 default menu raises BoardHeader", hev("root.headerMenu") == "default" and hev("header.z") == 40)
da = hev("(function(){ var m=null; function w(o){ if(!o) return; if(o.objectName==='defaultMenu') m=o; var ch=o.children||[]; for(var i=0;i<ch.length;i++) w(ch[i]) } w(header); return m ? m.color.a : -1 })()")
h.ok("Z7 defaultMenu fill is opaque (a=1)", da == 1, da)
h.ok("Z8 defaultMenu visible", menu("defaultMenu") is not None)

h.ev("root.headerMenu = ''"); h.spin(30)
h.ok("Z9 menus closed: z back to 0", hev("header.z") == 0)

sys.exit(h.finish())
