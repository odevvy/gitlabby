# v0.1.66: Settings > GitLab server (a plain field; Use or Enter switches, typing
# alone does nothing; http, a port or a path get the error under it and no Use,
# also for a bad value saved in shell.json, which the board treats as gitlab.com)
# and the setup panel for a server glab isn't signed in to. Usage: run166.py <src>
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from fixtures import BOARD
P, H = "group/app", "gitlab.example.com"
SETTINGS = {"id": "odevvy.gitlab-board", "settingsRevision": 2, "defaultProject": P, "defaultBoardId": "7", "defaultBoardName": "Development",
            "refreshIntervalSec": 60, "defaultCollapsed": ["closed"], "boardStates": {}}
h = Harness(sys.argv[1], SETTINGS)
writes = lambda: h.ev("root.bar.shell.writes") or []
sv = h.ctx_of(h.cls("SettingsView"))
def named(n): return [it for it in h.walk() if it.objectName() == n]
def shown(n): return [it for it in named(n) if it.isVisible()]
help_ = lambda: shown("hostHelp")[0].property("text") if shown("hostHelp") else ""
help_urgent = lambda: h.ev("hostHelp.color === view.host.urgent", sv) if False else shown("hostHelp")[0].property("color") == h.ev("root.urgent")
use = lambda: shown("hostUse")
def click_use():
    if use(): h.click(use()[0])
def typed(t): h.ev("hostField.text = %s" % json.dumps(t), sv); h.spin(60)
def setting(**kw):
    s = dict(h.ev("root.savedSettings")); s.update(kw); h.ev("root.settings = " + json.dumps(s)); h.spin(80)
def drain(kind, data):
    while h.running(kind): h.answer(kind, data)
h.ev("root.opened = true"); h.spin(60); drain("cached", {"state": "none"}); h.answer("board", BOARD)
h.ev("root.showView('settings')"); h.spin(80); drain("whoami", {"state": "ready", "user": "dev1"})

# --- the field ---------------------------------------------------------------------------
h.ok("F1 first in General: GitLab server, the server in use, no Use", len(shown("hostRow")) == 1 and h.ev("hostField.text", sv) == "gitlab.com" and not use())
h.ok("F2 its help: where glab must be signed in", help_() == "gitlab.com, or your company's own GitLab. glab must be signed in there: glab auth login --hostname <server>." and not help_urgent())
n = len(writes())
typed(H)
h.ok("F3 another name: Use, and what Use does", len(use()) == 1 and help_().startswith("Use switches to %s: you pick a project there. Your boards and settings on gitlab.com stay" % H), help_())
h.ok("F4 typing alone switches nothing, saves nothing", h.ev("root.gitlabHost") == "gitlab.com" and len(writes()) == n)
for bad in ["https://gitlab.example.com/gitlab", "gitlab.example.com:8443", "http://gitlab.example.com", "gitlab example", "gitlab.example.com/"+"x"]:
    typed(bad)
    h.ok("F5 %r: the error in the urgent color, no Use" % bad, not use() and help_() == "Just the server's name, like gitlab.example.com: no https://, no path, no port (glab keeps those)." and help_urgent(), help_())
    h.ev("view.useServer()", sv); h.spin(40)
    h.ok("F6 (%r: Use/Enter saves nothing)" % bad, len(writes()) == n and h.ev("root.gitlabHost") == "gitlab.com")
typed(""); h.ok("F7 empty: gitlab.com, nothing to use", not use() and not help_urgent())
typed("gitlab.com"); h.ok("F8 the server in use: no Use", not use())
h.ev("hostField.forceActiveFocus()", sv); h.spin(40)
h.ok("F9 while typing there, board keys stay off", h.ev("settingsView.typing") is True)
typed("other.example.org"); h.key(Qt.Key_Escape)
h.ok("F10 Esc puts the server in use back", h.ev("hostField.text", sv) == "gitlab.com" and h.ev("root.view") == "settings")
typed(" https://GitLab.Example.com/ ")
h.ok("F11 https:// and a trailing / are fine (dropped)", len(use()) == 1 and h.ev("view.hostCandidate", sv) == H)
click_use(); h.spin(120)
h.ok("F12 Use saves the bare name and switches", writes()[-1].get("gitlabHost") == H and h.ev("root.gitlabHost") == H and h.ev("hostField.text", sv) == H and not use(), writes()[-1].get("gitlabHost"))
h.ok("F12b Sign in names that server (Logic.signInCommand)", h.ev("root.loginCommand") == "glab auth login --hostname " + H, h.ev("root.loginCommand"))
h.ok("F13 ...and asks the new server who is signed in", [c[1:] for c in h.running("whoami", raw=True)] == [["whoami", "--hostname", H]], h.running(raw=True))
drain("whoami", {"state": "ready", "user": "dev2"})
typed("gitlab.com"); h.ev("hostField.forceActiveFocus()", sv); h.key(Qt.Key_Return, "\r"); h.spin(120)
h.ok("F14 Enter is Use: back to gitlab.com", writes()[-1].get("gitlabHost") == "gitlab.com" and h.ev("root.gitlabHost") == "gitlab.com" and h.ev("root.project") == P)
drain("whoami", {"state": "ready", "user": "dev1"})
# A bad value saved in shell.json: shown with the error, the board on gitlab.com meanwhile.
setting(gitlabHost="http://gitlab.example.com")
h.ok("F15 a bad saved value: shown as saved, with the error and what the board uses", h.ev("hostField.text", sv) == "http://gitlab.example.com" and help_urgent()
     and help_().endswith(" Until then the board uses gitlab.com.") and h.ev("root.gitlabHost") == "gitlab.com" and h.ev("root.hostInvalid") is True, help_())
typed("gitlab.com")
h.ok("F16 ...and gitlab.com can be used to fix it", len(use()) == 1)
click_use(); h.spin(80)
h.ok("F17 fixed: gitlab.com saved, no error", writes()[-1].get("gitlabHost") == "gitlab.com" and h.ev("root.hostInvalid") is False and not help_urgent())
drain("whoami", {"state": "ready", "user": "dev1"})
# --- the setup panel, signed out ------------------------------------------------------------
first = lambda n: (shown(n) or [None])[0]
setup_texts = lambda: [it.property("text") for it in h.visible(lambda it: it.metaObject().className().startswith("BoardText")) if it.property("text")]
labels = lambda: [it.property("label") for it in h.visible(lambda it: it.metaObject().className().startswith("ActionButton"))]
h.ev("root.showView('board')"); h.spin(40)
h.ev("root.boardState = 'logged-out'"); h.spin(80)
h.ok("P1 gitlab.com: the panel as before", "Sign in to GitLab" in setup_texts() and "This board reads your issues through glab. Sign in once and you're set." in setup_texts()
     and not shown("setupCommand") and sorted(labels()) == ["Sign in to GitLab", "Try again"], (labels()))
setting(gitlabHost=H); h.spin(60)
for k in ("cached", "board", "projects"):
    while h.running(k): h.answer(k, {"state": "logged-out", "message": "Not signed in"} if k != "cached" else {"state": "none"})
h.spin(120)
h.ok("P2 another server: Sign in to it, why, the exact command", h.ev("root.boardState") == "logged-out" and "Sign in to " + H in setup_texts()
     and "glab isn't signed in to %s yet. Sign in once in a terminal with:" % H in setup_texts() and first("setupCommand") is not None and first("setupCommand").property("text") == "glab auth login --hostname " + H, setup_texts())
h.ok("P3 buttons: Copy (not main), Sign in (main), Try again, Change server", sorted(labels()) == ["Change server", "Copy", "Sign in", "Try again"], labels())
h.ok("P3b Sign in is the main one, Copy is not", (first("setupCopy") is not None and first("setupCopy").property("main") is False))
h.ok("P4 the small print", any(t.startswith("Sign in opens a terminal with that command. Your token stays with glab") and "ca_cert or subfolder" in t for t in setup_texts()))
n = len(h.launched()); first("setupCopy") and h.click(first("setupCopy"))
h.ok("P5 Copy copies that command (wl-copy), and says so", h.launched()[n:] == [["wl-copy", "glab auth login --hostname " + H]] and (first("setupCopy") is not None and first("setupCopy").property("label") == "Copied"), h.launched()[n:])
n = len(h.launched()); h.key(Qt.Key_Return, "\r")
h.ok("P6 Enter signs in: a terminal with that command", h.launched()[n:] == [["omarchy-launch-floating-terminal-with-presentation", "glab auth login --hostname " + H]], h.launched()[n:])
h.ev("root.opened = true"); h.spin(60)
for k in ("cached", "board", "projects"):
    while h.running(k): h.answer(k, {"state": "logged-out", "message": "Not signed in"} if k != "cached" else {"state": "none"})
cs = [it for it in h.visible(lambda it: it.metaObject().className().startswith("ActionButton") and it.property("label") == "Change server")]
if cs: h.click(cs[0]); h.spin(150)
h.ok("P7 Change server: Settings, the field focused", bool(cs) and h.ev("root.view") == "settings" and h.ev("hostField.activeFocus", sv) is True)
sys.exit(h.finish())
