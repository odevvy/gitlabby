# v0.1.97: roomier two-line jump rows with × to unfavorite; widthAnim on board switch.
# Usage: run197.py <src>
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from fixtures import BOARD
h = Harness(sys.argv[1], {
    "id": "odevvy.gitlabby", "settingsRevision": 2,
    "defaultProject": "group/app", "defaultBoardId": "7", "defaultBoardName": "Development",
    "defaultCollapsed": [], "boardStates": {}, "refreshIntervalSec": 60,
    "favorites": [
        {"project": "group/wf", "id": "", "name": "Workflow labels"},
        {"project": "group/other", "id": "9", "name": "Ops"},
    ],
    "serverFavorites": {}
})
h.ev("panel.availableCardHeight = 520; panel.availableCardWidth = 1460")
h.ev("root.opened = true"); h.spin(60); h.answer("board", BOARD); h.spin(200)
hev = lambda e: h.ev(e)

def menu(name):
    return next((it for it in h.walk() if it.objectName() == name and it.isVisible()), None)

def named(name, visible_only=True):
    out = []
    for it in h.walk():
        if it.objectName() == name and (not visible_only or it.isVisible()):
            out.append(it)
    return out

# --- two-line jump rows --------------------------------------------------------
h.ev("root.openJumpMenu()"); h.spin(60)
h.ok("J0 jump menu open (opaque + raised header still)", hev("root.headerMenu") == "jump" and hev("header.z") == 40 and menu("jumpMenu") is not None)
# Walk order is not model order — read labels via QML in jumpBoards order.
names = hev("(function(){ var j=root.jumpBoards, o=[]; for (var i=0;i<j.length;i++) o.push(Logic.boardLabel(j[i].name, j[i].id)); return o })()")
projects = hev("(function(){ var j=root.jumpBoards, o=[]; for (var i=0;i<j.length;i++) o.push(String(j[i].project || '')); return o })()")
# Also confirm the visible two-line texts exist and match the set
ui_names = sorted(str(it.property("text")) for it in named("jumpBoardName"))
ui_projects = sorted(str(it.property("text")) for it in named("jumpProject"))
h.ok("J1 board names are two-line first lines (not project / board)",
     names == ["Development", "Workflow labels", "Ops"] and ui_names == sorted(names), (names, ui_names))
h.ok("J2 project paths on second line",
     projects == ["group/app", "group/wf", "group/other"] and ui_projects == sorted(projects), (projects, ui_projects))
h.ok("J3 no single-line project / board label in jump board names",
     all(" / " not in n for n in names) and all(" / " not in n for n in ui_names), names)
# Row height roomier
row_h = hev("(function(){ var m=null; function w(o){ if(!o)return; if(o.objectName==='jumpMenu') m=o; var ch=o.children||[]; for(var i=0;i<ch.length;i++) w(ch[i]) } w(header); if(!m) return 0; var col=m.children[0]; return col && col.children[0] ? col.children[0].height : 0 })()")
h.ok("J4 jump rows taller than old 28px", row_h >= 48, row_h)

# Default: badge, no ×
badges = named("jumpDefaultBadge")
xs = named("jumpUnfavorite")
h.ok("J5 Default badge only on default row", len(badges) == 1 and str(badges[0].property("text")) == "Default", len(badges))
h.ok("J6 × only on non-default favorites", len(xs) == 2, len(xs))

# × unfavorites without jumping; menu stays open
before_proj = hev("root.project")
before_len = hev("root.jumpBoards.length")
n_writes = len(hev("root.bar.shell.writes") or [])
h.click(xs[0]); h.spin(80)
h.ok("J7 × does not jump", hev("root.project") == before_proj and hev("root.headerMenu") == "jump", (hev("root.project"), hev("root.headerMenu")))
h.ok("J8 × removes a favorite row", hev("root.jumpBoards.length") == before_len - 1, (before_len, hev("root.jumpBoards.length")))
h.ok("J9 unfavorite persisted", len(hev("root.bar.shell.writes") or []) > n_writes)
# Default still listed, still no × on it
h.ok("J10 default still in list after unfavorite", hev("root.jumpBoards[0].isDefault") is True)
h.ok("J11 default still has no ×", len(named("jumpUnfavorite")) == 1, len(named("jumpUnfavorite")))

# Row click still jumps (use remaining non-default)
h.ev("root.jumpTo(root.jumpBoards[1])"); h.spin(60)
h.answer("board", dict(BOARD, project=hev("root.project"), board={"id": hev("root.boardId") or 0, "name": hev("root.boardName")}, boards=[]))
h.spin(100)
h.ok("J12 jumpTo switches board and closes menu", hev("root.headerMenu") == "" and hev("root.project") != "group/app")

# --- widthAnim -----------------------------------------------------------------
# Reset onto a known board, then switch — widthAnim should pulse true then clear.
h.ev("root.headerMenu = ''")
h.ev("root.switchTo('group/app', '7', 'Development')"); h.spin(30)
# Immediately after switchTo from a non-empty project, widthAnim is true
# (timer clears at 200ms). Call again and sample before the timer fires.
h.ev("root.widthAnim = false")  # clear
h.ev("root.switchTo('group/other', '9', 'Ops')")
wa = hev("root.widthAnim")
beh = hev("boardWidthBeh.enabled")
h.ok("W1 switchTo sets widthAnim", wa is True, wa)
h.ok("W2 Behavior enabled while widthAnim", beh is True, beh)
h.ok("W3 widthAnim does not set folding/held via fold", hev("root.folding") is False)
h.spin(250)
h.ok("W4 widthAnim clears after timer", hev("root.widthAnim") is False and hev("boardWidthBeh.enabled") is False)

# Fold still enables Behavior
h.ev("root.startFold()")
h.ok("W5 folding enables Behavior", hev("root.folding") is True and hev("boardWidthBeh.enabled") is True)
h.spin(250)
h.ok("W6 folding clears; Behavior off", hev("root.folding") is False and hev("boardWidthBeh.enabled") is False)

# First board from empty project: no widthAnim
h.ev("root.project = ''"); h.ev("root.widthAnim = false")
h.ev("root.switchTo('group/app', '7', 'Development')")
h.ok("W7 first pick from empty project does not widthAnim", hev("root.widthAnim") is False)

# Opaque fill still (0.1.96)
h.ev("root.openJumpMenu()"); h.spin(40)
a = hev("(function(){ var m=null; function w(o){ if(!o)return; if(o.objectName==='jumpMenu') m=o; var ch=o.children||[]; for(var i=0;i<ch.length;i++) w(ch[i]) } w(header); return m ? m.color.a : -1 })()")
h.ok("Z opaque jump fill retained", a == 1, a)

sys.exit(h.finish())
