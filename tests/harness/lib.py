# Shared harness: loads a copy of the plugin with the Omarchy stand-ins in ./stubs
# into an offscreen window. Usage in a test: from lib import *; h = Harness(src)
import sys, os, json, shutil, tempfile
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QUrl, QTimer, QObject, QPoint, QPointF, QRect, Qt, QEvent
from PySide6.QtGui import QGuiApplication, QFontDatabase, QKeyEvent
from PySide6.QtQml import QQmlApplicationEngine, QJSValue, QQmlExpression, QQmlEngine
from PySide6.QtTest import QTest
from PySide6.QtQuick import QQuickItem
HERE = os.path.dirname(os.path.abspath(__file__)); TOOLING = os.path.dirname(HERE)
app = QGuiApplication.instance() or QGuiApplication(sys.argv)
# Renders use the system fonts (Omarchy ships JetBrainsMono Nerd Font); OGB_FONTS
# may name a directory of extra font files.
for d in [os.environ.get("OGB_FONTS", ""), TOOLING + "/fonts"]:
    if d and os.path.isdir(d):
        for f in os.listdir(d): QFontDatabase.addApplicationFont(os.path.join(d, f))

class Harness:
    def __init__(self, src, settings=None):
        self.dir = tempfile.mkdtemp(prefix="ogb-h-"); dst = self.dir + "/app"
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns(".git")); shutil.copy(HERE + "/main.qml", dst + "/main.qml")
        self.eng = QQmlApplicationEngine(); self.eng.addImportPath(HERE + "/stubs")
        self.warnings = []; self.eng.warnings.connect(lambda ws: self.warnings.extend(w.toString() for w in ws))
        self.eng.load(QUrl.fromLocalFile(dst + "/main.qml"))
        if not self.eng.rootObjects(): print("LOAD FAILED"); print("\n".join(self.warnings)); sys.exit(1)
        self.win = self.eng.rootObjects()[0]; self.board = self.win.findChild(QQuickItem, "board")
        self.ctx = QQmlEngine.contextForObject(self.board.childItems()[0])  # Board.qml's ids (root, panel, settingsView, ...)
        self.results = []
        # bar.shell stand-in: records writes and feeds them back like the real shell.
        self.ev("root.bar = Qt.createQmlObject('import QtQuick; QtObject { property var shell: QtObject { property var writes: []; function updateEntryInline(id, s) { writes = writes.concat([JSON.parse(JSON.stringify(s))]); root.settings = JSON.parse(JSON.stringify(s)); return true } } }', root)")
        if settings is not None: self.ev("root.settings = " + json.dumps(settings))
    def ev(self, code, ctx=None, obj=None):
        e = QQmlExpression(ctx or self.ctx, obj or self.board, code); v = e.evaluate()
        if e.hasError(): print("JSERR", code[:100], e.error().toString())
        v = v[0] if isinstance(v, tuple) else v
        return v.toVariant() if isinstance(v, QJSValue) else v
    def ok(self, name, cond, extra=""):
        self.results.append((name, bool(cond))); print(("PASS " if cond else "FAIL ") + name + (("  " + str(extra)) if not cond and extra != "" else ""))
    def spin(self, ms):
        t = QTimer(); t.setSingleShot(True); t.start(ms)
        while t.isActive(): app.processEvents()
    # Spins until cond() holds or ms pass; returns cond()'s last value. For
    # waits on an animation or a timer, instead of a fixed spin that a busy
    # machine can outrun (run141's A1 was one).
    def until(self, cond, ms=3000, step=20):
        left = ms
        while not cond() and left > 0: self.spin(step); left -= step
        return cond()
    def walk(self, root=None):
        st = [root or self.win.contentItem()]
        while st:
            it = st.pop(); yield it; st.extend(it.childItems())
    def visible(self, pred): return [it for it in self.walk() if it.isVisible() and pred(it)]
    def cls(self, name): return next(it for it in self.walk() if it.metaObject().className().startswith(name))
    def ctx_of(self, item): return QQmlEngine.contextForObject(item.childItems()[0] if item.childItems() else item)
    # Processes declared on root and the views (Process stand-ins never run).
    PROCS = "(function(){ var r = []; function scan(o){ if (!o || !o.data) return; for (var i = 0; i < o.data.length; i++) { var c = o.data[i]; if (c && c.command !== undefined && c.stdout !== undefined) r.push(c) } } scan(root); if (root.feed) scan(root.feed); [issueView, settingsView, picker].forEach(scan); try { scan(bulkBar) } catch (e) {} return r })()"
    # A running board-fetch bulk process lists itself (kind "bulk") and, while
    # its last stdin line is unanswered, that card as the command it stands for.
    # gitlab.com's --hostname (v0.1.65: every command ends with the server) is
    # left off, so older tests read as before; raw=True keeps it (run165).
    def running(self, kind=None, raw=False):
        cs = self.ev(self.PROCS + ".reduce(function(r, p){ if (!p.running) return r; r.push(p.command);"
                     " if (p.command[1] === 'bulk' && p.written.length > p.readCount) r.push([p.command[0]].concat(JSON.parse(p.written[p.written.length - 1]))); return r }, [])") or []
        if not raw: cs = [c[:-2] if c and c[-2:] == ["--hostname", "gitlab.com"] else c for c in cs]
        return [c for c in cs if c and (kind is None or c[1] == kind)]
    def stop_all(self): self.ev(self.PROCS + ".forEach(function(p){ p.running = false })")
    def answer(self, kind, data):
        bulk = ("(function(){ var p = " + self.PROCS + ".filter(function(p){ return p.running && p.command[1] === 'bulk' && p.written.length > p.readCount"
                " && JSON.parse(p.written[p.written.length - 1])[0] === %s })[0];"
                " if (!p) return false; p.readCount = p.written.length; p.stdout.read(%s); p.endIfDone(); return true })()") % (json.dumps(kind), json.dumps(json.dumps(data)))
        if self.ev(bulk): self.spin(120); return True
        js = ("(function(){ var p = " + self.PROCS + ".filter(function(p){ return p.running && p.command[1] === %s })[0];"
              " if (!p) return false; p.stdout.text = %s; p.stdout.streamFinished(); p.running = false; p.exited(0, 0); return true })()") % (json.dumps(kind), json.dumps(json.dumps(data)))
        r = self.ev(js); self.spin(120); return r
    # Ages every saved board answer of the feed past any interval (a due timer tick fetches).
    def age_feed(self): self.ev("(function(){ if (!root.feed) return; var a = {}; for (var k in root.feed.answers) a[k] = Object.assign({}, root.feed.answers[k], { startedAt: 0 }); root.feed.answers = a })()")
    def launched(self): return self.ev("Quickshell.launched") or []
    def scene(self, it, fx=0.5, fy=0.5): c = it.mapToScene(QPointF(it.width() * fx, it.height() * fy)); return QPoint(int(c.x()), int(c.y()))
    def click(self, it): QTest.mouseClick(self.win, Qt.LeftButton, Qt.NoModifier, self.scene(it)); self.spin(120)
    def key(self, k, text=""):
        for typ in (QEvent.KeyPress, QEvent.KeyRelease): QGuiApplication.sendEvent(self.win, QKeyEvent(typ, k, Qt.NoModifier, text))
        self.spin(60)
    def grab_card(self, png):
        self.spin(200); img = self.win.grabWindow(); s = img.width() / self.win.width(); card = self.cls("KeyboardPanel")
        img.copy(QRect(int(card.x() * s) - 2, int(card.y() * s) - 2, int((card.width() + 4) * s), int((card.height() + 4) * s))).save(png)
    def finish(self):
        loops = [w for w in self.warnings if "oop" in w]
        self.ok("Z no binding-loop warnings", not loops, loops)
        self.ok("Z no QML warnings", not self.warnings, self.warnings[:3])
        print("QML warnings:", len(self.warnings)); print("\n".join(self.warnings[:30]))
        print("passed", sum(1 for _, c in self.results if c), "failed", sum(1 for _, c in self.results if not c))
        shutil.rmtree(self.dir, ignore_errors=True)
        return 0 if all(c for _, c in self.results) else 1
