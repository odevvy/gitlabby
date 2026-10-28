import QtQuick
import QtQuick.Controls
import Quickshell.Io
import qs.Commons

// One issue: title, state, labels, people, dates, the description as
// Markdown, then its comments and a box to add one. Back (or Esc) returns to
// the board. Comments load through `board-fetch notes` (GET); Post runs
// `board-fetch comment` with the text on stdin.
Item {
  id: view
  required property var host
  readonly property var issue: host.issue || ({})
  // The issue on screen ("" when hidden); its comments reload whenever it opens.
  readonly property string key: visible && issue.iid ? host.project + "#" + issue.iid : ""
  property string shownKey: ""
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
  readonly property bool typing: box.activeFocus

  function when(iso) {
    return iso ? new Date(iso).toLocaleString(Qt.locale(), "yyyy-MM-dd HH:mm") : "—"
  }

  onKeyChanged: {
    if (key === "") return
    if (key !== shownKey) {  // another issue: drop the last one's thread and draft
      shownKey = key
      notes = []; more = false; notesError = ""; postError = ""; box.text = ""
    }
    loadNotes()
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
    var data = host.parse(raw)
    notesError = data.state === "ready" ? "" : String(data.message || "Could not load comments.")
    if (data.state === "ready") { notes = data.notes || []; more = !!data.more; notesAt = new Date().toISOString() }
  }

  function post() {
    if (posting || key === "" || box.text.trim() === "") return
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
    if (data.state !== "ready") { postError = String(data.message || "Comment failed."); return }
    box.text = ""
    loadNotes()
  }

  Process {
    id: notesProcess
    onExited: if (view.reloadQueued) { view.reloadQueued = false; Qt.callLater(view.loadNotes) }
    stdout: StdioCollector { waitForEnd: true; onStreamFinished: view.notesDone(text) }
  }
  // The text goes in on stdin, then stdin closes so board-fetch sees the end.
  Process {
    id: commentProcess
    property string body: ""
    onStarted: { write(body); body = ""; stdinEnabled = false }
    stdout: StdioCollector { waitForEnd: true; onStreamFinished: view.postDone(text) }
  }

  implicitHeight: content.implicitHeight

  Flickable {
    anchors.fill: parent
    contentWidth: width; contentHeight: content.implicitHeight
    clip: true; boundsBehavior: Flickable.StopAtBounds
    ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

    Column {
      id: content
      width: parent.width - Style.space(8)
      spacing: Style.space(8)

      Item {
        width: parent.width
        implicitHeight: back.implicitHeight
        Pill { id: back; label: "‹ Back"; clickable: true; textColor: view.host.foreground; onClicked: view.host.back() }
        Pill {
          anchors.right: parent.right
          visible: !!view.issue.url
          label: "Open in browser ↗"; clickable: true
          onClicked: view.host.openUrl(view.issue.url)
        }
      }

      BoardText {
        width: parent.width; wrapMode: Text.Wrap
        textFormat: Text.StyledText
        text: "<font color='" + view.host.dim + "'>#" + (view.issue.iid || "") + "</font>&nbsp; " + view.host.escaped(view.issue.title || "")
        font { pixelSize: Style.font.title; bold: true }
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
          delegate: LabelChip { required property var modelData; host: view.host; name: String(modelData) }
        }
      }

      Grid {
        columns: 2; columnSpacing: Style.space(12); rowSpacing: Style.space(3)
        Repeater {
          model: [
            "Assignees", (view.issue.assignees || []).map(function(a) { return a.username || a }).join(", ") || "—",  // card rows carry objects
            "Author", view.issue.author || "—",
            "Milestone", view.issue.milestone || "—",
            "Created", view.when(view.issue.createdAt),
            "Updated", view.when(view.issue.updatedAt)
          ]
          delegate: BoardText {
            required property var modelData
            required property int index
            text: String(modelData)
            color: index % 2 === 0 ? view.host.dim : view.host.foreground
            font.pixelSize: Style.font.bodySmall
          }
        }
      }

      Rectangle { width: parent.width; height: 1; color: view.host.faint }

      BoardText {
        width: parent.width; wrapMode: Text.Wrap
        visible: view.host.issueLoading || view.host.issueError !== "" || !view.issue.description
        text: view.host.issueLoading ? "Loading…" : (view.host.issueError || "No description.")
        color: view.host.dim; font.italic: true
      }

      Text {
        width: parent.width; wrapMode: Text.Wrap
        visible: !view.host.issueLoading && !!view.issue.description
        textFormat: Text.MarkdownText
        text: view.issue.description || ""
        color: view.host.foreground
        linkColor: view.host.accent
        font { family: Style.font.family; pixelSize: Style.font.bodySmall }
        onLinkActivated: function(link) { view.host.openLink(link) }
        HoverHandler { cursorShape: parent.hoveredLink !== "" ? Qt.PointingHandCursor : Qt.ArrowCursor }
      }

      Rectangle { width: parent.width; height: 1; color: view.host.faint }

      BoardText {
        text: "Comments" + (view.notes.length > 0 ? " · " + view.notes.length : "")
        color: view.host.dim
        font { pixelSize: Style.font.bodySmall; bold: true }
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
              text: view.host.escaped((note.modelData.author || {}).username || "?")
                + "&nbsp; <font color='" + view.host.dim + "'>" + view.host.age(note.modelData.createdAt, view.notesAt) + "</font>"
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
        enabled: !view.posting
        wrapMode: TextEdit.Wrap
        placeholderText: "Write a comment…  (Ctrl+Enter to post)"
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
        Pill {
          id: postButton
          anchors.right: parent.right
          readonly property bool ready: !view.posting && box.text.trim() !== ""
          label: view.posting ? "Posting…" : "Post"
          clickable: ready
          opacity: ready ? 1 : 0.5
          textColor: view.host.accent
          border.color: view.host.accent
          onClicked: view.post()
        }
      }
    }
  }
}
