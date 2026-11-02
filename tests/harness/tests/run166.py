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
sys.exit(h.finish())
