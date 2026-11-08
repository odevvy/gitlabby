# GLB-02: 1,200 open issues go through the real board-fetch (fake glab) into the
# popup: at most 500 cards, and one note above the header that opens the board.
import sys, os, json, subprocess, tempfile, shutil, atexit
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
SRC = sys.argv[1]
def fetch(n, url="https://gitlab.com/group/app/-/issues/", boards=True):
    w = tempfile.mkdtemp(prefix="ogb-h219-"); atexit.register(shutil.rmtree, w, True)
    os.makedirs(w + "/bin"); os.makedirs(w + "/fx"); shutil.copy(SRC + "/tests/fake-glab", w + "/bin/glab")
    fx = {"project": {"namespace": {"kind": "user", "full_path": "someone"}}, "closed": [],
          "boards": [{"id": 7, "name": "Dev", "hide_backlog_list": False, "hide_closed_list": False, "labels": [], "milestone": None, "assignee": None,
                      "lists": [{"id": 1, "position": 0, "label": {"name": "Doing"}}]}] if boards else [],
          "open": [{"iid": i + 1, "title": "Issue %d" % (i + 1), "state": "opened", "labels": ["Doing"] if i % 2 else [], "web_url": url + str(i + 1)} for i in range(n)]}
    for k, v in fx.items(): open(w + "/fx/" + k + ".json", "w").write(json.dumps(v))
    env = dict(os.environ, PATH=w + "/bin:" + os.environ["PATH"], FAKE_DIR=w + "/fx", FAKE_LOG=w + "/log", XDG_CACHE_HOME=w + "/cache", TMPDIR=w)
    env.pop("XDG_RUNTIME_DIR", None)
    out = subprocess.run([SRC + "/board-fetch", "--project", "group/app"], env=env, capture_output=True, text=True, timeout=60).stdout
    return json.loads(out)
cards = lambda: len([i for i in h.walk() if i.objectName() == "cardIid"])
note = lambda: h.visible(lambda x: x.objectName() == "capNoteText")
link = lambda: h.visible(lambda x: x.objectName() == "capNoteLink")
def via_link():  # clicks View all when it is there; what it launched
    n = len(h.launched()); l = link()
    if l: h.click(l[0])
    return h.launched()[n:]
def header_y(): return h.cls("BoardHeader").mapToScene(QPointF(0, 0)).y()

h = Harness(SRC, {"id": "odevvy.gitlabby", "settingsRevision": 2, "defaultProject": "group/app", "openLinks": "app", "defaultCollapsed": []})
h.ev("root.opened = true"); h.spin(50)
small = fetch(40)
h.answer("board", small); h.spin(150)
h.ok("below the cap: no note, the board as before", small.get("openCapped") is None and not note() and cards() == 40)
y0 = header_y()
h.ok("below the cap: the header sits at the top of the popup, no space kept", y0 == h.cls("BoardKeys").mapToScene(QPointF(0, 0)).y(), (y0, h.cls("BoardKeys").mapToScene(QPointF(0, 0)).y()))
big = fetch(1200)
h.ok("board-fetch keeps 500 of 1,200 open issues and links to the board", sum(len(c["issues"]) for c in big["columns"]) == 500 and big["openCapped"] is True and big["openSeeAll"] == "https://gitlab.com/group/app/-/boards/7")
h.ev("root.refresh()"); h.answer("board", big); h.spin(300)
h.ok("1,200 open issues: 500 cards in the popup, never more", cards() == 500, cards())
h.ok("the note reads as mocked", len(note()) == 1 and len(link()) == 1 and note()[0].property("text") + link()[0].property("text") == "First 500 open issues shown · View all on GitLab ↗")
h.ok("the note sits above the header", len(note()) == 1 and note()[0].mapToScene(QPointF(0, 0)).y() < header_y() and header_y() > y0)
got = via_link()
h.ok("View all opens the board on GitLab through openUrl", got == [["omarchy-launch-webapp", "https://gitlab.com/group/app/-/boards/7"]], got)
h.ev("root.opened = true"); h.spin(80); y1 = header_y(); h.ev("root.showView('mrs')"); h.spin(80)
h.ok("the note stays in every view, so the header and its tabs never move", len(note()) == 1 and header_y() == y1)
h.ev("root.showView('board')"); h.spin(40)
nob = fetch(501, boards=False)
h.ev("root.opened = true; root.refresh()"); h.answer("board", nob); h.spin(200)
got = via_link()
h.ok("no board: the link opens the project's open issues", got == [["omarchy-launch-webapp", "https://gitlab.com/group/app/-/issues"]], got)
off = dict(big, openSeeAll="https://outside.invalid/group/app/-/boards/7")
h.ev("root.opened = true; root.refresh()"); h.answer("board", off); h.spin(200)
h.ok("an off-host link from the answer is shown but opens nothing (0.1.117 host check)", len(link()) == 1 and via_link() == [])
plain = fetch(501, url="http://gitlab.com/group/app/-/issues/")
h.ev("root.refresh()"); h.answer("board", plain); h.spin(200)
h.ok("capped with no usable link: the count line alone", len(note()) == 1 and not link())
h.ev("root.refresh()"); h.answer("board", small); h.spin(200)
h.ok("back under the cap: the note goes and the header returns", not note() and header_y() == y0 and cards() == 40)
sys.exit(h.finish())
