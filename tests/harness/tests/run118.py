# v0.1.18: settings show who is signed in, and Sign out (asks first) runs
# board-fetch logout and lands on the sign-in panel. Usage: run118.py <src> [settings.png confirm.png]
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from fixtures import BOARD
pngs = sys.argv[2:4]
h = Harness(sys.argv[1], {"id": "odevvy.gitlabby", "settingsRevision": 2, "defaultProject": "group/app", "defaultCollapsed": ["closed", "research", "open"], "boardStates": {}, "refreshIntervalSec": 60})
pills = lambda label: h.visible(lambda it: it.metaObject().className().startswith(("Pill", "ActionButton")) and it.property("label") == label)
texts = lambda: [it.property("text") for it in h.visible(lambda it: it.metaObject().className().startswith("BoardText")) if it.property("text")]
has = lambda frag: any(frag in t for t in texts())
# v0.1.24: Sign out is a text action (a BoardText), no longer a button.
signout = lambda: h.visible(lambda it: it.metaObject().className().startswith("BoardText") and it.property("text") == "Sign out")
timer = "(function(){ for (var i = 0; i < root.data.length; i++) { var t = root.data[i]; if (t && t.interval === root.refreshIntervalSec * 1000 && t.repeat === true) return t } return null })()"
h.ev("panel.contentHeight = Qt.binding(function() { return keyCatcher.implicitHeight + panel.padding * 2 + 4 })")

h.ev("root.opened = true"); h.spin(60); h.answer("board", BOARD)
h.ok("B0 board loaded", h.ev("root.boardState") == "ready" and len(h.ev("root.columns")) == 4)
h.ev("root.showView('settings')"); h.spin(80)
h.ok("A1 opening settings asks who is signed in", h.running("whoami") == [[h.ev("root.helperPath()"), "whoami"]], h.running())
h.ok("A2 while it loads: 'Checking…', no Sign out yet", has("Checking your GitLab account") and not signout())
h.answer("whoami", {"state": "ready", "message": "", "user": "dev1"})
h.ok("A3 'Signed in as dev1 on gitlab.com'", has("Signed in as dev1 on gitlab.com"), texts()[:6])
h.ok("A4 Sign out action, no confirm yet", len(signout()) == 1 and not pills("Yes, sign out"))
if pngs: h.grab_card(pngs[0])
h.click(signout()[0])
h.ok("C1 Sign out asks first, inline", has("Sign out of glab on gitlab.com? This also signs glab out in your terminal and scripts on this computer.") and len(pills("Yes, sign out")) == 1 and len(pills("Cancel")) == 1 and not signout())
h.ok("C2 nothing run yet", not h.running("logout") and h.launched() == [])
if len(pngs) > 1: h.grab_card(pngs[1])
h.click(pills("Cancel")[0])
h.ok("C3 Cancel: back to signed in, nothing run", has("Signed in as dev1") and len(signout()) == 1 and not h.running("logout"))
h.click(signout()[0]); h.key(Qt.Key_Escape); h.spin(60)
h.ok("C4 Esc while asking: back to the board, nothing run", h.ev("root.view") == "board" and not h.running("logout"))
h.ev("root.showView('settings')"); h.spin(60)
h.ok("C5 reopened settings: not asking, asks GitLab again", not pills("Yes, sign out") and bool(h.running("whoami")))
h.answer("whoami", {"state": "ready", "message": "", "user": "dev1"})

# Failure: the board and settings stay, the reason shows, Sign out can be tried again.
h.click(signout()[0]); h.click(pills("Yes, sign out")[0])
h.ok("O1 Yes runs board-fetch logout (no terminal)", h.running("logout") == [[h.ev("root.helperPath()"), "logout"]] and h.launched() == [], (h.running(), h.launched()))
h.ok("O2 'Signing out…', buttons hidden", has("Signing out") and not pills("Yes, sign out") and not signout())
h.ev("root.refresh()"); h.spin(30)
h.ok("O3 no refresh while signing out", not h.running("board"))
h.answer("logout", {"state": "error", "message": "glab could not sign out of gitlab.com."})
h.ok("O4 failure: reason shown, still in settings, board kept", has("glab could not sign out") and h.ev("root.view") == "settings" and h.ev("root.boardState") == "ready" and len(h.ev("root.columns")) == 4)
h.ok("O5 failure: Sign out offered again", len(signout()) == 1)

# Success, with a board refresh still in flight from before.
h.ev("root.back()"); h.ev("root.refresh()"); h.spin(30)
h.ok("S0 (a refresh is in flight)", bool(h.running("board")))
h.ev("root.showView('settings')"); h.spin(30); h.answer("whoami", {"state": "ready", "message": "", "user": "dev1"})
h.click(signout()[0]); h.click(pills("Yes, sign out")[0])
h.answer("logout", {"state": "logged-out", "message": "Signed out of gitlab.com."})
h.ok("S1 signed out: the sign-in panel", h.ev("root.view") == "board" and h.ev("root.setup") == "logged-out" and h.ev("setupView.visible") and len(pills("Sign in to GitLab")) == 1)
h.ok("S2 board, projects and username dropped from memory", h.ev("root.columns") == [] and h.ev("root.projects") == [] and h.ev("root.account") == "")
h.ok("S3 no refresh timer while signed out", h.ev(timer + ".running") is False)
h.answer("board", BOARD)
h.ok("S4 the refresh from before signing out is ignored", h.ev("root.setup") == "logged-out" and h.ev("root.columns") == [])
h.click(pills("Try again")[0])
h.ok("S5 Try again fetches again", bool(h.running("board")))
h.answer("board", BOARD)
h.ok("S6 signed in again: board back, timer on", h.ev("root.boardState") == "ready" and h.ev("boardView.visible") and h.ev(timer + ".running") is True)

# whoami answers other than ready.
h.ev("root.showView('settings')"); h.spin(30)
h.answer("whoami", {"state": "error", "message": "Could not check your GitLab sign-in. Check your connection and try again."})
h.ok("W1 offline: the reason, and Sign out still offered (it works offline)", has("Check your connection") and len(signout()) == 1)
h.ev("root.back()"); h.ev("root.showView('settings')"); h.spin(30)
h.answer("whoami", {"state": "logged-out", "message": "Not signed in to gitlab.com. Run: glab auth login"})
h.ok("W2 signed out elsewhere: the sign-in panel", h.ev("root.view") == "board" and h.ev("root.setup") == "logged-out")
h.ok("W3 nothing written to settings", (h.ev("root.bar.shell.writes") or []) == [])
sys.exit(h.finish())
