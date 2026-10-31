# v0.1.28: a capped count says so. Closed holds the latest 20; with more on
# GitLab its count reads "20+" on the collapsed strip, on the expanded header
# and in the summary pill. board-fetch asks for 21 to know (capped: true), so
# exactly 20 still reads "20". Open and label columns read every open issue,
# so their counts stay plain. End to end: the real board-fetch (fake glab,
# phrase41-shaped like the report) feeds the board.
# Also: the Settings new-bot form wraps (a Flow), so with a long name every
# "is busy with" choice stays inside the section at his popup width and narrower.
# Usage: run128.py <src> [collapsed.png expanded.png exact20.png add-form.png add-form-narrow.png]
import sys, os, json, subprocess, tempfile, shutil; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
src = sys.argv[1]; pngs = sys.argv[2:7]
shot = lambda i: len(pngs) > i and h.grab_card(pngs[i])
U = "https://gitlab.com/firelink21/phrase41/-/work_items/"
def iss(i, state, labels): return {"iid": i, "title": "Issue %d" % i, "state": state, "labels": labels, "web_url": U + str(i), "created_at": "2026-10-28T12:00:00Z", "user_notes_count": 0, "assignees": []}
lists = [{"id": n, "position": n, "label": {"name": l, "color": c}} for n, (l, c) in enumerate([("research", "#ffffff"), ("todo", "#3b82f6"), ("approved", "#dc2626"), ("in progress", "#eab308"), ("review", "#86efac")])]
def fetch(nclosed):
    work = tempfile.mkdtemp(prefix="ogb-128-"); os.makedirs(work + "/bin"); os.makedirs(work + "/fx")
    shutil.copy(src + "/tests/fake-glab", work + "/bin/glab")
    with open(work + "/bin/timeout", "w") as f: f.write('#!/usr/bin/env bash\nshift 3; exec "$@"\n')
    os.chmod(work + "/bin/timeout", 0o755)
    fx = {"boards": [{"id": 7, "name": "Development", "hide_backlog_list": False, "hide_closed_list": False, "labels": [], "milestone": None, "assignee": None, "lists": lists}],
          "open": [[iss(i, "opened", ["research"]) for i in range(1, 6)]],
          "closed": [iss(200 - i, "closed", ["api"]) for i in range(nclosed)]}  # fake glab returns them all; board-fetch keeps 20
    for k, v in fx.items():
        with open(work + "/fx/%s.json" % k, "w") as f: f.write("\n".join(json.dumps(x) for x in v) if k == "open" else json.dumps(v))
    env = dict(os.environ, PATH=work + "/bin:" + os.environ["PATH"], FAKE_LOG=work + "/log", FAKE_DIR=work + "/fx", XDG_CACHE_HOME=work + "/cache")
    r = subprocess.run([src + "/board-fetch", "--project", "firelink21/phrase41"], capture_output=True, text=True, env=env)
    shutil.rmtree(work); return json.loads(r.stdout)
MORE, EXACT = fetch(35), fetch(20)
cm = next(c for c in MORE["columns"] if c["kind"] == "closed"); ce = next(c for c in EXACT["columns"] if c["kind"] == "closed")
h = Harness(src, {"id": "odevvy.gitlab-board", "settingsRevision": 2, "defaultProject": "firelink21/phrase41", "defaultCollapsed": ["open", "research", "closed"]})
h.ok("C0 board-fetch: 35 closed on GitLab -> the latest 20, capped; exactly 20 -> not capped",
     len(cm["issues"]) == 20 and cm.get("capped") is True and len(ce["issues"]) == 20 and "capped" not in ce, [len(cm["issues"]), cm.get("capped"), ce.get("capped")])
h.ev("root.opened = true"); h.spin(80); h.answer("board", MORE); h.spin(400)
h.ev("root.columnChips = true"); h.spin(200)  # v0.1.52: the summary row opens from the header
cls_is = lambda it, n: it.metaObject().className().startswith(n)
def labels(pred):  # left to right, top to bottom on screen
    its = h.visible(lambda it: cls_is(it, "Pill") and it.parentItem() is not None and pred(it))
    return [str(it.property("label")) for it in sorted(its, key=lambda it: (round(it.mapToScene(QPointF(0, 0)).y() / 8), it.mapToScene(QPointF(0, 0)).x()))]
bv = h.cls("BoardView")
summary = lambda: labels(lambda it: cls_is(it.parentItem(), "QQuickFlow"))
h.ok("C1 summary row: 'Closed 20+'; the others plain", summary() == ["Open 0", "research 5", "todo 0", "approved 0", "in progress 0", "review 0", "Closed 20+"], summary())
# Strip and column counts: plain numbers (stripCount, columnCount) since v0.1.52,
# pills before; left to right.
counts = lambda name, pills: [str(it.property("text")) for it in sorted(h.visible(lambda it: cls_is(it, "BoardText") and it.objectName() == name), key=lambda it: it.mapToScene(QPointF(0, 0)).x())] or labels(pills)
strips = lambda: counts("stripCount", lambda it: it.property("y") > 0 and not cls_is(it.parentItem(), "QQuickFlow") and not cls_is(it.parentItem(), "QQuickRow"))
h.ok("C2 collapsed strips: Closed reads '20+', Open and research plain", strips() == ["0", "5", "20+"], strips())
heads = lambda: counts("columnCount", lambda it: cls_is(it.parentItem(), "QQuickRow"))
h.ok("C3 expanded label columns: plain counts", heads() == ["0", "0", "0", "0"], heads())
QTest.mouseMove(h.win, QPoint(1, 1)); shot(0)
h.ev("root.toggleCollapsed('Closed')"); h.spin(300)
h.ok("C4 Closed expanded: its header reads '20+'", heads() == ["0", "0", "0", "0", "20+"], heads())
foot = h.visible(lambda it: cls_is(it, "BoardText") and str(it.property("text") or "").startswith("Showing the latest"))
h.ok("C5 the footer still says the latest 20", len(foot) == 1 and foot[0].property("text") == "Showing the latest 20 · See all on GitLab \u2197")
QTest.mouseMove(h.win, QPoint(1, 1)); shot(1)
h.ev("root.refresh()"); h.answer("board", EXACT); h.spin(300)
foot = h.visible(lambda it: cls_is(it, "BoardText") and str(it.property("text") or "").startswith("Showing the latest"))
h.ok("C6 exactly 20 closed: '20' and 'Closed 20', no footer", heads()[-1:] == ["20"] and summary()[-1:] == ["Closed 20"] and not foot, [heads(), summary(), len(foot)])
h.ev("root.toggleCollapsed('Closed')"); h.spin(300)
h.ok("C7 exactly 20, collapsed: the strip reads '20'", strips() == ["0", "5", "20"], strips())
QTest.mouseMove(h.win, QPoint(1, 1)); shot(2)
# --- the new-bot form wraps ---------------------------------------------------
h.ev("panel.availableCardHeight = 1000")
h.ev("root.showView('settings')"); h.spin(60); h.answer("whoami", {"state": "ready", "message": "", "user": "o_devvy"}); h.spin(60)
sec = h.cls("BotsSection"); sc = h.ctx_of(sec); sev = lambda code: h.ev(code, sc, sec)
h.click(sev("invite")); h.answer("labels", {"state": "ready", "message": "", "status": [], "labels": [{"name": "needs-decision", "color": "#dc2626", "textColor": None}]}); h.spin(60)
sev("nameField.text = 'Product Lead'"); h.spin(60)
CHOICES = ("cards with a label", "every card in a column", "cards no bot owns")
def inside(width):
    h.ev("panel.contentWidth = %d" % width); h.spin(250)
    form = sev("form"); fx0 = form.mapToScene(QPointF(0, 0)).x(); fx1 = fx0 + form.width()
    sx1 = sec.mapToScene(QPointF(0, 0)).x() + sec.width()
    got = {}
    for it in h.visible(lambda it: it.property("clickable") is not None and str(it.property("label")) in CHOICES and form.isAncestorOf(it)):
        x0 = it.mapToScene(QPointF(0, 0)).x(); got[str(it.property("label"))] = (round(x0), round(x0 + it.width()))
    ok = set(got) == set(CHOICES) and all(a >= fx0 - 0.5 and b <= min(fx1, sx1) + 0.5 for a, b in got.values())
    return ok, [round(fx0), round(fx1), round(sx1), got]
r = inside(790); h.ok("F1 popup ~790 wide, name 'Product Lead': all three choices inside the form", r[0], r[1])
r = inside(560); h.ok("F2 popup 560 wide: they wrap, still all inside", r[0], r[1])
QTest.mouseMove(h.win, QPoint(1, 1)); shot(4)
r = inside(790)
QTest.mouseMove(h.win, QPoint(1, 1)); shot(3)
h.finish()
