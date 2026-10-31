import QtQuick
// Stand-in: never runs anything. The harness answers a "running" process by
// setting stdout.text, emitting stdout.streamFinished(), then running = false and exited().
QtObject {
  property var command: []
  property bool running: false
  property var stdout: null
  property var stderr: null
  property bool stdinEnabled: false
  property var environment: ({})
  property var written: []
  signal started()
  signal exited(int exitCode, int exitStatus)
  function write(s) { if (running && stdinEnabled) written = written.concat([String(s)]) }
  // A board-fetch bulk process: the harness answers each written line with one
  // stdout.read(); closing stdin with no line left unanswered ends it.
  property int readCount: 0
  function endIfDone() { if (running && !stdinEnabled && command && command[1] === "bulk" && written.length <= readCount) { running = false; exited(0, 0) } }
  onStdinEnabledChanged: endIfDone()
  onRunningChanged: if (running) { if (command && command[1] === "bulk") { written = []; readCount = 0 } started() }
}
