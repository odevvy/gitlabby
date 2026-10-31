import QtQuick
import QtQuick.Controls
import Quickshell.Io
import qs.Commons
import qs.Ui
import "Logic.js" as Logic
import "components"

// One issue: title, state, labels, a one-line byline, the description as
// Markdown, then its comments and a box to add one. ✕ (or Esc) returns to the
// board. The issue and its comments load through `board-fetch issue` and
// `board-fetch notes` (GET); Post runs `board-fetch comment` with the text on stdin.
// Edit labels (a text action after the labels) lists the project's labels
// (`board-fetch labels`, GET) and adds or removes one at a time
// (`board-fetch relabel`). Status labels (the board's lists) are never
// offered: they change only by dragging the card.
// Close issue asks first, then runs `board-fetch close` (state only, labels
// stay); a closed issue offers Reopen issue (`board-fetch reopen`) instead.
Item {
  id: view
  required property var host
  // The host sets the card's row; the full issue replaces it once loaded.
  property var issue: ({})
  // The issue on screen ("" when hidden); it and its comments reload whenever it opens.
  readonly property string key: visible && issue.iid ? host.project + "#" + issue.iid : ""
  property string shownKey: ""
  property string issueFor: ""
  property string issueReadyFor: ""
  property string issueError: ""
  property bool issueQueued: false
  readonly property bool issueReady: key !== "" && issueReadyFor === key
  property var notes: []
  property bool more: false
  property bool notesLoading: false
  property string notesError: ""
  property string notesFor: ""
  property string notesAt: ""
  property bool reloadQueued: false
  property bool posting: false
  property string postFor: ""
  property string postError: ""
  readonly property bool typing: box.activeFocus || labelFilter.activeFocus
  readonly property Item labelFilter: labelEditor.field
  // The comment box (IssueComments.qml).
  readonly property Item box: comments.box
  // Label editor: open only on request; the label list loads when it opens.
  property bool editing: false
  property string labelsFor: ""      // the project the labels are for
  property double labelsAt: 0        // when they loaded (reused for 5 minutes)
  property string labelsState: ""  // "", loading, ready, error
  property string labelsError: ""
  property var allLabels: []
  property var fetchedStatus: []
  property string labelBusy: ""  // the label being added or removed
  property string relabelFor: ""
  property string labelError: ""
  readonly property var status: Logic.statusLabels(fetchedStatus, host.columns)
  readonly property var colors: Logic.withColors(host.labelColors, allLabels)
  readonly property var addable: labelsState === "ready" ? Logic.addableLabels(allLabels, issue.labels, status, labelFilter.text) : []
  readonly property int addableShown: 60
  // Close / reopen: one at a time; closing asks first.
  property bool confirming: false
  property string stateBusy: ""  // "close" or "reopen" while it runs
  property string stateFor: ""
  property string stateError: ""
  readonly property var statusOn: Logic.statusOn(issue.labels, status)
  // The comment box opens only once the issue and its comments have arrived.
  property string notesReadyFor: ""
  readonly property bool loaded: issueReady && notesReadyFor === key

  // Styles for the description, which Logic.markdown turns into Text.RichText HTML.
  readonly property string css: "<style>"
    + "p, pre { line-height: 130%; margin-top: 0; margin-bottom: " + Style.space(6) + "px }"  // Qt's default is 12px above and below
    + ".h1, .h2, .h3 { font-weight: bold; color: " + host.accent + "; margin-top: " + Style.space(14) + "px; margin-bottom: " + Style.space(2) + "px }"
    + ".h1, .h2 { font-size: " + (Style.font.bodySmall + 2) + "px } .h3 { font-size: " + (Style.font.bodySmall + 1) + "px }"
    + ".li { margin-bottom: " + Style.space(2) + "px } .quote { color: " + host.dim + " }"
    + "code, pre { background-color: " + host.faint + " }"
    + "a { color: " + host.accent + " }"  // RichText ignores linkColor (Qt docs: Text.linkColor)
    + "table { border-collapse: collapse; border-color: " + host.faint + "; margin-bottom: " + Style.space(6) + "px }</style>"

  onKeyChanged: {
    closeEditor()
    confirming = false; stateError = ""
    if (key === "") return
    if (key !== shownKey) {  // another issue: drop the last one's thread and draft
      shownKey = key
      notes = []; more = false; notesError = ""; postError = ""; box.text = ""
    }
    // (Re)opened: lock the box until this visit's issue and notes arrive.
    issueReadyFor = ""; issueError = ""; notesReadyFor = ""
    loadIssue()
    loadNotes()
  }

  function loadIssue() {
    if (key === "") return
    if (issueProcess.running) { issueQueued = true; return }
    issueFor = key
    issueProcess.command = [host.helperPath(), "issue", "--project", host.project, "--iid", String(issue.iid)]
    issueProcess.running = true
  }
  function issueDone(raw) {
    if (issueFor !== key) return  // answer for an issue we already left
    var data = host.parse(raw)
    issueError = data.state === "ready" ? "" : String(data.message || "Request failed.")
    if (data.state === "ready" && data.issue) issue = data.issue
    issueReadyFor = key
  }

  function loadNotes() {
    if (key === "") return
    if (notesProcess.running) { reloadQueued = true; return }
    notesFor = key
    notesLoading = true
    notesProcess.command = [host.helperPath(), "notes", "--project", host.project, "--iid", String(issue.iid)]
    notesProcess.running = true
  }
  function notesDone(raw) {
    notesLoading = false
    if (notesFor !== key) return  // answer for an issue we already left
    notesReadyFor = key
    var data = host.parse(raw)
    notesError = data.state === "ready" ? "" : String(data.message || "Could not load comments.")
    if (data.state === "ready") { notes = data.notes || []; more = !!data.more; notesAt = new Date().toISOString() }
  }

  function editLabels() {
    if (!issueReady || issueError !== "" || !host.writable) return
    editing = true
    labelError = ""
    loadLabels()
    if (labelsState === "ready") labelFilter.forceActiveFocus()  // else once they load (labelsDone)
  }
  function closeEditor() { editing = false; labelFilter.text = ""; labelError = "" }
  function doneEditing() {
    closeEditor()
    host.showView("issue")  // hand the keys back to the panel, as Esc in the comment box does
  }
  // The project's labels, reused across its issues for 5 minutes (BulkBar keeps its own).
  function loadLabels() {
    if (labelsFor === host.project && labelsState === "ready" && Date.now() - labelsAt < 300000) return
    if (labelsProcess.running) return
    labelsFor = host.project
    labelsState = "loading"
    labelsProcess.command = [host.helperPath(), "labels", "--project", host.project]
    labelsProcess.running = true
  }
  function labelsDone(raw) {
    if (labelsFor !== host.project) { labelsState = ""; return }
    var data = host.parse(raw)
    labelsState = data.state === "ready" ? "ready" : "error"
    labelsError = data.state === "ready" ? "" : String(data.message || "Could not load labels.")
    if (data.state === "ready") { allLabels = data.labels || []; fetchedStatus = data.status || []; labelsAt = Date.now() }
    if (labelsState === "ready" && editing) labelFilter.forceActiveFocus()
  }
  // op: "add" or "remove"; one change at a time, never a status label.
  function relabel(op, name) {
    if (labelBusy !== "" || !issueReady || Logic.has(status, name)) return
    labelBusy = name
    relabelFor = key
    labelError = ""
    relabelProcess.command = [host.helperPath(), "relabel", "--project", host.project, "--iid", String(issue.iid), op === "add" ? "--add" : "--remove", name]
    relabelProcess.running = true
  }
  function relabelDone(raw) {
    labelBusy = ""
    if (relabelFor !== key) return
    var data = host.parse(raw)
    if (data.state !== "ready") { labelError = String(data.message || "Label change failed."); host.feed.noteRefused(host.project, data.message); loadIssue(); return }
    var next = Object.assign({}, issue)
    next.labels = data.labels || []
    issue = next
    host.refresh()  // the card on the board
  }

  function askClose() {
    if (stateBusy !== "" || !issueReady || issueError !== "") return
    stateError = ""
    confirming = true
  }
  // op: "close" or "reopen". Only the issue's state changes; labels stay.
  function setState(op) {
    if (stateBusy !== "" || !issueReady || issueError !== "") return
    confirming = false
    stateBusy = op
    stateFor = key
    stateError = ""
    stateProcess.command = [host.helperPath(), op, "--project", host.project, "--iid", String(issue.iid)]
    stateProcess.running = true
  }
  function stateDone(raw) {
    stateBusy = ""
    if (stateFor !== key) return
    var data = host.parse(raw)
    if (data.state !== "ready") { stateError = String(data.message || "Request failed."); host.feed.noteRefused(host.project, data.message); loadIssue(); return }
    var next = Object.assign({}, issue)
    next.state = data.issueState
    if (Array.isArray(data.labels)) next.labels = data.labels
    issue = next
    host.refresh()  // the card moves to or from Closed
  }

  function focusBox() { box.forceActiveFocus() }  // no-op while the box is disabled
  // Keys (Board.qml): x closes after the confirm, or reopens; Enter and Escape answer the confirm.
  function toggleState() {
    if (!host.writable) return  // view-only here (AccessHint.qml)
    if (issue.state === "closed") setState("reopen")
    else askClose()
  }
  function post() {
    if (posting || !loaded || box.text.trim() === "" || Logic.quickAction(box.text)) return
    posting = true
    postFor = key
    postError = ""
    commentProcess.body = box.text
    commentProcess.stdinEnabled = true
    commentProcess.command = [host.helperPath(), "comment", "--project", host.project, "--iid", String(issue.iid)]
    commentProcess.running = true
  }
  function postDone(raw) {
    posting = false
    if (postFor !== key) return
    var data = host.parse(raw)
    if (data.state === "timeout") loadNotes()  // it may have been posted: the reload shows whether
    if (data.state === "commands") { loadIssue(); loadNotes(); host.refresh() }  // GitLab ran it as quick actions
    if (data.state !== "ready") { postError = String(data.message || "Comment failed."); return }
    box.text = ""
    loadNotes()
  }

  Process {
    id: issueProcess
    onExited: if (view.issueQueued) { view.issueQueued = false; Qt.callLater(view.loadIssue) }
    stdout: StdioCollector { waitForEnd: true; onStreamFinished: view.issueDone(text) }
  }
  Process {
    id: notesProcess
    onExited: if (view.reloadQueued) { view.reloadQueued = false; Qt.callLater(view.loadNotes) }
    stdout: StdioCollector { waitForEnd: true; onStreamFinished: view.notesDone(text) }
  }
  Process {
    id: labelsProcess
    stdout: StdioCollector { waitForEnd: true; onStreamFinished: view.labelsDone(text) }
  }
  Process {
    id: relabelProcess
    stdout: StdioCollector { waitForEnd: true; onStreamFinished: view.relabelDone(text) }
  }
  Process {
    id: stateProcess
    stdout: StdioCollector { waitForEnd: true; onStreamFinished: view.stateDone(text) }
  }
  // The text goes in on stdin, then stdin closes so board-fetch sees the end.
  Process {
    id: commentProcess
    property string body: ""
    onStarted: { write(body); body = ""; stdinEnabled = false }
    stdout: StdioCollector { waitForEnd: true; onStreamFinished: view.postDone(text) }
  }

  implicitHeight: top.implicitHeight + Style.space(8) + content.implicitHeight

  // Fixed top row, right under the gear: only the issue below it scrolls.
  Row {
    id: top
    anchors.right: parent.right
    spacing: Style.space(8)
    Pill {
      anchors.verticalCenter: parent.verticalCenter
      visible: !!view.issue.url
      label: "Open in browser ↗"; clickable: true
      onClicked: view.host.openUrl(view.issue.url)
      HoverHandler { id: openHover }
      IconTip { host: view.host; shown: openHover.hovered; text: "Open in browser (o)" }
    }
    GlyphButton { host: view.host; glyph: "\uf00d"; tip: "Back to the board (Esc)"; onClicked: view.host.back() }
  }

  Flickable {
    anchors { top: top.bottom; topMargin: Style.space(8); left: parent.left; right: parent.right; bottom: parent.bottom }
    contentWidth: width; contentHeight: content.implicitHeight
    clip: true; boundsBehavior: Flickable.StopAtBounds
    ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

    Column {
      id: content
      width: parent.width - Style.space(8)
      spacing: Style.space(8)

      BoardText {
        width: parent.width; wrapMode: Text.Wrap
        textFormat: Text.StyledText
        text: "<font color='" + view.host.dim + "'>#" + (view.issue.iid || "") + "</font>&nbsp; " + Logic.escaped(view.issue.title || "")
        font { pixelSize: Style.font.title; bold: true }
      }

      // Loading: a short accent bar sliding under the title until the issue
      // and its comments are in (the gate that unlocks the comment box). Its
      // row stays when it hides, so nothing moves.
      Item {
        width: parent.width; height: Style.space(2)
        clip: true
        Rectangle { anchors.fill: parent; visible: loadingBar.visible; color: view.host.faint }
        Rectangle {
          id: loadingBar
          visible: !view.loaded
          width: parent.width / 4; height: parent.height; radius: height / 2
          color: view.host.accent
          NumberAnimation on x { running: loadingBar.visible; loops: Animation.Infinite; from: -loadingBar.width; to: loadingBar.parent.width; duration: 1100; easing.type: Easing.InOutQuad }
        }
      }

      // One row: the state, the labels, then Edit labels as an accent text
      // action (Done editing while the editor is open); Close or Reopen issue
      // as a quiet text action at its right. Neither moves when the editor or
      // the close question opens below.
      Item {
        id: labelRow
        width: parent.width
        implicitHeight: labelFlow.implicitHeight
        Flow {
          id: labelFlow
          width: parent.width - (stateAction.visible ? stateAction.implicitWidth + Style.space(12) : 0)
          spacing: Style.space(4)
          Pill {
            id: statePill
            visible: !!view.issue.state
            label: view.issue.state === "closed" ? "Closed" : "Open"
            textColor: view.issue.state === "closed" ? view.host.dim : view.host.accent
            border.color: textColor
          }
          Repeater {
            model: view.issue.labels || []
            // While editing, a label that is not a status label shows × and removes on click.
            delegate: LabelChip {
              id: chip
              required property var modelData
              readonly property bool removable: view.editing && !Logic.has(view.status, name)
              host: view.host; colors: view.colors; name: String(modelData)
              label: name + (removable ? "  \u00d7" : "")
              clickable: removable && view.labelBusy === ""
              // While editing, status labels fade: they are not editable here.
              opacity: view.labelBusy === name || (view.editing && !removable) ? 0.5 : 1
              onClicked: view.relabel("remove", name)
            }
          }
          BoardText {
            id: editAction
            visible: view.issueReady && view.issueError === "" && view.host.writable
            height: Math.max(implicitHeight, statePill.height)
            verticalAlignment: Text.AlignVCenter
            leftPadding: Style.space(4)
            // Font Awesome pencil / check (Nerd Font)
            text: view.editing ? "\uf00c  Done editing" : "\uf040  Edit labels"
            color: view.host.accent
            font.pixelSize: Style.font.bodySmall
            MouseArea { id: editMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: view.editing ? view.doneEditing() : view.editLabels() }
            IconTip { host: view.host; shown: editMouse.containsMouse; text: view.editing ? "Done editing (Esc)" : "Edit labels (e)" }
          }
        }
        BoardText {
          id: stateAction
          anchors.right: parent.right
          height: Math.max(implicitHeight, statePill.height)
          verticalAlignment: Text.AlignVCenter
          visible: view.issueReady && view.issueError === "" && view.host.writable
          enabled: view.stateBusy === ""
          text: view.stateBusy === "close" ? "Closing…" : view.stateBusy === "reopen" ? "Reopening…"
            : view.issue.state === "closed" ? "Reopen issue" : "Close issue"
          color: stateMouse.containsMouse && enabled ? view.host.foreground : view.host.dim
          font.pixelSize: Style.font.bodySmall
          MouseArea { id: stateMouse; anchors.fill: parent; enabled: parent.enabled; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: view.toggleState() }
          IconTip { host: view.host; shown: stateMouse.containsMouse; text: (view.issue.state === "closed" ? "Reopen issue" : "Close issue") + " (x)" }
        }
      }

      // Close asks first: what happens, which status label stays, Close / Cancel.
      Rectangle {
        id: confirmBox
        visible: view.confirming
        width: parent.width
        implicitHeight: confirmColumn.implicitHeight + Style.space(20)
        color: "transparent"
        border { width: 1; color: view.host.faint }
        Column {
          id: confirmColumn
          anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter; margins: Style.space(10) }
          spacing: Style.space(8)
          BoardText {
            width: parent.width; wrapMode: Text.Wrap
            text: "Close #" + (view.issue.iid || "") + "? This closes it on GitLab."
            font.bold: true
          }
          BoardText {
            width: parent.width; wrapMode: Text.Wrap
            visible: view.statusOn.length > 0
            text: "Its labels stay as they are, " + view.statusOn.join(", ") + " included."
            color: view.host.dim; font.pixelSize: Style.font.bodySmall
          }
          Row {
            spacing: Style.space(8)
            ActionButton { host: view.host; small: true; main: true; label: "Close"; onClicked: view.setState("close") }
            ActionButton { host: view.host; small: true; label: "Cancel"; onClicked: view.confirming = false }
          }
        }
      }
      BoardText {
        width: parent.width; wrapMode: Text.Wrap
        visible: view.stateError !== ""
        text: view.stateError
        color: view.host.urgent
        font.pixelSize: Style.font.bodySmall
      }

      // The label editor (IssueLabels.qml).
      IssueLabels { id: labelEditor; owner: view; width: parent.width }

      Column {
        width: parent.width; spacing: Style.space(2)
        BoardText { width: parent.width; elide: Text.ElideRight; text: Logic.byline(view.issue, new Date().toISOString()); color: view.host.dim; font.pixelSize: Style.font.bodySmall }
        BoardText { width: parent.width; wrapMode: Text.Wrap; visible: text !== ""; text: Logic.people(view.issue); color: view.host.dim; font.pixelSize: Style.font.bodySmall }
      }

      Rectangle { width: parent.width; height: 1; color: view.host.faint }

      BoardText {
        width: parent.width; wrapMode: Text.Wrap
        visible: !view.issueReady || view.issueError !== "" || !view.issue.description
        text: !view.issueReady ? "Loading…" : (view.issueError || "No description.")
        color: view.host.dim; font.italic: true
      }

      FontMetrics { id: metrics; font: description.font }
      Text {
        id: description
        width: parent.width; wrapMode: Text.Wrap
        visible: view.issueReady && !!view.issue.description
        textFormat: Text.RichText
        text: visible ? view.css + Logic.markdown(view.issue.description, function(t) { return metrics.advanceWidth(t) }, function(px) { return Style.space(px) }) : ""
        color: view.host.foreground
        linkColor: view.host.accent
        font { family: Style.font.family; pixelSize: Style.font.bodySmall }
        onLinkActivated: function(link) { var url = Logic.linkUrl(link, view.issue.url); if (url) view.host.openUrl(url) }
        HoverHandler { id: linkHover; cursorShape: parent.hoveredLink !== "" ? Qt.PointingHandCursor : Qt.ArrowCursor }
        // Where a link really goes, at the pointer: its text can say otherwise.
        PanelToolTip {
          x: linkHover.point.position.x; y: linkHover.point.position.y + Style.space(16)
          visible: description.hoveredLink !== ""
          text: Logic.linkUrl(description.hoveredLink, view.issue.url) || "Only https links open."
        }
      }
      Pill {
        visible: description.visible && String(view.issue.description).length > Logic.descriptionLimit
        label: "Truncated · Open in browser for the rest ↗"; clickable: true
        textColor: view.host.accent; border.color: view.host.accent
        onClicked: view.host.openUrl(view.issue.url)
      }

      IssueComments { id: comments; owner: view; width: parent.width }
    }
  }
}
