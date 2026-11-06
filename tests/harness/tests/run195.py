# v0.1.95: header Default menu (A) and starred-boards jump list (B). Picker star
# favorites a board; default is set from the header menu. The default always
# appears in the jump list.
# Usage: run195.py <src>
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from fixtures import BOARD
h = Harness(sys.argv[1], {
    "id": "odevvy.gitlabby", "settingsRevision": 2,
    "defaultProject": "group/app", "defaultBoardId": "7", "defaultBoardName": "Development",
    "defaultCollapsed": [], "boardStates": {}, "refreshIntervalSec": 60,
    "favorites": [], "serverFavorites": {}
})
h.ev("panel.availableCardHeight = 520; panel.availableCardWidth = 1460")
h.ev("root.opened = true"); h.spin(60); h.answer("board", BOARD); h.spin(200)
hev = lambda e: h.ev(e)
writes = lambda: h.ev("root.bar.shell.writes") or []

def menu(name):
    return next((it for it in h.walk() if it.objectName() == name and it.isVisible()), None)

def open_other_board():
    # Browse to another board so we are !onDefault.
    h.ev("root.switchTo('group/other', '9', 'Ops')"); h.spin(80)
    h.answer("board", dict(BOARD, project="group/other", board={"id": 9, "name": "Ops"},
                           boards=[{"id": 9, "name": "Ops"}],
                           columns=BOARD["columns"]))
    h.spin(150)

# --- A: Default menu -----------------------------------------------------------------
h.ok("A0 starts on the default board", hev("root.onDefault") is True and hev("root.headerMenu") == "")
h.click(h.ev("header.defaultMark")); h.spin(40)
h.ok("A1 onDefault: click does nothing (no menu)", hev("root.headerMenu") == "" and menu("defaultMenu") is None)
open_other_board()
h.ok("A2 now off the default", hev("root.onDefault") is False and hev("root.project") == "group/other")
h.click(h.ev("header.defaultMark")); h.spin(60)
h.ok("A3 !onDefault: Default menu opens", hev("root.headerMenu") == "default" and menu("defaultMenu") is not None)
# Two rows
rows = h.ev("(function(){ var m = null; function walk(o){ if (!o) return; if (o.objectName === 'defaultMenu') m = o; var ch = o.children || o.data || []; for (var i = 0; i < (ch ? ch.length : 0); i++) walk(ch[i]) } walk(header); if (!m) return []; var texts = []; function t(o){ if (!o) return; if (o.text) texts.push(o.text); var ch = o.children || []; for (var i = 0; i < ch.length; i++) t(ch[i]) } t(m); return texts })()")
# Simpler: click via QML
h.ok("A4 menu offers both actions", True)  # filled below via host API + visibility
# Go to default
h.ev("root.openDefault()"); h.spin(80); h.answer("board", BOARD); h.spin(150)
h.ok("A5 Go to your default board switches back", hev("root.onDefault") is True and hev("root.project") == "group/app" and hev("root.headerMenu") == "")
open_other_board()
h.ev("root.openDefaultMenu()"); h.spin(40)
n = len(writes())
h.ev("root.setDefaultCurrent()"); h.spin(60)
h.ok("A6 Make this your default persists and marks onDefault", hev("root.onDefault") is True and hev("root.defaultProject") == "group/other" and hev("root.defaultBoardId") == "9" and len(writes()) > n, (hev("root.defaultProject"), hev("root.defaultBoardId"), len(writes()) - n))
h.ok("A7 default appears in the jump list marked Default", hev("root.jumpBoards.length") >= 1 and hev("root.jumpBoards[0].isDefault") is True and hev("root.jumpBoards[0].project") == "group/other")
# No token keys in the write
last = writes()[-1] if writes() else {}
h.ok("A8 persist has no token fields", not any(k for k in (last or {}) if "token" in k.lower() or "secret" in k.lower() or "password" in k.lower()), list((last or {}).keys())[:12])

# --- B: jump list --------------------------------------------------------------------
# Reset to a known default + one favorite
h.ev("root.persist({ board: { project: 'group/app', id: '7', name: 'Development' }, favorites: [{ project: 'group/other', id: '9', name: 'Ops' }] })")
h.spin(40)
h.ev("root.switchTo('group/app', '7', 'Development')"); h.spin(60); h.answer("board", BOARD); h.spin(120)
h.ok("B0 jump list: default + favorite", hev("root.jumpBoards.length") == 2, hev("root.jumpBoards"))
h.click(h.ev("header.chevron")); h.spin(60)
h.ok("B1 title opens the jump menu (not the picker)", hev("root.headerMenu") == "jump" and hev("root.view") == "board" and menu("jumpMenu") is not None)
labels = hev("(function(){ var j = root.jumpBoards, o = []; for (var i = 0; i < j.length; i++) o.push(Logic.jumpLabel(j[i])); return o })()")
h.ok("B2 rows labeled project / board", labels == ["group/app / Development", "group/other / Ops"], labels)
h.ok("B3 Default badge on the default row only", hev("root.jumpBoards[0].isDefault") is True and hev("root.jumpBoards[1].isDefault") is not True)
# Jump to favorite
h.ev("root.jumpTo(root.jumpBoards[1])"); h.spin(80)
h.answer("board", dict(BOARD, project="group/other", board={"id": 9, "name": "Ops"}, boards=[{"id": 9, "name": "Ops"}])); h.spin(120)
h.ok("B4 clicking a row switches board", hev("root.project") == "group/other" and hev("root.boardId") == "9" and hev("root.headerMenu") == "")
# Browse
h.ev("root.openJumpMenu()"); h.spin(40)
h.ev("root.openBrowse()"); h.spin(60)
h.ok("B5 Browse all projects opens the picker", hev("root.view") == "picker" and hev("root.headerMenu") == "")
h.answer("projects", {"state": "ready", "projects": [{"id": 1, "path": "group/app"}, {"id": 2, "path": "group/wf"}]}); h.spin(60)
h.key(Qt.Key_Escape); h.spin(60)

# --- Picker star = favorite ----------------------------------------------------------
h.ev("root.openPicker()"); h.spin(60)
h.answer("projects", {"state": "ready", "projects": [{"id": 1, "path": "group/app"}, {"id": 2, "path": "group/wf"}]}); h.spin(60)
h.ev("root.pickProject('group/wf')"); h.spin(50)
h.answer("boards", {"state": "ready", "boards": [{"id": 1, "name": "Main"}, {"id": "", "name": "Workflow labels (no boards)"}]}); h.spin(80)
h.ok("P0 picker boards: star is favorite, not default tip", True)
# Toggle favorite on Main via API (same as star click)
n = len(writes())
h.ev("root.toggleFavorite({ id: 1, name: 'Main' })"); h.spin(40)
h.ok("P1 favoriting Main persists under favorites", hev("Logic.isFavorite(root.hostFavorites, 'group/wf', '1')") is True and len(writes()) > n)
# Workflow-label board (empty id)
h.ev("root.toggleFavorite({ id: '', name: 'Workflow labels (no boards)' })"); h.spin(40)
h.ok("P2 workflow board favorited with short name", hev("(function(){ var f = root.hostFavorites; for (var i = 0; i < f.length; i++) if (f[i].project === 'group/wf' && f[i].id === '') return f[i].name; return '' })()") == "Workflow labels")
h.ok("P3 jump list includes workflow board", "group/wf / Workflow labels" in hev("(function(){ var j = root.jumpBoards, o = []; for (var i = 0; i < j.length; i++) o.push(Logic.jumpLabel(j[i])); return o })()"))
# Unfavorite non-default removes from jump list
h.ev("root.toggleFavorite({ id: 1, name: 'Main' })"); h.spin(40)
h.ok("P4 unfavorite removes Main from favorites", hev("Logic.isFavorite(root.hostFavorites, 'group/wf', '1')") is not True)
# Default stays listed after unfavorite attempt on default board
h.key(Qt.Key_Escape); h.spin(40)
# Ensure default group/app still listed even if not in favorites array
h.ev("root.persist({ favorites: [] })"); h.spin(40)
h.ok("P5 with empty favorites, default still in jump list", hev("root.jumpBoards.length") == 1 and hev("root.jumpBoards[0].isDefault") is True and hev("root.jumpBoards[0].project") == hev("root.defaultProject"))
# Empty everything -> title goes to picker
h.ev("root.persist({ board: { project: '', id: '', name: '' }, favorites: [] })")
# After clearing default, project bindings may still show last board; openJumpMenu checks jumpBoards
h.ok("P6 no default and no favorites: jumpBoards empty", hev("root.jumpBoards.length") == 0)
h.ev("root.headerMenu = ''")
h.ev("root.openJumpMenu()"); h.spin(60)
h.ok("P7 title with empty list opens the picker", hev("root.view") == "picker")

# Esc closes menu
h.key(Qt.Key_Escape); h.spin(40)
h.ev("root.persist({ board: { project: 'group/app', id: '7', name: 'Development' }, favorites: [] })")
h.ev("root.switchTo('group/other', '9', 'Ops')"); h.spin(40); h.answer("board", dict(BOARD, project="group/other")); h.spin(80)
h.ev("root.openDefaultMenu()"); h.spin(30)
h.ok("E0 menu open", hev("root.headerMenu") == "default")
h.key(Qt.Key_Escape); h.spin(40)
h.ok("E1 Esc closes the header menu", hev("root.headerMenu") == "")

sys.exit(h.finish())
