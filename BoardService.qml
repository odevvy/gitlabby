import QtQuick
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

  // { key: { raw, ticket, startedAt (ms) } }: the last answer per board.
  property var answers: ({})
  // { key: { sig, calm, active } }: how much each board has been changing
  // (Logic.nextPace); every screen paces its refresh timer from it.
  property var paces: ({})
  // Boards waiting while another one loads, next first: [{ key, args }].
  property var queue: []
  readonly property var queuedKeys: queue.map(function(q) { return q.key })
  readonly property string runningKey: fetch.running ? fetch.key : ""
  // Fetches started so far; each answer carries its own number (ticket).
  property int tickets: 0
  // Bumped by forget() (sign out): answers to older requests are dropped.
  property int generation: 0
  signal answered(string key, string raw, int ticket)

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
    fetch.command = [helperPath()].concat(job.args)
    queue = queue.slice(1)
    fetch.running = true
  }

  function done(raw) {
    if (fetch.generation !== generation) return
    var stored = {}
    for (var k in answers) stored[k] = answers[k]
    stored[fetch.key] = { raw: raw, ticket: fetch.ticket, startedAt: fetch.startedAt }
    answers = stored
    var data = null
    try { data = JSON.parse(String(raw || "")) } catch (error) {}
    var pace = Logic.nextPace(paces[fetch.key], data)
    if (pace) {
      var p = {}
      for (var q in paces) p[q] = paces[q]
      p[fetch.key] = pace
      paces = p
    }
    answered(fetch.key, raw, fetch.ticket)
  }

  // Sign out: forget every answer and drop the ones on their way.
  function forget() {
    generation++
    answers = ({})
    paces = ({})
    queue = []
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
}
