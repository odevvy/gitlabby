# v0.1.37: the Merge requests view at Style.scale 1.5 (OGB_SCALE). m and the header
# button open it; it asks the shared service for board-fetch mrs only on open,
# on a scope change or r (an answer under a minute old is reused); rows show
# status, pipeline and every reviewer's state; Enter/o/click open the link and
# nothing else; signed out shows the message; the badge counts review requests.
# Usage: run137.py <src> [outdir]   (previews: mrs-view, mrs-header-badge, mrs-signed-out)
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import os
os.environ["OGB_SCALE"] = "1.5"
import lib
from lib import *
from PySide6.QtGui import QImage
src = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else None
P = "my-group/my-project"
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "run134.py")).read().split("ALL = []")[0].split("P = \"my-group/my-project\"")[1])
ALL = []
def ok(n, c, e=""): ALL.append(bool(c)); h.ok(n, c, e)
h = Harness(src, {"id": "odevvy.gitlabby", "settingsRevision": 2, "defaultProject": P, "defaultCollapsed": ["open", "research", "Closed"]})
h.ev("panel.availableCardHeight = %d; panel.availableCardWidth = 1460" % DESK)
h.ev("root.opened = true"); h.spin(60); h.answer("board", board()); h.spin(150)
def who(u, n, st): return {"username": u, "name": n, "avatar": "", "state": st}
def mr(iid, title, project, branch, status, author, reviewers, pipeline=None, draft=False, ago="2026-10-30T19:40:00Z"):
    return {"iid": iid, "title": title, "url": "https://gitlab.com/%s/-/merge_requests/%d" % (project, iid), "draft": draft, "project": project,
            "branch": branch, "updatedAt": ago, "status": status, "author": {"username": author.lower().replace(" ", "-"), "name": author, "avatar": ""},
            "pipeline": pipeline, "reviewers": reviewers}
import datetime
def ago_(minutes): return (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")
PIPE = lambda s: {"status": s, "url": "https://gitlab.com/my-group/my-project/-/pipelines/1"}
ANS = {"state": "ready", "message": "", "scope": "all", "updatedAt": "2026-10-30T20:52:00Z",
  "review": [mr(88, "Book motion: one open/close curve for every view <b>", P, "app-ui/book-motion", "ci_still_running", "App UI", [who("o_devvy", "odevvy", "review_started"), who("api", "API", "approved")], PIPE("running"), ago=ago_(12)),
             mr(86, "API: paginate story notes", P, "api/notes-pages", "requested_changes", "API", [who("o_devvy", "odevvy", "requested_changes")], PIPE("passed"), ago=ago_(130))],
  "mine": [mr(35, "feat: desktop alerts (0.1.36)", "o_devvy/gitlabby", "feat/alerts", "mergeable", "odevvy", [], None, ago=ago_(4)),
           mr(12, "Draft: hyprland gestures", "o_devvy/dotfiles", "gestures", "draft_status", "odevvy", [who("a", "Ann Lee", "unreviewed")], PIPE("failed"), draft=True, ago=ago_(3*1440)),
           mr(7, "Waybar module for build status", "o_devvy/tools", "waybar-ci", "conflict", "odevvy", [who("a", "Ann Lee", "reviewed"), who("b", "Bo", "approved")], PIPE("passed"), ago=ago_(5*1440))]}
mrs_runs = lambda: [c for c in h.running("mrs")]
calls = []
def launched_browser(): return [c for c in h.launched() if c and c[0] == "omarchy-launch-browser"]
def shot(name, crop=None):
    QTest.mouseMove(h.win, QPoint(1, 1)); h.spin(80)
    if out: h.grab_card(os.path.join(out, name + ".png"))

# --- closed view: nothing loads ----------------------------------------------------
# x and width in header coordinates (merge requests may sit in a group of tabs)
box = lambda n: (lambda x, w: (round(x), round(x + w)))(h.ev("header.%s.mapToItem(header, 0, 0).x" % n) if n == "mrsButton" else h.ev("header.%s.x" % n), h.ev("header.%s.width" % n))
hx = {n: box(n) for n in ("status", "refreshButton", "mrsButton", "keysButton", "gear")}
order = ["status", "refreshButton", "keysButton", "gear"]
ok("H1 header: Updated, refresh, keys, gear, left to right; merge requests overlaps none of them",
   all(hx[a][1] <= hx[b][0] for a, b in zip(order, order[1:])) and all(hx["mrsButton"][1] <= hx[o][0] or hx["mrsButton"][0] >= hx[o][1] for o in order), hx)
ok("M0 the board alone: no merge-request fetch", mrs_runs() == [] and h.ev("root.feed.mrs.answers") == {})
badge = lambda: next((it for it in h.walk() if it.objectName() == "mrsBadge"), None)
ok("M1 no answer yet: no badge", badge() is not None and not badge().isVisible())
# --- m opens it: one board-fetch mrs, all projects ---------------------------------
h.key(Qt.Key_M, "m")
ok("M2 m opens the view and asks for all projects once", h.ev("root.view") == "mrs" and len(mrs_runs()) == 1 and mrs_runs()[0][1:] == ["mrs"], mrs_runs())
ok("M3 while loading: a loading line", any(it.objectName() == "mrsMessage" and "Loading" in it.property("text") for it in h.visible(lambda it: True)))
h.answer("mrs", ANS); h.spin(120)
rows = lambda: sorted([it for it in h.visible(lambda it: it.objectName() == "mrRow")], key=lambda it: it.mapToScene(QPointF(0, 0)).y())
r = rows()
ok("M4 five rows: two for review, three of his", [x.property("row")["iid"] for x in r] == [88, 86, 35, 12, 7], [x.property("row")["iid"] for x in r])
pills = [p.property("label") if p.isVisible() else "" for p in sorted([it for it in h.walk() if it.objectName() == "mrStatus"], key=lambda it: it.mapToScene(QPointF(0, 0)).y())]
ok("M5 status pills from GitLab's merge status (draft first)", [x for x in pills if x] == ["Pipeline running", "Changes requested", "Ready", "Draft", "Conflicts"], pills)
revs = sorted([it for it in h.visible(lambda it: it.objectName() == "reviewer")], key=lambda it: (round(it.mapToScene(QPointF(0, 0)).y()), it.mapToScene(QPointF(0, 0)).x()))
tips = [it.property("mark").toVariant()["tip"] if hasattr(it.property("mark"), "toVariant") else it.property("mark")["tip"] for it in revs]
ok("M6 every reviewer with their state", tips == ["odevvy is reviewing", "API approved", "odevvy requested changes", "Ann Lee hasn't reviewed yet", "Ann Lee left a review", "Bo approved"], tips)
title88 = next(it for it in h.walk(r[0]) if it.property("text") == "Book motion: one open/close curve for every view <b>")
ok("M7 titles are plain text (markup shown, not run)", title88 is not None and h.ev("textFormat === Text.PlainText", ctx=QQmlEngine.contextForObject(title88), obj=title88) is True)
sub = [it.property("text") for it in h.walk(r[2]) if "·" in str(it.property("text") or "")]
import re as _re
ages = [str(it.property("text")) for x in r for it in sorted(h.walk(x), key=lambda i: i.mapToScene(QPointF(0, 0)).x()) if it.isVisible() and _re.fullmatch(r"\d+(m|h|d|w|mo|y)", str(it.property("text") or ""))]
ok("M8a how long ago each changed", ages == ["12m", "2h", "4m", "3d", "5d"], ages)
ok("M8 his row's second line: project, branch, reviewers", sub == ["o_devvy/gitlabby  ·  feat/alerts  ·  no reviewer yet"], sub)
shot("mrs-view")
# --- keys: cursor, Enter, o --------------------------------------------------------
ok("M9 cursor on the first row", h.ev("mrsView.cursor") == 0)
h.key(Qt.Key_J, "j"); h.key(Qt.Key_Down, ""); 
ok("M10 j and ↓ move down", h.ev("mrsView.cursor") == 2)
h.key(Qt.Key_K, "k")
ok("M11 k moves up", h.ev("mrsView.cursor") == 1)
for _ in range(9): h.key(Qt.Key_J, "j")
ok("M12 stops at the last row", h.ev("mrsView.cursor") == 4)
before = len(launched_browser())
h.key(Qt.Key_Return, "")
lb = launched_browser()
ok("M13 Enter opens the selected merge request in the browser, nothing else runs", len(lb) == before + 1 and lb[-1] == ["omarchy-launch-browser", "https://gitlab.com/o_devvy/tools/-/merge_requests/7"], lb[-1:])
ok("M14 no write: every command run is a read (mrs/board) or the browser", all(c and (c[0] in ("omarchy-launch-browser",)) for c in h.launched()) and not h.running("move"))
# opening the link closes the popup (openUrl); reopen
h.ev("root.opened = true"); h.spin(80)
if h.running("board"): h.answer("board", board())
h.spin(80)
ok("M15 back on the board, the badge shows 2 review requests", badge().isVisible() and next(it for it in h.walk(badge()) if it.property("text") is not None).property("text") == "2")
if out:
    QTest.mouseMove(h.win, QPoint(1, 1)); h.spin(80)
    h.grab_card(os.path.join(out, "mrs-board.png"))
    img = QImage(os.path.join(out, "mrs-board.png")); w = img.width()
    img.copy(w - 260, 0, 260, 60).scaled(780, 180).save(os.path.join(out, "mrs-header-badge.png"))
# --- the header button; a recent answer is reused --------------------------------
btn = h.ev("header.mrsButton")
h.click(btn); h.spin(60)
ok("M16 the header button opens it; under a minute old: no new fetch", h.ev("root.view") == "mrs" and mrs_runs() == [] and len(rows()) == 5)
h.key(Qt.Key_R, "r")
ok("M17 r fetches again", len(mrs_runs()) == 1)
h.key(Qt.Key_R, "r")
ok("M18 r again while loading: still one", len(mrs_runs()) == 1)
# Says so: the note under the header, or (v0.1.71) the header's "Updating…" alone.
ok("M19 refreshing keeps the rows and says so", len(rows()) == 5 and (any("refreshing" in str(it.property("text")) for it in h.visible(lambda it: it.objectName() == "mrsNote")) or h.ev("header.status.text") == "Updating\u2026"), h.ev("header.status.text"))
# --- scope: This project (asked while All projects still loads: it waits) ----------
pill = next(it for it in h.visible(lambda it: it.property("label") == "This project"))
h.click(pill); h.spin(60)
ok("M19b This project while All projects loads: it waits its turn", len(mrs_runs()) == 1 and mrs_runs()[0][1:] == ["mrs"], mrs_runs())
h.answer("mrs", ANS); h.spin(80)
ok("M20 then it asks for the board's project", h.ev("mrsView.scope") == P and mrs_runs() and mrs_runs()[0][1:] == ["mrs", "--project", P], mrs_runs())
h.answer("mrs", dict(ANS, scope=P, mine=[]))
ok("M21 its lists; an empty section says so", [x.property("row")["iid"] for x in rows()] == [88, 86] and any(it.property("text") == "No open merge requests of yours." for it in h.visible(lambda it: True)))
h.click(next(it for it in h.visible(lambda it: it.property("label") == "All projects"))); h.spin(60)
ok("M22 back to All projects: the minute-old answer, no fetch", mrs_runs() == [] and len(rows()) == 5)
# --- m toggles back; Esc too ----------------------------------------------------
h.key(Qt.Key_M, "m")
ok("M23 m again: back to the board", h.ev("root.view") == "board")
h.key(Qt.Key_M, "m"); h.key(Qt.Key_Escape, "")
ok("M24 Esc: back to the board", h.ev("root.view") == "board")
h.key(Qt.Key_M, "m"); h.key(Qt.Key_R, "r"); h.key(Qt.Key_R, "r")
h.answer("mrs", ANS); h.spin(120)
ok("M24b r twice while loading: one fetch, none queued after it", mrs_runs() == [], mrs_runs())
h.key(Qt.Key_Escape, "")
# --- signed out -----------------------------------------------------------------
h.ev("root.feed.mrs.answers = ({})"); h.key(Qt.Key_M, "m")
h.answer("mrs", {"state": "logged-out", "message": "Not signed in to gitlab.com. Run: glab auth login"})
msg = [it.property("text") for it in h.visible(lambda it: it.objectName() == "mrsMessage")]
ok("M25 signed out: GitLab's message and how to retry, no rows", msg and msg[0].startswith("Not signed in to gitlab.com.") and "r to try again" in msg[0] and rows() == [], msg)
ok("M26 no badge for a failed answer", h.ev("header.mrsButton.badge") == "")
shot("mrs-signed-out")
h.ev("root.feed.forget()"); h.spin(40)
ok("M27 sign-out forgets the lists", h.ev("root.feed.mrs.answers") == {})
ok("M28 the view's height fits under the popup cap (it scrolls past it)", h.ev("panel.contentHeight") <= 960 + 60, h.ev("panel.contentHeight"))
rc = h.finish()
print("passed", sum(ALL), "failed", len(ALL) - sum(ALL)) if False else None
sys.stdout.flush(); os._exit(rc)
