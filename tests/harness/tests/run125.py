# v0.1.25: GitLab.com now returns issue web URLs as /-/work_items/<iid>, so
# board-fetch never found the project URL and a full Closed column (20) had no
# "Showing the latest 20 · See all on GitLab" footer. End to end at the
# reporter's size (popup ~520 tall): the real board-fetch (fake glab, work-item
# URLs) feeds the board; the column headers show on open, the board scrolls,
# and the footer is there at the bottom of Closed and opens GitLab.
# Usage: run125.py <src> [closed-top.png closed-bottom.png]
import sys, os, json, subprocess, tempfile, shutil; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
src = sys.argv[1]; pngs = sys.argv[2:4]
shot = lambda i: len(pngs) > i and h.grab_card(pngs[i])
# --- the data: real board-fetch against fake glab, phrase41-shaped ----------
work = tempfile.mkdtemp(prefix="ogb-125-"); os.makedirs(work + "/bin"); os.makedirs(work + "/fx")
shutil.copy(src + "/tests/fake-glab", work + "/bin/glab")
with open(work + "/bin/timeout", "w") as f: f.write('#!/usr/bin/env bash\nshift 3; exec "$@"\n')
os.chmod(work + "/bin/timeout", 0o755)
U = "https://gitlab.com/firelink21/phrase41/-/work_items/"
def iss(i, state, labels): return {"iid": i, "title": "Issue %d with a title long enough to wrap onto a second line" % i, "state": state, "labels": labels, "web_url": U + str(i), "created_at": "2026-10-28T12:00:00Z", "user_notes_count": 2, "assignees": []}
lists = [{"id": n, "position": n, "label": {"name": l, "color": c}} for n, (l, c) in enumerate([("research", "#ffffff"), ("todo", "#3b82f6"), ("approved", "#dc2626"), ("in progress", "#eab308"), ("review", "#86efac")])]
fx = {"boards": [{"id": 7, "name": "Development", "hide_backlog_list": False, "hide_closed_list": False, "labels": [], "milestone": None, "assignee": None, "lists": lists}],
      "open": [[iss(40, "opened", ["in progress"]), iss(41, "opened", ["in progress"]), iss(50, "opened", ["review"])] + [iss(i, "opened", ["research"]) for i in range(1, 6)]],
      "closed": [iss(120 - i, "closed", ["api"]) for i in range(21)]}  # 21: board-fetch asks for one more than it shows (v0.1.28)
for k, v in fx.items():
    with open(work + "/fx/%s.json" % k, "w") as f: f.write("\n".join(json.dumps(x) for x in v) if k == "open" else json.dumps(v))
env = dict(os.environ, PATH=work + "/bin:" + os.environ["PATH"], FAKE_LOG=work + "/log", FAKE_DIR=work + "/fx", XDG_CACHE_HOME=work + "/cache")
r = subprocess.run([src + "/board-fetch", "--project", "firelink21/phrase41"], capture_output=True, text=True, env=env)
B = json.loads(r.stdout); shutil.rmtree(work)
closed = next(c for c in B["columns"] if c["kind"] == "closed")
h = Harness(src, {"id": "odevvy.gitlab-board", "settingsRevision": 2, "defaultProject": "firelink21/phrase41", "defaultCollapsed": ["open", "research"]})
h.ok("W1 board-fetch, work-item URLs, more than 20 closed: Closed links to all closed issues", len(closed["issues"]) == 20 and closed.get("seeAll") == "https://gitlab.com/firelink21/phrase41/-/issues?state=closed", closed.get("seeAll"))
# --- the board at his size ---------------------------------------------------
h.ev("panel.availableCardHeight = 520")  # the real cap (fittedContentHeight) stays bound
h.ev("root.opened = true"); h.spin(80); h.answer("board", B); h.spin(400)
cls_is = lambda it, n: it.metaObject().className().startswith(n)
bv = h.cls("BoardView"); c = h.ctx_of(bv); e = lambda x: h.ev(x, c, bv)
flick = next(it for it in h.walk() if cls_is(it, "QQuickFlickable") and it.parentItem() == bv)
def inview(it):  # wholly inside the Flickable's visible area
    p = it.mapToItem(flick, QPointF(0, 0)); return it.isVisible() and p.y() >= -0.5 and p.y() + it.height() <= flick.height() + 0.5
head = lambda name: [it for it in h.visible(lambda it: cls_is(it, "BoardText") and it.property("text") == name and flick.isAncestorOf(it))]
foot = lambda: h.visible(lambda it: cls_is(it, "BoardText") and str(it.property("text") or "").startswith("Showing the latest"))
h.ok("W2 a short popup: the card stops at 520 and the board scrolls inside it", h.ev("panel.height") == 520 and e("flick.contentHeight") > flick.height(), [h.ev("panel.height"), e("flick.contentHeight"), flick.height()])
hs = [head(n) for n in ("todo", "approved", "in progress", "review", "Closed")]
h.ok("W3 on open: at the top, every expanded column's header (CLOSED with it) in view", e("flick.contentY") == 0 and all(len(x) == 1 and inview(x[0]) for x in hs), [len(x) for x in hs])
shot(0)
h.ok("W4 the footer is laid out under the last of the 20 cards", len(foot()) == 1 and foot()[0].property("text") == "Showing the latest 20 · See all on GitLab \u2197")
e("flick.contentY = flick.contentHeight - flick.height"); h.spin(150)
h.ok("W5 scrolled to the end: the footer is in view", len(foot()) == 1 and inview(foot()[0]))
shot(1)
h.ev("Quickshell.launched = []"); foot() and h.click(foot()[0])
h.ok("W6 click: opens the closed issues on GitLab", h.launched() == [["omarchy-launch-browser", closed.get("seeAll")]], h.launched())
h.finish()
