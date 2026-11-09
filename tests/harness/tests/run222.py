# R2-02: label lists copy issues, so 460 issues can be 620 cards. They go through
# the real board-fetch (fake glab) into the popup: at most 500 cards, the cut list
# says "Showing N of M" and links to itself, and the note above the header says why.
import sys, os, json, subprocess, tempfile, shutil, atexit
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
SRC = sys.argv[1]
LISTS = [{"id": 1, "position": 0, "label": {"name": "to do"}}, {"id": 2, "position": 1, "label": {"name": "doing"}}, {"id": 3, "position": 2, "label": {"name": "review"}}]
def fetch(spec):
    w = tempfile.mkdtemp(prefix="ogb-h222-"); atexit.register(shutil.rmtree, w, True)
    os.makedirs(w + "/bin"); os.makedirs(w + "/fx"); shutil.copy(SRC + "/tests/fake-glab", w + "/bin/glab")
    fx = {"project": {"namespace": {"kind": "user", "full_path": "someone"}}, "closed": [],
          "boards": [{"id": 7, "name": "Dev", "hide_backlog_list": False, "hide_closed_list": False, "labels": [], "milestone": None, "assignee": None, "lists": LISTS}],
          "open": [{"iid": i, "title": "Issue %d" % i, "state": "opened", "labels": l, "web_url": "https://gitlab.com/group/app/-/issues/%d" % i} for a, b, l in spec for i in range(a, b + 1)]}
    for k, v in fx.items(): open(w + "/fx/" + k + ".json", "w").write(json.dumps(v))
    env = dict(os.environ, PATH=w + "/bin:" + os.environ["PATH"], FAKE_DIR=w + "/fx", FAKE_LOG=w + "/log", XDG_CACHE_HOME=w + "/cache", TMPDIR=w)
    env.pop("XDG_RUNTIME_DIR", None)
    return json.loads(subprocess.run([SRC + "/board-fetch", "--project", "group/app"], env=env, capture_output=True, text=True, timeout=60).stdout)
cards = lambda: len([i for i in h.walk() if i.objectName() == "cardIid"])
note = lambda: [x.property("text") for x in h.visible(lambda x: x.objectName() == "capNoteText")]
link = lambda: h.visible(lambda x: x.objectName() == "capNoteLink")
footers = lambda: sorted(x.property("text") for x in h.walk() if x.isVisible() and str(x.property("text") or "").startswith("Showing "))
def launched_by(item):
    n = len(h.launched()); h.click(item); return h.launched()[n:]
h = Harness(SRC, {"id": "odevvy.gitlabby", "settingsRevision": 2, "defaultProject": "group/app", "openLinks": "app", "defaultCollapsed": []})
h.ev("root.opened = true"); h.spin(50)
TRIM = [(1, 40, []), (41, 200, ["to do", "doing"]), (201, 400, ["to do"]), (401, 460, ["review"])]
h.answer("board", fetch(TRIM)); h.spin(300)
h.ok("620 cards from 460 issues: 500 in the popup", cards() == 500, cards())
h.ok("only the cut list says so, in the Closed footer's words", footers() == ["Showing 240 of 360 · See all on GitLab ↗"], footers())
h.ok("the note says the board was trimmed, with its link", note() == ["Board trimmed to 500 cards"] and len(link()) == 1, note())
for f in h.walk():
    if f.metaObject().className().startswith("QQuickFlickable") and f.isVisible(): f.setProperty("contentY", max(0, f.property("contentHeight") - f.property("height")))
h.spin(150)
foot = next(x for x in h.walk() if x.isVisible() and str(x.property("text") or "").startswith("Showing 240"))
got = launched_by(foot.childItems()[0])
h.ok("the footer opens that list's open issues on GitLab, host-checked", got == [["omarchy-launch-webapp", "https://gitlab.com/group/app/-/issues?label_name%5B%5D=to%20do"]], got)
h.ev("root.opened = true"); h.spin(60)
got = launched_by(link()[0])
h.ok("View all opens the board", got == [["omarchy-launch-webapp", "https://gitlab.com/group/app/-/boards/7"]], got)
h.ev("root.opened = true; root.refresh()"); h.answer("board", fetch([(1, 300, []), (301, 600, ["to do", "doing"])])); h.spin(300)
h.ok("issues capped and cards trimmed: both in one note", note() == ["First 500 open issues shown, trimmed to 500 cards"] and cards() == 498, (note(), cards()))
h.ok("... and every cut list, Open too, says its count", footers() == ["Showing 166 of 200 · See all on GitLab ↗"] * 2 + ["Showing 166 of 300 · See all on GitLab ↗"], footers())
h.ev("root.refresh()"); h.answer("board", fetch([(1, 40, []), (41, 200, ["to do", "doing"]), (201, 280, ["to do"]), (401, 460, ["review"])])); h.spin(300)
h.ok("exactly 500 cards: no note, no footer, every card", not note() and footers() == [] and cards() == 500, (note(), footers(), cards()))
h.ev("root.refresh()"); h.answer("board", dict(fetch(TRIM), openSeeAll="https://outside.invalid/b")); h.spin(200)
h.ok("an off-host board link opens nothing (0.1.117 host check)", len(link()) == 1 and launched_by(link()[0]) == [])
sys.exit(h.finish())
