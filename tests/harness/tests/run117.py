# v0.1.17 first run (rebuilt for the durable tooling): no glab, signed out, new
# users land in the picker, existing users keep their project.
# Usage: run117.py <src> [signed-out.png no-glab.png picker.png]
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from fixtures import BOARD
pngs = sys.argv[2:5]; grab = lambda i: h.grab_card(pngs[i]) if len(pngs) > i else None
h = Harness(sys.argv[1])
pills = lambda label: h.visible(lambda it: it.metaObject().className().startswith(("Pill", "ActionButton")) and it.property("label") == label)
timer_on = lambda: h.ev("(function(){ for (var i = 0; i < root.data.length; i++) { var t = root.data[i]; if (t && t.interval === root.refreshIntervalSec * 1000 && t.repeat === true) return t.running } return null })()")
h.ok("A1 no saved project: default empty", h.ev("root.defaultProject") == "" and h.ev("root.project") == "")
h.ev("root.opened = true"); h.spin(80)
h.ok("A2 opening checks with the project list only", bool(h.running("projects")) and not h.running("board") and not h.running("cached"))
h.ok("A3 'pick' panel, no skeleton, no timer", h.ev("root.setup") == "pick" and h.ev("setupView.visible") and not h.ev("skeleton.visible") and timer_on() is False)
h.answer("projects", {"state": "logged-out", "message": "Not signed in to gitlab.com. Run: glab auth login"})
h.ok("A4 signed out: Sign in + Try again", h.ev("root.setup") == "logged-out" and len(pills("Sign in to GitLab")) == 1 and len(pills("Try again")) == 1)
grab(0)
h.click(pills("Sign in to GitLab")[0])
h.ok("A5 Sign in opens glab auth login in Omarchy's floating terminal, closes", ["omarchy-launch-floating-terminal-with-presentation", "glab auth login"] in h.launched() and h.ev("root.opened") is False)
h.ev("root.opened = true"); h.spin(80); h.answer("projects", {"state": "no-glab", "message": "The GitLab CLI (glab) is not installed."})
h.ok("A6 no glab: install panel with Copy", h.ev("root.setup") == "no-glab" and len(pills("Copy")) == 1)
h.click(pills("Copy")[0])
h.ok("A7 Copy uses wl-copy", ["wl-copy", "sudo pacman -S glab"] in h.launched() and len(pills("Copied")) == 1)
grab(1)
h.click(pills("Try again")[0]); h.answer("projects", {"state": "error", "message": "Could not check your GitLab sign-in. Check your connection and try again."})
h.ok("A8 offline: error + Try again, no picker", h.ev("root.boardState") == "error" and len(pills("Try again")) == 1 and h.ev("root.view") == "board")
h.click(pills("Try again")[0]); h.answer("projects", {"state": "ready", "projects": [{"id": 1, "path": "group/app"}]})
h.ok("A9 signed in: lands in the project picker", h.ev("root.view") == "picker" and h.ev("root.pickerStep") == "projects")
grab(2)
h.ev("root.pickProject('group/app')"); h.spin(50); h.answer("boards", {"state": "ready", "boards": [{"id": 7, "name": "Development"}]})
h.ev("root.pickBoard({ id: 7, name: 'Development' })"); h.spin(80)
w = h.ev("root.bar.shell.writes") or []
h.ok("A10 first board opened becomes the default", len(w) == 1 and w[0]["defaultProject"] == "group/app" and w[0]["defaultBoardId"] == "7", w)
h.answer("board", BOARD)
h.ok("A11 board on screen, timer on, starred", h.ev("boardView.visible") and timer_on() is True and h.ev("root.onDefault"))
sys.exit(h.finish())
