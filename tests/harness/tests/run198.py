# v0.1.98: inset rounded jump/default hover, × keeps row hovered, more top gap,
# dismiss-on-outside-click for header menus.
# Usage: run198.py <src>
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from fixtures import BOARD
h = Harness(sys.argv[1], {
    "id": "odevvy.gitlabby", "settingsRevision": 2,
    "defaultProject": "group/app", "defaultBoardId": "7", "defaultBoardName": "Development",
    "defaultCollapsed": [], "boardStates": {}, "refreshIntervalSec": 60,
    "favorites": [{"project": "group/wf", "id": "", "name": "Workflow labels"}],
    "serverFavorites": {}
})
h.ev("panel.availableCardHeight = 520; panel.availableCardWidth = 1460")
h.ev("root.opened = true"); h.spin(60); h.answer("board", BOARD); h.spin(200)
hev = lambda e: h.ev(e)

def menu(name):
    return next((it for it in h.walk() if it.objectName() == name and it.isVisible()), None)

def named(name, visible_only=True):
    return [it for it in h.walk() if it.objectName() == name and (not visible_only or it.isVisible())]

# --- gap + inset hover ---------------------------------------------------------
h.ev("root.openJumpMenu()"); h.spin(60)
jm = menu("jumpMenu")
h.ok("G0 jump open", jm is not None and hev("root.headerMenu") == "jump")
# topMargin via anchors - read from QML
tm = hev("(function(){ var m=null; function w(o){ if(!o)return; if(o.objectName==='jumpMenu') m=o; var ch=o.children||[]; for(var i=0;i<ch.length;i++) w(ch[i]) } w(header); return m ? m.anchors.topMargin : -1 })()")
h.ok("G1 jump topMargin > old 4px gap", tm >= 10, tm)
h.ok("G2 jump menu clips to radius", hev("(function(){ var m=null; function w(o){ if(!o)return; if(o.objectName==='jumpMenu') m=o; var ch=o.children||[]; for(var i=0;i<ch.length;i++) w(ch[i]) } w(header); return m ? m.clip : false })()") is True)

hovers = named("jumpHover")
h.ok("G3 inset hover fills exist", len(hovers) >= 2, len(hovers))
# Inset: hover width < menu width; has radius; no accent border width when idle
hw = hovers[0].width()
mw = jm.width()
lm = hev("(function(){ var m=null; function w(o){ if(!o)return; if(o.objectName==='jumpHover'){ m=o; return } var ch=o.children||[]; for(var i=0;i<ch.length;i++) w(ch[i]) } w(header); return m ? m.anchors.leftMargin : -1 })()")
h.ok("G4 hover inset narrower than menu", hw < mw - 4 and lm >= 4, (hw, mw, lm))
h.ok("G5 hover has rounded corners", float(hovers[0].property("radius") or 0) >= 3, hovers[0].property("radius"))
# Hover fill is fill-only (no accent outline), unlike the old edge-to-edge row border.
has_border = hev("(function(){ var m=null; function w(o){ if(!o)return; if(o.objectName==='jumpHover'){ m=o; return } var ch=o.children||[]; for(var i=0;i<ch.length;i++) w(ch[i]) } w(header); return m ? m.border.width : -1 })()")
h.ok("G6 hover fill has no accent outline", has_border == 0, has_border)

# Default menu same top gap
h.ev("root.headerMenu = ''")
h.ev("root.switchTo('group/wf', '', 'Workflow labels')"); h.spin(40)
h.answer("board", dict(BOARD, project="group/wf", board={"id": "", "name": "Workflow labels"}, boards=[])); h.spin(80)
h.ev("root.openDefaultMenu()"); h.spin(40)
dtm = hev("(function(){ var m=null; function w(o){ if(!o)return; if(o.objectName==='defaultMenu') m=o; var ch=o.children||[]; for(var i=0;i<ch.length;i++) w(ch[i]) } w(header); return m ? m.anchors.topMargin : -1 })()")
h.ok("G7 defaultMenu topMargin matches larger gap", dtm >= 10, dtm)
h.ok("G8 default inset hover present", len(named("defHover")) >= 1)

# --- × keeps row hovered -------------------------------------------------------
h.ev("root.headerMenu = ''")
h.ev("root.switchTo('group/app', '7', 'Development')"); h.spin(40); h.answer("board", BOARD); h.spin(80)
h.ev("root.openJumpMenu()"); h.spin(60)
xs = named("jumpUnfavorite")
h.ok("X0 × visible on non-default", len(xs) >= 1, len(xs))
# Find parent rowHovered via QML
# Move pointer over ×
QTest.mouseMove(h.win, h.scene(xs[0])); h.spin(80)
hovered = hev("(function(){ var rows=[]; function w(o){ if(!o)return; if(o.rowHovered !== undefined && o.jumpRemove && o.jumpRemove.visible) rows.push(!!o.rowHovered); var ch=o.children||[]; for(var i=0;i<ch.length;i++) w(ch[i]) } w(header); return rows })()")
# Simpler: ask first non-default row
rh = hev("(function(){ var hit=false; function w(o){ if(!o)return; if(o.objectName==='jumpUnfavorite' && o.visible){ var p=o.parent; if(p && p.rowHovered) hit=true } var ch=o.children||[]; for(var i=0;i<ch.length;i++) w(ch[i]) } w(header); return hit })()")
h.ok("X1 row hovered while pointer over ×", rh is True, rh)

before = hev("root.project")
n = hev("root.jumpBoards.length")
h.click(xs[0]); h.spin(60)
h.ok("X2 × unfavorites without jump", hev("root.project") == before and hev("root.headerMenu") == "jump")
h.ok("X3 favorite removed", hev("root.jumpBoards.length") == n - 1, (n, hev("root.jumpBoards.length")))

# --- dismiss outside -----------------------------------------------------------
# Restore a favorite so jump list is non-empty, reopen (force closed first:
# openJumpMenu toggles, and the menu is still open after the × clicks above).
h.ev("root.persist({ favorites: [{ project: 'group/wf', id: '', name: 'Workflow labels' }] })"); h.spin(30)
h.ev("root.headerMenu = ''"); h.spin(20)
h.ev("root.openJumpMenu()"); h.spin(40)
dismiss = menu("headerMenuDismiss")
# MouseArea may not report isVisible the same way — also accept via QML
vis = hev("headerMenuDismiss.visible")
h.ok("D0 dismiss layer visible while menu open", (dismiss is not None or vis is True) and hev("header.z") == 40 and vis is True, (dismiss is not None, vis, hev("header.z")))
if dismiss is None:
    # resolve for click via walk without visibility filter
    dismiss = next((it for it in h.walk() if it.objectName() == "headerMenuDismiss"), None)
# Click dismiss (outside menu) — should clear menu, not jump
proj = hev("root.project")
h.click(dismiss); h.spin(40)
h.ok("D1 outside click clears headerMenu", hev("root.headerMenu") == "" and menu("jumpMenu") is None)
h.ok("D2 outside click did not switch board", hev("root.project") == proj)
h.ok("D3 dismiss layer hidden when closed", hev("headerMenuDismiss.visible") is not True)

# Menu / title / Default not eaten: reopen via title, click stays meaningful
h.click(h.ev("header.chevron")); h.spin(60)
h.ok("D4 title still opens jump (not eaten)", hev("root.headerMenu") == "jump")
# Click inside jump menu on Browse — should open picker (not only dismiss)
# Find browse text and click
browse = next((it for it in h.walk() if it.property("text") == "Browse all projects…" and it.isVisible()), None)
h.ok("D5 browse row present", browse is not None)
h.click(browse); h.spin(60)
h.ok("D6 browse still opens picker", hev("root.view") == "picker" and hev("root.headerMenu") == "")
h.key(Qt.Key_Escape); h.spin(40)

# Default mark still toggles default menu when !onDefault
h.ev("root.switchTo('group/wf', '', 'Workflow labels')"); h.spin(40)
h.answer("board", dict(BOARD, project="group/wf")); h.spin(80)
h.click(h.ev("header.defaultMark")); h.spin(40)
h.ok("D7 Default mark still opens default menu", hev("root.headerMenu") == "default" and menu("defaultMenu") is not None)
dismiss2 = next((it for it in h.walk() if it.objectName() == "headerMenuDismiss"), None)
h.click(dismiss2); h.spin(40)
h.ok("D8 dismiss closes default menu too", hev("root.headerMenu") == "")

# Opaque + z retained
h.ev("root.openJumpMenu()"); h.spin(30)
a = hev("(function(){ var m=null; function w(o){ if(!o)return; if(o.objectName==='jumpMenu') m=o; var ch=o.children||[]; for(var i=0;i<ch.length;i++) w(ch[i]) } w(header); return m ? m.color.a : -1 })()")
h.ok("Z opaque fill retained", a == 1 and hev("header.z") == 40, (a, hev("header.z")))

sys.exit(h.finish())
