# R2-03: a pasted 2,000,000-character log and a long thread go through the real
# board-fetch (fake glab) into the issue view: each comment shows its first
# 4,000 characters and says so, with a link to it; the thread its newest 100,000
# characters, with the line that older ones are on GitLab. Links are host-checked.
import sys, os, json, subprocess, tempfile, shutil, atexit
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from fixtures import BOARD
SRC = sys.argv[1]
def fetch(notes):
    w = tempfile.mkdtemp(prefix="ogb-h223-"); atexit.register(shutil.rmtree, w, True)
    os.makedirs(w + "/bin"); os.makedirs(w + "/fx"); shutil.copy(SRC + "/tests/fake-glab", w + "/bin/glab")
    open(w + "/fx/project.json", "w").write(json.dumps({"namespace": {"kind": "user", "full_path": "someone"}}))
    open(w + "/fx/notes.json", "w").write(json.dumps(notes))
    env = dict(os.environ, PATH=w + "/bin:" + os.environ["PATH"], FAKE_DIR=w + "/fx", FAKE_LOG=w + "/log", XDG_CACHE_HOME=w + "/cache", TMPDIR=w)
    env.pop("XDG_RUNTIME_DIR", None)
    return json.loads(subprocess.run([SRC + "/board-fetch", "notes", "--project", "group/app", "--iid", "2"], env=env, capture_output=True, text=True, timeout=60).stdout)
note = lambda i, body, who="bob": {"id": i, "body": body, "system": False, "created_at": "2026-11-08T21:00:00Z", "author": {"username": who, "name": who}}
LOG = "".join("2026-11-08T21:%02d:%02d build step %06d: compiling module.qml ... ok\n" % (i // 60 % 60, i % 60, i) for i in range(31250))[:2000000]
ISSUE = {"iid": 2, "title": "Second issue", "state": "opened", "labels": [], "url": "https://gitlab.com/group/app/-/issues/2", "description": "The CI log is in the comments.", "author": "ann", "assignees": []}
h = Harness(SRC, {"id": "odevvy.gitlabby", "settingsRevision": 2, "defaultProject": "group/app", "openLinks": "app", "showAvatars": False})
trimmed = lambda: h.visible(lambda x: x.objectName() == "noteTrimmed")
more = lambda: h.visible(lambda x: x.objectName() == "notesMore")
def reveal(item):
    f = item.parentItem()
    while f is not None and not f.metaObject().className().startswith("QQuickFlickable"): f = f.parentItem()
    if f is not None:
        y = item.mapToItem(f.property("contentItem"), QPointF(0, 0)).y()
        f.setProperty("contentY", max(0, min(y - 100, f.property("contentHeight") - f.property("height")))); h.spin(80)

def launched_by(item):
    reveal(item); n = len(h.launched()); h.click(item.childItems()[0]); return h.launched()[n:]
def show(notes, issue=ISSUE):
    h.ev("root.opened = true; root.showView('board')"); h.spin(40); h.answer("board", BOARD)
    h.ev("root.openIssue(root.columns[1].issues[0])"); h.spin(60)
    h.answer("issue", {"state": "ready", "message": "", "issue": issue}); h.answer("notes", fetch(notes)); h.spin(300)
show([note(3, "Thanks, looking."), note(2, LOG, "ci-bot"), note(1, "Build broke again, log below.")])
t = trimmed()
h.ok("the 2,000,000-character log: one trimmed line, in the mock's words", [x.property("text") for x in t] == ["Trimmed: first 4,000 of 2,000,000 characters · Read it all on GitLab ↗"], [x.property("text") for x in t])
kept = h.ev("issueView.notes.map(function(n) { return n.body.length })")
h.ok("its body is cut at a line break under 4,000; the short ones are whole", kept[0] == 29 and kept[2] == 16 and 3900 < kept[1] <= 4000 and h.ev("issueView.notes[1].body").endswith("ok") and len(t) == 1, kept)
h.ok("a short thread has no older-comments line", not more())
got = launched_by(t[0])
h.ok("Read it all opens that comment on GitLab", got == [["omarchy-launch-webapp", "https://gitlab.com/group/app/-/issues/2#note_2"]], got)
show([note(40 - i, "%d " % (40 - i) + "a" * 3990) for i in range(40)])
ids = h.ev("issueView.notes.map(function(n) { return n.id })")
h.ok("40 comments of ~4,000: the newest 25 (100,000 characters), oldest first", ids == list(range(16, 41)) and sum(h.ev("issueView.notes.map(function(n) { return n.body.length })")) <= 100000, ids)
h.ok("... and the line says older ones are on GitLab", [x.property("text") for x in more()] == ["Showing the latest 25 comments, up to 100,000 characters. Older ones are on GitLab ↗"], [x.property("text") for x in more()])
got = launched_by(more()[0])
h.ok("the line opens the issue", got == [["omarchy-launch-webapp", "https://gitlab.com/group/app/-/issues/2"]], got)
show([note(2, LOG, "ci-bot")] + [note(1, "x")] * 100, dict(ISSUE, url="https://outside.invalid/group/app/-/issues/2"))
h.ok("a full page, not the character budget: no characters clause", [x.property("text") for x in more()] == ["Showing the latest 100 comments. Older ones are on GitLab ↗"], [x.property("text") for x in more()])
h.ok("an off-host issue: neither link opens anything (0.1.117 host check)", len(trimmed()) == 1 and len(more()) == 1 and launched_by(trimmed()[0]) == [] and launched_by(more()[0]) == [])
show([])
h.ok("no comments: the line is not a link", [x.property("text") for x in more()] == ["No comments yet."] and launched_by(more()[0]) == [], [x.property("text") for x in more()])
show([note(40 - i, "a" * 4000) for i in range(40)])
h.ev("root.openIssue(root.columns[0].issues[0])"); h.spin(60)
h.ok("another issue starts without the flag", h.ev("issueView.budgeted") is False)
h.ev("root.openIssue(root.columns[1].issues[0])"); h.spin(60)
h.ok("... and says so again from the session's saved thread", [x.property("text") for x in more()] == ["Showing the latest 25 comments, up to 100,000 characters. Older ones are on GitLab ↗"], [x.property("text") for x in more()])
h.ev("issueView.budgeted = true; issueView.forgetAccount()")
h.ok("signed out: the flag goes with the thread", h.ev("issueView.budgeted") is False and h.ev("issueView.notes.length") == 0)
sys.exit(h.finish())
