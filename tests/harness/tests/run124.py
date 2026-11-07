# v0.1.24: the settings' account section is one row, no frame: who is signed in
# on the left, Sign out as a text action on the right; asking swaps the same row
# to the question with Yes / Cancel. The issue view: Edit labels and Close
# issue are text actions on the state + labels row and never move; the label
# filter is off until the labels load; the comment hint never runs under Post.
# Closed holds the latest 20 (board-fetch's cap): a full one says so and links to
# the rest on GitLab (seeAll).
# Usage: run124.py <src> [settings.png confirm.png issue.png issue-loading.png issue-edit.png comment.png closed-footer.png]
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from fixtures import BOARD
pngs = sys.argv[2:9]
shot = lambda i: len(pngs) > i and h.grab_card(pngs[i])
h = Harness(sys.argv[1], {"id": "odevvy.gitlabby", "settingsRevision": 2, "defaultProject": "group/app", "defaultCollapsed": ["closed", "research", "open"], "boardStates": {}, "refreshIntervalSec": 60})
h.ev("panel.contentHeight = Qt.binding(function() { return keyCatcher.implicitHeight + panel.padding * 2 + 4 })")
cls_is = lambda it, n: it.metaObject().className().startswith(n)
texts = lambda: [it.property("text") for it in h.visible(lambda it: cls_is(it, "BoardText")) if it.property("text")]
button = lambda label: h.visible(lambda it: cls_is(it, "ActionButton") and it.property("label") == label)
link = lambda: h.visible(lambda it: cls_is(it, "BoardText") and it.property("text") == "Sign out")
same = lambda a, b: abs(a.redF() - b.redF()) < 0.01 and abs(a.greenF() - b.greenF()) < 0.01 and abs(a.blueF() - b.blueF()) < 0.01
tips = lambda: [c for it in h.walk() for c in it.children() if c.metaObject().className().startswith("PanelToolTip")]
def box(it):
    p = it.mapToScene(QPointF(0, 0)); return p.x(), p.y(), p.x() + it.width(), p.y() + it.height()
mid = lambda it: (box(it)[1] + box(it)[3]) / 2

h.ev("root.opened = true"); h.spin(60); h.answer("board", BOARD)
h.ev("root.showView('settings')"); h.spin(80)
sv = h.cls("SettingsView"); ctx = h.ctx_of(sv)
sev = lambda code: h.ev(code, ctx, sv)
h.answer("whoami", {"state": "ready", "message": "", "user": "o_devvy"}); h.spin(60)
row = sev("accountRow"); acc = sev("accountText")

heads = [it.property("text") for it in h.visible(lambda it: it.metaObject().className().startswith("Heading"))]
h.ok("L1 the heading reads Account", "Account" in heads and "GitLab account" not in heads, heads)
h.ok("L2 no frame around it", sev("(function(){ var p = accountText.parent; while (p && p !== view) { if (p.border !== undefined && p.border.width > 0) return false; p = p.parent } return true })()"))
lk = link()
h.ok("L3 Sign out is a text action in the accent, small, no border", len(lk) == 1 and same(lk[0].property("color"), h.ev("root.accent"))
     and abs(lk[0].property("font").pixelSize() - sev("Style.font.bodySmall")) < 0.5 and not button("Sign out"))
h.ok("L4 one row: who on the left, Sign out flush right, same line", abs(mid(lk[0]) - mid(acc)) < 1 and abs(box(lk[0])[2] - box(row)[2]) < 1 and abs(box(acc)[0] - box(row)[0]) < 1
     and "Signed in as o_devvy on gitlab.com" == acc.property("text"))
h.ok("L5 the row is one line tall: the 32 high Sign out target", abs(row.height() - sev("Style.space(32)")) < 0.5 and acc.property("lineCount") == 1, row.height())
h0 = row.height()
QTest.mouseMove(h.win, QPoint(1, 1)); h.spin(60)
shot(0)

h.click(lk[0])
yes, cancel = button("Yes, sign out"), button("Cancel")
note = sev("cacheNote")
h.ok("C1 asks first: the question, then what it deletes, Yes / Cancel under them on the right (v0.1.107)", acc.property("text") == "Sign out of glab on gitlab.com? This also signs glab out in your terminal and scripts on this computer." and not link() and len(yes) == 1 and len(cancel) == 1
     and note.property("visible") and note.property("text") == "This also deletes this server's saved board cache on this computer."
     and box(note)[1] >= box(acc)[3] - 0.5 and box(yes[0])[1] >= box(note)[3] and abs(box(cancel[0])[2] - box(row)[2]) < 1 and box(yes[0])[2] <= box(cancel[0])[0])
h.ok("C2 compact: small buttons, Yes urgent, the row just fits question, note and buttons", yes[0].property("small") and cancel[0].property("small") and yes[0].property("danger") and not cancel[0].property("danger")
     and acc.property("lineCount") <= 3 and abs(row.height() - (acc.property("height") + note.property("height") + sev("Style.space(8)") + yes[0].property("height"))) < 0.5, (row.height(), acc.property("lineCount")))
h.ok("C3 nothing run yet", not h.running("logout"))
QTest.mouseMove(h.win, h.scene(yes[0])); h.spin(700)
shown = [tp for tp in tips() if tp.property("visible")]
h.ok("C4 hovering Yes says what it does, inside the popup", len(shown) == 1 and "your terminal too" in shown[0].property("text") and "deletes the saved boards" in shown[0].property("text")
     and box(yes[0])[0] + shown[0].property("x") + shown[0].property("width") <= box(yes[0])[2] + 1, [(tp.property("x"), tp.property("width"), tp.property("implicitWidth"), box(yes[0])) for tp in shown])
QTest.mouseMove(h.win, QPoint(1, 1)); h.spin(60)
shot(1)
h.click(cancel[0])
h.ok("C5 Cancel: back to who is signed in, nothing run", acc.property("text") == "Signed in as o_devvy on gitlab.com" and len(link()) == 1 and not button("Yes, sign out") and not h.running("logout"))

h.click(link()[0]); h.click(button("Yes, sign out")[0])
h.ok("S1 Yes runs board-fetch logout", h.running("logout") == [[h.ev("root.helperPath()"), "logout"]])
h.ok("S2 'Signing out…' in the same row, no actions, same height", acc.property("text") == "Signing out…" and not link() and not button("Yes, sign out") and not button("Cancel") and abs(row.height() - h0) < 0.5)
h.answer("logout", {"state": "error", "message": "glab could not sign out of gitlab.com because something went wrong on this computer; the reason is long enough to wrap."}); h.spin(60)
lk = link()
h.ok("E1 a long reason wraps beside Sign out, never under it", len(lk) == 1 and acc.property("lineCount") > 1 and box(acc)[0] + acc.property("width") <= box(lk[0])[0] - sev("Style.space(12)") + 0.5
     and same(acc.property("color"), h.ev("root.urgent")))

# --- the issue view -------------------------------------------------------------
h.ev("root.back()"); h.spin(40); h.ev("root.boardState = 'ready'"); h.stop_all()
h.ev("root.openIssue(root.columns[1].issues[0])"); h.spin(80)
ISSUE = {"iid": 2, "title": "Second issue with a longer title", "state": "opened", "labels": ["todo", "bug", "frontend"], "url": "https://gitlab.com/group/app/-/issues/2",
         "description": "Make the board faster on large projects.", "author": "dev1", "milestone": "", "assignees": ["dev1"], "createdAt": "2026-10-20T12:00:00Z", "updatedAt": "2026-10-29T12:00:00Z"}
h.answer("issue", {"state": "ready", "message": "", "issue": ISSUE}); h.answer("notes", {"state": "ready", "message": "", "iid": 2, "more": False, "notes": []}); h.spin(60)
iw = h.cls("IssueView"); ic = h.ctx_of(iw); iev = lambda code: h.ev(code, ic, iw)
lrow, pillI, editI, stateI = iev("labelRow"), iev("statePill"), iev("editAction"), iev("stateAction")
chip = lambda name: next(it for it in h.visible(lambda it: cls_is(it, "LabelChip") and it.property("label") == name))
pos = lambda it: (round(box(it)[0], 1), round(box(it)[1], 1))
h.ok("I1 one row: state, labels, Edit labels, Close issue", all(abs(mid(it) - mid(pillI)) < 1 for it in [chip("todo"), chip("frontend"), editI, stateI])
     and box(editI)[0] >= box(chip("frontend"))[2] and abs(box(stateI)[2] - box(lrow)[2]) < 1 and abs(lrow.height() - pillI.height()) < 0.5, (lrow.height(), pillI.height()))
h.ok("I1b the labels never run under Close issue", box(iev("labelFlow"))[2] <= box(stateI)[0])
h.ok("I2 both are text actions: Edit labels in the accent, Close issue quiet, small, no buttons",
     editI.property("text") == "\uf040  Edit labels" and same(editI.property("color"), h.ev("root.accent")) and stateI.property("text") == "Close issue" and same(stateI.property("color"), h.ev("root.dim"))
     and abs(stateI.property("font").pixelSize() - iev("Style.font.bodySmall")) < 0.5 and not button("Close issue") and not button("Edit labels"))
QTest.mouseMove(h.win, QPoint(1, 1)); h.spin(60)
shot(2)
before = (pos(editI), pos(stateI), pos(lrow))
h.click(editI)
# The editor and the comments are their own files (0.1.48): their ids live there.
lev = lambda code: h.ev(code, h.ctx_of(iev("labelEditor")), iev("labelEditor"))
cev = lambda code: h.ev(code, h.ctx_of(iev("comments")), iev("comments"))
filt, done = iev("labelFilter"), lev("doneButton")
# The labels gain a ×, so Edit labels may shift right on its row; it never drops a row.
h.ok("I3 the editor opens below; the row stays, Close issue stays put", pos(editI)[1] == before[0][1] and (pos(stateI), pos(lrow)) == before[1:] and editI.property("text") == "\uf00c  Done editing" and box(filt)[1] >= box(lrow)[3])
h.ok("I4 while labels load: the filter is off and dimmed; the line under it says Loading labels…", not filt.property("enabled") and filt.property("opacity") < 1 and "Loading labels…" in texts() and not iev("view.typing"))
h.key(Qt.Key_O, "o"); h.key(Qt.Key_X, "x")
h.ok("I5 typing while they load does nothing (no browser, no close question)", h.launched() == [] and not iev("view.confirming") and h.ev("root.view") == "issue")
shot(3)
h.key(Qt.Key_Escape)
h.ok("I6 Esc while they load closes the editor, stays on the issue", not iev("view.editing") and h.ev("root.view") == "issue")
h.stop_all(); h.click(editI)
LABELS = [{"name": n, "color": c, "textColor": None} for n, c in [("bug", "#dc2626"), ("docs", "#0ea5e9"), ("frontend", "#16a34a"), ("ux", "#6366f1")]]
h.answer("labels", {"state": "ready", "message": "", "status": ["approved", "in progress", "research", "review", "todo"], "labels": LABELS}); h.spin(60)
h.ok("I7 loaded: the filter is on and focused", filt.property("enabled") and filt.property("opacity") == 1 and filt.property("activeFocus"))
h.ok("I8 compact: a small filter, Done the same height beside it", filt.height() <= iev("Style.space(28)") + 0.5 and abs(done.height() - filt.height()) < 0.5 and abs(mid(done) - mid(filt)) < 1
     and abs(filt.property("font").pixelSize() - iev("Style.font.bodySmall")) < 0.5 and done.property("small"), (filt.height(), done.height()))
QTest.mouseMove(h.win, QPoint(1, 1)); h.spin(60)
shot(4)
h.click(editI)
h.ok("I9 Done editing closes the editor; the row is as before", not iev("view.editing") and editI.property("text") == "\uf040  Edit labels" and (pos(editI), pos(stateI), pos(lrow)) == before)
h.ev("keyCatcher.forceActiveFocus()"); h.spin(30); h.key(Qt.Key_E, "e")
h.ok("I10 e still opens the editor (v0.1.42: the labels just read are reused, no new read)", iev("view.editing") and not h.running("labels") and iev("view.labelsState") == "ready")
h.key(Qt.Key_Escape); h.stop_all(); h.ev("keyCatcher.forceActiveFocus()"); h.spin(30); h.key(Qt.Key_X, "x")
h.ok("I11 x still asks; the question sits below the row, Close issue stays put", iev("view.confirming") and box(iev("confirmBox"))[1] >= box(lrow)[3] and stateI.isVisible() and (pos(editI), pos(stateI)) == before[:2] and not h.running("close"))
h.key(Qt.Key_Escape)
h.click(stateI)
h.ok("I12 clicking Close issue asks too", iev("view.confirming") and not h.running("close"))
h.key(Qt.Key_Escape)

hint, post = cev("postStatus"), cev("postButton")
clear = lambda: box(hint)[0] + hint.property("width") <= box(post)[0] - iev("Style.space(8)") + 0.5 and box(hint)[0] + hint.property("contentWidth") <= box(post)[0]
h.ok("P1 the comment hint is whole, on one line, clear of Post", hint.property("text") == "Posts as you. Lines starting with / aren't sent." and not hint.property("truncated") and hint.property("lineCount") == 1 and clear())
h.ev("box.text = 'Looks good\\n/label ~review'", ic); h.spin(40)
h.ok("P2 the long / warning wraps beside Post, never under it", hint.property("lineCount") > 1 and clear() and box(hint)[3] <= box(cev("postStatus.parent"))[3] + 0.5)
h.ev("box.text = 'Looks good to me.'", ic); h.spin(40)
h.ev("issueView.focusBox()"); QTest.mouseMove(h.win, QPoint(1, 1)); h.spin(60)
shot(5)
# --- Closed: the latest 20, and a link to the rest -----------------------------
import copy
SEE = "https://gitlab.com/group/app/-/issues?state=closed&label_name%5B%5D=team-a"
def closed_board(n, see):
    b = copy.deepcopy(BOARD); c = b["columns"][3]
    c["issues"] = [{"iid": 200 + i, "title": "Closed issue %d" % (200 + i), "labels": [], "url": "https://gitlab.com/group/app/-/issues/%d" % (200 + i),
                    "createdAt": "2026-10-01T12:00:00Z", "notes": 0, "assignees": []} for i in range(n)]
    if see: c["seeAll"] = see
    return b
foot = lambda: h.visible(lambda it: cls_is(it, "BoardText") and str(it.property("text") or "").startswith("Showing the latest"))
h.ev("root.back()"); h.spin(40); h.stop_all(); h.ev("root.boardState = 'ready'")
h.ev("root.refresh()"); h.answer("board", closed_board(20, SEE)); h.spin(80)
h.ok("F0 Closed starts collapsed here: no footer on the strip", h.ev("root.isCollapsed('Closed')") and not foot())
h.ev("root.toggleCollapsed('Closed')"); h.spin(300)
f = foot()
cards = [it for it in h.visible(lambda it: cls_is(it, "BoardText") and str(it.property("text") or "").endswith("Closed issue 219"))]
h.ok("F1 a full Closed column: 'Showing the latest 20 · See all on GitLab ↗', quiet, under its last card", len(f) == 1 and f[0].property("text") == "Showing the latest 20 · See all on GitLab \u2197"
     and same(f[0].property("color"), h.ev("root.dim")) and len(cards) == 1 and box(f[0])[1] >= box(cards[0])[3], [x.property("text") for x in f])
h.ok("F2 only the Closed column has it", len(f) == 1 and abs(box(f[0])[0] - box(cards[0])[0]) < 40)
h.ev("panel.contentHeight = Qt.binding(function() { return panel.fittedContentHeight(keyCatcher.implicitHeight, Style.space(640)) })"); h.spin(100)  # the real cap: the column scrolls
fl = f[0].parentItem()
while fl is not None and not fl.metaObject().className().startswith("QQuickFlickable"): fl = fl.parentItem()
if fl is not None: fl.setProperty("contentY", max(0, fl.property("contentHeight") - fl.height()))  # the preview: the column's end
QTest.mouseMove(h.win, QPoint(1, 1)); h.spin(120)
shot(6)
h.click(f[0])
h.ok("F3 click: opens the project's closed issues (the board's filter kept) in the browser", h.launched() == [["omarchy-launch-browser", SEE]], h.launched())
h.ev("Quickshell.launched = []"); h.ev("root.opened = true"); h.spin(60)
h.ev("root.refresh()"); h.answer("board", closed_board(19, None)); h.spin(80)
h.ok("F4 fewer than 20: no footer", not foot() and not h.ev("root.isCollapsed('Closed')"))
h.ev("root.refresh()"); h.answer("board", closed_board(20, "http://gitlab.com/group/app/-/issues?state=closed")); h.spin(80)
if foot(): h.click(foot()[0])
h.ok("F5 only https links open", h.launched() == [])
h.ev("root.opened = true"); h.spin(40)
h.ev("root.refresh()"); h.answer("board", closed_board(20, SEE)); h.spin(80)
h.ev("root.toggleCollapsed('Closed')"); h.spin(300)
h.ok("F6 collapsed again: the strip shows 20, no footer", h.ev("root.isCollapsed('Closed')") and not foot())
sys.exit(h.finish())
