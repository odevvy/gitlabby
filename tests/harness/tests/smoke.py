# Smoke: v0.1.17+ loads with the stand-ins, opens, shows a board, the issue view,
# the settings, the picker, and the first-run panels. Usage: smoke.py <src> [board.png]
import sys; sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__))))
from lib import *
h = Harness(sys.argv[1], {"id": "odevvy.gitlabby", "settingsRevision": 2, "defaultProject": "group/app"})
from fixtures import BOARD
h.ok("S1 default project from settings", h.ev("root.project") == "group/app")
h.ev("root.opened = true"); h.spin(80)
h.ok("S2 opening fetches the board", any(c[1:4] == ["board", "--project", "group/app"] for c in h.running("board")), h.running())
h.answer("board", BOARD)
h.ok("S3 board on screen", h.ev("root.boardState") == "ready" and h.ev("boardView.visible"))
if len(sys.argv) > 2: h.grab_card(sys.argv[2])
h.ev("root.showView('settings')"); h.spin(80); h.ok("S4 settings view", h.ev("settingsView.visible"))
h.ev("root.back()"); h.ev("root.openPicker()"); h.spin(80); h.ok("S5 picker", h.ev("picker.visible"))
h.ev("root.back()"); h.stop_all(); h.ev("root.refresh()"); h.answer("board", {"state": "logged-out", "message": "Not signed in."})
h.ok("S6 signed-out panel", h.ev("setupView.visible") and h.ev("root.setup") == "logged-out")
sys.exit(h.finish())
