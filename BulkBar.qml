import QtQuick
import Quickshell.Io
import qs.Commons
import "Logic.js" as Logic
import "components"

// Bulk actions on the picked cards (host.picked; v or Ctrl+click picks one).
// Nothing is written until the second step: the first (a button, Shift+H/L,
// x, or a label) arms the bar, which says what happens to which card; the
// same key again, Enter or the main button confirms; Esc steps back.
// Writes run one card at a time in one board-fetch bulk process: each card
// is one stdin line with the single-card write's arguments (move, relabel,
// close, reopen), answered by one line, each with its own outcome. An ordinary
// failure is shown and the run goes on; signed out, no glab or no answer in
// time stops it. Esc while running stops before the next card.
// mode: "" (picking), "column" or "label" (choosing the target), "armed",
// "running", "results".
Rectangle {
  id: bar
  required property var host
  property string mode: ""
  property string labelOp: "add"      // label mode: add or remove
  property var action: null           // { kind, to | label }
  property string armKey: ""          // the key that armed it confirms too
  property var plan: []
  property var results: []            // [{ iid, status: done|failed|skipped|untried, text }]
  property int step: -1               // index in plan while running
  property bool stopping: false
  property string note: ""            // e.g. the cap, under the buttons
  // Labels for the label step: board-fetch labels (GET), loaded on first use per project.
  property string labelsFor: ""
  property string labelsState: ""
  property string labelsError: ""
  property var allLabels: []
  property var fetchedStatus: []

  readonly property var cards: Logic.pickedCards(host.columns, host.picked)
  readonly property bool armed: mode === "armed"
  readonly property bool running: mode === "running"
  readonly property bool busy: running || runProcess.running
  readonly property bool typing: mode === "label" && labelPicker.field.activeFocus
  readonly property var todo: plan.filter(function(s) { return !!s.args })
  readonly property var status: Logic.statusLabels(fetchedStatus, host.columns)
  readonly property var labelOptions: {
    if (labelsState !== "ready") return []
    var needle = labelPicker.filter.trim().toLowerCase()
    var on = {}
    cards.forEach(function(p) { (p.row.labels || []).forEach(function(l) { on[l] = true }) })
    return allLabels.filter(function(l) {
      return !Logic.has(status, l.name) && l.name.toLowerCase().indexOf(needle) !== -1 && (labelOp === "add" || on[l.name] === true)
    })
  }
  readonly property var lines: armed ? Logic.bulkLines(plan, action) : []
  readonly property var doneIids: results.filter(function(r) { return r.status === "done" }).map(function(r) { return "#" + r.iid }).join(" ")
  // While running only the failures so far; after it, every card not done.
  readonly property var otherResults: results.filter(function(r) { return mode === "results" ? r.status !== "done" : r.status === "failed" })
  visible: host.view === "board" && host.setup === "" && (host.picked.length > 0 || mode === "running" || mode === "results")
  implicitHeight: column.implicitHeight + Style.space(20)
  color: armed ? Qt.rgba(host.accent.r, host.accent.g, host.accent.b, 0.08) : "transparent"
  border { width: armed ? 2 : 1; color: mode === "results" && otherResults.some(function(r) { return r.status === "failed" || r.status === "untried" }) ? host.urgent : host.accent }
  radius: Style.space(6)

  function reset() { mode = ""; action = null; armKey = ""; plan = []; results = []; step = -1; stopping = false; note = "" }
  function pickNote(full) { note = full ? "Up to " + Logic.bulkCap + " cards at a time." : "" }

  // Arming. key: the text key that armed it ("" for a click).
  function arm(next, key) {
    // A write the watchdog gave up on (here or a single move) hasn't ended yet.
    if (!running && (runProcess.running || host.moveStillRunning)) { note = host.stillFinishing; return }
    if (busy || host.picked.length === 0 || !host.canMove) return
    action = next
    armKey = key || ""
    plan = Logic.bulkPlan(cards, next, host.project, host.resolvedBoardId)
    mode = "armed"
    host.focusBoard()  // keys back to the panel (from the label filter)
  }
  function armMove(to, key) { arm({ kind: "move", to: to }, key) }
  // Shift+H/L: the nearest column the cards can go to on that side of the
  // cursor's column (or of the first picked card's).
  function armSide(dx, key) {
    var at = host.cursor ? host.cursor.col : -1
    if (at < 0 && cards.length > 0) at = host.shownColumns.map(function(c) { return Logic.columnKey(c) }).indexOf(Logic.columnKey(cards[0].column))
    if (at < 0) return
    for (var i = at + dx; i >= 0 && i < host.shownColumns.length; i += dx)
      if (host.canDrop(host.shownColumns[i])) { armMove(host.shownColumns[i], key); return }
  }
  function armClose(key) { arm({ kind: Logic.closeOrReopen(cards) }, key) }
  function chooseLabel(op) {
    if (busy || host.picked.length === 0 || !host.canMove) return
    labelOp = op
    mode = "label"
    labelPicker.filter = ""
    loadLabels()
    Qt.callLater(function() { if (labelsState === "ready") labelPicker.field.forceActiveFocus() })
  }
  function loadLabels() {
    if (labelsFor === host.project && labelsState === "ready") return
    if (labelsProcess.running) return
    labelsFor = host.project
    labelsState = "loading"
    labelsProcess.command = [host.helperPath(), "labels", "--project", host.project]
    labelsProcess.running = true
  }
  function labelsDone(raw) {
    var data = host.parse(raw)
    if (labelsFor !== host.project) { labelsState = ""; return }
    labelsState = data.state === "ready" ? "ready" : "error"
    labelsError = data.state === "ready" ? "" : String(data.message || "Could not load labels.")
    if (data.state === "ready") { allLabels = data.labels || []; fetchedStatus = data.status || [] }
    if (labelsState === "ready" && mode === "label") labelPicker.field.forceActiveFocus()
  }
  function backToPicking() { if (busy || mode === "results") return; mode = ""; action = null; armKey = ""; plan = []; host.focusBoard() }

  // Esc: one step back. Returns false when the bar has nothing to undo.
  function stepBack() {
    if (running) { stopping = true; return true }
    if (mode === "results") { done(); return true }
    if (mode !== "") { backToPicking(); return true }
    if (host.picked.length > 0) { host.picked = []; note = ""; return true }
    return false
  }

  function confirm() {
    if (!armed || todo.length === 0 || runProcess.running || host.move !== null) return
    results = plan.map(function(s) { return { iid: s.iid, key: s.key, status: s.skip ? "skipped" : "untried", text: s.skip } })
    stopping = false
    mode = "running"
    step = -1
    next()
  }
  function next() {
    for (var i = step + 1; i < plan.length; i++) if (plan[i].args) break
    if (i >= plan.length) { finish(); return }
    step = i
    watchdog.restart()
    if (runProcess.running) { runProcess.write(JSON.stringify(plan[i].args) + "\n"); return }
    pendingLine = JSON.stringify(plan[i].args) + "\n"  // written once it has started
    runProcess.command = [host.helperPath(), "bulk", "--project", host.project]
    runProcess.stdinEnabled = true
    runProcess.running = true
  }
  property string pendingLine: ""
  function setResult(i, status, text) {
    var r = results.slice()
    r[i] = Object.assign({}, r[i], { status: status, text: text })
    results = r
  }
  function stepDone(raw) {
    if (!running) return  // a late answer after the watchdog gave up
    watchdog.stop()
    var data = host.parse(raw)
    var out = Logic.bulkOutcome(data, action)
    if (!out.ok) host.feed.noteRefused(host.project, data.message)  // a 403: view-only here
    setResult(step, out.ok ? "done" : "failed", out.text)
    if (out.ok) host.feed.noteOwnMove(host.fetchKey, plan[step].iid)  // no alert for his own change
    if (out.stop) stopping = true
    if (stopping) { finish(); return }
    next()
  }
  function finish() {
    runProcess.stdinEnabled = false  // end of input: board-fetch ends after the card it is on
    var r = results.map(function(x) { return x.status === "untried" ? Object.assign({}, x, { text: stopping ? "Not tried: the run stopped." : x.text }) : x })
    results = r
    host.bulkFinished()  // before busy ends, so the queued refresh runs then
    mode = "results"
    step = -1
  }
  function done() { reset(); host.picked = []; host.focusBoard() }
  function keepFailed() {
    var keys = results.filter(function(r) { return r.status === "failed" || r.status === "untried" }).map(function(r) { return r.key })
    reset()
    host.picked = Logic.livePicks(host.columns, keys)
  }

  Process {
    id: runProcess
    onStarted: { if (bar.pendingLine !== "") write(bar.pendingLine); bar.pendingLine = "" }
    // Ended without answering the card it was on: that card has no answer.
    onRunningChanged: if (!running && bar.running) Qt.callLater(function() { if (!runProcess.running && bar.running) bar.stepDone("") })
    stdout: SplitParser { onRead: function(line) { bar.stepDone(line) } }
  }
  Process {
    id: labelsProcess
    stdout: StdioCollector { waitForEnd: true; onStreamFinished: bar.labelsDone(text) }
  }
  // No answer in 50 s (board-fetch ends by its 40 s deadline): count it as a
  // timeout, which may have gone through, and stop.
  Timer {
    id: watchdog; interval: 50000
    onTriggered: bar.stepDone(JSON.stringify({ state: "timeout", message: "No answer from glab in 50 seconds." }))
  }

  Column {
    id: column
    anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter; margins: Style.space(10) }
    spacing: Style.space(8)

    // --- picking, and choosing a column or a label ----------------------------
    Row {
      visible: bar.mode === "" || bar.mode === "column" || bar.mode === "label"
      spacing: Style.space(10)
      BoardText { anchors.verticalCenter: parent.verticalCenter; text: bar.host.picked.length + (bar.host.picked.length === 1 ? " card selected" : " cards selected"); font.bold: true }
      BoardText { anchors.verticalCenter: parent.verticalCenter; text: bar.cards.map(function(p) { return "#" + p.row.iid }).join("  "); color: bar.host.dim; font.pixelSize: Style.font.bodySmall }
    }
    Flow {
      visible: bar.mode === ""
      width: parent.width; spacing: Style.space(8)
      ActionButton { objectName: "bulkMoveTo"; host: bar.host; small: true; enabled: bar.host.canMove; label: "Move to \u25be"; onClicked: bar.mode = "column" }
      ActionButton { objectName: "bulkAdd"; host: bar.host; small: true; enabled: bar.host.canMove; label: "Add label \u25be"; onClicked: bar.chooseLabel("add") }
      ActionButton { objectName: "bulkRemove"; host: bar.host; small: true; enabled: bar.host.canMove; label: "Remove label \u25be"; onClicked: bar.chooseLabel("remove") }
      ActionButton { objectName: "bulkClose"; host: bar.host; small: true; enabled: bar.host.canMove; label: (Logic.closeOrReopen(bar.cards) === "close" ? "Close " : "Reopen ") + bar.host.picked.length; onClicked: bar.armClose("") }
      ActionButton { objectName: "bulkClear"; host: bar.host; small: true; label: "Clear"; onClicked: bar.stepBack() }
    }
    Flow {
      visible: bar.mode === "column"
      width: parent.width; spacing: Style.space(8)
      Repeater {
        model: bar.host.shownColumns.filter(function(c) { return bar.host.canDrop(c) })
        delegate: ActionButton { required property var modelData; objectName: "bulkColumn"; host: bar.host; small: true; label: modelData.name; onClicked: bar.armMove(modelData, "") }
      }
      ActionButton { host: bar.host; small: true; label: "Back"; onClicked: bar.backToPicking() }
    }
    LabelPicker {
      id: labelPicker
      visible: bar.mode === "label"
      width: parent.width
      host: bar.host; colors: Logic.withColors(bar.host.labelColors, bar.allLabels)
      options: bar.labelOptions
      labelsState: bar.labelsState
      error: bar.labelsState === "error" ? bar.labelsError : ""
      emptyText: bar.labelOp === "add" ? "No labels to add." : "The selected cards have no labels to remove."
      onPicked: function(name) { bar.arm({ kind: bar.labelOp, label: name }, "") }
      onEscaped: bar.backToPicking()
      ActionButton { host: bar.host; small: true; height: labelPicker.field.height; label: "Back"; onClicked: bar.backToPicking() }
    }
    BoardText {
      visible: bar.mode === ""
      width: parent.width; wrapMode: Text.Wrap
      text: bar.note !== "" ? bar.note : !bar.host.canMove ? "Wait for the board to load before changing cards."
        : "v picks the card under the cursor  \u00b7  Ctrl+click picks a card  \u00b7  Shift+H/L, x or e pick an action  \u00b7  Esc clears"
      color: bar.note !== "" ? bar.host.urgent : bar.host.dim; font.pixelSize: Style.font.caption
    }

    // --- armed: exactly what happens ---------------------------------------------
    BoardText { objectName: "bulkQuestion"; visible: bar.armed; width: parent.width; wrapMode: Text.Wrap; text: bar.armed ? Logic.bulkQuestion(bar.action, bar.todo.length) : ""; font.bold: true }
    Column {
      visible: bar.armed
      width: parent.width; spacing: Style.space(2)
      Repeater {
        model: bar.lines
        delegate: Row {
          required property var modelData
          objectName: "bulkLine"
          spacing: Style.space(10)
          BoardText { text: modelData.text; color: modelData.skip ? bar.host.dim : bar.host.accent; font.pixelSize: Style.font.bodySmall }
          BoardText { text: modelData.iids; color: modelData.skip ? bar.host.dim : bar.host.foreground; font.pixelSize: Style.font.bodySmall }
        }
      }
    }
    BoardText { visible: bar.armed; width: parent.width; wrapMode: Text.Wrap; text: bar.armed ? Logic.bulkNote(bar.action) : ""; color: bar.host.dim; font.pixelSize: Style.font.bodySmall }
    Row {
      visible: bar.armed
      spacing: Style.space(8)
      ActionButton { objectName: "bulkConfirm"; host: bar.host; small: true; main: true; enabled: bar.todo.length > 0; label: bar.armed ? Logic.bulkButton(bar.action, bar.todo.length) : ""; onClicked: bar.confirm() }
      ActionButton { host: bar.host; small: true; label: "Cancel"; onClicked: bar.backToPicking() }
      BoardText {
        anchors.verticalCenter: parent.verticalCenter; leftPadding: Style.space(6)
        text: (bar.armKey === "H" || bar.armKey === "L" ? "Enter or Shift+" + bar.armKey + " again confirms" : bar.armKey === "x" ? "Enter or x again confirms" : "Enter confirms") + "  \u00b7  Esc cancels"
        color: bar.host.dim; font.pixelSize: Style.font.caption
      }
    }

    // --- running and results ------------------------------------------------------
    Row {
      visible: bar.running
      spacing: Style.space(8)
      Spinner { running: bar.running; anchors.verticalCenter: parent.verticalCenter }
      BoardText {
        objectName: "bulkProgress"
        anchors.verticalCenter: parent.verticalCenter
        text: bar.running ? (bar.stopping ? "Stopping after #" + bar.plan[bar.step].iid + "…"
          : "Working on #" + (bar.step >= 0 ? bar.plan[bar.step].iid : "") + " (" + (bar.results.filter(function(r) { return r.status === "done" || r.status === "failed" }).length + 1) + " of " + bar.todo.length + ")  \u00b7  Esc stops after this card") : ""
        font.bold: true
      }
    }
    BoardText { objectName: "bulkSummary"; visible: bar.mode === "results"; width: parent.width; wrapMode: Text.Wrap; text: bar.mode === "results" ? Logic.bulkSummary(bar.action, bar.results) : ""; font.bold: true }
    BoardText {
      visible: (bar.running || bar.mode === "results") && bar.doneIids !== ""
      width: parent.width; wrapMode: Text.Wrap
      text: "\uf058  " + Logic.bulkOutcome({ state: "ready" }, bar.action || { kind: "close" }).text + ": " + bar.doneIids
      color: "#2da160"; font.pixelSize: Style.font.bodySmall
    }
    Column {
      visible: (bar.running || bar.mode === "results") && bar.otherResults.length > 0
      width: parent.width; spacing: Style.space(3)
      Repeater {
        model: bar.otherResults
        delegate: BoardText {
          required property var modelData
          objectName: "bulkResult"
          width: parent.width; wrapMode: Text.Wrap
          text: (modelData.status === "failed" ? "\uf057  " : "\u00b7  ") + "#" + modelData.iid + "  " + modelData.text
          color: modelData.status === "failed" ? bar.host.urgent : bar.host.dim
          font.pixelSize: Style.font.bodySmall
        }
      }
    }
    Row {
      visible: bar.mode === "results"
      spacing: Style.space(8)
      ActionButton { objectName: "bulkDone"; host: bar.host; small: true; main: true; label: "Done"; onClicked: bar.done() }
      ActionButton {
        objectName: "bulkKeep"
        readonly property int n: bar.otherResults.filter(function(r) { return r.status === "failed" || r.status === "untried" }).length
        visible: n > 0; host: bar.host; small: true
        label: "Keep " + (n === 1 ? "it" : "these " + n) + " selected"; onClicked: bar.keepFailed()
      }
      BoardText { anchors.verticalCenter: parent.verticalCenter; leftPadding: Style.space(6); text: "Esc closes this"; color: bar.host.dim; font.pixelSize: Style.font.caption }
    }
  }
}
