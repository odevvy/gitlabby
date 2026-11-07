import QtQuick
import Quickshell.Io

// One list fetched on demand per scope, for a view every widget copy shares
// (Merge requests, To-do). A copy asks with request(scope, force) when the view
// opens, its scope changes, or r there; never on a timer. An answer under a
// minute old is shown again (a second screen, the scope flipped back) unless
// force. One scope loads at a time; one asked for meanwhile waits its turn (the
// last one asked). answers: { scope: { data: parse(raw), startedAt } }.
// clear() (sign out, another server) forgets them; an answer already on its way
// is dropped (the service's generation). A Process itself, so the service lists
// it with its other fetches.
Process {
  id: list
  // Set by BoardService. Not `required`: qmllint (CI) misses bindings on a
  // Process-based type and would call them unset.
  property var service  // helperCommand(args) and generation
  property var args     // scope -> board-fetch arguments
  property var parse    // raw stdout -> the checked answer
  property var answers: ({})
  readonly property string loading: running ? scope : ""
  property var pending: null     // { scope, force }
  property string scope: ""
  property int generation: 0
  property real startedAt: 0

  // maxAgeMs: how old an answer may be and still do (60 s when not given).
  // Returns true when that answer does and nothing is fetched.
  function request(next, force, maxAgeMs) {
    if (loading === next) return false
    var last = answers[next]
    if (!force && last && Date.now() - last.startedAt < (maxAgeMs || 60000)) return true
    if (running) { pending = { scope: next, force: force === true }; return false }
    scope = next
    generation = service.generation
    startedAt = Date.now()
    command = service.helperCommand(args(next))
    running = true
    return false
  }
  function clear() { answers = ({}); pending = null }
  function done(raw) {
    if (generation !== service.generation) return
    var a = {}
    for (var k in answers) a[k] = answers[k]
    a[scope] = { data: parse(raw), startedAt: startedAt }
    answers = a
  }
  function next() {
    var p = pending
    pending = null
    if (p) request(p.scope, p.force)
  }
  onRunningChanged: if (!running) Qt.callLater(list.next)
  stdout: StdioCollector { waitForEnd: true; onStreamFinished: list.done(text) }
}
