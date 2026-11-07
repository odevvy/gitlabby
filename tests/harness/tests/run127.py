# v0.1.27: Settings > Bots edits settings.bots for the project on screen:
# the invite, add (label / column / no owner) with the label picker, remove,
# busy columns; saved at once through persist / updateEntryInline, the rest of
# the JSON byte-stable; the busy row follows live. Edge cases: & in names,
# duplicates, unknown labels/columns, malformed bots, an invalid setting,
# a project switch, keys while typing.
# Usage: run127.py <src> [empty.png list.png adding.png invalid.png]
import sys, os, json, shutil; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *

# v0.1.99: the longer Open links in note pushes Settings > Bots below the fold,
# so scroll the settings Flickable to an item before pointing at it.
_scene0 = Harness.scene
def _into_view(self, it, *a, **k):
    f = it.parentItem() if it is not None else None
    while f is not None and not f.metaObject().className().startswith("QQuickFlickable"): f = f.parentItem()
    if f is not None:
        y = it.mapToItem(f.property("contentItem"), QPointF(0, 0)).y()
        top, h_ = f.property("contentY"), f.height()
        if y < top or y + it.height() > top + h_:
            f.setProperty("contentY", max(0.0, min(y - 20, f.property("contentHeight") - h_)))
            QGuiApplication.processEvents()
    return _scene0(self, it, *a, **k)
Harness.scene = _into_view
pngs = sys.argv[2:6]
P = "firelink21/phrase41"
COLS = [("Open", "open", None), ("research", "label", "#e5e7eb"), ("todo", "label", "#3b82f6"), ("approved", "label", "#dc2626"), ("in progress", "label", "#eab308"), ("review", "label", "#86efac"), ("Closed", "closed", None)]
LC = {"app-ui": "#9ca3af", "api": "#6366f1", "auth-mail": "#14b8a6", "needs-decision": "#f97316", "research": "#e5e7eb", "todo": "#3b82f6", "approved": "#dc2626", "in progress": "#eab308", "review": "#86efac"}
def card(i, labels): return {"iid": i, "title": "Issue %d" % i, "labels": labels, "url": "https://gitlab.com/%s/-/work_items/%d" % (P, i), "createdAt": "2026-10-29T12:00:00Z", "notes": 0, "assignees": []}
ISSUES = {"in progress": [card(40, ["in progress", "auth-mail"])], "review": [card(50, ["review", "api"])], "approved": [card(30, ["approved"])]}
B = {"state": "ready", "project": P, "updatedAt": "2026-10-29T20:10:00Z", "labelColors": {k: {"color": v, "textColor": None} for k, v in LC.items()},
     "boards": [{"id": 7, "name": "Development"}], "board": {"id": 7, "name": "Development"}, "fallback": False, "message": "",
     "columns": [dict({"name": n, "kind": k, "issues": ISSUES.get(n, [])}, **({"listId": i, "color": c} if c else {})) for i, (n, k, c) in enumerate(COLS)]}
LABELS = {"state": "ready", "message": "", "status": ["approved", "in progress", "research", "review", "todo"], "labels": [{"name": k, "color": v, "textColor": None} for k, v in LC.items()]}
P41 = '{"' + P + '":{"busyLists":["approved","in progress","review"],"bots":[{"name":"App UI","label":"app-ui"},{"name":"API Engineer","label":"api"},{"name":"Auth & Mail","label":"auth-mail"},{"name":"Product Lead","label":""},{"name":"Spec QA","list":"review"}]},"other/proj":{"bots":[{"name":"X","label":"x"}],"workingLists":["Doing"],"note":1}}'
cls_is = lambda it, n: it.metaObject().className().startswith(n)
ALL = []  # several harnesses (one per starting setting); one total at the end
def start(bots, shot=None):
    global h, sec, sev
    s = {"id": "odevvy.gitlabby", "settingsRevision": 2, "defaultProject": P, "defaultCollapsed": ["open", "research"]}
    if bots is not None: s["bots"] = bots
    h = Harness(sys.argv[1], s)
    h.ev("panel.availableCardHeight = 1000"); h.ev("panel.contentWidth = 790")  # his popup: ~820 wide
    h.ev("root.opened = true"); h.spin(60); h.answer("board", B); h.spin(80)
    h.ev("panel.contentHeight = 1000")  # v0.1.29: the section is taller; keep it all in view so clicks land
    h.ev("root.showView('settings')"); h.spin(60); h.answer("whoami", {"state": "ready", "message": "", "user": "o_devvy"}); h.spin(60)
    sec = h.cls("BotsSection"); c = h.ctx_of(sec); sev = lambda code: h.ev(code, c, sec)
writes = lambda: h.ev("root.bar.shell.writes") or []
# The last write's bots, stringified in JS: key order as saved (a QVariantMap would sort it).
saved = lambda: h.ev("(function(){ var w = root.bar.shell.writes; return w.length ? JSON.stringify(w[w.length - 1].bots) : null })()")
texts = lambda: [it.property("text") for it in h.visible(lambda it: cls_is(it, "BoardText")) if it.property("text")]
pill = lambda label: [it for it in h.visible(lambda it: it.property("clickable") is not None and not cls_is(it, "LabelChip") and it.property("label") == label) if sec.isAncestorOf(it)]
fpill = lambda label: [it for it in pill(label) if sev("form").isAncestorOf(it)]  # in the new-bot form
bpill = lambda label: [it for it in pill(label) if sev("busyRow").isAncestorOf(it)]  # a busy column
chip = lambda label: [it for it in h.visible(lambda it: cls_is(it, "LabelChip") and it.property("label") == label) if sec.isAncestorOf(it)]
xs = lambda: sorted([it for it in h.visible(lambda it: cls_is(it, "GlyphButton")) if sec.isAncestorOf(it)], key=lambda it: it.mapToScene(QPointF(0, 0)).y())  # top to bottom
botsRow = lambda: [s["name"] + ":" + s["state"] for s in (h.ev("root.botStates") or [])]
def ok(name, cond, extra=""): h.ok(name, cond, extra)
def finish():
    loops = [w for w in h.warnings if "oop" in w]
    h.ok("Z no binding-loop warnings", not loops, loops); h.ok("Z no QML warnings", not h.warnings, h.warnings[:3])
    ALL.extend(h.results); shutil.rmtree(h.dir, ignore_errors=True)

# --- empty -> add -> list ---------------------------------------------------------
start(None)
ok("E1 no bots: the invite, no list, no busy columns, no busy row", sev("invite.visible") and not sev("pane.visible") and not sev("busyRow.visible") and botsRow() == []
   and any(t.startswith("Show who is busy on " + P) for t in texts()))
if len(pngs) > 0: h.grab_card(pngs[0])
h.click(sev("invite"))
ok("A1 the invite opens the new-bot form, name focused, the labels load (spinner)", sev("adding") and sev("nameField.activeFocus") and bool(h.running("labels")) and "Loading labels…" in texts()
   and writes() == [])
h.key(Qt.Key_S, "s"); h.key(Qt.Key_Question, "?")
ok("A2 typing a name: s and ? go into the field, not to the panel", h.ev("root.view") == "settings" and sev("nameField.text") == "s?")
h.answer("labels", LABELS); h.spin(60)
opts = sev("options.map(function(l){ return l.name })")
ok("A3 the picker offers owner labels only (no board column or status label)", opts == ["app-ui", "api", "auth-mail", "needs-decision"], opts)
sev("nameField.text = 'Auth & Mail'"); h.spin(30)
ok("A4 no pick yet: Add is off", not sev("addButton.enabled") and sev("addButton.label") == "Add Auth & Mail")
h.click(chip("+ auth-mail")[0] if chip("+ auth-mail") else chip("auth-mail")[0])
ok("A5 a label picked: checked, Add on", len(chip("\uf00c  auth-mail")) == 1 and sev("addButton.enabled"))
h.click(sev("addButton"))
ok("A6 Add saves the first bot with every label column busy; the form closes", saved() == '{"' + P + '":{"busyLists":["research","todo","approved","in progress","review"],"bots":[{"name":"Auth & Mail","label":"auth-mail"}]}}'
   and not sev("adding"), saved())
ok("A7 the list row says it plainly, & and all; the busy row under the header follows at once", "Auth & Mail" in texts() and "cards labelled" in texts() and botsRow() == ["Auth & Mail:working"], botsRow())
h.click(bpill("research")[0])
ok("B1 a busy column toggles off and saves; names stay as the board spells them", json.loads(saved())[P]["busyLists"] == ["todo", "approved", "in progress", "review"])
h.click(bpill("in progress")[0])
ok("B2 the busy row follows the busy columns live", botsRow() == ["Auth & Mail:idle"], botsRow())
h.click(bpill("in progress")[0])
h.click(sev("addLink")); sev("nameField.text = 'Spec QA'"); h.click(fpill("every card in a column")[0]); h.click(fpill("review")[0]); h.click(sev("addButton"))
ok("C1 a column bot: every card in review", json.loads(saved())[P]["bots"][-1] == {"name": "Spec QA", "list": "review"} and "every card in" in texts() and "Spec QA:working" in botsRow(), botsRow())
h.click(sev("addLink")); h.answer("labels", LABELS); sev("nameField.text = ' spec qa '"); h.spin(30); h.click(chip("+ api")[0] if chip("+ api") else chip("api")[0])
ok("C2 a name taken in any case: said in red, Add off", "There's already a bot named spec qa." in texts() and not sev("addButton.enabled"))
sev("nameField.text = 'Product Lead'"); h.click(pill("cards no bot owns")[0]); h.click(sev("addButton"))
ok("C3 a no-owner bot saves label \"\"; the list says 'cards no other bot owns'", json.loads(saved())[P]["bots"][-1] == {"name": "Product Lead", "label": ""} and "cards no other bot owns" in texts())
h.click(sev("addLink")); h.spin(30)
opts = sev("options.map(function(l){ return l.name })")
ok("C4 next time: 'cards no bot owns' is shown but off (v0.1.29), and auth-mail (taken) is not offered", len(pill("cards no bot owns")) == 1 and not pill("cards no bot owns")[0].property("enabled") and opts == ["app-ui", "api", "needs-decision"], opts)
h.key(Qt.Key_Escape)
ok("C5 Esc in the name field closes the form, stays in Settings", not sev("adding") and h.ev("root.view") == "settings")
h.click(sev("addLink")); h.click(pill("cards with a label")[0]); h.spin(30)
h.ev("keyCatcher.forceActiveFocus()"); h.spin(30); h.key(Qt.Key_Escape)
ok("C6 Esc with the field not focused also closes the form first", not sev("adding") and h.ev("root.view") == "settings")
n0 = len(writes())
for i in range(3): h.click(xs()[0])
ok("R1 x removes at once, saving each time", len(writes()) == n0 + 3)
ok("R2 the last bot out: the project's entry goes, the invite is back, no busy row", saved() == "{}" and sev("invite.visible") and not sev("pane.visible") and botsRow() == [], saved())
finish()

# --- phrase41's JSON round-trips -------------------------------------------------
start(json.loads(P41))
h.answer("labels", LABELS); h.spin(60)
ok("J1 phrase41's 5 bots listed in order; nothing written by opening", [sev("bots[%d].name" % i) for i in range(5)] == ["App UI", "API Engineer", "Auth & Mail", "Product Lead", "Spec QA"] and writes() == []
   and len(xs()) == 5 and "not a label here" not in texts() and "not a column here" not in texts())
if len(pngs) > 1: h.grab_card(pngs[1])
h.click(bpill("todo")[0]); h.click(bpill("todo")[0])
ok("J2 a busy column on and off: byte-stable", saved() == P41, saved())
h.click(sev("addLink")); sev("nameField.text = 'Decider'"); h.spin(30)
opts = sev("options.map(function(l){ return l.name })")
h.click(chip("needs-decision")[0]); h.spin(30)
ok("J3 the picker: only labels no bot has", opts == ["needs-decision"], opts)
if len(pngs) > 2: h.grab_card(pngs[2])
h.click(sev("addButton"))
ok("J4 add: only the new bot appended", saved() == P41.replace('{"name":"Spec QA","list":"review"}]', '{"name":"Spec QA","list":"review"},{"name":"Decider","label":"needs-decision"}]'))
h.click(xs()[5])
ok("J5 remove it again: byte-stable, other projects and keys untouched", saved() == P41, saved())
finish()

# --- unknown labels and columns, malformed bots -----------------------------------
start({P: {"busyLists": ["review", "Doing"], "bots": [{"name": "Gone", "label": "old-label"}, {"name": "Q", "list": "qa"}, {"name": ""}, {"name": "A", "label": "api"}]}})
ok("U1 settings with bots opens the labels", bool(h.running("labels")))
h.answer("labels", LABELS); h.spin(60)
ok("U2 a label the project lacks, a column not on this board: kept, flagged", texts().count("not a label here") == 1 and texts().count("not a column here") == 1 and writes() == [])
ok("U3 a malformed bot: listed as ignored", "ignored: needs a name and a label or a column" in texts() and h.ev("root.botStates").__len__() == 3)
h.click(xs()[2])
ok("U4 x removes it; the rest (and the Doing busy list from another board) stay", json.loads(saved()) == {P: {"busyLists": ["review", "Doing"], "bots": [{"name": "Gone", "label": "old-label"}, {"name": "Q", "list": "qa"}, {"name": "A", "label": "api"}]}}, saved())
finish()

# --- an invalid setting ----------------------------------------------------------
start(P41)  # bar set without --json: the JSON text as a string
ok("I1 a string setting: said in red, the invite offered, nothing written", "The bots setting isn't a JSON object (set without --json?). Adding a bot here replaces it." in texts()
   and sev("invite.visible") and writes() == [] and botsRow() == [])
if len(pngs) > 3: h.grab_card(pngs[3])
h.click(sev("invite")); h.answer("labels", LABELS); h.spin(60); sev("nameField.text = 'API'"); h.click(chip("api")[0]); h.click(sev("addButton"))
ok("I2 adding replaces it with a proper object", json.loads(saved()) == {P: {"busyLists": ["research", "todo", "approved", "in progress", "review"], "bots": [{"name": "API", "label": "api"}]}}
   and "The bots setting isn't a JSON object (set without --json?). Adding a bot here replaces it." not in texts())
finish()
start({P: {"bots": "x"}, "k": 1})
ok("I3 a malformed entry for this project: said in red", "The bots entry for " + P + " isn't valid. Adding a bot here replaces it." in texts() and sev("invite.visible"))
finish()

# --- a project switch ------------------------------------------------------------
start(json.loads(P41))
h.click(sev("addLink")); sev("nameField.text = 'Half done'"); h.spin(30)
h.ev("root.project = 'other/proj'"); h.spin(80)
ok("P1 switching project closes the form; the section shows the new project's bots", not sev("adding") and sev("bots.length") == 1 and sev("bots[0].name") == "X" and sev("listTitle.visible") and sev("listTitle.text") == "On other/proj")
h.ev("root.project = 'new/proj'"); h.spin(80)
ok("P2 a project without bots: the invite, phrase41 untouched", sev("invite.visible") and writes() == [])
finish()
print("passed", sum(1 for _, c in ALL if c), "failed", sum(1 for _, c in ALL if not c))
sys.exit(0 if all(c for _, c in ALL) else 1)
