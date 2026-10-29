import QtQuick
import QtQuick.Controls
import Quickshell.Io
import qs.Commons
import qs.Ui
import "Logic.js" as Logic

// One issue: title, state, labels, a one-line byline, the description as
// Markdown, then its comments and a box to add one. ✕ (or Esc) returns to the
// board. The issue and its comments load through `board-fetch issue` and
// `board-fetch notes` (GET); Post runs `board-fetch comment` with the text on stdin.
// Edit labels lists the project's labels (`board-fetch labels`, GET) and adds or
// removes one at a time (`board-fetch relabel`). Status labels (the board's
// lists) are never offered: they change only by dragging the card.
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
  // Label editor: open only on request; the label list loads when it opens.
  property bool editing: false
  property string labelsFor: ""
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
    if (!issueReady || issueError !== "") return
    editing = true
    labelError = ""
    loadLabels()
    labelFilter.forceActiveFocus()
  }
  function closeEditor() { editing = false; labelFilter.text = ""; labelError = "" }
  function doneEditing() {
    closeEditor()
    host.showView("issue")  // hand the keys back to the panel, as Esc in the comment box does
  }
  function loadLabels() {
    if (labelsProcess.running) return
    labelsFor = key
    labelsState = "loading"
    labelsProcess.command = [host.helperPath(), "labels", "--project", host.project]
    labelsProcess.running = true
  }
  function labelsDone(raw) {
    if (labelsFor !== key) { labelsState = ""; return }
    var data = host.parse(raw)
    labelsState = data.state === "ready" ? "ready" : "error"
    labelsError = data.state === "ready" ? "" : String(data.message || "Could not load labels.")
    if (data.state === "ready") { allLabels = data.labels || []; fetchedStatus = data.status || [] }
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
    if (data.state !== "ready") { labelError = String(data.message || "Label change failed."); loadIssue(); return }
    var next = Object.assign({}, issue)
    next.labels = data.labels || []
    issue = next
    host.refresh()  // the card on the board
  }

  function focusBox() { box.forceActiveFocus() }  // no-op while the box is disabled
  function post() {
    if (posting || !loaded || box.text.trim() === "") return
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
    }
    GlyphButton { host: view.host; glyph: "\uf00d"; onClicked: view.host.back() }
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

      Flow {
        width: parent.width; spacing: Style.space(4)
        Pill {
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
      }

      // A text action, not a pill, so it never reads as a label.
      BoardText {
        id: editAction
        visible: !view.editing && view.issueReady && view.issueError === ""
        text: "\uf040  Edit labels"  // Font Awesome pencil (Nerd Font)
        color: view.host.accent
        font.pixelSize: Style.font.bodySmall
        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: view.editLabels() }
      }

      // The label editor: a filter with Done, then the labels the issue could take.
      Column {
        id: editor
        visible: view.editing
        width: parent.width; spacing: Style.space(6)
        Row {
          spacing: Style.space(8)
          TextField {
            id: labelFilter
            width: Math.min(editor.width - doneButton.width - parent.spacing, Style.space(280))
            foreground: view.host.foreground
            placeholderText: "Filter labels"
            onAccepted: if (view.addable.length > 0) view.relabel("add", view.addable[0].name)
            Keys.onEscapePressed: view.doneEditing()
          }
          ActionButton {
            id: doneButton
            host: view.host; small: true
            height: labelFilter.height
            label: "Done"
            onClicked: view.doneEditing()
          }
        }
        Flow {
          width: parent.width; spacing: Style.space(4)
          visible: view.addable.length > 0
          Repeater {
            model: view.addable.slice(0, view.addableShown)
            delegate: LabelChip {
              required property var modelData
              host: view.host; colors: view.colors; name: String(modelData.name)
              label: "+ " + name
              clickable: view.labelBusy === ""
              opacity: view.labelBusy === "" || view.labelBusy === name ? 1 : 0.5
              onClicked: view.relabel("add", name)
            }
          }
        }
        BoardText {
          id: labelStatus
          width: parent.width; wrapMode: Text.Wrap
          visible: text !== ""
          readonly property bool bad: view.labelError !== "" || view.labelsState === "error"
          text: view.labelError !== "" ? view.labelError
            : view.labelsState === "error" ? view.labelsError
            : view.labelBusy !== "" ? "Saving " + view.labelBusy + "…"
            : view.labelsState === "loading" ? "Loading labels…"
            : view.labelsState !== "ready" ? ""
            : view.addable.length > view.addableShown ? (view.addable.length - view.addableShown) + " more: filter to find them."
            : view.addable.length === 0 ? (labelFilter.text.trim() !== "" ? "No label matches." : "No other labels to add.")
            : ""
          color: bad ? view.host.urgent : view.host.dim
          font.pixelSize: Style.font.bodySmall
        }
        BoardText {
          width: parent.width; wrapMode: Text.Wrap
          text: "Board list labels change only by dragging the card."
          color: view.host.dim; font.pixelSize: Style.font.caption
        }
      }

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

      Rectangle { width: parent.width; height: 1; color: view.host.faint }

      Row {
        spacing: Style.space(6)
        BoardText {
          text: "Comments" + (view.notes.length > 0 ? " · " + view.notes.length : "")
          color: view.host.dim
          font { pixelSize: Style.font.bodySmall; bold: true }
        }
        // Same spin as the header's refresh icon (Board.qml), while comments load.
        BoardText {
          visible: view.notesLoading
          text: "\uf021"
          color: view.host.accent
          font.pixelSize: Style.font.bodySmall
          RotationAnimation on rotation { running: view.notesLoading; alwaysRunToEnd: true; loops: Animation.Infinite; from: 0; to: 360; duration: 900 }
        }
      }
      BoardText {
        width: parent.width; wrapMode: Text.Wrap
        visible: text !== ""
        text: view.notesError !== "" ? view.notesError
          : view.notesLoading && view.notes.length === 0 ? "Loading comments…"
          : view.notes.length === 0 ? "No comments yet."
          : view.more ? "Showing the latest 100 notes. Older ones are on GitLab." : ""
        color: view.notesError !== "" ? view.host.urgent : view.host.dim
        font.italic: true
      }

      Repeater {
        model: view.notes
        delegate: Row {
          id: note
          required property var modelData
          width: parent.width
          spacing: Style.space(8)
          Avatar { host: view.host; person: note.modelData.author || ({}) }
          Column {
            width: note.width - Style.space(18) - note.spacing
            spacing: Style.space(2)
            BoardText {
              textFormat: Text.StyledText
              text: Logic.escaped((note.modelData.author || {}).username || "?")
                + "&nbsp; <font color='" + view.host.dim + "'>" + Logic.age(note.modelData.createdAt, view.notesAt) + "</font>"
              font { pixelSize: Style.font.bodySmall; bold: true }
            }
            BoardText {
              width: parent.width; wrapMode: Text.WrapAtWordBoundaryOrAnywhere
              text: String(note.modelData.body || "")
              font.pixelSize: Style.font.bodySmall
            }
          }
        }
      }

      TextArea {
        id: box
        width: parent.width
        enabled: view.loaded && !view.posting
        wrapMode: TextEdit.Wrap
        placeholderText: view.loaded ? "Write a comment…  (Ctrl+Enter to post)" : "Loading…"
        placeholderTextColor: view.host.dim
        color: view.host.foreground
        selectionColor: view.host.accent
        selectedTextColor: view.host.background
        font { family: Style.font.family; pixelSize: Style.font.bodySmall }
        padding: Style.space(8)
        background: Rectangle {
          implicitHeight: Style.space(64)
          radius: Style.space(6)
          color: "transparent"
          border { width: 1; color: box.activeFocus ? view.host.accent : view.host.faint }
        }
        Keys.onPressed: function(event) {
          if ((event.key === Qt.Key_Return || event.key === Qt.Key_Enter) && (event.modifiers & Qt.ControlModifier)) {
            view.post(); event.accepted = true
          } else if (event.key === Qt.Key_Escape) {
            view.host.showView("issue"); event.accepted = true  // hand the keys back to the panel
          }
        }
      }

      Item {
        width: parent.width
        implicitHeight: Math.max(postButton.implicitHeight, postStatus.implicitHeight)
        BoardText {
          id: postStatus
          anchors { left: parent.left; right: postButton.left; rightMargin: Style.space(8); verticalCenter: parent.verticalCenter }
          wrapMode: Text.Wrap
          text: view.postError !== "" ? view.postError : "Posts as you on GitLab."
          color: view.postError !== "" ? view.host.urgent : view.host.dim
          font.pixelSize: Style.font.caption
        }
        ActionButton {
          id: postButton
          anchors.right: parent.right
          host: view.host; small: true; main: true
          enabled: view.loaded && !view.posting && box.text.trim() !== ""
          label: view.posting ? "Posting…" : "Post"
          onClicked: view.post()
        }
      }
    }
  }
}
