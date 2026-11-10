# 0.1.133 (SEC-01): copyLink uses the same configured-host check as a click.
# Off-host or non-https links are not copied; on-host https links are.
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from fixtures import BOARD

h = Harness(sys.argv[1], {"id": "odevvy.gitlabby", "settingsRevision": 2, "defaultProject": "group/app"})
h.ev("root.opened = true"); h.spin(50); h.answer("board", BOARD); h.spin(200)

def try_copy(url):
    h.ev("root.copiedNote = ''")
    n = len(h.launched())
    ok = h.ev("root.copyLink({url: %s, iid: 2}, '#')" % json.dumps(url))
    h.spin(30)
    return ok, h.launched()[n:], h.ev("root.copiedNote")

on = "https://gitlab.com/group/app/-/issues/2"
off = "https://evil.example/phish"
ok, launched, note = try_copy(on)
h.ok("on-host https is copied", ok is True and launched == [["wl-copy", on]] and note == "Copied #2", (ok, launched, note))
ok, launched, note = try_copy(off)
h.ok("off-host https is not copied", ok is False and launched == [] and note == "", (ok, launched, note))
for bad in ["javascript:alert(1)", "file:///etc/passwd", "http://gitlab.com/group/app/-/issues/2", ""]:
    ok, launched, note = try_copy(bad)
    h.ok("non-https is not copied: " + (bad or "(empty)"), ok is False and launched == [] and note == "", (bad, ok, launched, note))

h.ev("root.settings = Object.assign({}, root.settings, {gitlabHost: 'gitlab.example'})")
h.spin(60)
ok, launched, note = try_copy("https://gitlab.example/group/app/-/issues/2")
h.ok("the configured self-hosted server is copied", ok is True and launched == [["wl-copy", "https://gitlab.example/group/app/-/issues/2"]] and note == "Copied #2", (ok, launched, note))
ok, launched, note = try_copy(on)
h.ok("the previous host is not copied after a switch", ok is False and launched == [] and note == "", (ok, launched, note))
sys.exit(h.finish())
