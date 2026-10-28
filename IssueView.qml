import QtQuick
import QtQuick.Controls
import Quickshell.Io
import qs.Commons

// One issue: title, state, labels, a one-line byline, the description as
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
  // The comment box opens only once the issue and its comments have arrived.
  property string notesReadyFor: ""
  readonly property bool loaded: key !== "" && !host.issueLoading && notesReadyFor === key

  // "o_devvy · created 3h ago · updated 5m ago"; card rows (shown while the
  // issue loads) have no author or updatedAt yet, so those parts come later.
  function byline(i) {
    var now = new Date().toISOString()
    var created = host.age(i.createdAt, now), updated = host.age(i.updatedAt, now)
    return [i.author || "", created ? "created " + created + " ago" : "", updated ? "updated " + updated + " ago" : ""]
      .filter(function(part) { return part !== "" }).join(" · ")
  }
  function people(i) {
    var names = (i.assignees || []).map(function(a) { return a.username || a })  // card rows carry objects
    return [names.length ? "assigned " + names.join(", ") : "", i.milestone ? "milestone " + i.milestone : ""]
      .filter(function(part) { return part !== "" }).join(" · ")
  }

  // GitLab Markdown to the HTML subset Text.RichText draws, so headings,
  // spacing, bullets and code can be styled (Text.MarkdownText can't be).
  // All text is escaped first: raw HTML in the issue shows as text, and
  // images become links, so nothing is loaded from the network.
  readonly property string css: "<style>"
    + "p, pre { line-height: 130%; margin-top: 0; margin-bottom: " + Style.space(6) + "px }"  // Qt's default is 12px above and below
    + ".h1, .h2, .h3 { font-weight: bold; color: " + host.accent + "; margin-top: " + Style.space(14) + "px; margin-bottom: " + Style.space(2) + "px }"
    + ".h1, .h2 { font-size: " + (Style.font.bodySmall + 2) + "px } .h3 { font-size: " + (Style.font.bodySmall + 1) + "px }"
    + ".li { margin-bottom: " + Style.space(2) + "px } .quote { color: " + host.dim + " }"
    + "code, pre { background-color: " + host.faint + " }"
    + "table { border-collapse: collapse; border-color: " + host.faint + "; margin-bottom: " + Style.space(6) + "px }</style>"
  function inline(text) {
    var spans = []
    return host.escaped(text)
      .replace(/`([^`]+)`/g, function(m, c) { spans.push(c); return "\x01" + (spans.length - 1) + "\x01" })
      .replace(/!?\[([^\]]*)\]\(([^)\s"]+)[^)]*\)/g, function(m, t, url) { return "<a href=\"" + url + "\">" + (t || url) + "</a>" })
      .replace(/(^|[\s(])(https?:\/\/[^\s()"]+)/g, "$1<a href=\"$2\">$2</a>")
      .replace(/\*\*(.+?)\*\*|__(.+?)__/g, "<b>$1$2</b>")
      .replace(/(^|\W)([*_])(\S(?:.*?\S)?)\2(?=\W|$)/g, "$1<i>$3</i>")
      .replace(/~~(.+?)~~/g, "<s>$1</s>")
      .replace(/\x01(\d+)\x01/g, function(m, i) { return "<code>&nbsp;" + spans[i] + "&nbsp;</code>" })
  }
  function html(md) {
    var out = [], block = [], open = "<p>", rows = [], code = null
    function flush() {
      if (block.length) out.push(open + block.map(inline).join("<br>") + "</p>")
      if (rows.length) out.push("<table border='1' cellspacing='0' cellpadding='" + Style.space(3) + "'>" + rows.join("") + "</table>")
      block = []; rows = []; open = "<p>"
    }
    String(md).replace(/\r/g, "").split("\n").forEach(function(line) {
      var m
      if (code !== null) {
        if (/^\s*(```|~~~)/.test(line)) { out.push("<pre>" + code.join("\n") + "</pre>"); code = null }
        else code.push(host.escaped(line))
      } else if (/^\s*(```|~~~)/.test(line)) { flush(); code = [] }
      else if ((m = /^(#{1,6})\s+(.*?)[\s#]*$/.exec(line))) { flush(); out.push("<p class='h" + Math.min(m[1].length, 3) + "'>" + inline(m[2]) + "</p>") }
      else if (/^\s*([-*_])(\s*\1){2,}\s*$/.test(line)) { flush(); out.push("<hr>") }
      else if ((m = /^(\s*)([-*+]|\d+[.)])\s+(\[[ xX]\]\s+)?(.*)$/.exec(line))) {
        // Hanging indent: wrapped lines line up with the text, not the bullet.
        flush()
        var mark = (m[3] ? (/[xX]/.test(m[3]) ? "☑" : "☐") : /\d/.test(m[2]) ? m[2] : "•") + " "
        var level = Math.floor(m[1].replace(/\t/g, "  ").length / 2), hang = metrics.advanceWidth(mark)
        open = "<p class='li' style='margin-left: " + Math.round(level * metrics.advanceWidth("  ") + hang) + "px; text-indent: -" + Math.round(hang) + "px'>"
        block = [mark + m[4]]
      } else if ((m = /^\s*\|(.*)\|\s*$/.exec(line))) {
        if (block.length) flush()
        if (!/^[\s|:-]+$/.test(m[1])) {
          var tag = rows.length ? "td" : "th"
          rows.push("<tr>" + m[1].split("|").map(function(c) { return "<" + tag + ">" + inline(c.trim()) + "</" + tag + ">" }).join("") + "</tr>")
        }
      } else if ((m = /^\s*>\s?(.*)$/.exec(line))) {
        if (open.indexOf("quote") === -1) { flush(); open = "<p class='quote' style='margin-left: " + Style.space(10) + "px'>" }
        block.push(m[1])
      } else if (line.trim() === "") flush()
      else { if (rows.length) flush(); block.push(line.trim()) }  // GitLab keeps single line breaks
    })
    if (code !== null) out.push("<pre>" + code.join("\n") + "</pre>")
    flush()
    return css + out.join("")
  }

  onKeyChanged: {
    if (key === "") return
    if (key !== shownKey) {  // another issue: drop the last one's thread and draft
      shownKey = key
      notes = []; more = false; notesError = ""; postError = ""; box.text = ""
    }
    notesReadyFor = ""  // (re)opened: lock the box until this visit's notes arrive
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
    notesReadyFor = key
    var data = host.parse(raw)
    notesError = data.state === "ready" ? "" : String(data.message || "Could not load comments.")
    if (data.state === "ready") { notes = data.notes || []; more = !!data.more; notesAt = new Date().toISOString() }
  }

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
          delegate: LabelChip { required property var modelData; host: view.host; name: String(modelData) }
        }
      }

      Column {
        width: parent.width; spacing: Style.space(2)
        BoardText { id: byline; width: parent.width; elide: Text.ElideRight; text: view.byline(view.issue); color: view.host.dim; font.pixelSize: Style.font.bodySmall }
        BoardText { id: people; width: parent.width; wrapMode: Text.Wrap; visible: text !== ""; text: view.people(view.issue); color: view.host.dim; font.pixelSize: Style.font.bodySmall }
      }

      Rectangle { width: parent.width; height: 1; color: view.host.faint }

      BoardText {
        width: parent.width; wrapMode: Text.Wrap
        visible: view.host.issueLoading || view.host.issueError !== "" || !view.issue.description
        text: view.host.issueLoading ? "Loading…" : (view.host.issueError || "No description.")
        color: view.host.dim; font.italic: true
      }

      FontMetrics { id: metrics; font: description.font }
      Text {
        id: description
        width: parent.width; wrapMode: Text.Wrap
        visible: !view.host.issueLoading && !!view.issue.description
        textFormat: Text.RichText
        text: visible ? view.html(view.issue.description) : ""
        color: view.host.foreground
        linkColor: view.host.accent
        font { family: Style.font.family; pixelSize: Style.font.bodySmall }
        onLinkActivated: function(link) { view.host.openLink(link) }
        HoverHandler { cursorShape: parent.hoveredLink !== "" ? Qt.PointingHandCursor : Qt.ArrowCursor }
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
          id: notesSpinner
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
        Pill {
          id: postButton
          anchors.right: parent.right
          readonly property bool ready: view.loaded && !view.posting && box.text.trim() !== ""
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
