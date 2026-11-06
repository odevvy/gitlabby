# v0.1.40: the header moved into BoardHeader.qml with no change: it spans the
# panel, its controls sit at the right edge in order, the title shows the
# project and board, and the merge-request badge counts MrsView's scope.
# Usage: run140.py <src> [outdir]   (preview: header-split)
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from fixtures import BOARD
out = sys.argv[2] if len(sys.argv) > 2 else None
h = Harness(sys.argv[1], {"id": "odevvy.gitlabby", "settingsRevision": 2, "defaultProject": "group/app"})
def shot(name): QTest.mouseMove(h.win, QPoint(1, 1)); h.spin(60); out and h.grab_card(os.path.join(out, name + ".png"))
h.ev("root.opened = true"); h.spin(80); h.answer("board", BOARD); h.spin(150)
hw, kw = h.ev("header.width"), h.ev("keyCatcher.width")
h.ok("S1 the header spans the panel", hw > 300 and abs(hw - kw) < 1, [hw, kw])
right = h.ev("header.gear.x + header.gear.width")
h.ok("S2 the gear ends at the header's right edge", abs(right - hw) < 1, [right, hw])
xs = [h.ev("header." + n + ".x") for n in ("status", "refreshButton", "keysButton", "gear")]
mx = h.ev("header.mrsButton.mapToItem(header, 0, 0).x")
h.ok("S3 status, refresh, keys, gear, left to right; merge requests after the title", xs == sorted(xs) and xs[0] > h.ev("header.chevron.x") and mx > h.ev("header.chevron.x"), xs + [mx])
h.ok("S4 the title names the project", "group/app" in h.ev("header.children[0].text"), h.ev("header.children[0].text"))
h.ok("S5 the badge reads MrsView's scope", h.ev("header.mrsScope") == h.ev("mrsView.scope") and h.ev("header.mrsScope") != "", h.ev("header.mrsScope"))
shot("header-split")
h.finish()
