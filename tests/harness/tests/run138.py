# v0.1.38: bulk actions at Style.scale 1.5 (OGB_SCALE). v and Ctrl+click pick
# cards (cap 20); Shift+H/L, x, e or a button arms the bar, which lists what
# happens to which card and writes nothing; the same key, Enter or the main
# button confirms; writes run one card at a time with the single-card
# board-fetch commands; ordinary failures go on, timeouts and sign-in stop;
# Esc steps back, or stops a run after the current card.
# Usage: run138.py <src> [outdir]   (previews: bulk-selection, bulk-armed, bulk-running, bulk-results, bulk-label)
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import os
os.environ["OGB_SCALE"] = "1.5"
import lib
from lib import *
from PySide6.QtGui import QKeyEvent
src = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else None
P = "firelink21/phrase41"
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "run134.py")).read().split("ALL = []")[0].split("P = \"firelink21/phrase41\"")[1])
ALL = []
def ok(n, c, e=""): ALL.append(bool(c)); h.ok(n, c, e)
def shot(name):
    QTest.mouseMove(h.win, QPoint(1, 1)); h.spin(80)
    if out: h.grab_card(os.path.join(out, name + ".png"))
def start():
    global h
    h = Harness(src, {"id": "odevvy.gitlab-board", "settingsRevision": 2, "defaultProject": P, "defaultCollapsed": ["open", "research", "Closed"], "bots": FOUR})
    h.ev("panel.availableCardHeight = %d; panel.availableCardWidth = 1460" % DESK)
    h.ev("root.opened = true"); h.spin(60); h.answer("board", board()); h.spin(150)
def shift(k, t):
    for typ in (QEvent.KeyPress, QEvent.KeyRelease): QGuiApplication.sendEvent(h.win, QKeyEvent(typ, k, Qt.ShiftModifier, t))
    h.spin(60)
def md(it):  # a card's data: a declared property since v0.1.57 (keyed cards), a QJSValue
    v = it.property("modelData"); return v.toVariant() if hasattr(v, "toVariant") else v
def cards(): return {md(it)["iid"]: it for it in h.visible(lambda it: it.property("picked") is not None and it.property("keyed") is not None)}
def to_card(iid):  # cursor onto a card
    h.ev("root.cursor = (function(){ for (var c = 0; c < root.lanes.length; c++) { var l = root.lanes[c]; if (l && l.indexOf(%d) !== -1) return { col: c, row: l.indexOf(%d), iid: %d } } return null })()" % (iid, iid, iid)); h.spin(40)
picked = lambda: h.ev("root.picked")
mode = lambda: h.ev("bulkBar.mode")
moves = lambda: h.running("move")
writes = lambda: [c for c in h.running() if c[1] in ("move", "relabel", "close", "reopen")]
text_of = lambda name: next((it.property("text") for it in h.visible(lambda it: it.objectName() == name)), None)
texts = lambda name: [it.property("text") for it in sorted(h.visible(lambda it: it.objectName() == name), key=lambda it: it.mapToScene(QPointF(0, 0)).y())]
btn = lambda name: next(it for it in h.visible(lambda it: it.objectName() == name))
summary = lambda: text_of("bulkSummary")

start()
# --- picking ------------------------------------------------------------------------
ok("P0 nothing picked: no bar", not h.ev("bulkBar.visible"))
to_card(20); h.key(Qt.Key_V, "v")
ok("P1 v picks the card under the cursor", picked() == ["label:2|20"] and cards()[20].property("picked"), picked())
mark = [it for it in h.visible(lambda it: it.objectName() == "pickMark")]
ok("P2 one check mark, on #20", len(mark) == 1 and cards()[20].isAncestorOf(mark[0]))
ok("P3 the bar says what is picked", h.ev("bulkBar.visible") and any("1 card selected" == t for t in [it.property("text") for it in h.visible(lambda it: True) if it.property("text") is not None]))
c21 = cards()[21]
QTest.mouseClick(h.win, Qt.LeftButton, Qt.ControlModifier, h.scene(c21, 0.5, 0.3)); h.spin(120)
ok("P4 Ctrl+click picks a card and opens nothing", picked() == ["label:2|20", "label:2|21"] and h.ev("root.view") == "board", (picked(), h.ev("root.view")))
to_card(40); h.key(Qt.Key_V, "v")
ok("P5 three picked, in pick order", picked() == ["label:2|20", "label:2|21", "label:4|40"], picked())
h.key(Qt.Key_V, "v"); ok("P6 v again drops it", picked() == ["label:2|20", "label:2|21"])
h.key(Qt.Key_V, "v")
shot("bulk-selection")
# cap
h.ev("root.picked = " + json.dumps(["label:2|%d" % (100 + i) for i in range(20)]))
h.ev("bulkBar.pickNote(false)")
saved = ["label:2|20", "label:2|21", "label:4|40"]
h.ev("root.picked = [" + ",".join('"%s"' % k for k in saved) + "].concat(" + json.dumps(["label:2|%d" % (100 + i) for i in range(17)]) + ")")
to_card(41); h.key(Qt.Key_V, "v")
ok("P8 the 21st card is refused, with a note", len(picked()) == 20 and "Up to 20 cards at a time." in h.ev("bulkBar.note"), (len(picked()), h.ev("bulkBar.note")))
h.ev("root.columns = root.columns.slice()"); h.spin(40)
ok("P9 picks of cards no longer on the board drop out", picked() == saved, picked())
h.ev("bulkBar.pickNote(false)")
# --- arming ----------------------------------------------------------------------------
to_card(40); shift(Qt.Key_L, "L")
ok("A1 Shift+L with picks arms a move to the column right of the cursor's", mode() == "armed" and h.ev("bulkBar.action.to.name") == "review", (mode(), h.ev("bulkBar.action")))
ok("A2 armed writes nothing and is not a single-card move", writes() == [] and h.ev("root.pendingMove") is None and h.ev("root.move") is None)
ok("A3 the question counts the cards", text_of("bulkQuestion") == "Move 3 cards to review?", text_of("bulkQuestion"))
lines = [[t.property("text") for t in it.childItems()] for it in sorted(h.visible(lambda it: it.objectName() == "bulkLine"), key=lambda it: it.mapToScene(QPointF(0, 0)).y())]
ok("A4 each card with its own from, grouped", lines == [["todo \u2192 review", "#20 #21"], ["in progress \u2192 review", "#40"]], lines)
ok("A5 the main button says it", btn("bulkConfirm").property("label") == "Move 3 cards")
ok("A6 armed holds board answers (like a pending move)", h.ev("root.held"))
shot("bulk-armed")
h.key(Qt.Key_R, "r"); h.key(Qt.Key_S, "s"); h.key(Qt.Key_V, "v")
ok("A7 other keys do nothing while armed", mode() == "armed" and h.running("board") == [] and h.ev("root.view") == "board" and len(picked()) == 3)
h.key(Qt.Key_Escape)
ok("A8 Esc disarms and keeps the picks; the popup stays", mode() == "" and picked() == saved and h.ev("root.opened"))
# a column that needs no move is skipped, and said
to_card(20); h.ev("bulkBar.armMove(root.shownColumns.filter(function(c){ return c.name === 'todo' })[0], '')")
ok("A9 cards already there are skipped, out loud; the count drops", text_of("bulkQuestion") == "Move 1 card to todo?" and any("Skipped, already in todo" in [t.property("text") for t in it.childItems()] for it in h.visible(lambda it: it.objectName() == "bulkLine")))
h.key(Qt.Key_Escape)
# --- running ----------------------------------------------------------------------------
to_card(40); shift(Qt.Key_L, "L"); shift(Qt.Key_L, "L")
ok("R1 Shift+L again confirms: one write, the first card, its own from", mode() == "running" and writes() == [[h.ev("root.helperPath()"), "move", "--project", P, "--board", "7", "--iid", "20", "--from", "2", "--to", "5"]], writes())
ok("R1b a watchdog runs for the card", h.ev("(function(){ for (var i = 0; i < bulkBar.data.length; i++) if (bulkBar.data[i].interval === 50000) return bulkBar.data[i].running; return false })()"))
h.ev("bulkBar.backToPicking()"); ok("R1c nothing steps the bar back while it runs", mode() == "running")
ok("R2 a running batch holds the board and refuses a drag", h.ev("root.held") and not h.ev("root.requestMove(root.columns[2].issues[0], root.columns[2], root.columns[3])"))
h.answer("move", {"state": "ready", "message": "Moved #20."}); h.spin(80)
ok("R3 one at a time: #21 starts after #20 answered", [c[7] for c in writes()] == ["21"], writes())
h.answer("move", {"state": "error", "message": "Move failed: 409 Conflict"}); h.spin(80)
ok("R4 an ordinary failure: the run goes on to #40", [c[7] for c in writes()] == ["40"], writes())
ok("R4b while running: what is done and each failure so far", texts("bulkResult") == ["\uf057  #21  Move failed: 409 Conflict"] and "#20" in h.ev("bulkBar.doneIids"), texts("bulkResult"))
shot("bulk-running")
h.answer("move", {"state": "ready", "message": "Moved #40."}); h.spin(150)
ok("R5 results: 2 of 3, 1 failed", mode() == "results" and summary() == "Moved 2 of 3 cards to review. 1 failed.", summary())
ok("R6 every failure on its own line with GitLab's reason", texts("bulkResult") == ["\uf057  #21  Move failed: 409 Conflict"], texts("bulkResult"))
ok("R7 his own moves raise no alert (noteOwnMove for each one done)", sorted(m["iid"] for m in (h.ev("root.feed.ownMoves")[h.ev("root.fetchKey")] or [])) == [20, 40], h.ev("root.feed.ownMoves"))
ok("R8 the board is fetched again after the last write", len(h.running("board")) == 1 and h.ev("root.moveFloor") > 0, h.running("board"))
shot("bulk-results")
h.answer("board", board()); h.spin(100)
ok("R9 results stay until closed; picks stay put", mode() == "results" and len(picked()) == 3)
btn("bulkKeep").property("label") == "Keep it selected" and h.click(btn("bulkKeep"))
ok("R10 Keep it selected: only the failed card stays picked", mode() == "" and picked() == ["label:2|21"], (mode(), picked()))
# --- stops -------------------------------------------------------------------------------
h.ev("root.picked = " + json.dumps(saved)); h.spin(40)
h.key(Qt.Key_X, "x")
ok("S1 x arms close for the picks", mode() == "armed" and text_of("bulkQuestion") == "Close 3 cards?")
h.key(Qt.Key_X, "x")
ok("S2 x again confirms: board-fetch close #20", [c[1:] for c in writes()] == [["close", "--project", P, "--iid", "20"]], writes())
h.answer("close", {"state": "error", "message": "GitLab did not answer within 30 seconds. The issue may have been closed."}); h.spin(150)
ok("S3 a timeout stops the run: nothing else runs", writes() == [] and mode() == "results", writes())
ok("S4 it says it may have gone through, and what was not tried", summary() == "Closed 0 of 3 cards. 1 failed, 2 not tried." and texts("bulkResult")[0].endswith("The issue may have been closed.") and texts("bulkResult")[1:] == ["\u00b7  #21  Not tried: the run stopped.", "\u00b7  #40  Not tried: the run stopped."], (summary(), texts("bulkResult")))
h.key(Qt.Key_Escape)
ok("S5 Esc closes the results and clears the picks", mode() == "" and picked() == [] and not h.ev("bulkBar.visible"))
h.answer("board", board()) if h.running("board") else None
h.ev("root.picked = " + json.dumps(saved)); h.spin(40)
h.key(Qt.Key_X, "x"); h.key(Qt.Key_Return)
ok("S6 Enter confirms too", len(writes()) == 1)
h.answer("close", {"state": "logged-out", "message": "Not signed in to gitlab.com. Run: glab auth login"}); h.spin(150)
ok("S7 signed out stops the run", writes() == [] and summary() == "Closed 0 of 3 cards. 1 failed, 2 not tried.", summary())
h.key(Qt.Key_Escape); h.answer("board", board()) if h.running("board") else None
h.ev("root.picked = " + json.dumps(saved)); h.spin(40)
h.key(Qt.Key_X, "x"); h.key(Qt.Key_X, "x")
wd = h.ev("(function(){ for (var i = 0; i < bulkBar.data.length; i++) if (bulkBar.data[i].interval === 50000) { bulkBar.data[i].triggered(); return true } return false })()")
h.spin(150)
ok("S8 no answer in 45 s: stopped, may have gone through", wd and mode() == "results" and "may have gone through" in texts("bulkResult")[0], texts("bulkResult"))
h.answer("close", {"state": "ready"}); h.spin(100)
ok("S9 the late answer changes nothing", summary() == "Closed 0 of 3 cards. 1 failed, 2 not tried.")
h.key(Qt.Key_Escape); h.answer("board", board()) if h.running("board") else None
# --- labels, and Esc during a run ----------------------------------------------------------
h.ev("root.picked = " + json.dumps(saved)); h.spin(40)
h.key(Qt.Key_E, "e")
ok("L1 e with picks: the label step loads the project's labels (GET)", mode() == "label" and [c[1:] for c in h.running("labels")] == [["labels", "--project", P]])
h.answer("labels", LABELS); h.spin(120)
opts = h.ev("bulkBar.labelOptions.map(function(l){ return l.name })")
ok("L2 add offers every label but the status ones", sorted(opts) == ["api", "app-ui", "auth-mail"], opts)
shot("bulk-label")
chip = next(it for it in h.visible(lambda it: it.property("name") == "app-ui" and it.property("clickable") is not None) if h.ev("bulkBar").isAncestorOf(it))
h.click(chip); h.spin(80)
ok("L3 a label chip arms: #20 already has it and is skipped; keys back to the panel", text_of("bulkQuestion") == "Add app-ui to 2 cards?" and h.ev("keyCatcher.activeFocus"), (text_of("bulkQuestion"), h.ev("keyCatcher.activeFocus")))
h.key(Qt.Key_Return)
ok("L4 relabel, one label, for #21 first", [c[1:] for c in writes()] == [["relabel", "--project", P, "--iid", "21", "--add", "app-ui"]], writes())
h.key(Qt.Key_Escape)
ok("L5 Esc while running stops after this card (it says so)", h.ev("bulkBar.stopping") and "Stopping after #21" in text_of("bulkProgress") and h.ev("root.opened"))
h.answer("relabel", {"state": "ready", "message": "Added app-ui."}); h.spin(150)
ok("L6 stopped: #40 not tried, #21 done", writes() == [] and summary() == "Added app-ui to 1 of 2 cards. 1 not tried.", summary())
h.key(Qt.Key_Escape); h.answer("board", board()) if h.running("board") else None
h.ev("root.picked = " + json.dumps(saved)); h.spin(40)
h.ev("bulkBar.chooseLabel('remove')"); h.spin(60)
opts = h.ev("bulkBar.labelOptions.map(function(l){ return l.name })")
ok("L7 remove offers only labels the picked cards have", sorted(opts) == ["app-ui", "auth-mail"], opts)
h.key(Qt.Key_Escape)
ok("L8 Esc leaves the label step, picks kept", mode() == "" and len(picked()) == 3)
# --- switching boards, closing --------------------------------------------------------------
h.ev("root.opened = false"); h.spin(60)
ok("C1 closing the popup clears picks when nothing runs", picked() == [] and mode() == "")
h.ev("root.opened = true"); h.spin(100)
h.answer("board", board()) if h.running("board") else None
ok("C2 no picks: Shift+L is the single-card move again", (to_card(40), shift(Qt.Key_L, "L"), mode() == "" and len(moves()) == 1)[2])
code = h.finish(); sys.exit(code or (0 if all(ALL) else 1))
