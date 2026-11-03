import QtQuick
import Quickshell
import Quickshell.Io
import "Logic.js" as Logic

// One board fetch for the whole shell. Omarchy draws a bar on every screen, so
// the widget runs once per screen (Bar.qml: Variants over Quickshell.screens;
// moduleWidgets: "live once per screen"). This file is also the manifest's
// "service" entry point, which the shell creates once (shell.qml
// ensureService), and every copy reaches it through bar.shell.serviceFor().
// So one board-fetch runs per board at a time, and its answer goes to every
// copy showing that board. Under a replacement bar there is no service: the
// widget makes a private one of these and behaves as before (Board.qml).
Item {
  id: service
  // Host injection (shell.qml ensureService); not used.
  property var shell: null
  property var manifest: null
  property string omarchyPath: ""

  // { key: { raw, ticket, startedAt (ms), state } }: the last answer per board.
  property var answers: ({})
  // { key: { sig, calm, active } }: how much each board has been changing
  // (Logic.nextPace); every screen paces its refresh timer from it.
  property var paces: ({})
  // Desktop alerts. watchers: { key: { owner: { key, project, boardId, review,
  // idle, bots, base } } }, one entry per widget copy whose board has an alert
  // on. baselines: { key: the last good answer } while watched; the next good
  // one is compared with it (Logic.alertEvents) here only, so one notification
  // per event however many screens. ownMoves: { key: [{ iid, after }] } cards
  // this user moved, not announced back to him.
  property var watchers: ({})
  // Alerts sent since a popup was last open, on any screen: the bar icon's
  // dot (Board.iconLit). seenAlerts() when a popup opens, or is open.
  property int unseenAlerts: 0
  function seenAlerts() { unseenAlerts = 0 }
  property var baselines: ({})
  property var ownMoves: ({})
  readonly property var watchedKeys: Object.keys(watchers)
  // Boards waiting while another one loads, next first: [{ key, args }].
  property var queue: []
  readonly property var queuedKeys: queue.map(function(q) { return q.key })
  readonly property string runningKey: fetch.running ? fetch.key : ""
  // Fetches started so far; each answer carries its own number (ticket).
  property int tickets: 0
  // Bumped by forget() (sign out): answers to older requests are dropped.
  property int generation: 0
  signal answered(string key, string raw, int ticket)

  // The Merge requests view: { scope: { data (Logic.mrsAnswer), startedAt } },
  // scope "all" or a project path. Fetched only when a widget copy asks (the
  // view opens, its scope changes, or r there); never on a timer. Its own
  // Process, so it never waits behind a board, and one answer for every screen.
  property var mrAnswers: ({})
  readonly property string mrRunning: mrFetch.running ? mrFetch.scope : ""
  property var mrPending: null  // { scope, force }: asked for while another scope loads
  signal mrsAnswered(string scope)

  // Write access per project: { project: Logic.accessEntry }. Asked once per
  // project per session (board-fetch access, GETs only), when its board first
  // loads; a write GitLab refuses (403, or a token without api) marks it too.
  // Never on a timer. Board.qml turns writes off and shows AccessHint.qml.
  property var access: ({})
  property var accessWaiting: []  // projects asked for while another one loads
  function requestAccess(project) {
    if (project === "" || access[project] !== undefined || accessWaiting.indexOf(project) !== -1) return
    if (accessFetch.running) { if (accessFetch.project !== project) accessWaiting = accessWaiting.concat([project]); return }
    accessFetch.project = project
    accessFetch.generation = generation
    accessFetch.command = helperCommand(["access", "--project", project])
    accessFetch.running = true
  }
  function accessDone(raw) { if (accessFetch.generation === generation) setAccess(accessFetch.project, Logic.accessEntry(raw)) }
  function accessNext() { var w = accessWaiting; if (w.length > 0) { accessWaiting = w.slice(1); requestAccess(w[0]) } }
  function setAccess(project, entry) {
    var a = {}
    for (var k in access) a[k] = access[k]
    a[project] = entry
    access = a
  }
  function noteRefused(project, message) {
    var kind = Logic.writeRefusal(message)
    if (kind !== "" && project !== "") setAccess(project, Logic.refusedEntry(access[project], kind))
  }

  // The GitLab server every board-fetch here runs against (--hostname), from
  // the widget's setting. Another one forgets everything from the last.
  property string host: "gitlab.com"
  function setHost(h) { if (h === host) return; host = h; forget() }
  function helperCommand(args) { return [helperPath()].concat(args, ["--hostname", host]) }

  function keyOf(project, boardId) { return project + "#" + boardId }
  function busy(key) { return runningKey === key || queuedKeys.indexOf(key) !== -1 }

  // The board of project/boardId. A request joins a fetch of that board that is
  // running (or waiting) and started at or after minTicket. ifDue (the timer,
  // opening the popup): the last answer, if its fetch started under maxAgeMs ago
  // and at or after minTicket, is returned instead; no fetch. Otherwise (Refresh,
  // r, a click on the icon, after a move) a new fetch. The answer comes as
  // answered(); a returned one is the caller's alone.
  function request(project, boardId, ifDue, maxAgeMs, minTicket) {
    var key = keyOf(project, boardId)
    if (runningKey === key && fetch.ticket >= minTicket) return null
    if (queuedKeys.indexOf(key) !== -1) return null
    var last = answers[key]
    if (ifDue && last && last.ticket >= minTicket && Date.now() - last.startedAt < maxAgeMs) return last
    // Newest first: a board just switched to goes before one left behind.
    queue = [{ key: key, args: ["board", "--project", project, "--board", boardId] }].concat(queue)
    next()  // at once if nothing runs, as the widget's own fetch did
    return null
  }

  function next() {
    if (fetch.running || queue.length === 0) return
    var job = queue[0]
    tickets++
    fetch.key = job.key
    fetch.ticket = tickets
    fetch.generation = generation
    fetch.startedAt = Date.now()
    fetch.command = helperCommand(job.args)
    queue = queue.slice(1)
    fetch.running = true
  }

  function done(raw) {
    if (fetch.generation !== generation) return
    var stored = {}
    for (var k in answers) stored[k] = answers[k]
    var data = null
    try { data = JSON.parse(String(raw || "")) } catch (error) {}
    stored[fetch.key] = { raw: raw, ticket: fetch.ticket, startedAt: fetch.startedAt, state: data ? String(data.state || "") : "" }
    answers = stored
    var pace = Logic.nextPace(paces[fetch.key], data)
    if (pace) {
      var p = {}
      for (var q in paces) p[q] = paces[q]
      p[fetch.key] = pace
      paces = p
    }
    watchAnswer(fetch.key, data, fetch.ticket)
    answered(fetch.key, raw, fetch.ticket)
  }

  // A widget copy's alerts for the board it shows (cfg.key), or null for none.
  // A board that stops being watched loses its baseline, so when it is watched
  // again its next answer is a first load, never announced.
  function watch(owner, cfg) {
    var next = {}, key
    for (key in watchers) {
      var owners = {}, any = false
      for (var o in watchers[key]) if (o !== owner) { owners[o] = watchers[key][o]; any = true }
      if (any) next[key] = owners
    }
    if (cfg && (cfg.review || cfg.idle)) {
      if (!next[cfg.key]) next[cfg.key] = {}
      next[cfg.key][owner] = cfg
    }
    for (key in baselines) if (!next[key]) dropBaseline(key)
    watchers = next
  }
  function dropBaseline(key) {
    var b = {}
    for (var k in baselines) if (k !== key) b[k] = baselines[k]
    baselines = b
  }
  function noteOwnMove(key, iid) {
    var m = {}
    for (var k in ownMoves) m[k] = ownMoves[k]
    m[key] = (m[key] || []).concat([{ iid: Number(iid), after: tickets + 1 }])
    ownMoves = m
  }
  function cfgOf(key) {
    var owners = watchers[key]
    for (var o in owners) return owners[o]
    return null
  }
  // A good answer after a good one: notify. A failed one drops the baseline,
  // so the answer after it is a fresh start, not announced either.
  function watchAnswer(key, data, ticket) {
    var cfg = cfgOf(key)
    if (!cfg) return
    if (!data || data.state !== "ready") { dropBaseline(key); return }
    var moved = ownMoves[key] || []
    var events = baselines[key] ? Logic.alertEvents(baselines[key], data, { review: cfg.review, idle: cfg.idle, bots: cfg.bots, ignore: moved.map(function(m) { return m.iid }), host: cfg.host }) : []
    events.forEach(function(ev) { Quickshell.execDetached(Logic.notifyArgv(ev, cfg.links)) })
    unseenAlerts += events.length
    var b = {}, k
    for (k in baselines) b[k] = baselines[k]
    b[key] = data
    baselines = b
    var m = {}
    for (k in ownMoves) m[k] = ownMoves[k]
    m[key] = moved.filter(function(x) { return ticket < x.after })
    ownMoves = m
  }

  // With the popup closed nothing else refreshes: a watched board is fetched
  // here when due at its pace (Logic.adaptiveInterval), as the timer would.
  // Not while signed out or without glab: the popup's setup panel handles that.
  function background() {
    watchedKeys.forEach(function(key) {
      var cfg = cfgOf(key), last = answers[key]
      if (!cfg || (last && (last.state === "logged-out" || last.state === "no-glab"))) return
      var cad = Logic.adaptiveInterval(cfg.base, paces[key])
      request(cfg.project, cfg.boardId, true, cad.sec * 1000 - 2000, 0)
    })
  }
  Timer {
    id: backgroundTimer
    interval: 15000; repeat: true
    running: service.watchedKeys.length > 0
    onTriggered: service.background()
  }

  // An answer under a minute old is shown again (a second screen opening the
  // view, or flipping the scope back), unless force (r).
  function requestMrs(scope, force) {
    if (mrRunning === scope) return
    var last = mrAnswers[scope]
    if (!force && last && Date.now() - last.startedAt < 60000) return
    if (mrFetch.running) { mrPending = { scope: scope, force: force === true }; return }
    mrFetch.scope = scope
    mrFetch.generation = generation
    mrFetch.startedAt = Date.now()
    mrFetch.command = helperCommand(Logic.mrsArgs(scope))
    mrFetch.running = true
  }
  function mrsDone(raw) {
    if (mrFetch.generation !== generation) return
    var a = {}
    for (var k in mrAnswers) a[k] = mrAnswers[k]
    a[mrFetch.scope] = { data: Logic.mrsAnswer(raw), startedAt: mrFetch.startedAt }
    mrAnswers = a
    mrsAnswered(mrFetch.scope)
  }
  function mrsNext() {
    var p = mrPending
    mrPending = null
    if (p) requestMrs(p.scope, p.force)
  }

  // Sign out, or another server: forget every answer and drop the ones on their way.
  function forget() {
    generation++
    answers = ({})
    paces = ({})
    baselines = ({})
    ownMoves = ({})
    queue = []
    mrAnswers = ({})
    mrPending = null
    access = ({})
    accessWaiting = []
  }

  function helperPath() {
    return decodeURIComponent(Qt.resolvedUrl("board-fetch").toString().replace(/^file:\/\//, ""))
  }

  Process {
    id: fetch
    property string key: ""
    property int ticket: 0
    property int generation: 0
    property real startedAt: 0
    onRunningChanged: if (!running) Qt.callLater(service.next)
    stdout: StdioCollector { waitForEnd: true; onStreamFinished: service.done(text) }
  }
  Process {
    id: mrFetch
    property string scope: ""
    property int generation: 0
    property real startedAt: 0
    onRunningChanged: if (!running) Qt.callLater(service.mrsNext)
    stdout: StdioCollector { waitForEnd: true; onStreamFinished: service.mrsDone(text) }
  }
  Process {
    id: accessFetch
    property string project: ""
    property int generation: 0
    onRunningChanged: if (!running) Qt.callLater(service.accessNext)
    stdout: StdioCollector { waitForEnd: true; onStreamFinished: service.accessDone(text) }
  }
}
