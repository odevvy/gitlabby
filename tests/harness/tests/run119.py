# v0.1.19: setup panels at the placeholder board's size, centred, GitLab icon,
# ConfirmDialog-style buttons, Enter = main button, r = Try again.
# Usage: run119.py <src> [signed-out.png no-glab.png]
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
pngs = sys.argv[2:4]
h = Harness(sys.argv[1], {"id": "odevvy.gitlabby", "settingsRevision": 2, "defaultProject": "group/app"})
buttons = lambda label: h.visible(lambda it: it.metaObject().className().startswith("ActionButton") and it.property("label") == label)
texts = lambda: [it.property("text") for it in h.visible(lambda it: it.metaObject().className().startswith("BoardText")) if it.property("text")]
size = lambda: (h.ev("panel.contentWidth"), h.ev("panel.contentHeight"))
sv = h.cls("SetupView")
def centred():
    col = next(c for c in sv.childItems() if c.metaObject().className() == "QQuickColumn")
    c = col.mapToItem(sv, QPointF(col.width() / 2, col.height() / 2))
    return abs(c.x() - sv.width() / 2) <= 1 and abs(c.y() - sv.height() / 2) <= 1, (c.x(), c.y(), sv.width(), sv.height())
same = lambda a, b: abs(a.redF() - b.redF()) < 0.01 and abs(a.greenF() - b.greenF()) < 0.01 and abs(a.blueF() - b.blueF()) < 0.01

h.ev("root.opened = true"); h.spin(80)
loading = size()
h.ok("P0 (placeholder board while loading)", h.ev("skeleton.visible"), loading)
h.answer("board", {"state": "logged-out", "message": "Not signed in to gitlab.com. Run: glab auth login"})
h.ok("L1 signed out: the popup keeps the placeholder board's size", size() == loading, (size(), loading))
ok_c, info = centred(); h.ok("L2 content centred both ways", ok_c, info)
icon = h.visible(lambda it: it.metaObject().className().startswith("BoardText") and it.property("text") == "\uf296")
h.ok("L3 GitLab icon (the bar icon's glyph) on top, in the accent", len(icon) == 1 and h.ev("button.text") == "\uf296" and same(icon[0].property("color"), h.ev("root.accent")))
t = texts()
h.ok("L4 copy", "Sign in to GitLab" in t and "This board reads your issues through glab. Sign in once and you're set." in t
     and "A terminal opens. Follow the steps there, then come back here." in t and not any("keeps the login" in x for x in t), t)
si, ta = buttons("Sign in to GitLab"), buttons("Try again")
h.ok("L5 Sign in is the main button: accent border and text, faint fill, 34 high", len(si) == 1 and si[0].property("main") is True
     and round(si[0].height()) == 34 and si[0].width() >= 120)
h.ok("L6 Try again is the quiet one", len(ta) == 1 and ta[0].property("main") is False and si[0].x() < ta[0].x())
h.ok("L7 Sign in is larger than the old caption pills", si[0].height() > 20 and si[0].width() > 140, (si[0].width(), si[0].height()))
if pngs: h.grab_card(pngs[0])
h.key(Qt.Key_Return)
h.ok("K1 Enter = Sign in", ["omarchy-launch-floating-terminal-with-presentation", "glab auth login"] in h.launched() and h.ev("root.opened") is False, h.launched())
h.ev("root.opened = true"); h.spin(80)
h.answer("board", {"state": "logged-out", "message": "Not signed in."})
n = len(h.launched()); h.stop_all(); h.key(Qt.Key_R, "r")
h.ok("K2 r = Try again (fetches, launches nothing)", bool(h.running("board")) and len(h.launched()) == n)
h.answer("board", {"state": "no-glab", "message": "The GitLab CLI (glab) is not installed."})
h.ok("N1 no glab: same size, centred", size() == loading and centred()[0], size())
t = texts()
h.ok("N2 copy: 'Install glab', what glab is, the command in a box", "Install glab" in t and any("glab, GitLab's command-line tool" in x for x in t) and "sudo pacman -S glab" in t, t)
cp, ta = buttons("Copy"), buttons("Try again")
h.ok("N3 Copy is the main button, Try again quiet", len(cp) == 1 and cp[0].property("main") is True and len(ta) == 1 and ta[0].property("main") is False)
if len(pngs) > 1: h.grab_card(pngs[1])
h.key(Qt.Key_Return)
h.ok("N4 Enter = Copy (wl-copy), label says Copied", ["wl-copy", "sudo pacman -S glab"] in h.launched() and len(buttons("Copied")) == 1)
h.click(buttons("Try again")[0])
h.ok("N5 Try again fetches", bool(h.running("board")))
h.answer("board", {"state": "error", "message": "Could not check your GitLab sign-in."})
# v0.1.23: with nothing loaded, the error takes the board's place (was: an empty body).
h.ok("E1 an error is not a setup state, but nothing loaded: the error panel with Try again", h.ev("root.setup") == "" and h.ev("setupView.visible") and "Could not reach GitLab" in texts() and len(buttons("Try again")) == 1)
# New user: 'pick' panel, Enter opens the picker.
h.stop_all(); h.ev("root.project = ''; root.boardState = 'loading'"); h.ev("root.refresh()"); h.spin(30)
h.ok("C1 checking: 'Checking GitLab…', same size", "Checking GitLab…" in texts() and size() == loading)
h.answer("projects", {"state": "error", "message": "Could not check your GitLab sign-in. Check your connection and try again."})
h.ok("C2 offline: Try again is the main button", len(buttons("Try again")) == 1 and buttons("Try again")[0].property("main") is True)
h.key(Qt.Key_Return); h.ok("C3 Enter = Try again", bool(h.running("projects")))
h.answer("projects", {"state": "ready", "projects": [{"id": 1, "path": "group/app"}]})
h.ev("root.back()"); h.spin(50)
h.ok("C4 back from the picker: 'Choose a project' main button", len(buttons("Choose a project")) == 1)
h.key(Qt.Key_Return); h.ok("C5 Enter = Choose a project", h.ev("root.view") == "picker")
sys.exit(h.finish())
