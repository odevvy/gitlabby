# v0.1.56: smooth fold. Folding or hiding a column keeps the board state in
# memory and saves it once: when the popup closes, or 2 s after the last fold
# (each save rewrites shell.json, which made Omarchy reload mid-animation).
# For 200 ms after a fold (root.folding) the column width, the popup width and
# its height animate 150 ms ease-out together, cards and strip fade in turns,
# and a board answer waits; board and view switches stay instant.
# (Stage 1: the save and the popup; the column and fade checks come with BoardView.qml.)
# Usage: run156.py <src> [outdir]   (outdir: frame PNGs of a fold and an unfold)
import sys, os, time; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
src = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else None
P = "firelink21/phrase41"
def iss(iid, labels): return {"iid": iid, "title": "Issue %d" % iid, "labels": labels, "url": "https://gitlab.com/%s/-/issues/%d" % (P, iid), "createdAt": "2026-10-31T09:00:00Z", "notes": 0, "assignees": []}
def col_(n, i, k): return {"name": n, "kind": "label", "listId": i, "color": "#5b9bd5", "issues": [iss(100 * i + j, [n]) for j in range(k)]}
def board(extra=()):
    names = [("research", 1), ("todo", 7), ("approved", 2), ("review", 1)] + list(extra)
    return {"state": "ready", "project": P, "updatedAt": "2026-10-31T13:20:00Z", "message": "", "labelColors": {}, "boards": [{"id": 1, "name": "Development"}], "board": {"id": 1, "name": "Development"}, "fallback": False,
            "columns": [{"name": "Open", "kind": "open", "issues": []}] + [col_(n, i + 1, k) for i, (n, k) in enumerate(names)] + [{"name": "Closed", "kind": "closed", "issues": []}]}
h = Harness(src, {"id": "odevvy.gitlab-board", "settingsRevision": 2, "defaultProject": P, "defaultCollapsed": ["open", "closed"]})
h.ev("panel.availableCardHeight = 1200; panel.availableCardWidth = 2400")
h.ev("root.opened = true"); h.spin(60); h.answer("board", board()); h.spin(300)
card = h.cls("KeyboardPanel")
writes = lambda: h.ev("root.bar.shell.writes.length")
def column(name):
    for it in h.walk():
        if it.objectName() == "stripCount":
            c = it.parentItem().parentItem()
            if h.ev("modelData.name", QQmlEngine.contextForObject(c), c) == name: return c
def parts(c):  # (strip, cards): the strip holds stripCount; the cards Column is the other child with a Column class
    strip = next(it for it in c.childItems() if any(k.objectName() == "stripCount" for k in it.childItems()))
    cards = next(it for it in c.childItems() if it.metaObject().className().startswith("QQuickColumn"))
    return strip, cards
def sample(name, n=None):
    c = column(name); strip, cards = parts(c); rows = []; t = time.perf_counter(); i = 0
    while time.perf_counter() - t < 0.26:
        app.processEvents()
        rows.append(((time.perf_counter() - t) * 1000, c.width(), card.width(), card.height(), strip.opacity(), cards.opacity()))
        if out and n: h.win.grabWindow().save("%s/%s-%02d.png" % (out, n, i)); i += 1
        time.sleep(0.012)
    return rows
S = lambda n: h.ev("Style.space(%d)" % n)
w0 = writes(); cw = h.ev("root.columnWidth"); sw = h.ev("root.stripWidth")
# --- fold ----------------------------------------------------------------------
h0 = card.height()
h.ev("root.toggleCollapsed('todo')"); fold = sample("todo", "fold")
h.ok("F1 a fold writes nothing at once", writes() == w0, writes() - w0)
mid = [r for r in fold if sw + 2 < r[1] < cw - 2]
h.ok("F2 the column width animates (in-between frames)", len(mid) >= 2, [r[1] for r in fold][:12])
edge = [round(r[2] - r[1]) for r in fold]
ws = [r[2] for r in fold]
h.ok("F3 the popup width animates too (in-between frames)", sum(1 for x in ws if min(ws) + 2 < x < max(ws) - 2) >= 2, sorted(set(int(x) for x in ws)))
h.ok("F4 the fold ends at the strip width within 200 ms", fold[-1][1] == sw and all(r[1] == sw for r in fold if r[0] > 200), [(int(r[0]), r[1]) for r in fold if r[0] > 150][:4])
hs = [r[3] for r in fold]
h.ok("F6 the height animates too (the tallest column folded)", fold[-1][3] < h0 - 4 and any(fold[-1][3] + 2 < x < h0 - 2 for x in hs), (h0, sorted(set(int(x) for x in hs))))
h.ok("F7 folding is over after 200 ms", not h.ev("root.folding"))
# --- unfold ----------------------------------------------------------------------
h.ev("root.toggleCollapsed('todo')"); unfold = sample("todo", "unfold")
h.ok("U1 the unfold animates and ends at the column width", any(sw + 2 < r[1] < cw - 2 for r in unfold) and unfold[-1][1] == cw)
edge = [round(r[2] - r[1]) for r in unfold]
early = [r for r in unfold if r[0] < 40]
h.ok("U4 still nothing written", writes() == w0)
# --- saving ------------------------------------------------------------------------
h.ev("root.toggleCollapsed('research')"); h.spin(1200); h.ev("root.toggleHidden('review')"); h.spin(1500)
h.ok("S1 two folds 1.2 s apart: nothing written 1.5 s after the last", writes() == w0)
h.spin(700)
st = (h.ev("root.bar.shell.writes") or [{}])[-1].get("boardStates", {})
key = h.ev("root.stateKey")
h.ok("S2 one write 2 s after the last fold, with every fold and hide in it", writes() == w0 + 1 and "research" in st.get(key, {}).get("collapsed", []) and "review" in st.get(key, {}).get("hidden", []), (writes() - w0, st.get(key)))
h.spin(2200); h.ok("S3 no second write", writes() == w0 + 1)
w1 = writes(); h.ev("root.toggleCollapsed('approved')"); h.spin(300); h.ev("root.opened = false"); h.spin(60)
st = h.ev("root.bar.shell.writes")[-1].get("boardStates", {})
h.ok("S4 closing the popup writes the pending fold at once", writes() == w1 + 1 and "approved" in st.get(key, {}).get("collapsed", []), writes() - w1)
h.spin(2200); h.ok("S5 and the 2 s save does not write it again", writes() == w1 + 1)
h.ev("root.opened = true"); h.spin(300); w2 = writes()
h.ev("root.toggleDefaultCollapsed('todo')"); h.spin(60)
h.ok("S6 a Settings default that folds the board is saved at once", writes() == w2 + 1)
h.spin(2300); h.ok("S7 once", writes() == w2 + 1)
h.ev("root.toggleHidden('review')"); h.spin(400)  # back on screen
# --- answers wait --------------------------------------------------------------------
h.ev("root.refresh(false)"); h.spin(30)
h.ok("A0 a board fetch is running", len(h.running("board")) == 1)
n0 = h.ev("root.columns.length")
h.ev("root.toggleCollapsed('research')")
h.ev("(function(){ var p = " + h.PROCS + ".filter(function(p){ return p.running && p.command[1] === 'board' })[0]; p.stdout.text = %s; p.stdout.streamFinished(); p.running = false; p.exited(0, 0) })()" % json.dumps(json.dumps(board([("extra", 3)]))))
app.processEvents()
h.ok("A1 an answer landing mid-fold waits", h.ev("root.columns.length") == n0 and h.ev("root.refreshQueued"))
h.spin(500)
h.ok("A2 and lands once the fold is over", h.ev("root.columns.length") == n0 + 1 and not h.ev("root.refreshQueued"), (n0, h.ev("root.columns.length")))
# --- instant switches ------------------------------------------------------------------
c = column("approved"); was = c.width(); bw = h.ev("root.boardWidth")
h.ev("(function(){ var s = {}; s[root.stateKey] = { collapsed: [], hidden: [] }; root.boardStates = s })()"); app.processEvents()
h.ok("I2 and the popup width at once", h.ev("root.shownBoardWidth") == h.ev("root.boardWidth") != bw)
hh = h.ev("root.shownHeight"); h.ev("root.showView('settings')"); app.processEvents()
h.ok("I3 a view switch sizes the popup at once", h.ev("root.shownHeight") == h.ev("keyCatcher.implicitHeight") and h.ev("root.shownHeight") != hh)
h.ev("root.showView('board')"); h.spin(200)
h.finish()
fails = [n for n, c in h.results if not c]
print("passed %d failed %d" % (len(h.results) - len(fails), len(fails)))
sys.exit(1 if fails else 0)
