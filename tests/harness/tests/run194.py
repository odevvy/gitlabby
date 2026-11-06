# v0.1.94: quiet × inside Filter projects and Filter labels. Same mark as the
# picker's close (\uf00d). Only while the field has text; click clears and keeps
# focus; typed text stops short of the mark (rightPadding).
# Usage: run194.py <src>
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from fixtures import BOARD
from PySide6.QtGui import QGuiApplication, QKeyEvent
from PySide6.QtCore import QEvent
h = Harness(sys.argv[1], {"id": "odevvy.gitlabby", "settingsRevision": 2, "defaultProject": "group/app", "defaultCollapsed": [], "boardStates": {}, "refreshIntervalSec": 60})
h.ev("panel.availableCardHeight = 520; panel.availableCardWidth = 1460")
h.ev("root.opened = true"); h.spin(60); h.answer("board", BOARD); h.spin(200)

def typed(s):
    for ch in s:
        k = getattr(Qt, "Key_" + ch.upper(), Qt.Key_unknown) if ch.isalpha() else Qt.Key_unknown
        for typ in (QEvent.KeyPress, QEvent.KeyRelease):
            QGuiApplication.sendEvent(h.win, QKeyEvent(typ, k, Qt.NoModifier, ch))
        h.spin(30)

GLYPH = "(function(){ for (var i = 0; i < clear.children.length; i++) { var c = clear.children[i]; if (c && c.text !== undefined && c.text.length === 1) return c.text } return '' })()"
# String form avoids float drift between theme dim and the painted glyph.
DIM = "(function(){ for (var i = 0; i < clear.children.length; i++) { var c = clear.children[i]; if (c && c.text !== undefined && c.text.length === 1) return c.color.toString() === clear.host.dim.toString() && c.color.toString() !== clear.host.accent.toString() } return false })()"

# --- Filter projects --------------------------------------------------------------------------
h.ev("root.openPicker()"); h.spin(80)
h.answer("projects", {"state": "ready", "projects": [{"id": i, "path": "group/app%d" % i} for i in range(1, 6)]}); h.spin(150)
pv = h.cls("Picker"); pc = h.ctx_of(pv); pev = lambda e: h.ev(e, pc, pv)
h.ok("P0 filter starts empty: no ×", pev("filter.text") == "" and pev("!clear.visible"), pev("filter.text"))
typed("app"); h.spin(60)
h.ok("P1 typing shows the × with the close glyph", pev("clear.visible") is True and pev(GLYPH) == "\uf00d", (pev("clear.visible"), pev(GLYPH)))
h.ok("P2 field rightPadding leaves room for the ×", pev("filter.rightPadding >= filter.horizontalPadding + 1 + clear.reserve - 0.5") and pev("clear.reserve") > 0, (pev("filter.rightPadding"), pev("clear.reserve")))
h.ok("P3 idle × is dim (not the accent)", pev(DIM) is True)
clr = next((it for it in h.walk(pv) if it.objectName() == "filterClear"), None)
h.ok("P3b found the clear control", clr is not None)
# Blur first so forceActiveFocus on clear is what restores the caret.
h.ev("keyCatcher.forceActiveFocus()"); h.spin(40)
h.ok("P3c filter blurred before clear", pev("!filter.activeFocus") is True)
h.click(clr); h.spin(80)
h.ok("P4 click clears the text", pev("filter.text") == "", pev("filter.text"))
h.ok("P5 clear puts focus back in the field", pev("filter.activeFocus") is True)
h.ok("P6 × gone once empty", pev("!clear.visible") is True)
typed("x"); h.spin(40)
h.ok("P7 can type again right away", pev("filter.text") == "x", pev("filter.text"))
h.key(Qt.Key_Escape); h.spin(80)

# --- Filter labels (IssueLabels → LabelPicker) ------------------------------------------------
iw = h.cls("IssueView"); ic = h.ctx_of(iw); iev = lambda code: h.ev(code, ic, iw)
card = [i for col in h.ev("root.columns") for i in col["issues"] if i["iid"] == 2][0]
h.ev("root.openIssue(%s)" % json.dumps(card)); h.spin(60)
ISSUE = {"iid": 2, "title": "Second issue", "state": "opened", "labels": ["todo"], "url": "https://gitlab.com/group/app/-/issues/2",
         "description": "Body", "author": "dev1", "milestone": "", "assignees": [],
         "createdAt": "2026-10-20T12:00:00Z", "updatedAt": "2026-10-29T12:00:00Z"}
h.answer("issue", {"state": "ready", "message": "", "issue": ISSUE})
h.answer("notes", {"state": "ready", "message": "", "iid": 2, "more": False, "notes": []}); h.spin(200)
iev("view.editLabels()"); h.spin(60)
LABELS = [{"name": n, "color": c, "textColor": None} for n, c in [("bug", "#dc2626"), ("docs", "#0ea5e9"), ("frontend", "#16a34a")]]
h.answer("labels", {"state": "ready", "message": "", "status": ["todo"], "labels": LABELS}); h.spin(80)
le = iev("labelEditor"); lec = h.ctx_of(le)
lp = h.ev("labelPicker", lec, le); lpc = h.ctx_of(lp); lev = lambda e: h.ev(e, lpc, lp)
h.ok("L0 labels filter empty: no ×", lev("field.text") == "" and lev("!clear.visible"))
typed("do"); h.spin(60)
h.ok("L1 typing shows the ×", lev("clear.visible") is True and lev(GLYPH) == "\uf00d", (lev("clear.visible"), lev(GLYPH)))
h.ok("L2 rightPadding reserves the ×", lev("field.rightPadding >= field.horizontalPadding + 1 + clear.reserve - 0.5") and lev("clear.reserve") > 0)
lclr = next((it for it in h.walk(lp) if it.objectName() == "filterClear"), None)
h.ok("L3 found labels clear", lclr is not None)
h.ev("keyCatcher.forceActiveFocus()"); h.spin(40)
h.ok("L3b filter blurred before clear", lev("!field.activeFocus") is True)
h.click(lclr); h.spin(80)
h.ok("L4 click clears and restores focus", lev("field.text") == "" and lev("field.activeFocus") is True, (lev("field.text"), lev("field.activeFocus")))
h.ok("L5 × hidden again", lev("!clear.visible") is True)
typed("b"); h.spin(40)
h.ok("L6 can type again", lev("field.text") == "b", lev("field.text"))

sys.exit(h.finish())
