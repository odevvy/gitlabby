# 0.1.138: Report an issue (Settings) and Report this (failed load only)
# open GitLabby's own new-issue page on gitlab.com, never the board project.
import sys, os, json, re, shutil
from urllib.parse import quote, unquote
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from fixtures import BOARD

MANIFEST = os.path.join(sys.argv[1], "manifest.json")
with open(MANIFEST) as f:
    VERSION = json.load(f)["version"]
assert re.fullmatch(r"[0-9A-Za-z._-]{1,32}", VERSION), VERSION
BASE = "https://gitlab.com/o_devvy/gitlabby/-/issues/new"
FAILED = BASE + "?issue[title]=" + quote("GitLabby %s: Could not reach GitLab" % VERSION, safe="") \
    + "&issue[description]=" + quote("Plugin: GitLabby %s\nState: load failed\n\nWhat happened:\n" % VERSION, safe="")
LEAKS = ["group/app", "git.example.com", "glpat-secret", "/var/cache/boards", "Could not load boards for"]
HOSTILE = "Could not load boards for group/app. token=glpat-secret host=git.example.com path=/var/cache/boards"

ALL = []
h = None

def ok(name, cond, extra=""):
    ALL.append(bool(cond))
    h.ok(name, cond, extra)

def finish():
    ok("Z no binding-loop warnings", not [w for w in h.warnings if "oop" in w], [w for w in h.warnings if "oop" in w])
    ok("Z no QML warnings", not h.warnings, h.warnings[:3])
    if h.warnings:
        print("QML warnings:", len(h.warnings)); print("\n".join(h.warnings[:30]))
    shutil.rmtree(h.dir, ignore_errors=True)

def named(name, visible=True):
    return [it for it in h.walk() if it.objectName() == name and (it.isVisible() if visible else True)]

def into_view(it):
    f = it.parentItem() if it is not None else None
    while f is not None and not f.metaObject().className().startswith("QQuickFlickable"):
        f = f.parentItem()
    if f is not None:
        y = it.mapToItem(f.property("contentItem"), QPointF(0, 0)).y()
        top, height = f.property("contentY"), f.height()
        if y < top or y + it.height() > top + height:
            f.setProperty("contentY", max(0.0, min(y - 20, f.property("contentHeight") - height)))
            QGuiApplication.processEvents()

def settings(**extra):
    s = {"id": "odevvy.gitlabby", "settingsRevision": 2, "defaultProject": "group/app"}
    s.update(extra)
    return s

# Settings: the footer link opens a blank form, even on a self-hosted server
# and with Open links in set to an app window.
h = Harness(sys.argv[1], settings(openLinks="app", gitlabHost="git.example.com"))
ok("V0 version comes from the manifest, not a hardcoded string", h.ev("root.pluginVersion") == VERSION, (h.ev("root.pluginVersion"), VERSION))
h.ev("root.opened = true"); h.spin(80)
h.answer("board", BOARD); h.spin(120)
h.ev("root.showView('settings')"); h.spin(80)
links = named("reportIssueLink")
ok("S1 Settings shows Report an issue", len(links) == 1 and links[0].property("text") == "Report an issue", len(links))
ok("S2 the failed-load link is not on Settings", named("reportThisLink") == [])
if links:
    into_view(links[0])
n = len(h.launched())
if links:
    h.click(links[0]); h.spin(80)
launched = (h.launched() or [])[n:]
ok("S3 the Settings link opens the blank GitLabby form in a browser",
   launched == [["omarchy-launch-browser", BASE]], launched)
ok("S4 it does not use a webapp, even when Open links in is an app window",
   all(not cmd or cmd[0] != "omarchy-launch-webapp" for cmd in launched), launched)
ok("S5 the URL has no prefill and no board host or project",
   launched and launched[0][1] == BASE and not any(s in launched[0][1] for s in LEAKS), launched)
ok("S6 the Settings link closes the popup", h.ev("root.opened") is False, h.ev("root.opened"))
h.stop_all(); finish()

# Load-failure panel (project set, no board on screen). The raw message is
# hostile on purpose; it must not appear in the URL.
h = Harness(sys.argv[1], settings())
h.ev("root.opened = true"); h.spin(80)
h.answer("board", {"state": "error", "message": HOSTILE})
h.spin(150)
ok("F0 the failed panel is on screen", h.ev("root.failed") is True and h.ev("setupView.visible") is True and h.ev("setupView.step") == "error" and h.ev("setupView.mode") == "failed",
   (h.ev("root.failed"), h.ev("setupView.visible"), h.ev("setupView.step"), h.ev("setupView.mode"), h.ev("root.boardState")))
this_link = named("reportThisLink")
ok("F1 Report this is visible on a failed load", len(this_link) == 1 and this_link[0].property("text") == "Report this", len(this_link))
ok("F2 Settings' Report an issue is not on the failed panel", named("reportIssueLink") == [])
n = len(h.launched())
if this_link:
    h.click(this_link[0]); h.spin(80)
launched = (h.launched() or [])[n:]
ok("F3 Report this opens the prefilled GitLabby form in a browser",
   launched == [["omarchy-launch-browser", FAILED]], launched)
if launched:
    url = launched[0][1]
    ok("F4 the prefill has no project, host, path, token or raw message",
       not any(s in url for s in LEAKS) and VERSION in unquote(url), url)
else:
    ok("F4 the prefill has no project, host, path, token or raw message", False, launched)
ok("F5 Report this closes the popup", h.ev("root.opened") is False, h.ev("root.opened"))
h.stop_all(); finish()

# The same link stays hidden on the other setup states, and when a refresh
# fails but the board is still on screen.
def on_state(name, kind, payload, expect_failed_link=False, project="group/app"):
    global h
    h = Harness(sys.argv[1], settings(defaultProject=project) if project else {"id": "odevvy.gitlabby", "settingsRevision": 2, "defaultProject": ""})
    h.ev("root.opened = true"); h.spin(80)
    h.answer(kind, payload); h.spin(150)
    visible = named("reportThisLink")
    ok("%s Report this visible=%s" % (name, expect_failed_link), bool(visible) is expect_failed_link,
       (h.ev("root.setup"), h.ev("setupView.step") if h.ev("setupView") else None, h.ev("root.failed"), h.ev("root.boardState"), len(visible)))
    h.stop_all(); finish()

# Checking: the board fetch has not answered yet.
h = Harness(sys.argv[1], settings())
h.ev("root.opened = true"); h.spin(80)
ok("G0 checking: Report this is hidden", named("reportThisLink") == [] and h.ev("root.boardState") == "loading",
   (h.ev("root.boardState"), h.ev("root.failed"), h.ev("setupView.visible")))
h.stop_all(); finish()

on_state("G1 no-glab:", "board", {"state": "no-glab", "message": "The GitLab CLI (glab) is not installed."}, False)
on_state("G2 logged-out:", "board", {"state": "logged-out", "message": "Not signed in to git.example.com. Run: glab auth login --hostname git.example.com"}, False)
on_state("G3 pick:", "projects", {"state": "ready", "projects": []}, False, project="")
# pick + error (project list failed): heading is the same, but this is not mode "failed"
on_state("G4 pick-error:", "projects", {"state": "error", "message": "Could not reach GitLab"}, False, project="")

# Refresh failure keeps the board: no setup panel, no Report this.
h = Harness(sys.argv[1], settings())
h.ev("root.opened = true"); h.spin(80)
h.answer("board", BOARD); h.spin(120)
ok("R0 board is on screen", h.ev("root.boardState") == "ready" and h.ev("boardView.visible") is True)
h.stop_all(); h.ev("root.refresh()"); h.spin(40)
h.answer("board", {"state": "error", "message": "Could not load boards for group/app"})
h.spin(120)
ok("R1 a failed refresh keeps the board", h.ev("root.boardState") == "ready" and h.ev("boardView.visible") is True and h.ev("root.refreshError") != "",
   (h.ev("root.boardState"), h.ev("root.refreshError"), h.ev("root.failed")))
ok("R2 Report this is not in the header refresh-error state", named("reportThisLink") == [])
h.stop_all(); finish()

print("passed %d failed %d" % (ALL.count(True), ALL.count(False)))
sys.exit(0 if all(ALL) else 1)
